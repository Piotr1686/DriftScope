"""Testy block bootstrap — alternatywny null (W6).

Weryfikuje: konstrukcje nulla MBB, kontrole FPR (konserwatywna) na nullu, detekcje autocorr,
gradient zachowania struktury z block_size, determinizm, guardy.
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
    """MBB null zwraca n_boot statystyk."""
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    null = _block_boot_overlap_null(_main_matrix(draws), n_boot=50, block_size=10, seed=1)
    assert null.shape == (50,)
    assert np.all(null >= 0.0)


def test_fpr_on_null_conservative() -> None:
    """FPR ≤ α na nullu uniform (alternatywny null jest konserwatywny). Deterministyczne."""
    det = block_bootstrap_detector(block_size=10, n_boot=199)
    n_trials = 40
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    assert rejects / n_trials <= 0.10


def test_detects_autocorr() -> None:
    """Sygnal lag-1 przebija null blokowy przy umiarkowanym block_size."""
    det = block_bootstrap_detector(block_size=10, n_boot=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_larger_block_preserves_more_structure() -> None:
    """Wiekszy block_size zachowuje wiecej zaleznosci → wyzszy sredni overlap nulla.

    Na danych z autocorr: null b=20 ma overlap >= null b=5 (mniej rozcienczenia na
    granicach blokow). To mechanizm gradientu konserwatyzmu.
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
