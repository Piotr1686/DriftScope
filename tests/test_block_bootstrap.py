"""Block bootstrap tests — alternative null (W6).

Verifies: MBB null construction, (conservative) FPR control on the null, autocorr detection,
the structure-preservation gradient with block_size, determinism, guards.
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.block_bootstrap import (
    BLOCK_SIZES,
    _block_boot_overlap_null,
    block_bootstrap_detector,
    block_bootstrap_test,
)
from driftscope.methodology.permutation import _main_matrix


def test_block_sizes_pre_registered() -> None:
    assert BLOCK_SIZES == (5, 10, 20)


def test_null_array_shape() -> None:
    """The MBB null returns n_boot statistics."""
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    null = _block_boot_overlap_null(_main_matrix(draws), n_boot=50, block_size=10, seed=1)
    assert null.shape == (50,)
    assert np.all(null >= 0.0)


def test_fpr_on_null_conservative() -> None:
    """FPR ≤ α on the uniform null (the alternative null is conservative). Deterministic."""
    det = block_bootstrap_detector(block_size=10, n_boot=199)
    n_trials = 40
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    assert rejects / n_trials <= 0.10


def test_detects_autocorr() -> None:
    """A lag-1 signal breaks through the block null at a moderate block_size."""
    det = block_bootstrap_detector(block_size=10, n_boot=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_larger_block_preserves_more_structure() -> None:
    """A larger block_size preserves more dependence → higher mean null overlap.

    On autocorr data: the b=20 null has overlap >= the b=5 null (less dilution at
    block boundaries). This is the conservatism-gradient mechanism.
    """
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(5))
    r5 = block_bootstrap_test(draws, block_size=5, n_boot=199, seed=42)
    r20 = block_bootstrap_test(draws, block_size=20, n_boot=199, seed=42)
    assert r20.metadata["null_mean_overlap"] >= r5.metadata["null_mean_overlap"]


def test_detector_is_pure_function() -> None:
    draws = generate_planted_draws(200, "R2", "autocorr", 0.20, np.random.default_rng(4))
    r1 = block_bootstrap_detector(block_size=10, n_boot=99)(draws)
    r2 = block_bootstrap_detector(block_size=10, n_boot=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(3, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        block_bootstrap_test(draws, n_boot=99)


def test_block_size_out_of_range_raises() -> None:
    draws = generate_uniform_draws(50, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        block_bootstrap_test(draws, block_size=100, n_boot=99)
