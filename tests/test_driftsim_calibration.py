"""Testy kalibracji DriftSim.

W2 (active): `null_uniform.generate_uniform_draws` — niezmienniki uczciwego nullu.
W3 (stub):   detection power >70% dla planted signals (Decision Gate W5).
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import chisquare

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import (
    EURON_POOL_SIZE,
    generate_uniform_draws,
)

REGIMES = ["R1", "R2", "R3"]


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


# ---------------------------------------------------------------------------
# W3 — planted signal detection (stub, Decision Gate W5)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Implementacja w W3 (planted_signals.py)")
def test_planted_freq_shift_detected() -> None:
    pass


@pytest.mark.skip(reason="Implementacja w W3 (planted_signals.py)")
def test_null_uniform_no_false_signal() -> None:
    pass
