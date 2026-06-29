"""Recurrence / gap analysis (W6, preregistration §5b).

Time (number of draws) between consecutive appearances of a given number. Under the
uniform-iid null gap ~ Geometric(q), q = 5/50 = 0.1 for the main pool. This module tests the
TEMPORAL structure of number appearances — a dimension orthogonal to the margin (chi²) and to
co-occurrences (§5c).

**What it detects, and what it does NOT (the key property of the null):** null = a permutation
of the draw ORDER (draw-order shuffle). The permutation preserves each number's COUNT → the
test CONDITIONS on the margin. Consequences:
- DETECTS clumping/runs (autocorr): a number reappears faster than Geometric → an excess of
  short gaps; shuffling destroys this → observed in the tail of the null.
- DETECTS periodicity / non-stationarity of arrivals (seasonality, trend) — the gap pattern
  departs from exchangeable.
- BLIND to freq_shift (purely marginal): a higher count gives shorter gaps, BUT the shuffle
  has the same count → the null shifts too → the marginal is conditioned out. This is a FEATURE:
  the marginal is caught by chi², recurrence adds the temporal dimension.

**Statistic (KS vs Geometric, permutation-calibrated):** per number D_k = the KS distance of
the empirical gap CDF from Geometric(q). ⚠️ NOT the analytic KS p-value (invalid for discrete
distributions — preregistration §5b). Omnibus = **max_k D_k** (like max-pair in §5c),
null = draw-order shuffle (max_k D_k per shuffle), location: the most anomalous number.
p = (1 + #{maxD_perm ≥ maxD_obs})/(n_perm+1).

Additionally (§5b diagnostics, NOT the decision engine):
- **Nelson-Aalen** cumulative hazard per number — linearity (slope ≈ q) = constant
  intensity = consistency with uniform.
- **EVT max-gap** — the maximum gap asymptotically has a Gumbel distribution (geometric gaps
  in the Gumbel domain of attraction); the Gumbel p-value as a sanity check for extremely long gaps.

Determinism (DoD-6): a PURE FUNCTION of the input — the shuffle seed from the hash of draws.
Feeds Family B FDR (§5).
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt

from driftscope.core.types import Detector, DrawRecord, TestResult

_MAIN_POOL_SIZE = 50
_MAIN_DRAW = 5
_Q_MAIN = _MAIN_DRAW / _MAIN_POOL_SIZE  # 0.1 — P(number in one draw) under uniform

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05


# ---------------------------------------------------------------------------
# Gaps
# ---------------------------------------------------------------------------

def _incidence_matrix(draws: list[DrawRecord]) -> npt.NDArray[np.int8]:
    """Binary matrix (n_draws, pool): M[t, k]=1 ⇔ number (k+1) in draw t.

    The pool width is derived from the records (`draws[0].pool_size`; EJ=50, MM=80).
    """
    n = len(draws)
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    m = np.zeros((n, pool), dtype=np.int8)
    for t, d in enumerate(draws):
        for k in d.main_numbers:
            m[t, k - 1] = 1
    return m


def number_gaps(draws: list[DrawRecord], number: int) -> npt.NDArray[np.int64]:
    """Gaps (in draws) between consecutive appearances of `number` (1-based).

    Gap = the index difference of consecutive appearances (>=1). Returns [] when the number
    appears < 2 times (no gap).
    """
    col = _incidence_matrix(draws)[:, number - 1]
    return _gaps_from_column(col)


def _gaps_from_column(col: npt.NDArray[np.int8]) -> npt.NDArray[np.int64]:
    """Gaps from a binary appearance column (1D 0/1)."""
    pos = np.flatnonzero(col)
    if pos.size < 2:
        return np.empty(0, dtype=np.int64)
    return np.diff(pos).astype(np.int64)


def _ks_vs_geometric(gaps: npt.NDArray[np.int64], q: float) -> float:
    """KS distance of the empirical gap CDF from Geometric(q) on {1,2,...}.

    Geometric CDF: F(g) = 1 − (1−q)^g for g >= 1. Two-sided variant (upper and lower
    jumps of the empirical CDF). Returns 0.0 for < 2 gaps (no signal).
    """
    m = gaps.size
    if m < 2:
        return 0.0
    g = np.sort(gaps)
    cdf_geom = 1.0 - (1.0 - q) ** g
    emp_upper = np.arange(1, m + 1) / m
    emp_lower = np.arange(0, m) / m
    d_upper = np.abs(emp_upper - cdf_geom).max()
    d_lower = np.abs(emp_lower - cdf_geom).max()
    return float(max(d_upper, d_lower))


def _max_ks_over_numbers(m: npt.NDArray[np.int8], q: float) -> tuple[float, int]:
    """(max_k D_k, argmax_k) over all pool numbers (m.shape[1]) for the matrix `m`."""
    best_d = 0.0
    best_k = 0
    for k in range(m.shape[1]):
        d = _ks_vs_geometric(_gaps_from_column(m[:, k]), q)
        if d > best_d:
            best_d = d
            best_k = k
    return best_d, best_k


# ---------------------------------------------------------------------------
# Nelson-Aalen cumulative hazard (§5b diagnostics)
# ---------------------------------------------------------------------------

def nelson_aalen(
    gaps: npt.NDArray[np.int64],
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]]:
    """Nelson-Aalen cumulative-hazard estimator from gaps (~20 LOC, no lifelines).

    Treats gaps as event times (recurrence). The step hazard at time t = the number of
    events at t / the number "at risk" (gaps >= t). Returns (times, cumhaz) — a step function.
    Under uniform-iid the cumulative hazard rises ~linearly with slope q/(1−q)·... ≈ constant
    intensity; curvature signals non-stationarity of the intensity.
    """
    if gaps.size == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
    times = np.unique(gaps)
    cumhaz = np.empty(times.size, dtype=np.float64)
    acc = 0.0
    for i, t in enumerate(times):
        at_risk = int((gaps >= t).sum())
        events = int((gaps == t).sum())
        if at_risk > 0:
            acc += events / at_risk
        cumhaz[i] = acc
    return times, cumhaz


def nelson_aalen_linearity_deviation(gaps: npt.NDArray[np.int64]) -> float:
    """Max deviation of the cumulative hazard from the line (0,0)→(t_max, H_max).

    0 = perfectly linear (constant intensity, consistent with uniform); grows with curvature
    (varying intensity). A pure diagnostic number, NOT permutation-tested here.
    """
    times, cumhaz = nelson_aalen(gaps)
    if times.size < 3:
        return 0.0
    t0, t1 = float(times[0]), float(times[-1])
    h1 = float(cumhaz[-1])
    if t1 == t0:
        return 0.0
    line = h1 * (times - t0) / (t1 - t0)
    return float(np.abs(cumhaz - line).max())


# ---------------------------------------------------------------------------
# EVT max-gap (Gumbel, §5b diagnostics)
# ---------------------------------------------------------------------------

def evt_max_gap_pvalue(gaps: npt.NDArray[np.int64], q: float) -> tuple[int, float]:
    """(max_gap, p-value) of an extremely long gap per the Gumbel asymptotics.

    For gaps ~ Geometric(q), the maximum of m gaps approximately follows the maximum of a
    geometric distribution: P(max <= x) ≈ (1 − (1−q)^x)^m. p-value = P(max >= obs)
    = 1 − (1 − (1−q)^(obs−1))^m (uses obs−1 for the right tail, conservatively).
    A sanity check for a single extreme gap; does NOT replace the KS test.
    """
    if gaps.size == 0:
        return 0, 1.0
    m = gaps.size
    obs = int(gaps.max())
    # P(single gap >= obs) = (1−q)^(obs−1); P(max < obs) = (1 − (1−q)^(obs−1))^m
    tail_single = (1.0 - q) ** (obs - 1)
    p = 1.0 - (1.0 - tail_single) ** m
    return obs, float(min(max(p, 0.0), 1.0))


# ---------------------------------------------------------------------------
# Recurrence test (gap GoF, permutation-calibrated)
# ---------------------------------------------------------------------------

def gap_recurrence_test(
    draws: list[DrawRecord],
    q: float | None = None,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Permutation test of the temporal gap structure (preregistration §5b).

    H0: each number's appearances are exchangeable in time (an iid pattern). The omnibus
    statistic = max_k KS(gaps_k, Geometric(q)); null = a permutation of the draw order (preserves
    counts → conditions on the margin). reject_h0 ⇔ p < alpha. Locates the most
    anomalous number (top_number, 1-based).

    `q` = P(number in one draw) under uniform; None → derived from the data as
    k/pool (EJ=5/50=0.1, MM=20/80=0.25).
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"gap_recurrence_test requires >=4 draws, got {n}")
    if q is None:
        q = len(draws[0].main_numbers) / draws[0].pool_size
    m0 = _incidence_matrix(draws)
    d_obs, k_obs = _max_ks_over_numbers(m0, q)

    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n_perm):
        perm = rng.permutation(n)
        d_perm, _ = _max_ks_over_numbers(m0[perm], q)
        if d_perm >= d_obs:
            ge += 1
    p_value = (1 + ge) / (n_perm + 1)

    return TestResult(
        test_name="gap_recurrence_maxks",
        statistic=d_obs,
        p_value=p_value,
        reject_h0=bool(p_value < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_perm": n_perm,
            "q": q,
            "top_number": k_obs + 1,   # most anomalous number (1-based)
            "h0": "per-number arrivals exchangeable in time (uniform-iid)",
            "null": "draw-order permutation (counts preserved → conditions on marginal)",
        },
    )


def recurrence_detector(
    q: float | None = None,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    base_seed: int = 20260531,
) -> Detector:
    """Factory for a detector matching `calibration.Detector` (the W3/W4/W6 harness interface).

    Determinism (DoD-6): a pure function of `draws` — the permutation seed from a digest of
    the contents of `draws` ⊕ `base_seed` (like k4_mmd / cooccurrence).
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _incidence_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return gap_recurrence_test(draws, q=q, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
