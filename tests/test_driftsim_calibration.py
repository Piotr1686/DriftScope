"""DriftSim calibration tests.

W2 (active): `null_uniform.generate_uniform_draws` — honest-null invariants.
W3 (stub):   detection power >70% for planted signals (Decision Gate W5).
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import chisquare

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.calibration import (
    REGIME_N,
    calibration_curve,
    chi2_main_uniformity,
    estimate_rejection_rate,
    false_positive_rate,
)
from driftscope.driftsim.null_uniform import (
    EURON_POOL_SIZE,
    generate_uniform_draws,
)
from driftscope.driftsim.planted_signals import (
    EFFECT_SIZES,
    PLANTED_MAIN,
    PLANTED_PAIR,
    enumerate_scenarios,
    generate_planted_draws,
)

REGIMES = ["R1", "R2", "R3"]
SIGNALS = list(EFFECT_SIZES.keys())


def _rng(base_seed: int = 42, offset: int = 0) -> np.random.Generator:
    """Reproducible generator from make_worker_seeds (the official seed path)."""
    return np.random.default_rng(make_worker_seeds(base_seed, offset + 1)[offset])


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_count_and_chronology(regime: str) -> None:
    """Returns exactly n_draws records in chronological order."""
    draws = generate_uniform_draws(200, regime, _rng())
    assert len(draws) == 200
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)


@pytest.mark.parametrize("regime", REGIMES)
def test_main_numbers_valid(regime: str) -> None:
    """5 main numbers: increasing, unique, in range 1-50."""
    for d in generate_uniform_draws(300, regime, _rng()):
        nums = d.main_numbers
        assert len(set(nums)) == 5
        assert nums == sorted(nums)
        assert all(1 <= n <= 50 for n in nums)


@pytest.mark.parametrize("regime", REGIMES)
def test_euron_range_matches_regime(regime: str) -> None:
    """Euro numbers: increasing, unique, in range 1..pool(regime) (§1)."""
    high = EURON_POOL_SIZE[regime]
    seen_max = 0
    for d in generate_uniform_draws(500, regime, _rng()):
        euron = d.euronumbers
        assert len(set(euron)) == 2
        assert euron == sorted(euron)
        assert all(1 <= e <= high for e in euron)
        seen_max = max(seen_max, *euron)
    # Sanity: over 500 draws the pool's upper bound actually appears.
    assert seen_max == high


# ---------------------------------------------------------------------------
# Guard signal #4 — weekday label only in R3 (preregistration_v2 §6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", ["R1", "R2"])
def test_pre_r3_single_weekday(regime: str) -> None:
    """R1/R2: all draws on Fridays (no Tue/Fri contrast exists)."""
    weekdays = {d.draw_date.weekday() for d in generate_uniform_draws(100, regime, _rng())}
    assert weekdays == {4}  # 4 = Friday


def test_r3_two_weekdays() -> None:
    """R3: draws on Tuesdays (1) and Fridays (4) — enables signal #4."""
    weekdays = {d.draw_date.weekday() for d in generate_uniform_draws(100, "R3", _rng())}
    assert weekdays == {1, 4}


# ---------------------------------------------------------------------------
# Determinizm
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_determinism_same_seed(regime: str) -> None:
    """Same seed → bit-identical stream (DoD-6 reproducibility)."""
    a = generate_uniform_draws(150, regime, _rng(offset=0))
    b = generate_uniform_draws(150, regime, _rng(offset=0))
    assert [d.model_dump() for d in a] == [d.model_dump() for d in b]


def test_different_seed_differs() -> None:
    """Different seeds → different streams (RNG is actually consumed)."""
    a = generate_uniform_draws(150, "R2", _rng(offset=0))
    b = generate_uniform_draws(150, "R2", _rng(offset=1))
    assert [d.model_dump() for d in a] != [d.model_dump() for d in b]


# ---------------------------------------------------------------------------
# Marginal uniformity — the null does NOT produce a false signal
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_main_marginal_uniform(regime: str) -> None:
    """chi-squared does NOT reject uniformity for the main pool under the null."""
    draws = generate_uniform_draws(4000, regime, _rng())
    counts = np.zeros(50, dtype=int)
    for d in draws:
        for n in d.main_numbers:
            counts[n - 1] += 1
    _, p = chisquare(counts)  # H0: uniform distribution
    assert p > 0.05


@pytest.mark.parametrize("regime", REGIMES)
def test_euron_marginal_uniform(regime: str) -> None:
    """chi-squared does NOT reject uniformity for the regime's euron pool under the null."""
    high = EURON_POOL_SIZE[regime]
    draws = generate_uniform_draws(4000, regime, _rng())
    counts = np.zeros(high, dtype=int)
    for d in draws:
        for e in d.euronumbers:
            counts[e - 1] += 1
    _, p = chisquare(counts)
    assert p > 0.05


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_invalid_regime_raises() -> None:
    with pytest.raises(ValueError, match="Unknown regime"):
        generate_uniform_draws(10, "R9", _rng())  # type: ignore[arg-type]


def test_nonpositive_n_raises() -> None:
    with pytest.raises(ValueError, match="n_draws"):
        generate_uniform_draws(0, "R1", _rng())


# ===========================================================================
# planted_signals (W2)
# ===========================================================================

def test_enumerate_scenarios_count() -> None:
    """21 scenarios/regime = 5 signals × 4 effects + 1 null (§6)."""
    scen = enumerate_scenarios()
    assert len(scen) == 21
    assert ("null", None) in scen
    assert sum(1 for s, _ in scen if s != "null") == 20
    assert len(scen) * 3 == 63  # × 3 regimes = 63 unique


@pytest.mark.parametrize("signal", SIGNALS)
def test_planted_structurally_valid(signal: str) -> None:
    """Plant at max effect: records structurally valid (R3 has all signals)."""
    effect = EFFECT_SIZES[signal][-1]
    draws = generate_planted_draws(300, "R3", signal, effect, _rng())  # type: ignore[arg-type]
    assert len(draws) == 300
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)
    high = EURON_POOL_SIZE["R3"]
    for d in draws:
        assert len(set(d.main_numbers)) == 5
        assert d.main_numbers == sorted(d.main_numbers)
        assert all(1 <= n <= 50 for n in d.main_numbers)
        assert len(set(d.euronumbers)) == 2
        assert all(1 <= e <= high for e in d.euronumbers)


@pytest.mark.parametrize("signal", SIGNALS)
def test_planted_determinism(signal: str) -> None:
    """Same seed → bit-identical plant (DoD-6)."""
    effect = EFFECT_SIZES[signal][-1]
    a = generate_planted_draws(120, "R3", signal, effect, _rng(offset=0))  # type: ignore[arg-type]
    b = generate_planted_draws(120, "R3", signal, effect, _rng(offset=0))  # type: ignore[arg-type]
    assert [d.model_dump() for d in a] == [d.model_dump() for d in b]


# --- Guard signal #4 (preregistration_v2 §6) ---

@pytest.mark.parametrize("regime", ["R1", "R2"])
def test_seasonality_degenerates_to_null(regime: str) -> None:
    """seasonality outside R3 = pure null (same seed → identical stream)."""
    planted = generate_planted_draws(200, regime, "seasonality", 0.10, _rng(offset=0))  # type: ignore[arg-type]
    null = generate_uniform_draws(200, regime, _rng(offset=0))  # type: ignore[arg-type]
    assert [d.model_dump() for d in planted] == [d.model_dump() for d in null]


def test_seasonality_active_in_r3() -> None:
    """seasonality in R3 is NOT the null (Tue/Fri contrast actually injected)."""
    planted = generate_planted_draws(200, "R3", "seasonality", 0.10, _rng(offset=0))
    null = generate_uniform_draws(200, "R3", _rng(offset=0))
    assert [d.model_dump() for d in planted] != [d.model_dump() for d in null]


# --- Signal actually present (sanity, NOT full power calibration) ---

def _planted_count(draws: list, number: int) -> int:
    return sum(number in d.main_numbers for d in draws)


def test_freq_shift_boosts_target() -> None:
    """freq_shift δ=0.10: planted number more frequent than uniform (≈n·5/50)."""
    draws = generate_planted_draws(4000, "R2", "freq_shift", 0.10, _rng())
    uniform_expected = 4000 * 5 / 50  # = 400
    assert _planted_count(draws, PLANTED_MAIN) > 2 * uniform_expected


def test_trend_grows_over_time() -> None:
    """trend β=0.10: planted number more frequent in the 2nd half than the 1st."""
    draws = generate_planted_draws(4000, "R2", "trend", 0.10, _rng())
    half = len(draws) // 2
    first = _planted_count(draws[:half], PLANTED_MAIN)
    second = _planted_count(draws[half:], PLANTED_MAIN)
    assert second > first


def test_autocorr_increases_recurrence() -> None:
    """autocorr ρ=0.20: higher fraction of consecutive draws sharing a number than the null."""
    def shared_fraction(draws: list) -> float:
        hits = sum(
            bool(set(draws[i].main_numbers) & set(draws[i - 1].main_numbers))
            for i in range(1, len(draws))
        )
        return hits / (len(draws) - 1)

    planted = generate_planted_draws(2000, "R2", "autocorr", 0.20, _rng(offset=0))
    null = generate_uniform_draws(2000, "R2", _rng(offset=0))
    assert shared_fraction(planted) > shared_fraction(null)


def test_pair_corr_increases_cooccurrence_preserving_margins() -> None:
    """pair_corr p=0.10: planted pair co-occurs more often, BUT margins ~uniform (v5).

    New mechanism (margin-preserving): raises the joint (7,13) without changing the margins —
    a pure joint signal that chi²/MMD are provably blind to.
    """
    def cooc(draws: list) -> int:
        i, j = PLANTED_PAIR
        return sum(i in d.main_numbers and j in d.main_numbers for d in draws)

    planted = generate_planted_draws(8000, "R2", "pair_corr", 0.10, _rng(offset=0))
    null = generate_uniform_draws(8000, "R2", _rng(offset=0))
    assert cooc(planted) > cooc(null)

    # Pair numbers' margin ~ uniform (0.1): the construction compensates via "force-neither".
    i, j = PLANTED_PAIR
    margin_i = sum(i in d.main_numbers for d in planted) / len(planted)
    assert margin_i == pytest.approx(0.1, abs=0.015)


# --- Input validation ---

def test_planted_invalid_signal_raises() -> None:
    with pytest.raises(ValueError, match="Unknown signal"):
        generate_planted_draws(10, "R2", "ghost", 0.1, _rng())  # type: ignore[arg-type]


def test_planted_invalid_effect_raises() -> None:
    with pytest.raises(ValueError, match="§6 grid"):
        generate_planted_draws(10, "R2", "freq_shift", 0.99, _rng())


def test_planted_nonpositive_n_raises() -> None:
    with pytest.raises(ValueError, match="n_draws"):
        generate_planted_draws(0, "R2", "freq_shift", 0.10, _rng())


# ===========================================================================
# calibration (W3) — sensitivity/specificity Monte Carlo
# ===========================================================================

def test_chi2_detector_basic() -> None:
    """chi2_main_uniformity: does not reject on the null, rejects on a strong freq_shift."""
    null = generate_uniform_draws(400, "R2", _rng())
    assert chi2_main_uniformity(null).reject_h0 is False
    planted = generate_planted_draws(400, "R2", "freq_shift", 0.10, _rng())
    assert chi2_main_uniformity(planted).reject_h0 is True


def test_regime_n_matches_w0() -> None:
    """Default calibration n = real counts from the seed CSV (W0)."""
    assert REGIME_N == {"R1": 133, "R2": 389, "R3": 436}


@pytest.mark.parametrize("regime", REGIMES)
def test_specificity_fpr_near_alpha(regime: str) -> None:
    """FPR on the null ≈ α=0.05 (specificity ≈ 0.95); loose upper limit for MC error."""
    fpr = false_positive_rate(regime, n_trials=200)
    assert fpr <= 0.12  # α=0.05 + margin for Monte Carlo error (200 trials)


def test_freq_shift_power_passes_gate() -> None:
    """freq_shift δ=0.10 in R2: power > 70% (Decision Gate W5 criterion)."""
    power = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=200)
    assert power > 0.70


def test_power_increases_with_effect() -> None:
    """Power grows with effect-size (δ=0.01 sub-threshold < δ=0.10)."""
    low = estimate_rejection_rate("freq_shift", 0.01, "R2", n_trials=150)
    high = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=150)
    assert high > low


def test_chi2_blind_to_pair_correlation() -> None:
    """chi² (marginal) is blind to pair_corr — power ≈ FPR << freq_shift.

    The new pair_corr mechanism (v5) preserves the margins EXACTLY → chi² is provably blind
    even at the strongest p=0.10 (the whole signal is in the joint dimension). Only the
    dedicated co-occurrence test detects it (§5c, W6 — see test_cooccurrence).
    (chi² DOES detect autocorr and seasonality, though — via over-dispersion of counts.)
    """
    pair_power = estimate_rejection_rate("pair_corr", 0.10, "R2", n_trials=150)
    freq_power = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=150)
    assert pair_power < 0.15
    assert pair_power < freq_power


def test_chi2_detects_overdispersion_signals() -> None:
    """chi² detects autocorr and seasonality (over-dispersion), not just the marginal."""
    autocorr_power = estimate_rejection_rate("autocorr", 0.20, "R3", n_trials=120)
    seasonality_power = estimate_rejection_rate("seasonality", 0.10, "R3", n_trials=120)
    assert autocorr_power > 0.70
    assert seasonality_power > 0.70


def test_estimate_determinism() -> None:
    """Same base_seed → identical estimate (DoD-6)."""
    a = estimate_rejection_rate("freq_shift", 0.05, "R2", n_trials=60, base_seed=7)
    b = estimate_rejection_rate("freq_shift", 0.05, "R2", n_trials=60, base_seed=7)
    assert a == b


def test_calibration_curve_shape() -> None:
    """calibration_curve returns power per effect from the §6 grid, in [0,1]."""
    curve = calibration_curve("freq_shift", "R2", n_trials=8)
    assert set(curve.keys()) == set(EFFECT_SIZES["freq_shift"])
    assert all(0.0 <= p <= 1.0 for p in curve.values())
