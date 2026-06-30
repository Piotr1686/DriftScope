"""Information-theoretic audit tests (reporting/information_theory.py, wow option #3).

Verifies: the canonical LZ76 complexity properties, FPR ≤ α calibration on the null, power on
SEQUENTIAL structure (autocorr), blindness to a pure marginal (freq_shift) — proof of the
order-shuffle null's complementarity — and determinism (DoD-6).
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.reporting.information_theory import (
    information_detector,
    information_test,
    lz76_complexity,
)

# ---------------------------------------------------------------------------
# Canonical Lempel-Ziv 1976 complexity properties
# ---------------------------------------------------------------------------

def _arr(*xs: int) -> np.ndarray:
    return np.array(xs, dtype=np.int32)


def test_lz76_single_symbol() -> None:
    """A single symbol → c = 1 (lower bound)."""
    assert lz76_complexity(_arr(7)) == 1


def test_lz76_constant_sequence() -> None:
    """A constant sequence (all repetitions) → c = 2, regardless of length."""
    assert lz76_complexity(_arr(3, 3, 3, 3, 3, 3)) == 2
    assert lz76_complexity(np.full(100, 9, dtype=np.int32)) == 2


def test_lz76_all_distinct_maximal() -> None:
    """All distinct symbols → c = n (maximal complexity)."""
    seq = _arr(1, 2, 3, 4, 5, 6, 7)
    assert lz76_complexity(seq) == seq.shape[0]


def test_lz76_structure_below_random() -> None:
    """A structured (periodic) sequence is LESS complex than its random permutation."""
    rng = np.random.default_rng(0)
    periodic = np.tile(_arr(1, 2, 3, 4), 50)              # period 4
    shuffled = periodic[rng.permutation(periodic.shape[0])]
    assert lz76_complexity(periodic) < lz76_complexity(shuffled)


# ---------------------------------------------------------------------------
# FPR <= alpha calibration on the null + power
# ---------------------------------------------------------------------------

def test_fpr_on_null() -> None:
    """FPR ≤ α=0.05 (± MC margin) on the uniform null. Deterministic (fixed seeds)."""
    det = information_detector(n_perm=199)
    n_trials = 60
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(11, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.10, f"FPR={fpr} > threshold (MC margin over α=0.05)"


def test_detects_autocorr() -> None:
    """Sensitive to SEQUENTIAL structure (autocorr) — the order-shuffle breaks it → left tail."""
    det = information_detector(n_perm=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_blind_to_freq_shift() -> None:
    """Blind to a pure marginal (freq_shift) — the order-shuffle preserves the multiset → ~floor.

    Complementarity proof: the marginal is caught by chi²/MMD, not IT (~FPR).
    """
    det = information_detector(n_perm=99)
    rejects = sum(
        det(
            generate_planted_draws(436, "R3", "freq_shift", 0.10, np.random.default_rng(s))
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4


# ---------------------------------------------------------------------------
# Metadata cross-check + determinism (DoD-6) + guards
# ---------------------------------------------------------------------------

def test_metadata_fields_present() -> None:
    """TestResult carries LZ76 (raw/norm) + bz2 cross-check within consistent bounds."""
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(1))
    res = information_test(draws, n_perm=99, seed=0)
    assert res.test_name == "lz76_sequential"
    assert 0.0 < res.metadata["bz2_ratio"] <= 1.0
    assert 0.0 <= res.metadata["bz2_p"] <= 1.0
    assert res.metadata["lz76_raw"] >= 1
    assert res.statistic == pytest.approx(res.metadata["lz76_norm"])


def test_detector_is_pure_function() -> None:
    """DoD-6: identical draws → identical result (seed from a content digest)."""
    draws = generate_planted_draws(200, "R3", "autocorr", 0.20, np.random.default_rng(4))
    r1 = information_detector(n_perm=99)(draws)
    r2 = information_detector(n_perm=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(1, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        information_test(draws, n_perm=99)
