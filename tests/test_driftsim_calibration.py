"""Testy kalibracji DriftSim.

W2 (active): `null_uniform.generate_uniform_draws` — niezmienniki uczciwego nullu.
W3 (stub):   detection power >70% dla planted signals (Decision Gate W5).
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
    """Reprodukowalny generator z make_worker_seeds (oficjalna sciezka seedow)."""
    return np.random.default_rng(make_worker_seeds(base_seed, offset + 1)[offset])


# ---------------------------------------------------------------------------
# Niezmienniki strukturalne
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_count_and_chronology(regime: str) -> None:
    """Zwraca dokladnie n_draws rekordow w porzadku chronologicznym."""
    draws = generate_uniform_draws(200, regime, _rng())
    assert len(draws) == 200
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)


@pytest.mark.parametrize("regime", REGIMES)
def test_main_numbers_valid(regime: str) -> None:
    """5 liczb glownych: rosnaco, unikalne, w zakresie 1-50."""
    for d in generate_uniform_draws(300, regime, _rng()):
        nums = d.main_numbers
        assert len(set(nums)) == 5
        assert nums == sorted(nums)
        assert all(1 <= n <= 50 for n in nums)


@pytest.mark.parametrize("regime", REGIMES)
def test_euron_range_matches_regime(regime: str) -> None:
    """Euronumery: rosnaco, unikalne, w zakresie 1..pool(rezim) (§1)."""
    high = EURON_POOL_SIZE[regime]
    seen_max = 0
    for d in generate_uniform_draws(500, regime, _rng()):
        euron = d.euronumbers
        assert len(set(euron)) == 2
        assert euron == sorted(euron)
        assert all(1 <= e <= high for e in euron)
        seen_max = max(seen_max, *euron)
    # Sanity: przy 500 losowaniach gorna granica puli realnie sie pojawia.
    assert seen_max == high


# ---------------------------------------------------------------------------
# Guard signal #4 — etykieta dnia tylko w R3 (preregistration_v2 §6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", ["R1", "R2"])
def test_pre_r3_single_weekday(regime: str) -> None:
    """R1/R2: wszystkie losowania w piatki (kontrast Tue/Fri nie istnieje)."""
    weekdays = {d.draw_date.weekday() for d in generate_uniform_draws(100, regime, _rng())}
    assert weekdays == {4}  # 4 = piatek


def test_r3_two_weekdays() -> None:
    """R3: losowania we wtorki (1) i piatki (4) — umozliwia signal #4."""
    weekdays = {d.draw_date.weekday() for d in generate_uniform_draws(100, "R3", _rng())}
    assert weekdays == {1, 4}


# ---------------------------------------------------------------------------
# Determinizm
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_determinism_same_seed(regime: str) -> None:
    """Ten sam seed → bit-identyczny strumien (DoD-6 reproducibility)."""
    a = generate_uniform_draws(150, regime, _rng(offset=0))
    b = generate_uniform_draws(150, regime, _rng(offset=0))
    assert [d.model_dump() for d in a] == [d.model_dump() for d in b]


def test_different_seed_differs() -> None:
    """Rozne seedy → rozne strumienie (RNG faktycznie zuzywany)."""
    a = generate_uniform_draws(150, "R2", _rng(offset=0))
    b = generate_uniform_draws(150, "R2", _rng(offset=1))
    assert [d.model_dump() for d in a] != [d.model_dump() for d in b]


# ---------------------------------------------------------------------------
# Marginalna jednorodnosc — null NIE produkuje falszywego sygnalu
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regime", REGIMES)
def test_main_marginal_uniform(regime: str) -> None:
    """chi-squared NIE odrzuca uniformu dla puli glownej pod nullem."""
    draws = generate_uniform_draws(4000, regime, _rng())
    counts = np.zeros(50, dtype=int)
    for d in draws:
        for n in d.main_numbers:
            counts[n - 1] += 1
    _, p = chisquare(counts)  # H0: rozklad jednostajny
    assert p > 0.05


@pytest.mark.parametrize("regime", REGIMES)
def test_euron_marginal_uniform(regime: str) -> None:
    """chi-squared NIE odrzuca uniformu dla puli euron rezimu pod nullem."""
    high = EURON_POOL_SIZE[regime]
    draws = generate_uniform_draws(4000, regime, _rng())
    counts = np.zeros(high, dtype=int)
    for d in draws:
        for e in d.euronumbers:
            counts[e - 1] += 1
    _, p = chisquare(counts)
    assert p > 0.05


# ---------------------------------------------------------------------------
# Walidacja wejscia
# ---------------------------------------------------------------------------

def test_invalid_regime_raises() -> None:
    with pytest.raises(ValueError, match="Nieznany rezim"):
        generate_uniform_draws(10, "R9", _rng())  # type: ignore[arg-type]


def test_nonpositive_n_raises() -> None:
    with pytest.raises(ValueError, match="n_draws"):
        generate_uniform_draws(0, "R1", _rng())


# ===========================================================================
# planted_signals (W2)
# ===========================================================================

def test_enumerate_scenarios_count() -> None:
    """21 scenariuszy/rezim = 5 sygnalow × 4 effect + 1 null (§6)."""
    scen = enumerate_scenarios()
    assert len(scen) == 21
    assert ("null", None) in scen
    assert sum(1 for s, _ in scen if s != "null") == 20
    assert len(scen) * 3 == 63  # × 3 rezimy = 63 unikalne


@pytest.mark.parametrize("signal", SIGNALS)
def test_planted_structurally_valid(signal: str) -> None:
    """Plant na max effect: rekordy strukturalnie poprawne (R3 ma wszystkie sygnaly)."""
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
    """Ten sam seed → bit-identyczny plant (DoD-6)."""
    effect = EFFECT_SIZES[signal][-1]
    a = generate_planted_draws(120, "R3", signal, effect, _rng(offset=0))  # type: ignore[arg-type]
    b = generate_planted_draws(120, "R3", signal, effect, _rng(offset=0))  # type: ignore[arg-type]
    assert [d.model_dump() for d in a] == [d.model_dump() for d in b]


# --- Guard signal #4 (preregistration_v2 §6) ---

@pytest.mark.parametrize("regime", ["R1", "R2"])
def test_seasonality_degenerates_to_null(regime: str) -> None:
    """seasonality poza R3 = czysty null (ten sam seed → identyczny strumien)."""
    planted = generate_planted_draws(200, regime, "seasonality", 0.10, _rng(offset=0))  # type: ignore[arg-type]
    null = generate_uniform_draws(200, regime, _rng(offset=0))  # type: ignore[arg-type]
    assert [d.model_dump() for d in planted] == [d.model_dump() for d in null]


def test_seasonality_active_in_r3() -> None:
    """seasonality w R3 NIE jest nullem (kontrast Tue/Fri faktycznie wstrzykniety)."""
    planted = generate_planted_draws(200, "R3", "seasonality", 0.10, _rng(offset=0))
    null = generate_uniform_draws(200, "R3", _rng(offset=0))
    assert [d.model_dump() for d in planted] != [d.model_dump() for d in null]


# --- Sygnal faktycznie obecny (sanity, NIE pelna kalibracja power) ---

def _planted_count(draws: list, number: int) -> int:
    return sum(number in d.main_numbers for d in draws)


def test_freq_shift_boosts_target() -> None:
    """freq_shift δ=0.10: liczba planted czesciej niz uniform (≈n·5/50)."""
    draws = generate_planted_draws(4000, "R2", "freq_shift", 0.10, _rng())
    uniform_expected = 4000 * 5 / 50  # = 400
    assert _planted_count(draws, PLANTED_MAIN) > 2 * uniform_expected


def test_trend_grows_over_time() -> None:
    """trend β=0.10: liczba planted czestsza w 2. polowie niz w 1."""
    draws = generate_planted_draws(4000, "R2", "trend", 0.10, _rng())
    half = len(draws) // 2
    first = _planted_count(draws[:half], PLANTED_MAIN)
    second = _planted_count(draws[half:], PLANTED_MAIN)
    assert second > first


def test_autocorr_increases_recurrence() -> None:
    """autocorr ρ=0.20: wyzszy odsetek kolejnych losowan dzielacych liczbe niz null."""
    def shared_fraction(draws: list) -> float:
        hits = sum(
            bool(set(draws[i].main_numbers) & set(draws[i - 1].main_numbers))
            for i in range(1, len(draws))
        )
        return hits / (len(draws) - 1)

    planted = generate_planted_draws(2000, "R2", "autocorr", 0.20, _rng(offset=0))
    null = generate_uniform_draws(2000, "R2", _rng(offset=0))
    assert shared_fraction(planted) > shared_fraction(null)


def test_pair_corr_increases_cooccurrence() -> None:
    """pair_corr lift=2.0: para planted wspolwystepuje czesciej niz w nullu."""
    def cooc(draws: list) -> int:
        i, j = PLANTED_PAIR
        return sum(i in d.main_numbers and j in d.main_numbers for d in draws)

    planted = generate_planted_draws(8000, "R2", "pair_corr", 2.0, _rng(offset=0))
    null = generate_uniform_draws(8000, "R2", _rng(offset=0))
    assert cooc(planted) > cooc(null)


# --- Walidacja wejscia ---

def test_planted_invalid_signal_raises() -> None:
    with pytest.raises(ValueError, match="Nieznany sygnal"):
        generate_planted_draws(10, "R2", "ghost", 0.1, _rng())  # type: ignore[arg-type]


def test_planted_invalid_effect_raises() -> None:
    with pytest.raises(ValueError, match="spoza siatki"):
        generate_planted_draws(10, "R2", "freq_shift", 0.99, _rng())


def test_planted_nonpositive_n_raises() -> None:
    with pytest.raises(ValueError, match="n_draws"):
        generate_planted_draws(0, "R2", "freq_shift", 0.10, _rng())


# ===========================================================================
# calibration (W3) — sensitivity/specificity Monte Carlo
# ===========================================================================

def test_chi2_detector_basic() -> None:
    """chi2_main_uniformity: nie odrzuca na nullu, odrzuca na silnym freq_shift."""
    null = generate_uniform_draws(400, "R2", _rng())
    assert chi2_main_uniformity(null).reject_h0 is False
    planted = generate_planted_draws(400, "R2", "freq_shift", 0.10, _rng())
    assert chi2_main_uniformity(planted).reject_h0 is True


def test_regime_n_matches_w0() -> None:
    """Domyslne n kalibracji = realne liczby z seed CSV (W0)."""
    assert REGIME_N == {"R1": 133, "R2": 389, "R3": 436}


@pytest.mark.parametrize("regime", REGIMES)
def test_specificity_fpr_near_alpha(regime: str) -> None:
    """FPR na nullu ≈ α=0.05 (specificity ≈ 0.95); luzny gorny limit na MC error."""
    fpr = false_positive_rate(regime, n_trials=200)
    assert fpr <= 0.12  # α=0.05 + zapas na blad Monte Carlo (200 prob)


def test_freq_shift_power_passes_gate() -> None:
    """freq_shift δ=0.10 w R2: power > 70% (kryterium Decision Gate W5)."""
    power = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=200)
    assert power > 0.70


def test_power_increases_with_effect() -> None:
    """Power rosnie z effect-size (δ=0.01 sub-threshold < δ=0.10)."""
    low = estimate_rejection_rate("freq_shift", 0.01, "R2", n_trials=150)
    high = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=150)
    assert high > low


def test_chi2_blind_to_pair_correlation() -> None:
    """chi² (marginalny) jest ~slepy na pair_corr — power ≈ FPR << freq_shift.

    pair_corr zmienia tylko wspolwystapienia jednej pary (joint), marginal ~uniform.
    Uczciwy wynik kalibracji: ten sygnal wymaga dedykowanego testu wspolwystapien (W6).
    (autocorr i seasonality chi² JEDNAK wykrywa — przez nadmierna dyspersje zliczen.)
    """
    pair_power = estimate_rejection_rate("pair_corr", 2.0, "R2", n_trials=150)
    freq_power = estimate_rejection_rate("freq_shift", 0.10, "R2", n_trials=150)
    assert pair_power < 0.30
    assert pair_power < freq_power


def test_chi2_detects_overdispersion_signals() -> None:
    """chi² wykrywa autocorr i seasonality (nadmierna dyspersja), nie tylko marginal."""
    autocorr_power = estimate_rejection_rate("autocorr", 0.20, "R3", n_trials=120)
    seasonality_power = estimate_rejection_rate("seasonality", 0.10, "R3", n_trials=120)
    assert autocorr_power > 0.70
    assert seasonality_power > 0.70


def test_estimate_determinism() -> None:
    """Ten sam base_seed → identyczna estymata (DoD-6)."""
    a = estimate_rejection_rate("freq_shift", 0.05, "R2", n_trials=60, base_seed=7)
    b = estimate_rejection_rate("freq_shift", 0.05, "R2", n_trials=60, base_seed=7)
    assert a == b


def test_calibration_curve_shape() -> None:
    """calibration_curve zwraca power per effect z siatki §6, w [0,1]."""
    curve = calibration_curve("freq_shift", "R2", n_trials=8)
    assert set(curve.keys()) == set(EFFECT_SIZES["freq_shift"])
    assert all(0.0 <= p <= 1.0 for p in curve.values())
