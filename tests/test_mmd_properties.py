"""MMD property tests (W4).

Verifies: frequency vectors Δ⁴⁹, MMD² properties (zero for the same distribution,
positive for different ones), the median heuristic (anti-leakage), permutation
calibration, and the FPR ≤ 7.5% stability threshold on the shuffled null at N=200
(preregistration_v3 §3).
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.calibration import estimate_rejection_rate
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.k4_mmd import (
    frequency_vector,
    median_heuristic,
    mmd_permutation_test,
    mmd_rbf_squared,
    mmd_uniform_detector,
    sliding_frequency_vectors,
)

# ---------------------------------------------------------------------------
# Frequency vectors p ∈ Δ⁴⁹
# ---------------------------------------------------------------------------

def test_frequency_vector_is_on_simplex() -> None:
    """Frequency vector has dimension 50 and sums to 1 (p ∈ Δ⁴⁹)."""
    draws = generate_uniform_draws(100, "R2", np.random.default_rng(0))
    p = frequency_vector(draws)
    assert p.shape == (50,)
    assert p.sum() == pytest.approx(1.0)
    assert (p >= 0).all()


def test_sliding_windows_shape_and_simplex() -> None:
    """Number of windows = floor((n-w)/step)+1; each row on the simplex."""
    draws = generate_uniform_draws(389, "R2", np.random.default_rng(1))
    vecs = sliding_frequency_vectors(draws, window=25, step=25)
    assert vecs.shape == ((389 - 25) // 25 + 1, 50)
    assert np.allclose(vecs.sum(axis=1), 1.0)


def test_sliding_window_too_large_raises() -> None:
    draws = generate_uniform_draws(20, "R2", np.random.default_rng(2))
    with pytest.raises(ValueError):
        sliding_frequency_vectors(draws, window=25, step=25)


# ---------------------------------------------------------------------------
# MMD² — estimator properties
# ---------------------------------------------------------------------------

def test_mmd_zero_for_identical_distributions() -> None:
    """MMD² ~ 0 for two samples from the SAME distribution; much smaller than for different ones."""
    rng = np.random.default_rng(3)
    X = rng.normal(size=(40, 50))
    Y = rng.normal(size=(40, 50))           # same distribution
    Z = rng.normal(loc=2.0, size=(40, 50))  # shifted distribution
    bw = median_heuristic(X)
    mmd_same = mmd_rbf_squared(X, Y, bw)
    mmd_diff = mmd_rbf_squared(X, Z, bw)
    assert abs(mmd_same) < 0.05          # close to zero (unbiased estimator, may be < 0)
    assert mmd_diff > 0.3                # clearly positive for different distributions
    assert mmd_diff > 10 * abs(mmd_same)


def test_mmd_self_is_near_zero() -> None:
    """MMD²(X, X) ~ 0 (the unbiased estimator excludes the diagonal)."""
    rng = np.random.default_rng(4)
    X = rng.normal(size=(30, 50))
    bw = median_heuristic(X)
    assert abs(mmd_rbf_squared(X, X, bw)) < 0.05


def test_median_heuristic_positive() -> None:
    """Bandwidth > 0 for non-degenerate data; fallback 1.0 for <2 points."""
    rng = np.random.default_rng(5)
    X = rng.normal(size=(20, 50))
    assert median_heuristic(X) > 0.0
    assert median_heuristic(X[:1]) == 1.0  # degenerate → fallback


# ---------------------------------------------------------------------------
# Permutation test
# ---------------------------------------------------------------------------

def test_permutation_pvalue_in_range_and_detects_shift() -> None:
    """p-value ∈ (0,1]; the test rejects for clearly different distributions."""
    rng = np.random.default_rng(6)
    X = rng.normal(size=(30, 50))
    Z = rng.normal(loc=1.5, size=(30, 50))
    res = mmd_permutation_test(X, Z, n_perm=199, rng=rng)
    assert 0.0 < res.p_value <= 1.0
    assert res.reject_h0 is True
    assert res.test_name == "mmd_rbf_permutation"


def test_permutation_does_not_reject_same_distribution() -> None:
    """For samples from the same distribution the p-value is not significant (no rejection)."""
    rng = np.random.default_rng(7)
    X = rng.normal(size=(40, 50))
    Y = rng.normal(size=(40, 50))
    res = mmd_permutation_test(X, Y, n_perm=199, rng=rng)
    assert res.reject_h0 is False


# ---------------------------------------------------------------------------
# Detector — guard non-overlap + power sanity
# ---------------------------------------------------------------------------

def test_detector_rejects_overlapping_windows() -> None:
    """step < window breaks permutation exchangeability → forbidden (FPR ~1.0)."""
    with pytest.raises(ValueError, match="non-overlap"):
        mmd_uniform_detector(window=25, step=5)


def test_detector_detects_freq_shift() -> None:
    """The detector rejects H0 on a stream with a strong freq_shift (δ=0.10)."""
    det = mmd_uniform_detector(window=25, n_perm=199)
    draws = generate_planted_draws(389, "R2", "freq_shift", 0.10, np.random.default_rng(8))
    assert det(draws).reject_h0 is True


def test_mmd_blind_to_pair_corr() -> None:
    """MMD (frequency-vector, marginal) is blind to pair_corr — power ≈ FPR.

    pair_corr (v5, margin-preserving) keeps the marginal frequencies ~uniform, so MMD²
    on frequency vectors sees no signal (all of it is in the JOINT dimension). Complements
    test_chi2_blind_to_pair_correlation (test_driftsim_calibration) and
    test_serial_blind_to_pair_corr (test_permutation_null): BOTH marginal pillars (H1,
    MMD) are provably blind; only co-occurrence catches it (test_detects_planted_pair_corr_
    showcase). This justifies that 'must agree' is NOT a hard threshold (clean cell = 1/3).
    Deterministic (estimate_rejection_rate: base_seed=42 + detector seed from draws hash).
    """
    det = mmd_uniform_detector(window=25, n_perm=99)
    pair_power = estimate_rejection_rate("pair_corr", 0.10, "R2", det, n_trials=50)
    freq_power = estimate_rejection_rate("freq_shift", 0.10, "R2", det, n_trials=50)
    assert pair_power < 0.15, f"MMD should not see pair_corr (power={pair_power})"
    assert freq_power > 0.70, f"MMD should see freq_shift (power={freq_power})"
    assert pair_power < freq_power


# ---------------------------------------------------------------------------
# §3 stability threshold — FPR ≤ 7.5% on the shuffled null
# ---------------------------------------------------------------------------

def test_mmd_stability_n200_fpr() -> None:
    """FPR ≤ 7.5% on the uniform null at WINDOW size N=200 (preregistration_v3 §3).

    "N=200" = window size, not stream length. Non-overlapping windows (step=window) are
    the permutation exchangeability condition; the permutation test with `+1` is provably
    conservative (E[FPR] ≤ α=0.05). Stream = 2000 draws → 10 windows: at N=200 you need
    >=~10 windows for a stable estimate (5 windows give a liberal, noisy FPR).

    Methodological note: the real EuroJackpot stream (~958) yields only ~4 non-overlap
    windows at window=200 — too thin. The implemented calibration configuration is
    window=25 (many windows; see test_mmd_fpr_window25). Fully deterministic (fixed seeds).
    """
    det = mmd_uniform_detector(window=200, n_perm=199)
    n_trials = 80
    rejects = sum(
        det(generate_uniform_draws(2000, "R2", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.075, f"FPR={fpr} exceeds the §3 stability threshold (7.5%)"


def test_mmd_fpr_window25() -> None:
    """FPR ≤ 7.5% on the IMPLEMENTED calibration configuration (window=25).

    This is the DriftSim harness's actual operating point (window=25 → R2=15, R3=17
    non-overlap windows). FPR computed pooled over R2+R3 (lower MC variance). Fully
    deterministic (fixed seeds + detector seed from draws hash → pure function).
    """
    det = mmd_uniform_detector(window=25, n_perm=199)
    n_trials = 100
    rejects = 0
    for regime, n in (("R2", 389), ("R3", 436)):
        rejects += sum(
            det(generate_uniform_draws(n, regime, np.random.default_rng(seq))).reject_h0
            for seq in make_worker_seeds(7, n_trials)
        )
    fpr = rejects / (2 * n_trials)
    assert fpr <= 0.075, f"FPR(window=25, R2+R3 pooled)={fpr} exceeds 7.5%"
