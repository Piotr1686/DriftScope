"""Co-occurrence test tests (W6, preregistration §5c).

Verifies: the incidence matrix, curveball invariants (preserving both margins),
FPR ≈ α calibration on the null (max-pair), power + pair localization on a forced signal,
and pure-function determinism (DoD-6).
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
    """n draws where, with probability `pair_frac`, the pair `pair` is forced."""
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
# Incidence matrix
# ---------------------------------------------------------------------------

def test_incidence_matrix_shape_and_margins() -> None:
    """Binary (n, 50) matrix; row sum = 5; column sum = number's count."""
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    m = _incidence_matrix(draws)
    assert m.shape == (120, 50)
    assert set(np.unique(m)).issubset({0, 1})
    assert (m.sum(axis=1) == 5).all()
    # column sum k = how many times number (k+1) occurred
    assert m.sum(axis=0).sum() == 120 * 5


# ---------------------------------------------------------------------------
# Curveball — margin invariants
# ---------------------------------------------------------------------------

def test_curveball_preserves_both_margins() -> None:
    """Curveball swaps preserve row sums (=5) and column sums (margins)."""
    draws = generate_uniform_draws(300, "R3", np.random.default_rng(1))
    m = _incidence_matrix(draws)
    row0, col0 = m.sum(axis=1).copy(), m.sum(axis=0).copy()
    _seed_numba(123)
    m2 = m.copy()
    _curveball_trades(m2, 4000)
    assert np.array_equal(m2.sum(axis=1), row0)
    assert np.array_equal(m2.sum(axis=0), col0)


def test_curveball_actually_randomizes() -> None:
    """Enough swaps change the matrix (the null is not the identity)."""
    draws = generate_uniform_draws(300, "R3", np.random.default_rng(2))
    m = _incidence_matrix(draws)
    _seed_numba(7)
    m2 = m.copy()
    _curveball_trades(m2, 4000)
    assert not np.array_equal(m, m2)


# ---------------------------------------------------------------------------
# FPR calibration on the null (max-pair)
# ---------------------------------------------------------------------------

def test_cooccurrence_fpr_on_null() -> None:
    """FPR ≈ α on the uniform null — max-pair calibrates correctly (curveball null).

    Fully deterministic (fixed seeds). The 0.12 threshold leaves an MC margin for
    n_trials=60/n_perm=99; a gross miscalibration (e.g. rejected sum, FPR ~0.17) would exceed it.
    """
    det = cooccurrence_detector(n_perm=99)
    n_trials = 60
    rejects = sum(
        det(generate_uniform_draws(200, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.12, f"FPR(null, max-pair)={fpr} — possible miscalibration"


# ---------------------------------------------------------------------------
# Power + localization on a forced co-occurrence
# ---------------------------------------------------------------------------

def test_detects_and_localizes_forced_pair() -> None:
    """Strong forced pairing (frac=0.15) → reject H0 + correct pair localization."""
    draws = _forced_pair_draws(300, pair_frac=0.15, seed=11, pair=(7, 13))
    res = cooccurrence_test(draws, n_perm=199, seed=999)
    assert res.reject_h0 is True
    assert res.p_value <= 0.01
    assert res.metadata["top_pair"] == (7, 13)


def test_detects_planted_pair_corr_showcase() -> None:
    """W6 showcase: planted pair_corr p=0.10 (margin-preserving) → reject + localization.

    End-to-end with `generate_planted_draws` (not an ad-hoc helper): the joint signal
    that chi²/MMD are blind to (see test_driftsim_calibration) is detected here and the
    pair localized.
    """
    draws = generate_planted_draws(436, "R3", "pair_corr", 0.10, np.random.default_rng(5))
    res = cooccurrence_test(draws, n_perm=199, seed=5)
    assert res.reject_h0 is True
    assert res.metadata["top_pair"] == (7, 13)


def test_planted_pair_corr_smallest_effect_below_floor() -> None:
    """W6 finding: the smallest effect p=0.01 is below the detection floor (~FPR).

    Documents the sensitivity limit as an executable contract — power grows with the
    effect (p=0.05 → >0.7, validated in calibration), but p=0.01 stays at the floor.
    """
    rejects = sum(
        cooccurrence_test(
            generate_planted_draws(436, "R3", "pair_corr", 0.01, np.random.default_rng(s)),
            n_perm=99,
            seed=s * 3 + 1,
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4, f"expected below-floor (~FPR), got power={rejects/20}"


# ---------------------------------------------------------------------------
# Determinism (DoD-6) + guards
# ---------------------------------------------------------------------------

def test_detector_is_pure_function() -> None:
    """Two fresh detector instances on the same `draws` → identical p-value (DoD-6)."""
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
