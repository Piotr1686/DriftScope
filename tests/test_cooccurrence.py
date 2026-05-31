"""Testy testu wspolwystapien (W6, preregistration §5c).

Weryfikuje: macierz incydencji, niezmienniki curveball (zachowanie obu marginesow),
kalibracje FPR ≈ α na nullu (max-pair), power + lokalizacja pary na wymuszonym sygnale,
oraz determinizm czystej funkcji (DoD-6).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.cooccurrence import (
    _curveball_trades,
    _incidence_matrix,
    _seed_numba,
    cooccurrence_detector,
    cooccurrence_test,
)


def _forced_pair_draws(
    n: int, pair_frac: float, seed: int, pair: tuple[int, int] = (7, 13)
) -> list[DrawRecord]:
    """n losowan, gdzie z prawdopodobienstwem `pair_frac` para `pair` jest wymuszana."""
    rng = np.random.default_rng(seed)
    i, j = pair
    rest_pool = [k for k in range(1, 51) if k not in (i, j)]
    d0 = date(2022, 3, 25)
    recs: list[DrawRecord] = []
    for t in range(n):
        if rng.random() < pair_frac:
            extra = rng.choice(rest_pool, size=3, replace=False)
            main = np.sort(np.array([i, j, *extra]))
        else:
            main = np.sort(rng.choice(50, size=5, replace=False) + 1)
        recs.append(
            DrawRecord(
                draw_date=d0 + timedelta(days=3 * t),
                main_1=int(main[0]), main_2=int(main[1]), main_3=int(main[2]),
                main_4=int(main[3]), main_5=int(main[4]), euron_1=1, euron_2=2,
            )
        )
    return recs


# ---------------------------------------------------------------------------
# Macierz incydencji
# ---------------------------------------------------------------------------

def test_incidence_matrix_shape_and_margins() -> None:
    """Macierz (n, 50) binarna; suma wiersza = 5; suma kolumny = liczebnosc liczby."""
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    m = _incidence_matrix(draws)
    assert m.shape == (120, 50)
    assert set(np.unique(m)).issubset({0, 1})
    assert (m.sum(axis=1) == 5).all()
    # suma kolumny k = ile razy liczba (k+1) wystapila
    assert m.sum(axis=0).sum() == 120 * 5


# ---------------------------------------------------------------------------
# Curveball — niezmienniki marginesow
# ---------------------------------------------------------------------------

def test_curveball_preserves_both_margins() -> None:
    """Wymiany curveball zachowuja sumy wierszy (=5) i sumy kolumn (marginesy)."""
    draws = generate_uniform_draws(300, "R3", np.random.default_rng(1))
    m = _incidence_matrix(draws)
    row0, col0 = m.sum(axis=1).copy(), m.sum(axis=0).copy()
    _seed_numba(123)
    m2 = m.copy()
    _curveball_trades(m2, 4000)
    assert np.array_equal(m2.sum(axis=1), row0)
    assert np.array_equal(m2.sum(axis=0), col0)


def test_curveball_actually_randomizes() -> None:
    """Wystarczajaco wiele wymian zmienia macierz (null nie jest tozsamoscia)."""
    draws = generate_uniform_draws(300, "R3", np.random.default_rng(2))
    m = _incidence_matrix(draws)
    _seed_numba(7)
    m2 = m.copy()
    _curveball_trades(m2, 4000)
    assert not np.array_equal(m, m2)


# ---------------------------------------------------------------------------
# Kalibracja FPR na nullu (max-pair)
# ---------------------------------------------------------------------------

def test_cooccurrence_fpr_on_null() -> None:
    """FPR ≈ α na nullu uniform — max-pair kalibruje sie poprawnie (curveball null).

    W pelni deterministyczne (stale seedy). Prog 0.12 zostawia margines MC dla
    n_trials=60/n_perm=99; gruba miskalibracja (np. odrzucona suma, FPR ~0.17) by przekroczyla.
    """
    det = cooccurrence_detector(n_perm=99)
    n_trials = 60
    rejects = sum(
        det(generate_uniform_draws(200, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.12, f"FPR(null, max-pair)={fpr} — mozliwa miskalibracja"


# ---------------------------------------------------------------------------
# Power + lokalizacja na wymuszonym wspolwystapieniu
# ---------------------------------------------------------------------------

def test_detects_and_localizes_forced_pair() -> None:
    """Silne wymuszone parowanie (frac=0.15) → odrzucenie H0 + poprawna lokalizacja pary."""
    draws = _forced_pair_draws(300, pair_frac=0.15, seed=11, pair=(7, 13))
    res = cooccurrence_test(draws, n_perm=199, seed=999)
    assert res.reject_h0 is True
    assert res.p_value <= 0.01
    assert res.metadata["top_pair"] == (7, 13)


def test_detects_planted_pair_corr_showcase() -> None:
    """Showcase W6: planted pair_corr p=0.10 (margin-preserving) → odrzucenie + lokalizacja.

    End-to-end z `generate_planted_draws` (nie ad-hoc helperem): sygnal joint, na ktory
    chi²/MMD sa slepe (zob. test_driftsim_calibration), jest tu wykryty i para zlokalizowana.
    """
    draws = generate_planted_draws(436, "R3", "pair_corr", 0.10, np.random.default_rng(5))
    res = cooccurrence_test(draws, n_perm=199, seed=5)
    assert res.reject_h0 is True
    assert res.metadata["top_pair"] == (7, 13)


def test_planted_pair_corr_smallest_effect_below_floor() -> None:
    """Finding W6: najmniejszy effect p=0.01 jest ponizej progu detekcji (~FPR).

    Dokumentuje granice czulosci jako wykonywalny kontrakt — power rosnie z effectem
    (p=0.05 → >0.7, walidowane w kalibracji), ale p=0.01 pozostaje przy floorze.
    """
    rejects = sum(
        cooccurrence_test(
            generate_planted_draws(436, "R3", "pair_corr", 0.01, np.random.default_rng(s)),
            n_perm=99,
            seed=s * 3 + 1,
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4, f"oczekiwano below-floor (~FPR), otrzymano power={rejects/20}"


# ---------------------------------------------------------------------------
# Determinizm (DoD-6) + guardy
# ---------------------------------------------------------------------------

def test_detector_is_pure_function() -> None:
    """Dwie swieze instancje detektora na tym samym `draws` → identyczny p-value (DoD-6)."""
    draws = _forced_pair_draws(200, pair_frac=0.10, seed=3)
    r1 = cooccurrence_detector(n_perm=99)(draws)
    r2 = cooccurrence_detector(n_perm=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic
    assert r1.metadata["top_pair"] == r2.metadata["top_pair"]


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(1, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        cooccurrence_test(draws, n_perm=99)
