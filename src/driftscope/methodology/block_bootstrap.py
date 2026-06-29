"""Block bootstrap — an alternative null preserving short-range dependence (W6).

The permutation null (`permutation.py`, `recurrence.py`) assumes FULL exchangeability (iid) —
shuffling destroys ALL serial structure. The moving block bootstrap (MBB) is an alternative,
more CONSERVATIVE null: it resamples overlapping BLOCKS of consecutive draws, so it preserves
within-block dependence (of length `block_size`) and randomly concatenates blocks. A signal
that breaks through this null is NOT explained by short-range dependence at the `block_size` scale.

Block size ∈ {5, 10, 20} (pre-registered). The default statistic = lag-1 serial overlap
(the same as `permutation.serial_overlap_test`) → a direct comparison of the two nulls:
- shuffle (permutation): very sensitive to autocorr (lag-1) — power ~1.0.
- block bootstrap: ABSORBS lag-1 within a block → low power on autocorr (a feature:
  distinguishes short-range dependence from longer range). The shuffle−block gap = a signature
  of the dependence range. On the iid null both give FPR ≈ α.

Determinism (DoD-6): a pure function of `draws` (seed from hash). njit hot loop (Axis 3).
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.methodology.permutation import _main_matrix, _mean_lag1_overlap, permutation_pvalue

BLOCK_SIZES: tuple[int, ...] = (5, 10, 20)  # pre-registered
DEFAULT_N_BOOT = 999
DEFAULT_ALPHA = 0.05
_DEFAULT_BLOCK = 10


@njit(cache=True)
def _block_boot_overlap_null(
    mat: npt.NDArray[np.int64], n_boot: int, block_size: int, seed: int
) -> npt.NDArray[np.float64]:
    """Lag-1 overlap null under the moving block bootstrap (njit hot loop).

    Each replica: concatenates ceil(n/block_size) overlapping blocks of length `block_size`
    (random start ∈ [0, n−block_size]), takes the first n indices, computes the mean overlap
    of consecutive draws in this resampled order.
    """
    np.random.seed(seed)
    n = mat.shape[0]
    kd = mat.shape[1]  # draw size (EJ=5, MM=20)
    n_blocks = (n + block_size - 1) // block_size
    idx = np.empty(n_blocks * block_size, dtype=np.int64)
    out = np.empty(n_boot, dtype=np.float64)
    for k in range(n_boot):
        pos = 0
        for _ in range(n_blocks):
            start = np.random.randint(n - block_size + 1)
            for j in range(block_size):
                idx[pos] = start + j
                pos += 1
        total = 0
        for t in range(n - 1):
            r1 = idx[t]
            r2 = idx[t + 1]
            c = 0
            for a in range(kd):
                for b in range(kd):
                    if mat[r1, a] == mat[r2, b]:
                        c += 1
            total += c
        out[k] = total / (n - 1)
    return out


def block_bootstrap_test(
    draws: list[DrawRecord],
    block_size: int = _DEFAULT_BLOCK,
    n_boot: int = DEFAULT_N_BOOT,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Serial-dependence test with a moving block bootstrap null (an alternative null).

    H0: the serial structure is explained by within-block dependence of length `block_size`.
    Statistic = lag-1 serial overlap. reject_h0 ⇔ p < alpha (right tail — overlap breaks through
    the block null). More conservative than shuffle for dependence at scale ≤ block_size.
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"block_bootstrap_test requires >=4 draws, got {n}")
    if block_size < 1 or block_size > n:
        raise ValueError(f"block_size={block_size} out of [1, n={n}]")
    mat = _main_matrix(draws)
    obs = _mean_lag1_overlap(mat)
    null = _block_boot_overlap_null(mat, n_boot, block_size, seed & 0xFFFFFFFF)
    p_value = permutation_pvalue(obs, null)
    return TestResult(
        test_name="block_bootstrap_serial_overlap",
        statistic=obs,
        p_value=p_value,
        reject_h0=bool(p_value < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_boot": n_boot,
            "block_size": block_size,
            "null_mean_overlap": float(null.mean()),
            "h0": "serial structure explained by within-block dependence",
            "null": f"moving block bootstrap (block={block_size})",
        },
    )


def block_bootstrap_detector(
    block_size: int = _DEFAULT_BLOCK,
    n_boot: int = DEFAULT_N_BOOT,
    alpha: float = DEFAULT_ALPHA,
    base_seed: int = 20260531,
) -> Detector:
    """Factory for a detector matching `calibration.Detector`. Pure-function reseed (DoD-6)."""
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _main_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return block_bootstrap_test(
            draws, block_size=block_size, n_boot=n_boot, alpha=alpha, seed=seed
        )

    return detector
