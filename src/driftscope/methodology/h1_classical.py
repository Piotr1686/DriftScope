"""H1 Classical Baseline — ADF, KPSS, BOCPD (Adams-MacKay 2007), Welch PSD, ACF.

Czyste funkcje na listach DrawRecord. Nie zna ingestion ani reporting.
BOCPD: Dirichlet-Multinomial conjugate, własna impl (preregistration_v1 §2).
"""
from __future__ import annotations

import warnings
from typing import Literal

import numpy as np
from scipy.signal import find_peaks, welch
from scipy.special import logsumexp
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, kpss

from driftscope.core.types import DrawRecord, TestResult

# ---------------------------------------------------------------------------
# Ekstraktory szeregów
# ---------------------------------------------------------------------------

def extract_series(
    draws: list[DrawRecord],
    kind: Literal["euron_mean", "euron_max", "main_mean", "main_std"],
) -> np.ndarray:
    """Skalarne szeregi czasowe z DrawRecord — do testów ADF/KPSS/Welch/ACF."""
    if kind == "euron_mean":
        return np.array([(d.euron_1 + d.euron_2) / 2.0 for d in draws])
    if kind == "euron_max":
        return np.array([float(max(d.euron_1, d.euron_2)) for d in draws])
    if kind == "main_mean":
        return np.array([sum(d.main_numbers) / 5.0 for d in draws])
    if kind == "main_std":
        return np.array([float(np.std(d.main_numbers)) for d in draws])
    raise ValueError(f"Nieznany kind: {kind!r}")


# ---------------------------------------------------------------------------
# ADF
# ---------------------------------------------------------------------------

def run_adf(series: np.ndarray, label: str = "") -> TestResult:
    """ADF test — H0: unit root. Odrzucenie (p < 0.05) → szereg stacjonarny."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval, nlags, nobs, crit, _ = adfuller(series, autolag="AIC")
    return TestResult(
        test_name="adf",
        series_label=label,
        statistic=float(stat),
        p_value=float(pval),
        reject_h0=bool(pval < 0.05),
        metadata={
            "n_lags": int(nlags),
            "n_obs": int(nobs),
            "critical_values": {k: float(v) for k, v in crit.items()},
            "h0": "unit root (non-stationary)",
            "reject_means": "series is stationary",
        },
    )


# ---------------------------------------------------------------------------
# KPSS
# ---------------------------------------------------------------------------

def run_kpss(series: np.ndarray, label: str = "") -> TestResult:
    """KPSS test — H0: level-stationary. Odrzucenie (p < 0.05) → niestacjonarny.

    Uwaga: p_value ograniczone do [0.01, 0.10] przez statsmodels (tabele tabel).
    Interpretacja ODWROTNA do ADF: odrzucenie = brak stacjonarności.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval, nlags, crit = kpss(series, regression="c", nlags="auto")
    return TestResult(
        test_name="kpss",
        series_label=label,
        statistic=float(stat),
        p_value=float(pval),
        reject_h0=bool(pval < 0.05),
        metadata={
            "n_lags": int(nlags),
            "critical_values": {k: float(v) for k, v in crit.items()},
            "h0": "level stationary",
            "reject_means": "non-stationary (OPPOSITE of ADF reject)",
            "note": "p_value bounded [0.01, 0.10] by statsmodels interpolation",
        },
    )


# ---------------------------------------------------------------------------
# BOCPD — Bayesian Online Change Point Detection
# ---------------------------------------------------------------------------

# Skalibrowane progi reject_h0 = 95. percentyl rozkladu max(cp_prob[warmup:]) pod
# nullem uniform-iid (FPR ~= 0.05). Wyznaczone: scripts/calibrate_bocpd_threshold.py
# (BASE_SEED=42, 200 trials, R3, hazard=0.005, alpha=0.1, warmup=N//K). Prog zalezy
# od (N, K): wieksza pula symboli = wyzszy poziom szumu w cp_prob pod nullem.
# NIEzalezny od dlugosci serii (max to wczesny transient, identyczny dla n=436/n=958).
#
# WARM-UP (preregistration_v6 §0): max(cp_prob) liczymy POMIJAJAC pierwsze
# warmup = N // K losowan. BOCPD potrzebuje "zobaczyc" alfabet — zanim pula symboli
# zostanie pokryta, KAZDE losowanie wnosi nowe symbole → sztuczny spike cp_prob
# (transient burn-in, argmax~=4-7). To artefakt, NIE change-point: na realnych danych
# pole main (negative control) mialo JEDYNY ponadprogowy peak wlasnie w idx=7 (burn-in),
# 2. peak juz 0.208. Wykluczenie warm-up daje czysty negative control (main: 0.770→0.208,
# brak reject) i nie rusza positive control euron (peaki 2014/2022 sa mid-series).
# Stary magiczny prog 0.3 (bez warm-up) dawal FPR=0.07 (euron) i FPR=0.77 (main).
_BOCPD_REJECT_THRESHOLD: dict[str, float] = {
    "euron": 0.33,  # N=12, K=2, warmup=6;  p95 null = 0.329
    "main": 0.70,   # N=50, K=5, warmup=10; p95 null = 0.699
}


def _bocpd_dirichlet(
    obs_indices_list: list[list[int]],
    n_symbols: int,
    k_per_draw: int,
    alpha: float,
    hazard: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Rdzeń BOCPD z Dirichlet-Multinomial (Adams-MacKay 2007).

    Aproksymacja: K losowań bez zwracania traktowane jako K niezależnych próbek
    z Multinomial (Dirichlet-konjugat). Błąd aproksymacji pomijalny dla K << N.

    Returns:
        cp_probs: (T,) tablica P(R_t = 0 | x_{1:t}) — prob. change-point w chwili t
        rl_map:   (T,) MAP run-length per chwila
    """
    T = len(obs_indices_list)
    log_H = np.log(hazard)
    log_1mH = np.log(1.0 - hazard)

    # log_R[r] = log P(run_length == r po t-1 krokach)
    log_R = np.array([0.0])  # P(R_0 = 0) = 1.0 na starcie

    # counts[r, i]: zliczenia symbolu i w hipotezie "aktualny run ma r obs."
    counts = np.zeros((1, n_symbols))

    cp_probs = np.zeros(T)
    rl_map = np.zeros(T, dtype=np.int64)

    for t, obs_idx in enumerate(obs_indices_list):
        n_hyp = len(log_R)

        # Mianowniki: N*α + r*K dla r = 0, 1, ..., n_hyp-1
        run_totals = np.arange(n_hyp, dtype=float) * k_per_draw
        denominators = n_symbols * alpha + run_totals  # (n_hyp,)

        # Log-predyktywne P(x_t | run_r) = Σ_{k in obs} log(α + c[r,k]) - log(denom[r])
        log_pred = np.zeros(n_hyp)
        for idx in obs_idx:
            log_pred += np.log(alpha + counts[:, idx]) - np.log(denominators)

        # --- Message passing (Adams-MacKay 2007, eq. 2) ---
        # Gdy CP: nowy run startuje od zera → predyktywne = PRIOR (counts[0] = zeros)
        # Σ_{r'} P(r_{t-1}=r') = 1 → log_q_cp nie zależy od rozkładu run-length
        log_pred_prior = log_pred[0]  # counts[0] zawsze zeros
        log_q_cp = log_H + log_pred_prior
        # Kontynuacja: r_{t-1}=r → r_t=r+1, predyktywne wg accumulated counts[r]
        log_q_cont = log_1mH + log_R + log_pred
        log_q = np.concatenate([[log_q_cp], log_q_cont])
        log_R = log_q - logsumexp(log_q)  # normalizacja posterior

        cp_probs[t] = float(np.exp(log_R[0]))
        rl_map[t] = int(np.argmax(log_R))

        # Aktualizacja counts na następny krok:
        # new[0] = 0 (nowy run bez obserwacji), new[r+1] = old[r] + obs_vec
        obs_vec = np.zeros(n_symbols)
        for idx in obs_idx:
            obs_vec[idx] += 1.0

        new_counts = np.zeros((n_hyp + 1, n_symbols))
        new_counts[1:] = counts + obs_vec
        counts = new_counts

    return cp_probs, rl_map


def run_bocpd(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    alpha: float = 0.1,
    hazard: float = 0.005,
    top_k: int = 5,
    warmup: int | None = None,
) -> TestResult:
    """BOCPD Adams-MacKay 2007 — detekcja change-pointów w rozkładzie symboli.

    Domyślnie pole 'euron' (N=12, K=2) — wrażliwe na zmiany puli 2014/2022.
    alpha=0.1: świadoma decyzja (MEMORY.md 2026-05-26) — α=1 osłabia sygnał przy
    zmianie puli; α=0.1 daje cp_prob>0.4 przy pierwszym niewidzianym symbolu.
    p_value = 1 - max(cp_prob): bayesowska posterior, nie frequentist.
    reject_h0: max(cp_prob[warmup:]) > prog per-pole skalibrowany na FPR~=0.05 pod
    nullem uniform-iid (zob. `_BOCPD_REJECT_THRESHOLD`; ważny dla alpha=0.1, hazard=0.005).

    warmup: liczba początkowych losowań pomijanych przy detekcji (preregistration_v6 §0).
    None → N // K (jeden nominalny przebieg przez pulę): pomija transient burn-in,
    w którym cp_prob sztucznie rośnie, bo pula symboli nie została jeszcze "zobaczona".
    """
    if field == "euron":
        n_symbols, k_per_draw = 12, 2
        obs_list = [[e - 1 for e in d.euronumbers] for d in draws]
    else:
        n_symbols, k_per_draw = 50, 5
        obs_list = [[m - 1 for m in d.main_numbers] for d in draws]

    cp_probs, rl_map = _bocpd_dirichlet(
        obs_list, n_symbols, k_per_draw, alpha, hazard
    )

    # Warm-up: pomijamy transient burn-in (cp_prob[:warmup]). Clamp by zostawic >=1 punkt.
    if warmup is None:
        warmup = n_symbols // k_per_draw
    warmup = max(0, min(warmup, len(cp_probs) - 1))

    # Lokalne maksima cp_probs = kandydaci na change-pointy (tylko POZA warm-up)
    # distance=5: ~5 losowan ≈ 5 tygodni EuroJackpot (piątek) — pozwala na bliskie szczyty
    peaks, _ = find_peaks(cp_probs, height=0.05, distance=5)
    peaks = peaks[peaks >= warmup]
    if len(peaks) == 0:
        peaks = np.array([warmup + int(np.argmax(cp_probs[warmup:]))])

    top_idx = peaks[np.argsort(cp_probs[peaks])[::-1]][:top_k]
    top_dates = [str(draws[i].draw_date) for i in top_idx]
    top_probs = [float(cp_probs[i]) for i in top_idx]

    max_prob = float(np.max(cp_probs[warmup:]))
    reject_threshold = _BOCPD_REJECT_THRESHOLD[field]
    return TestResult(
        test_name="bocpd_dirichlet_multinomial",
        series_label=f"{field}_counts (N={n_symbols}, K={k_per_draw}, H={hazard})",
        statistic=max_prob,
        p_value=float(1.0 - max_prob),
        reject_h0=bool(max_prob > reject_threshold),
        metadata={
            "field": field,
            "hazard": hazard,
            "alpha": alpha,
            "n_symbols": n_symbols,
            "k_per_draw": k_per_draw,
            "n_draws": len(draws),
            "warmup": warmup,
            "top_changepoint_dates": top_dates,
            "top_changepoint_probs": top_probs,
            "reject_threshold": reject_threshold,
            "note": (
                "p_value = 1 - max(cp_prob); Bayesian posterior, nie frequentist. "
                "reject_h0 gdy max(cp_prob) > prog skalibrowany na FPR~=0.05 pod nullem "
                "(per-pole; wazny dla alpha=0.1, hazard=0.005)"
            ),
        },
    )


# ---------------------------------------------------------------------------
# Welch PSD
# ---------------------------------------------------------------------------

def run_welch_test(
    series: np.ndarray,
    fs: float = 1.0,
    label: str = "",
) -> TestResult:
    """Welch PSD — eksploracja periodyczności (SNR dominującej częst.).

    Diagnostyczne — brak formalnego p-value (p_value = -1.0).
    reject_h0 = True gdy SNR dominującej częstotliwości > 5.
    """
    nperseg = min(256, max(8, len(series) // 4))
    freqs, psd = welch(series, fs=fs, nperseg=nperseg)

    # Pomijamy DC (freq=0)
    mask = freqs > 0
    freqs_ac, psd_ac = freqs[mask], psd[mask]

    peak_idx = int(np.argmax(psd_ac))
    peak_freq = float(freqs_ac[peak_idx])
    peak_power = float(psd_ac[peak_idx])
    median_power = float(np.median(psd_ac))
    snr = peak_power / (median_power + 1e-12)

    return TestResult(
        test_name="welch_psd",
        series_label=label,
        statistic=float(snr),
        p_value=-1.0,
        reject_h0=bool(snr > 5.0),
        metadata={
            "dominant_freq": peak_freq,
            "dominant_period_draws": float(1.0 / peak_freq) if peak_freq > 0 else float("inf"),
            "peak_power": peak_power,
            "median_power": median_power,
            "snr": snr,
            "nperseg": nperseg,
            "note": "p_value=-1 (exploratory); reject_h0 gdy SNR > 5",
        },
    )


# ---------------------------------------------------------------------------
# ACF / Ljung-Box
# ---------------------------------------------------------------------------

def run_acf_test(
    series: np.ndarray,
    nlags: int = 40,
    label: str = "",
) -> TestResult:
    """Ljung-Box test — H0: brak auto-korelacji (biały szum).

    Odrzucenie (p < 0.05) → auto-korelacja → potencjalna niestacjonarność.
    """
    max_lag = min(nlags, len(series) // 2 - 1)
    lags = sorted({min(10, max_lag), min(20, max_lag), max_lag})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lb_df = acorr_ljungbox(series, lags=lags, return_df=True)

    min_pval = float(lb_df["lb_pvalue"].min())
    min_lag_val = int(lb_df["lb_pvalue"].idxmin())

    return TestResult(
        test_name="ljung_box_acf",
        series_label=label,
        statistic=float(lb_df["lb_stat"].iloc[-1]),
        p_value=min_pval,
        reject_h0=bool(min_pval < 0.05),
        metadata={
            "lags_tested": lags,
            "min_pvalue_lag": min_lag_val,
            "lb_stats": lb_df["lb_stat"].tolist(),
            "lb_pvalues": lb_df["lb_pvalue"].tolist(),
            "h0": "no autocorrelation (white noise)",
        },
    )


# ---------------------------------------------------------------------------
# High-level runner
# ---------------------------------------------------------------------------

def run_all_h1(draws: list[DrawRecord]) -> list[TestResult]:
    """Uruchamia pełen zestaw H1 testów klasycznych na liście losowań.

    Wyniki (10 TestResult):
      - ADF × 2 (euron_mean, euron_max)
      - KPSS × 2
      - Welch PSD × 2
      - Ljung-Box ACF × 2
      - BOCPD Dirichlet-Multinomial × 2 (euron, main)
    """
    results: list[TestResult] = []

    for kind in ("euron_mean", "euron_max"):
        series = extract_series(draws, kind)  # type: ignore[arg-type]
        results.append(run_adf(series, label=kind))
        results.append(run_kpss(series, label=kind))
        results.append(run_welch_test(series, label=kind))
        results.append(run_acf_test(series, label=kind))

    results.append(run_bocpd(draws, field="euron"))
    results.append(run_bocpd(draws, field="main"))

    return results
