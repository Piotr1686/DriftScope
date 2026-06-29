"""K4-MMD Kernel Two-Sample Test (W4).

Maximum Mean Discrepancy (Gretton et al. 2012) on frequency vectors p ∈ Δ⁴⁹
computed per sliding window (preregistration_v3 §3). A two-sample test: whether two
sets of frequency vectors come from the same distribution.

**Framing (W4 decision, 2026-05-31):** §3 pins the input space (Δ⁴⁹ per window), the
kernel (Gaussian RBF), the bandwidth (median heuristic, anti-leakage), the FPR ≤ 7.5%
threshold — but does NOT pin what is X and what is Y for a single stream. The choice:
**homogeneity to uniform** — X = windows of the observed stream, Y = windows of freshly
generated uniform 5/50 (`generate_uniform_draws`, the same n). The test rejects when the
distribution of the observation's windowed frequency vectors departs from uniform. It catches
freq_shift (mean shift), trend (global shift) and autocorr (window over-dispersion); by
design BLIND to pair_corr (joint, marginal ~uniform) → motivates the W6 co-occurrence test.
The framing choice is an implementation detail (outside prereg §3); changing the method
(kernel/input/bandwidth) would require preregistration_v4.

**Window vs real n:** §3 says N=200, §4 spec curve N ∈ {100,200,400}. That concerns the
FULL real stream (~958 draws). In DriftSim per-regime calibration n is small
(R1=133/R2=389/R3=436 < 200), so the window is smaller and set by the `window` parameter.
A sample-size adaptation, NOT a method change.

Numba (Axis 3): the permutation null is computed in a `@njit(cache=True)` hot loop over a
pre-computed Gram matrix (PoC: 10–30× for MMD). joblib NEVER over single permutations.

RBF/distances are computed by hand (`_pairwise_sq_dists`/`_rbf_gram`) instead of sklearn
`pairwise_kernels` (despite the CLAUDE.md hint) — DELIBERATELY: the Gram matrix goes straight
into the njit hot loop, no sklearn import on the hot path and zero numerical-regression risk.
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.driftsim.null_uniform import (
    Regime,
    generate_generic_uniform,
    generate_uniform_draws,
)

_MAIN_POOL_SIZE = 50  # main pool 1-50 → frequency vector p ∈ Δ⁴⁹ (EJ default; MM=80)

# Default parameters. WINDOW=200 = the §3 value for the full stream; per-regime calibration
# overrides it to smaller (n < 200). No DEFAULT_STEP: `step` is REQUIRED in
# `sliding_frequency_vectors` — a default step was a footgun (overlap → FPR~1.0).
DEFAULT_WINDOW = 200
DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05


# ---------------------------------------------------------------------------
# Frequency vectors p ∈ Δ⁴⁹
# ---------------------------------------------------------------------------

def _main_matrix(draws: list[DrawRecord]) -> npt.NDArray[np.int64]:
    """Matrix (n_draws, 5) of main numbers (1-based). MMD reads only the main pool."""
    return np.array([d.main_numbers for d in draws], dtype=np.int64)


def frequency_vector(draws: list[DrawRecord]) -> npt.NDArray[np.float64]:
    """Marginal frequency vector p ∈ Δ^(pool-1) (sum=1) of the main pool for a set of draws."""
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    return _block_frequency(_main_matrix(draws), pool)


def _block_frequency(
    main_block: npt.NDArray[np.int64], pool: int = _MAIN_POOL_SIZE
) -> npt.NDArray[np.float64]:
    """Frequency vector (pool,) for a block of main numbers (w, k); normalized to sum 1."""
    counts = np.bincount(main_block.ravel() - 1, minlength=pool).astype(float)
    total = counts.sum()
    return counts / total if total > 0 else counts


def sliding_frequency_vectors(
    draws: list[DrawRecord],
    window: int,
    step: int,
) -> npt.NDArray[np.float64]:
    """Frequency vectors Δ^(pool-1) from a sliding `window` (step `step`).

    Returns a matrix (n_windows, pool). Each row = the marginal main-pool frequency in one
    window of consecutive draws. The pool dimension is derived from the records (EJ=50/MM=80).

    `step` is REQUIRED (no default): under the MMD permutation null
    (`mmd_permutation_test`) the windows must be NON-OVERLAPPING (step >= window), otherwise
    window correlation breaks exchangeability → FPR~1.0. The absence of a default step forces
    a deliberate choice.

    Raises:
        ValueError: when `window` > the number of draws or `window`/`step` <= 0.
    """
    if window <= 0 or step <= 0:
        raise ValueError(f"window and step must be > 0 (window={window}, step={step})")
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    mains = _main_matrix(draws)
    n = mains.shape[0]
    if window > n:
        raise ValueError(f"window={window} > number of draws={n} — the window does not fit")
    vectors = [
        _block_frequency(mains[start : start + window], pool)
        for start in range(0, n - window + 1, step)
    ]
    return np.asarray(vectors, dtype=float)


# ---------------------------------------------------------------------------
# Gaussian RBF + median heuristic
# ---------------------------------------------------------------------------

def _pairwise_sq_dists(
    A: npt.NDArray[np.float64], B: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Matrix of squared Euclidean distances ||a_i - b_j||² (clipped to >= 0)."""
    aa = np.sum(A * A, axis=1)[:, None]
    bb = np.sum(B * B, axis=1)[None, :]
    return np.maximum(aa + bb - 2.0 * A @ B.T, 0.0)


def median_heuristic(X: npt.NDArray[np.float64]) -> float:
    """Bandwidth σ = median of pairwise Euclidean distances in X (Gretton 2012).

    Anti-leakage (§3): computed EXCLUSIVELY on the training window (the passed X = observation),
    never on the combined X∪Y. Degeneracy (median 0 — e.g. identical vectors) → 1.0.
    """
    if X.shape[0] < 2:
        return 1.0
    sq = _pairwise_sq_dists(X, X)
    iu = np.triu_indices(X.shape[0], k=1)
    dist = np.sqrt(sq[iu])
    med = float(np.median(dist))
    return med if med > 0.0 else 1.0


def _rbf_gram(
    A: npt.NDArray[np.float64], B: npt.NDArray[np.float64], bandwidth: float
) -> npt.NDArray[np.float64]:
    """Gaussian RBF Gram matrix: k(a,b) = exp(-||a-b||² / (2σ²))."""
    return np.exp(-_pairwise_sq_dists(A, B) / (2.0 * bandwidth * bandwidth))


def mmd_rbf_squared(
    X: npt.NDArray[np.float64], Y: npt.NDArray[np.float64], bandwidth: float
) -> float:
    """Unbiased MMD² estimator (Gretton 2012, eq. 3) with a Gaussian RBF.

    Excludes the diagonal (i≠j) in the within-sample terms. May be slightly negative
    (a property of the unbiased estimator) when X and Y come from the same distribution.
    """
    m, n = X.shape[0], Y.shape[0]
    if m < 2 or n < 2:
        raise ValueError(f"MMD² requires >=2 observations in each sample (m={m}, n={n})")
    k_xx = _rbf_gram(X, X, bandwidth)
    k_yy = _rbf_gram(Y, Y, bandwidth)
    k_xy = _rbf_gram(X, Y, bandwidth)
    term_xx = (k_xx.sum() - np.trace(k_xx)) / (m * (m - 1))
    term_yy = (k_yy.sum() - np.trace(k_yy)) / (n * (n - 1))
    term_xy = k_xy.sum() / (m * n)
    return float(term_xx + term_yy - 2.0 * term_xy)


# ---------------------------------------------------------------------------
# Permutation null — Numba hot loop (Axis 3) over a pre-computed Gram matrix
# ---------------------------------------------------------------------------

@njit(cache=True)
def _mmd2_permuted(gram: npt.NDArray[np.float64], perm: npt.NDArray[np.int64], m: int) -> float:
    """Unbiased MMD² for the split given by permutation `perm` of the pool Z=[X;Y] indices.

    The first `m` indices of perm → X', the rest → Y'. Indexes the pre-computed `gram` matrix
    (L×L), so the kernel is computed once and each permutation is just a summation.
    """
    length = gram.shape[0]
    n = length - m
    s_xx = 0.0
    for i in range(m):
        pi = perm[i]
        for j in range(m):
            if i != j:
                s_xx += gram[pi, perm[j]]
    s_yy = 0.0
    for i in range(m, length):
        pi = perm[i]
        for j in range(m, length):
            if i != j:
                s_yy += gram[pi, perm[j]]
    s_xy = 0.0
    for i in range(m):
        pi = perm[i]
        for j in range(m, length):
            s_xy += gram[pi, perm[j]]
    return s_xx / (m * (m - 1)) + s_yy / (n * (n - 1)) - 2.0 * s_xy / (m * n)


@njit(cache=True)
def _permutation_null(
    gram: npt.NDArray[np.float64], perms: npt.NDArray[np.int64], m: int
) -> npt.NDArray[np.float64]:
    """MMD² null distribution for `perms.shape[0]` label permutations (hot loop)."""
    n_perm = perms.shape[0]
    out = np.empty(n_perm, dtype=np.float64)
    for p in range(n_perm):
        out[p] = _mmd2_permuted(gram, perms[p], m)
    return out


def mmd_permutation_test(
    X: npt.NDArray[np.float64],
    Y: npt.NDArray[np.float64],
    n_perm: int = DEFAULT_N_PERM,
    rng: np.random.Generator | None = None,
    bandwidth: float | None = None,
    alpha: float = DEFAULT_ALPHA,
) -> TestResult:
    """MMD² test with a permutation (shuffled) null over window labels.

    H0: X and Y come from the same distribution. The null shuffles the labels of the
    combined pool Z=[X;Y] (Gretton 2012 §8). p-value = (1 + #{null >= obs}) / (n_perm+1)
    (a conservative +1 estimator, MC-correct).

    WARNING (exchangeability): the null assumes the L=m+n rows of X∪Y are EXCHANGEABLE
    under H0. For windowed vectors this means NON-OVERLAPPING windows (step >= window) —
    overlapping windows are within-sample correlated, break exchangeability and give FPR~1.0.
    The function CANNOT detect overlap itself (it only gets matrices) — that is the caller's
    responsibility (see `mmd_uniform_detector`).

    Args:
        X: (m, d) — observation frequency vectors (training; bandwidth source). m >= 2.
        Y: (n, d) — reference frequency vectors. n >= 2.
        n_perm: number of label permutations.
        rng: NumPy generator (the only source of randomness); None → default_rng().
        bandwidth: RBF σ; None → median_heuristic(X) (anti-leakage, §3).
        alpha: rejection threshold.

    Raises:
        ValueError: when m < 2 or n < 2 (the unbiased estimator divides by m*(m-1)).
    """
    if rng is None:
        rng = np.random.default_rng()
    m, n = X.shape[0], Y.shape[0]
    if m < 2 or n < 2:
        raise ValueError(
            f"MMD² requires >=2 windows in each sample (m={m}, n={n}); "
            "increase n_draws or decrease window."
        )
    if bandwidth is None:
        bandwidth = median_heuristic(X)  # anti-leakage: training window only (X)

    pooled = np.vstack([X, Y])
    gram = _rbf_gram(pooled, pooled, bandwidth)
    length = m + n

    observed = _mmd2_permuted(gram, np.arange(length, dtype=np.int64), m)

    perms = np.empty((n_perm, length), dtype=np.int64)
    for p in range(n_perm):
        perms[p] = rng.permutation(length)
    null = _permutation_null(gram, perms, m)

    p_value = (1.0 + float(np.sum(null >= observed))) / (n_perm + 1.0)
    return TestResult(
        test_name="mmd_rbf_permutation",
        statistic=observed,
        p_value=p_value,
        reject_h0=bool(p_value < alpha),
        metadata={
            "alpha": alpha,
            "n_perm": n_perm,
            "bandwidth": bandwidth,
            "m_windows": m,
            "n_windows": n,
            "h0": "obs window freq ~ uniform reference",
        },
    )


# ---------------------------------------------------------------------------
# Detector for calibration.py (framing: homogeneity to uniform)
# ---------------------------------------------------------------------------

def mmd_uniform_detector(
    window: int = 25,
    step: int | None = None,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    ref_regime: Regime = "R2",
    base_seed: int = 20260531,
    bandwidth_mult: float = 1.0,
) -> Detector:
    """Factory for an MMD detector matching the `calibration.Detector` interface.

    Test: MMD²(observation windows, uniform-reference windows). The reference is generated by
    `generate_uniform_draws` with the same length as the observation (symmetric
    exchangeability under the null → clean FPR calibration). The main pool is independent of
    the regime (always 5/50), so `ref_regime` does not affect the frequency vectors.

    **NON-OVERLAPPING windows (step = window) — required for calibration.** The test's null
    is a permutation of the combined window-pool labels, which assumes EXCHANGEABILITY of
    units. Overlapping windows (step < window) are strongly correlated (within-X) and
    independent across streams (X⊥Y) → exchangeability broken → observed MMD² systematically
    > permutation null → FPR ~1.0 (measured empirically W4, 2026-05-31). Hence `step`
    defaults to `window` and `step < window` is FORBIDDEN. (The §3 "sliding window" does not
    pin the step; the §3 FPR ≤ 7.5% requires non-overlap under this null.)

    Default `window=25` (step=25): calibration on real n gives FPR ≤ 7.5% across all
    regimes (R1 n=133 → 5 windows, R2 → 15, R3 → 17). For the full stream (~958) use
    `window=200` (§3). R1 (n=133) is at the data limit for windowed MMD — lower power.

    Determinism (DoD-6): the detector is a PURE FUNCTION of the input. Each call's rng
    is seeded deterministically from the CONTENTS of `draws` (a digest of the main-number
    matrix ⊕ `base_seed`), so the result depends solely on (draws, base_seed) — NOT on the
    order or the number of earlier calls. Two fresh detector instances on the same `draws`
    give an identical p-value; different `draws` → independent streams. Seeding from the hash
    of the observation introduces no bias: the reference stays uniform regardless of the seed,
    and the seed→sample mapping is uncorrelated with the observation's deviation.

    `bandwidth_mult` (spec curve §4): bandwidth multiplier relative to the median heuristic
    (σ = bandwidth_mult · median_heuristic(X)). 1.0 = the default heuristic; {0.5, 2.0}
    are spec-curve points. Anti-leakage preserved (the heuristic is computed on X only).
    """
    actual_step = window if step is None else step
    if bandwidth_mult <= 0.0:
        raise ValueError(f"bandwidth_mult must be > 0, got {bandwidth_mult}")
    if actual_step < window:
        raise ValueError(
            f"step={actual_step} < window={window}: overlapping windows break "
            "permutation exchangeability → FPR ~1.0. Use step >= window (non-overlap)."
        )

    def detector(draws: list[DrawRecord]) -> TestResult:
        n = len(draws)
        n_windows = (n - window) // actual_step + 1 if n >= window else 0
        if n_windows < 2:
            raise ValueError(
                f"n_draws={n} yields {n_windows} windows at window={window}/step={actual_step}; "
                "MMD requires >=2 windows — increase n_draws or decrease window."
            )
        # Seed purely from the contents of draws (⊕ base_seed) → the detector is reproducible
        # regardless of call order (DoD-6). 8B digest of the main-number matrix.
        digest = hashlib.blake2b(_main_matrix(draws).tobytes(), digest_size=8).digest()
        seed_int = int.from_bytes(digest, "little")
        rng = np.random.default_rng(np.random.SeedSequence([base_seed, seed_int]))

        # Uniform reference of the same length. EJ (pool=50) → the existing per-regime generator
        # (bit-identical, DoD-6); a different pool (e.g. MM 20/80) → generic uniform k-of-pool.
        pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
        if pool == _MAIN_POOL_SIZE:
            reference = generate_uniform_draws(n, ref_regime, rng)
        else:
            k = len(draws[0].main_numbers)
            reference = generate_generic_uniform(n, pool, k, rng)
        x = sliding_frequency_vectors(draws, window, actual_step)
        y = sliding_frequency_vectors(reference, window, actual_step)
        bandwidth = bandwidth_mult * median_heuristic(x)  # anti-leakage: σ from X only
        result = mmd_permutation_test(
            x, y, n_perm=n_perm, rng=rng, alpha=alpha, bandwidth=bandwidth
        )
        return result.model_copy(
            update={
                "metadata": {
                    **result.metadata,
                    "window": window,
                    "step": actual_step,
                    "bandwidth_mult": bandwidth_mult,
                }
            }
        )

    return detector
