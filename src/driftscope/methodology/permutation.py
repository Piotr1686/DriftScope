"""Shuffle test core — the canonical permutation engine (W6, DoD-2).

Pattern (PoC Step 6, 2026-05-17): `@njit(cache=True)` controls the ENTIRE inner permutation
loop; `joblib.Parallel` (when needed) over CONFIGURATIONS (test, regime, kernel, seed),
NEVER over single permutations (16× slower — MEMORY.md).

**The statistic MUST depend on ORDER** — we permute the draw order, so a statistic invariant
to row permutation (e.g. global chi² of counts) is degenerate (identical for every permutation
→ p=1). The canonical order-dependent test: **lag-1 serial overlap** — the mean number of
shared numbers between consecutive draws |S_t ∩ S_{t+1}|. Under iid the draws are independent;
autocorr (boosting numbers from the previous draw) raises the overlap → right tail. Shuffling
the order preserves the margins, breaks the serial structure → a clean null (DoD-2).

`permutation_pvalue` is the shared primitive (1 + #{null ≥ obs})/(B+1) — a conservative Monte
Carlo estimator (E[FPR] ≤ α). Determinism (DoD-6): a pure function of `draws` (seed from hash).
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05


def permutation_pvalue(observed: float, null_stats: npt.NDArray[np.float64]) -> float:
    """One-sided (right tail) Monte Carlo p-value: (1 + #{null ≥ obs})/(B + 1).

    The `+1` in numerator and denominator → a provably conservative estimator (E[FPR] ≤ α under
    H0), never returns 0. The shared primitive for all of the framework's permutation tests.
    """
    b = null_stats.size
    ge = int(np.sum(null_stats >= observed))
    return (1 + ge) / (b + 1)


def _main_matrix(draws: list[DrawRecord]) -> npt.NDArray[np.int64]:
    """Matrix (n, k) of main numbers (1-based); k from the data (EJ=5, MM=20)."""
    return np.array([d.main_numbers for d in draws], dtype=np.int64)


@njit(cache=True)
def _mean_lag1_overlap(mat: npt.NDArray[np.int64]) -> float:
    """Mean number of shared numbers between consecutive draws (order-dependent).

    The draw size k = mat.shape[1] (derived from the data: EJ=5, MM=20).
    """
    n = mat.shape[0]
    if n < 2:
        return 0.0
    k = mat.shape[1]
    total = 0
    for t in range(n - 1):
        c = 0
        for a in range(k):
            for b in range(k):
                if mat[t, a] == mat[t + 1, b]:
                    c += 1
        total += c
    return total / (n - 1)


@njit(cache=True)
def _shuffle_overlap_null(
    mat: npt.NDArray[np.int64], n_perm: int, seed: int
) -> npt.NDArray[np.float64]:
    """Lag-1 overlap null under an ORDER permutation (njit hot loop — the PoC pattern)."""
    np.random.seed(seed)
    n = mat.shape[0]
    kd = mat.shape[1]  # draw size (EJ=5, MM=20)
    idx = np.arange(n)
    out = np.empty(n_perm, dtype=np.float64)
    for k in range(n_perm):
        # Fisher-Yates on idx
        for i in range(n - 1, 0, -1):
            j = np.random.randint(i + 1)
            tmp = idx[i]
            idx[i] = idx[j]
            idx[j] = tmp
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


def serial_overlap_test(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Permutation test of serial dependence (lag-1 overlap; DoD-2).

    H0: the draw order is exchangeable (iid). Statistic = mean overlap of consecutive draws;
    null = order permutation. reject_h0 ⇔ p < alpha (right tail — excess overlap).
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"serial_overlap_test requires >=4 draws, got {n}")
    mat = _main_matrix(draws)
    obs = _mean_lag1_overlap(mat)
    null = _shuffle_overlap_null(mat, n_perm, seed & 0xFFFFFFFF)
    p_value = permutation_pvalue(obs, null)
    return TestResult(
        test_name="serial_lag1_overlap",
        statistic=obs,
        p_value=p_value,
        reject_h0=bool(p_value < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_perm": n_perm,
            "null_mean_overlap": float(null.mean()),
            "h0": "draw order exchangeable (uniform-iid, no serial dependence)",
            "null": "draw-order permutation",
        },
    )


def serial_overlap_detector(
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    base_seed: int = 20260531,
) -> Detector:
    """Factory for a detector matching `calibration.Detector`. Pure-function reseed (DoD-6)."""
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _main_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return serial_overlap_test(draws, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
