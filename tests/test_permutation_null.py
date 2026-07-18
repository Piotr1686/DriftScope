"""Permutation engine tests (W6, DoD-2).

Verifies: the p-value primitive, the lag-1 overlap statistic (order-dependent), FPR ≤ α
calibration on shuffled/null (DoD-2), power on autocorr, blindness to non-serial signals,
determinism.
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.permutation import (
    _main_matrix,
    _mean_lag1_overlap,
    permutation_pvalue,
    serial_overlap_detector,
    serial_overlap_test,
)

# ---------------------------------------------------------------------------
# p-value primitive
# ---------------------------------------------------------------------------

def test_permutation_pvalue_bounds() -> None:
    null = np.arange(100, dtype=float)
    # obs above all null → minimal p = 1/(B+1)
    assert permutation_pvalue(1000.0, null) == pytest.approx(1 / 101)
    # obs below all null → p = 1.0
    assert permutation_pvalue(-1.0, null) == pytest.approx(1.0)
    # never 0, always conservative
    assert permutation_pvalue(99.0, null) > 0.0


# ---------------------------------------------------------------------------
# lag-1 overlap statistic
# ---------------------------------------------------------------------------

def test_lag1_overlap_exact() -> None:
    """Mean overlap of consecutive draws computed exactly."""
    # 3 draws: (1-5),(4-8),(10-14). Overlap(1,2)={4,5}=2; overlap(2,3)={}=0 → mean 1.0
    mat = np.array([[1, 2, 3, 4, 5], [4, 5, 6, 7, 8], [10, 11, 12, 13, 14]], dtype=np.int64)
    assert _mean_lag1_overlap(mat) == pytest.approx(1.0)


def test_lag1_overlap_identical_rows() -> None:
    """Identical consecutive draws → overlap = 5 (full coverage)."""
    mat = np.array([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]], dtype=np.int64)
    assert _mean_lag1_overlap(mat) == pytest.approx(5.0)


def test_main_matrix_shape() -> None:
    draws = generate_uniform_draws(10, "R2", np.random.default_rng(0))
    assert _main_matrix(draws).shape == (10, 5)


# ---------------------------------------------------------------------------
# DoD-2: FPR <= alpha on shuffled/null + power
# ---------------------------------------------------------------------------

def test_serial_fpr_on_null() -> None:
    """DoD-2: FPR ≤ α=0.05 (± MC error) on the uniform null. Deterministic (fixed seeds)."""
    det = serial_overlap_detector(n_perm=199)
    n_trials = 60
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.10, f"FPR={fpr} > DoD-2 threshold (MC margin over α=0.05)"


def test_serial_detects_autocorr() -> None:
    """Lag-1 overlap is sensitive to autocorr (boost of numbers from the previous draw)."""
    det = serial_overlap_detector(n_perm=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.10, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_serial_blind_to_pair_corr() -> None:
    """Blind to pair_corr (within-draw structure, not serial) — ~floor."""
    det = serial_overlap_detector(n_perm=99)
    rejects = sum(
        det(
            generate_planted_draws(436, "R3", "pair_corr", 0.10, np.random.default_rng(s))
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4


# ---------------------------------------------------------------------------
# Determinism (DoD-6) + guards
# ---------------------------------------------------------------------------

def test_detector_is_pure_function() -> None:
    draws = generate_planted_draws(200, "R2", "autocorr", 0.20, np.random.default_rng(4))
    r1 = serial_overlap_detector(n_perm=99)(draws)
    r2 = serial_overlap_detector(n_perm=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(3, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        serial_overlap_test(draws, n_perm=99)
