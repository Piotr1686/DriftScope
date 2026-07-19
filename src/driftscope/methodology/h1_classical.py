"""H1 Classical Baseline — ADF, KPSS, BOCPD (Adams-MacKay 2007), Welch PSD, ACF.

Pure functions over lists of DrawRecord. Knows neither ingestion nor reporting.
BOCPD: Dirichlet-Multinomial conjugate, own implementation (preregistration_v1 §2).
"""
from __future__ import annotations

import warnings
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.signal import find_peaks, welch
from scipy.special import logsumexp
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, kpss

from driftscope.core.types import DrawRecord, TestResult

# ---------------------------------------------------------------------------
# Series extractors
# ---------------------------------------------------------------------------

def extract_series(
    draws: list[DrawRecord],
    kind: Literal["euron_mean", "euron_max", "main_mean", "main_std"],
) -> npt.NDArray[np.float64]:
    """Scalar time series from DrawRecord — for the ADF/KPSS/Welch/ACF tests."""
    if kind == "euron_mean":
        return np.array([sum(d.euronumbers) / 2.0 for d in draws])
    if kind == "euron_max":
        return np.array([float(max(d.euronumbers)) for d in draws])
    if kind == "main_mean":
        return np.array([sum(d.main_numbers) / len(d.main_numbers) for d in draws])
    if kind == "main_std":
        return np.array([float(np.std(d.main_numbers)) for d in draws])
    raise ValueError(f"Unknown kind: {kind!r}")


# ---------------------------------------------------------------------------
# ADF
# ---------------------------------------------------------------------------

def run_adf(series: npt.NDArray[np.float64], label: str = "") -> TestResult:
    """ADF test — H0: unit root. Rejection (p < 0.05) → series is stationary."""
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

def run_kpss(series: npt.NDArray[np.float64], label: str = "") -> TestResult:
    """KPSS test — H0: level-stationary. Rejection (p < 0.05) → non-stationary.

    Note: p_value is bounded to [0.01, 0.10] by statsmodels (table interpolation).
    Interpretation is OPPOSITE to ADF: rejection = absence of stationarity.
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

# Calibrated reject_h0 thresholds = 95th percentile of the max(cp_prob[warmup:]) distribution
# under the uniform-iid null (FPR ~= 0.05). Derived: scripts/calibrate_bocpd_threshold.py
# (BASE_SEED=42, 200 trials, R3, hazard=0.005, alpha=0.1, warmup=N//K). The threshold depends
# on (N, K): a larger symbol pool = a higher noise level in cp_prob under the null.
# INDEPENDENT of series length (the max is an early transient, identical for n=436/n=958).
#
# WARM-UP (preregistration_v6 §0): we compute max(cp_prob) SKIPPING the first
# warmup = N // K draws. BOCPD needs to "see" the alphabet — before the symbol pool is
# covered, EVERY draw brings new symbols → an artificial cp_prob spike
# (transient burn-in, argmax~=4-7). This is an artifact, NOT a change-point: on real data the
# main field (negative control) had its ONLY above-threshold peak exactly at idx=7 (burn-in),
# the 2nd peak already 0.208. Excluding warm-up yields a clean negative control (main: 0.770→0.208,
# no reject) and does not touch the euron positive control (the 2014/2022 peaks are mid-series).
# The old magic threshold 0.3 (no warm-up) gave FPR=0.07 (euron) and FPR=0.77 (main).
_BOCPD_REJECT_THRESHOLD: dict[str, float] = {
    "euron": 0.33,  # N=12, K=2, warmup=6;  p95 null = 0.329
}
# The 'main' field: the threshold depends on a game's pool (N, K) → keyed by pool_size. Calibrated
# per game by scripts/calibrate_bocpd_threshold.py (BASE_SEED=42, 200 trials, hazard=0.005).
_MAIN_REJECT_THRESHOLD_BY_POOL: dict[int, float] = {
    50: 0.70,  # EuroJackpot N=50, K=5, warmup=10; p95 null = 0.699
    80: 0.34,  # Multi Multi N=80, K=20, warmup=4; p95 null = 0.3314 (n=2000, trials=200)
               # → round up to 0.34 (EJ convention: threshold >= p95, FPR<=0.05)
               # cross-validation n=5000/trials=200: p95=0.3314 (delta=0.0000), FPR@0.34=0.04
               # → length-invariant (burn-in transient, prereg v6 §0): the threshold holds
               #   independently of the MM series length
    # World Lottery Audit (reporting/lottery_audit.py): thresholds calibrated at the
    # COVERAGE warm-up ceil((N/k)·H_N) — NOT the default N//K, which grossly under-covers
    # the coupon-collector transient for k=5 pools (null mean max drops 0.43→0.19).
    # Callers MUST pass the matching warmup (see lottery_audit.coverage_warmup).
    69: 0.49,  # Powerball white N=69, K=5, warmup=67; p95 null = 0.4815 (n=1968, trials=200)
    75: 0.39,  # Mega Millions white N=75, K=5, warmup=74; p95 null = 0.3858 (n=2520, trials=200)
}


def _bocpd_dirichlet(
    obs_indices_list: list[list[int]],
    n_symbols: int,
    k_per_draw: int,
    alpha: float,
    hazard: float,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """BOCPD core with Dirichlet-Multinomial (Adams-MacKay 2007).

    Approximation: K draws without replacement treated as K independent samples from a
    Multinomial (Dirichlet conjugate). The approximation error is negligible for K << N.

    Returns:
        cp_probs: (T,) array P(R_t = 0 | x_{1:t}) — change-point prob. at time t
        rl_map:   (T,) MAP run-length per time step
    """
    T = len(obs_indices_list)
    log_H = np.log(hazard)
    log_1mH = np.log(1.0 - hazard)

    # log_R[r] = log P(run_length == r after t-1 steps)
    log_R = np.array([0.0])  # P(R_0 = 0) = 1.0 at start

    # counts[r, i]: count of symbol i under the hypothesis "the current run has r obs."
    counts = np.zeros((1, n_symbols))

    cp_probs = np.zeros(T)
    rl_map = np.zeros(T, dtype=np.int64)

    for t, obs_idx in enumerate(obs_indices_list):
        n_hyp = len(log_R)

        # Denominators: N*α + r*K for r = 0, 1, ..., n_hyp-1
        run_totals = np.arange(n_hyp, dtype=float) * k_per_draw
        denominators = n_symbols * alpha + run_totals  # (n_hyp,)

        # Log-predictive P(x_t | run_r) = Σ_{k in obs} log(α + c[r,k]) - log(denom[r])
        log_pred = np.zeros(n_hyp)
        for idx in obs_idx:
            log_pred += np.log(alpha + counts[:, idx]) - np.log(denominators)

        # --- Message passing (Adams-MacKay 2007, eq. 2) ---
        # On a CP: a new run starts from zero → predictive = PRIOR (counts[0] = zeros)
        # Σ_{r'} P(r_{t-1}=r') = 1 → log_q_cp does not depend on the run-length distribution
        log_pred_prior = log_pred[0]  # counts[0] is always zeros
        log_q_cp = log_H + log_pred_prior
        # Continuation: r_{t-1}=r → r_t=r+1, predictive per accumulated counts[r]
        log_q_cont = log_1mH + log_R + log_pred
        log_q = np.concatenate([[log_q_cp], log_q_cont])
        log_R = log_q - logsumexp(log_q)  # posterior normalization

        cp_probs[t] = float(np.exp(log_R[0]))
        rl_map[t] = int(np.argmax(log_R))

        # Update counts for the next step:
        # new[0] = 0 (new run with no observations), new[r+1] = old[r] + obs_vec
        obs_vec = np.zeros(n_symbols)
        for idx in obs_idx:
            obs_vec[idx] += 1.0

        new_counts = np.zeros((n_hyp + 1, n_symbols))
        new_counts[1:] = counts + obs_vec
        counts = new_counts

    return cp_probs, rl_map


def compute_bocpd_curve(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    alpha: float = 0.1,
    hazard: float = 0.005,
    warmup: int | None = None,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.int64], int, float]:
    """Full BOCPD curve + detection parameters — a pure accessor (reuse reporting/W8).

    Extracted from `run_bocpd`: maps `field → (n_symbols, K, obs_list)`, runs
    `_bocpd_dirichlet`, clamps the warm-up and reads the per-field reject threshold. ZERO
    methodological decisions beyond what `run_bocpd` did — it exposes the raw `cp_prob` curve
    (length T), which `TestResult` does not carry (only top-K in metadata).

    Returns:
        cp_probs:          (T,) P(R_t = 0 | x_{1:t}) — change-point prob. per time step
        rl_map:            (T,) MAP run-length per time step
        warmup:            number of skipped burn-in draws (clamped to [0, T-1])
        reject_threshold:  per-field reject threshold (FPR~=0.05 under the uniform-iid null)
    """
    if field == "euron":
        n_symbols, k_per_draw = 12, 2
        obs_list = [[e - 1 for e in d.euronumbers] for d in draws]
        reject_threshold = _BOCPD_REJECT_THRESHOLD["euron"]
    else:
        # Pool/k derived from records (EJ=50/5, MM=80/20); threshold per-pool from calibration.
        n_symbols = draws[0].pool_size
        k_per_draw = len(draws[0].main_numbers)
        obs_list = [[m - 1 for m in d.main_numbers] for d in draws]
        if n_symbols not in _MAIN_REJECT_THRESHOLD_BY_POOL:
            raise KeyError(
                f"no calibrated BOCPD threshold for the main pool N={n_symbols} — "
                "run scripts/calibrate_bocpd_threshold.py and add an entry"
            )
        reject_threshold = _MAIN_REJECT_THRESHOLD_BY_POOL[n_symbols]

    cp_probs, rl_map = _bocpd_dirichlet(
        obs_list, n_symbols, k_per_draw, alpha, hazard
    )

    # Warm-up: skip the transient burn-in (cp_prob[:warmup]). Clamp to leave >=1 point.
    if warmup is None:
        warmup = n_symbols // k_per_draw
    warmup = max(0, min(warmup, len(cp_probs) - 1))

    return cp_probs, rl_map, warmup, reject_threshold


def run_bocpd(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    alpha: float = 0.1,
    hazard: float = 0.005,
    top_k: int = 5,
    warmup: int | None = None,
) -> TestResult:
    """BOCPD Adams-MacKay 2007 — detection of change-points in the symbol distribution.

    Defaults to the 'euron' field (N=12, K=2) — sensitive to the 2014/2022 pool changes.
    alpha=0.1: a deliberate choice (MEMORY.md 2026-05-26) — α=1 weakens the signal on a
    pool change; α=0.1 gives cp_prob>0.4 at the first unseen symbol.
    p_value = 1 - max(cp_prob): a Bayesian posterior, not frequentist.
    reject_h0: max(cp_prob[warmup:]) > the per-field threshold calibrated to FPR~=0.05 under
    the uniform-iid null (see `_BOCPD_REJECT_THRESHOLD`; valid for alpha=0.1, hazard=0.005).

    warmup: number of initial draws skipped during detection (preregistration_v6 §0).
    None → N // K (one nominal pass through the pool): skips the transient burn-in in which
    cp_prob rises artificially because the symbol pool has not yet been "seen".
    """
    cp_probs, rl_map, warmup, reject_threshold = compute_bocpd_curve(
        draws, field, alpha, hazard, warmup
    )
    if field == "euron":
        n_symbols, k_per_draw = 12, 2
    else:
        n_symbols = draws[0].pool_size
        k_per_draw = len(draws[0].main_numbers)

    # Local maxima of cp_probs = change-point candidates (only OUTSIDE warm-up)
    # distance=5: ~5 draws ≈ 5 EuroJackpot weeks (Friday) — allows nearby peaks
    peaks, _ = find_peaks(cp_probs, height=0.05, distance=5)
    peaks = peaks[peaks >= warmup]
    if len(peaks) == 0:
        peaks = np.array([warmup + int(np.argmax(cp_probs[warmup:]))])

    top_idx = peaks[np.argsort(cp_probs[peaks])[::-1]][:top_k]
    top_dates = [str(draws[i].draw_date) for i in top_idx]
    top_probs = [float(cp_probs[i]) for i in top_idx]

    max_prob = float(np.max(cp_probs[warmup:]))
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
                "p_value = 1 - max(cp_prob); Bayesian posterior, not frequentist. "
                "reject_h0 when max(cp_prob) > a threshold calibrated to FPR~=0.05 under the null "
                "(per-field; valid for alpha=0.1, hazard=0.005)"
            ),
        },
    )


# ---------------------------------------------------------------------------
# Welch PSD
# ---------------------------------------------------------------------------

def run_welch_test(
    series: npt.NDArray[np.float64],
    fs: float = 1.0,
    label: str = "",
) -> TestResult:
    """Welch PSD — periodicity exploration (SNR of the dominant frequency).

    Diagnostic — no formal p-value (p_value = -1.0).
    reject_h0 = True when the dominant-frequency SNR > 5.
    """
    nperseg = min(256, max(8, len(series) // 4))
    freqs, psd = welch(series, fs=fs, nperseg=nperseg)

    # Skip DC (freq=0)
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
            "note": "p_value=-1 (exploratory); reject_h0 when SNR > 5",
        },
    )


# ---------------------------------------------------------------------------
# ACF / Ljung-Box
# ---------------------------------------------------------------------------

def run_acf_test(
    series: npt.NDArray[np.float64],
    nlags: int = 40,
    label: str = "",
) -> TestResult:
    """Ljung-Box test — H0: no autocorrelation (white noise).

    Rejection (p < 0.05) → autocorrelation → potential non-stationarity.
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
    """Runs the full set of classical H1 tests on a list of draws.

    Results (10 TestResult):
      - ADF × 2 (euron_mean, euron_max)
      - KPSS × 2
      - Welch PSD × 2
      - Ljung-Box ACF × 2
      - BOCPD Dirichlet-Multinomial × 2 (euron, main)
    """
    results: list[TestResult] = []

    for kind in ("euron_mean", "euron_max"):
        series = extract_series(draws, kind)
        results.append(run_adf(series, label=kind))
        results.append(run_kpss(series, label=kind))
        results.append(run_welch_test(series, label=kind))
        results.append(run_acf_test(series, label=kind))

    results.append(run_bocpd(draws, field="euron"))
    results.append(run_bocpd(draws, field="main"))

    return results
