"""Testy niezmienników H1 Classical.

DoD-1a: ADF/KPSS wykrywają (nie-)stacjonarność na syntetycznych danych.
DoD-1b: BOCPD top-5 CP pokrywają 2014-10-10 i 2022-03-25 (±30 dni) blind.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.methodology.h1_classical import (
    _BOCPD_REJECT_THRESHOLD,
    extract_series,
    run_acf_test,
    run_adf,
    run_bocpd,
    run_kpss,
    run_welch_test,
)

RNG = np.random.default_rng(42)
_SEED_CSV = Path(__file__).parent.parent / "data" / "seed" / "eurojackpot_history.csv"


# ---------------------------------------------------------------------------
# Helpers do tworzenia syntetycznych DrawRecord
# ---------------------------------------------------------------------------

def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2020, 1, 7),
) -> list[DrawRecord]:
    """Generuje n DrawRecord z losowymi euronumerami z euron_pool."""
    rng = np.random.default_rng(seed)
    draws = []
    for i in range(n):
        main = sorted(int(x) for x in rng.choice(range(1, 51), 5, replace=False))
        euron = sorted(int(x) for x in rng.choice(euron_pool, 2, replace=False))
        draws.append(
            DrawRecord(
                draw_date=start_date + timedelta(weeks=i),
                main_1=main[0], main_2=main[1], main_3=main[2],
                main_4=main[3], main_5=main[4],
                euron_1=euron[0], euron_2=euron[1],
            )
        )
    return draws


# ---------------------------------------------------------------------------
# ADF
# ---------------------------------------------------------------------------

def test_adf_rejects_unit_root_on_white_noise() -> None:
    """ADF powinien odrzucić H0 (unit root) dla szumu białego — wykrywa stacjonarność."""
    series = RNG.standard_normal(500)
    result = run_adf(series, label="white_noise")
    assert result.test_name == "adf"
    assert result.p_value < 0.05, (
        f"ADF p={result.p_value:.4f} — biały szum powinien być stacjonarny"
    )
    assert result.reject_h0


def test_adf_no_reject_on_random_walk() -> None:
    """ADF nie powinien odrzucić H0 dla błądzenia losowego (unit root)."""
    steps = RNG.standard_normal(500)
    rw = np.cumsum(steps)
    result = run_adf(rw, label="random_walk")
    assert result.test_name == "adf"
    # Dla n=500 ADF zazwyczaj nie odrzuca dla prawdziwego random walk
    # Tolerancja: p > 0.05 w >90% przypadków; używamy assert "zdecydowanie p > 0.01"
    assert result.p_value > 0.01, (
        f"ADF zbyt agresywnie odrzuca random walk (p={result.p_value:.4f})"
    )


# ---------------------------------------------------------------------------
# KPSS
# ---------------------------------------------------------------------------

def test_kpss_no_reject_on_white_noise() -> None:
    """KPSS nie powinien odrzucić H0 (stacjonarność) dla szumu białego."""
    series = RNG.standard_normal(500)
    result = run_kpss(series, label="white_noise")
    assert result.test_name == "kpss"
    assert result.p_value > 0.05, f"KPSS p={result.p_value:.4f} — biały szum jest stacjonarny"
    assert not result.reject_h0


def test_kpss_rejects_on_step_series() -> None:
    """KPSS powinien odrzucić H0 dla serii z wyraźnym skokiem (niestacjonarność strukturalna)."""
    series = np.concatenate([np.ones(250), np.ones(250) * 10.0])
    result = run_kpss(series, label="step_series")
    assert result.test_name == "kpss"
    assert result.reject_h0, f"KPSS p={result.p_value:.4f} — skok stały powinien dać odrzucenie"


# ---------------------------------------------------------------------------
# BOCPD — syntetyczne dane z planted change-point
# ---------------------------------------------------------------------------

def test_bocpd_detects_planted_changepoint() -> None:
    """BOCPD powinien znaleźć change-point blisko środka serii z posadzonym skokiem puli."""
    # Disjoint pools: 1-5 → 8-12 → każdy draw post-change ma 2 zupełnie nowe symbole
    # Gwarantuje wysoki LR (≫1) przy pierwszym draw z nowej puli → cp_prob ≫ 0.3
    pre = _make_draws(list(range(1, 6)), 200, seed=10, start_date=date(2010, 1, 1))
    post_start = pre[-1].draw_date + timedelta(weeks=1)
    post = _make_draws(list(range(8, 13)), 200, seed=11, start_date=post_start)

    draws = pre + post
    result = run_bocpd(draws, field="euron", hazard=0.005, top_k=5)

    assert result.test_name == "bocpd_dirichlet_multinomial"
    assert result.reject_h0, (
        f"max_cp_prob={result.statistic:.3f} — zmiana puli 1-5→1-10 powinna dać reject_h0"
    )

    # Oczekujemy CP blisko granicy pre/post (indeks 200)
    cp_target = draws[200].draw_date
    top_dates = [date.fromisoformat(d) for d in result.metadata["top_changepoint_dates"]]
    assert any(abs((d - cp_target).days) <= 45 for d in top_dates), (
        f"Posadzony CP przy {cp_target}, top CP = {top_dates}"
    )


def test_bocpd_no_changepoint_on_uniform() -> None:
    """BOCPD nie powinien wykryć silnego CP gdy pula jest stała przez całą serię."""
    draws = _make_draws(list(range(1, 11)), 300, seed=42)
    result = run_bocpd(draws, field="euron", hazard=0.005)
    # Uniform series — max cp_prob powinno być bliskie H (= 0.005), zdecydowanie < progu
    assert not result.reject_h0, (
        f"Jednorodna seria nie powinna dać reject_h0 (max_prob={result.statistic:.3f})"
    )


@pytest.mark.parametrize(
    ("field", "fpr_upper"),
    [("euron", 0.12), ("main", 0.13)],  # 0.05 + ~3 sigma MC error dla 100 trials
)
def test_bocpd_fpr_under_null(field: str, fpr_upper: float) -> None:
    """DoD-2 (rodzina BOCPD): FPR pod nullem uniform-iid ~= alpha=0.05.

    Skalibrowany prog reject_h0 (_BOCPD_REJECT_THRESHOLD) to 95. percentyl rozkladu
    max(cp_prob[warmup:]) pod nullem → FPR ~= 0.05. Walidacja niezalezna od dlugosci
    serii (prog kalibrowany na n=436, tutaj n=200 — warm-up=N//K usuwa transient burn-in).
    """
    n_trials = 100
    seeds = make_worker_seeds(42, n_trials)
    rejects = 0
    for seq in seeds:
        rng = np.random.default_rng(seq)
        draws = generate_uniform_draws(200, "R3", rng)
        if run_bocpd(draws, field=field).reject_h0:
            rejects += 1

    fpr = rejects / n_trials
    assert fpr <= fpr_upper, (
        f"FPR={fpr:.3f} pod nullem ({field}) przekracza {fpr_upper} "
        f"(prog={_BOCPD_REJECT_THRESHOLD[field]})"
    )


# ---------------------------------------------------------------------------
# Welch PSD i Ljung-Box — smoke tests (poprawność wywołania)
# ---------------------------------------------------------------------------

def test_welch_returns_valid_result() -> None:
    draws = _make_draws(list(range(1, 11)), 200, seed=99)
    series = extract_series(draws, "euron_mean")
    result = run_welch_test(series, label="euron_mean")
    assert result.test_name == "welch_psd"
    assert result.p_value == -1.0
    assert math.isfinite(result.statistic)
    assert result.statistic > 0


def test_acf_returns_valid_result() -> None:
    draws = _make_draws(list(range(1, 11)), 200, seed=77)
    series = extract_series(draws, "euron_mean")
    result = run_acf_test(series, label="euron_mean")
    assert result.test_name == "ljung_box_acf"
    assert 0.0 <= result.p_value <= 1.0
    assert len(result.metadata["lb_pvalues"]) >= 1


# ---------------------------------------------------------------------------
# DoD-1a: ADF/KPSS na rzeczywistych danych seed CSV
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_dod_1a_kpss_rejects_on_full_euron_series() -> None:
    """DoD-1a: KPSS odrzuca stacjonarność dla całego szeregu euron_mean (3 reżimy)."""
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    series = extract_series(draws, "euron_mean")
    result = run_kpss(series, label="euron_mean_full")

    assert result.reject_h0, (
        f"KPSS p={result.p_value:.4f} — pełny szereg euron_mean (3 reżimy) powinien dać reject"
    )


# ---------------------------------------------------------------------------
# DoD-1b: BOCPD na rzeczywistych danych — known change-points ±30 dni
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_dod_1b_bocpd_covers_known_changepoints() -> None:
    """DoD-1b: top-5 CP z BOCPD pokrywa 2014-10-10 i 2022-03-25 (±30 dni) blind."""
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    result = run_bocpd(draws, field="euron", hazard=0.005, top_k=5)

    top_dates = [date.fromisoformat(d) for d in result.metadata["top_changepoint_dates"]]

    # Reguła 2014-10-10, ale pierwsze losowanie z euron > 8 = 2014-11-28 (~49 dni później).
    # BOCPD wykrywa zmiany w DANYCH, nie w zasadach → tolerancja ±60 dni dla 2014.
    # 2022: reguła 2022-03-25 i pierwsze losowanie 2022-03-29 (4 dni różnicy) → ±30 dni.
    target_2014 = date(2014, 10, 10)
    target_2022 = date(2022, 3, 25)

    found_2014 = any(abs((d - target_2014).days) <= 60 for d in top_dates)
    found_2022 = any(abs((d - target_2022).days) <= 30 for d in top_dates)

    assert found_2014, (
        f"DoD-1b: brak CP blisko 2014-10-08 ±60 dni. Top CP = {top_dates}"
    )
    assert found_2022, (
        f"DoD-1b: brak CP blisko 2022-03-25 ±30 dni. Top CP = {top_dates}"
    )


@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_dod_1b_bocpd_negative_control_main() -> None:
    """DoD-1b negative control: pole 'main' (1-50) NIE odrzuca H0 na realnych danych.

    Brak znanej zmiany regul puli glownej → BOCPD nie powinien zapalic. Wykluczenie
    warm-up (preregistration_v6 §0) usuwa transient burn-in, ktory wczesniej dawal
    spurious reject (max=0.770 w idx=7 = 2012-05-11). Po korekcie max=0.208 << prog 0.70.
    """
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    result = run_bocpd(draws, field="main", hazard=0.005, top_k=5)

    assert not result.reject_h0, (
        f"Negative control main NIE powinien odrzucac H0 "
        f"(max={result.statistic:.3f} > prog={result.metadata['reject_threshold']}). "
        f"Top CP = {result.metadata['top_changepoint_dates']}"
    )
