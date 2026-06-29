"""Co-occurrence test — detecting JOINT structure of number pairs (W6, preregistration §5c).

The marginal detectors (chi² §5, MMD §3) are by design BLIND to signal #5 (pair_corr):
a pair (i,j) co-occurs in one draw more often than under uniform, while EVERY single
margin stays ~uniform (W3/W4 — power ≈ FPR). This module closes the gap with a dedicated
co-occurrence test.

**Null — swap-randomization (curveball, Strona et al. 2014):** the draw×number incidence
matrix (n × 50, row sum = 5) is randomly reshuffled so as to preserve SIMULTANEOUSLY the
row sums (5 numbers/draw) and the column sums (the marginal frequency of each number), while
breaking ONLY the pairing structure. This isolates the joint signal from the marginal one —
the analytic Binomial(n, p_pair) is invalid under non-uniform margins (e.g. under
freq_shift), so the null must be permutation-based and conditioned on the margins. A
sequential chain (burn-in + thinning, Gotelli 2000; Besag-Clifford serial) — one curveball
"trade" swaps many elements at once, so it mixes faster than single edge swaps.

**Statistic — max-pair (W6 decision, §5c correction):**
  z_ij = (O_ij − E_ij) / sqrt(E_ij),   reject ⇔ max_ij z_ij in the right tail of the null.
E_ij and the null distribution from `n_perm` curveball reshuffles (E_ij = mean co-occurrence
under the null). p-value = (1 + #{maxstat_perm ≥ maxstat_obs})/(n_perm+1).

  **Rejected statistic — sum T = Σ_{i<j}(O−E)²/E (originally pinned §5c):** planted
  pair_corr is a SPARSE signal (one pair out of 1225). (a) The sum dilutes a single deviating
  pair in the noise of 1224 null pairs (null T ~ 1225 ± 49; a single pair's contribution is of
  the order of a few units → drowns → power ≈ FPR, the same blindness as chi²/MMD). (b) The chi²
  form (/E, Poisson scale) is poorly calibrated for co-occurrences — empirically FPR ~0.17 on the
  null (R3, W6). The EXTREME max-pair statistic is appropriate for the sparse alternative and
  calibrates correctly (FPR ≈ α). A structural + empirical argument on DriftSim
  (not a data-dredge on real EuroJackpot) — ratified in preregistration_v5.

**Finding W6 (validated on DriftSim, preregistration_v5):** after redesigning the
pair_corr mechanism to MARGIN-PRESERVING (forced-frac p, uniform margins — §6/v5) the
co-occurrence test yields a clean Disagreement-Protocol cell: it is the ONLY detector catching
this signal. Power (n_trials=50, n_perm=99):
  p:         0.01   0.02   0.05   0.10
  R1 (133):  0.06   0.08   0.80   1.00
  R2 (389):  0.06   0.40   1.00   1.00
  R3 (436):  0.08   0.36   1.00   1.00
At p=0.10 (the strongest): chi²=0.06, MMD=0.03 — both at the FPR floor (margins preserved
→ provably blind). FPR(null)=0.03. The Decision Gate (>70%) is met for p ≥ 0.05 in all
regimes (R1@0.05=0.80). p=0.01 is below the floor everywhere; p=0.02 floor in R1,
partial in R2/R3. The pair location (top_pair) is correct on rejection.

Determinism (DoD-6): the detector is a PURE FUNCTION of the input — the curveball rng is
seeded from the CONTENTS of `draws` (digest of the main-number matrix ⊕ base_seed), as in `k4_mmd`.

Numba (Axis 3): the curveball hot loop in `@njit(cache=True)`.
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult

_MAIN_POOL_SIZE = 50  # main pool 1-50
_MAIN_DRAW = 5        # 5 numbers per draw (incidence row sum)

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05
# Curveball chain mixing. burn-in proportional to the number of draws (orders of
# magnitude per Strona 2014: a few×n trades suffice); thinning = n trades/sample.
DEFAULT_BURN_FACTOR = 5   # burn-in = BURN_FACTOR * n_draws (min DEFAULT_BURN_MIN)
DEFAULT_BURN_MIN = 1000
DEFAULT_THIN_FACTOR = 1   # thinning = THIN_FACTOR * n_draws trades between samples


# ---------------------------------------------------------------------------
# Incidence matrix and co-occurrences
# ---------------------------------------------------------------------------

def _incidence_matrix(draws: list[DrawRecord]) -> npt.NDArray[np.int8]:
    """Binary incidence matrix (n_draws, pool): M[t, k]=1 ⇔ number (k+1) in draw t.

    Each row sum = k_drawn (main numbers); column k sum = the count of number (k+1).
    The pool width is derived from the records (`draws[0].pool_size`; EJ=50, MM=80).
    """
    n = len(draws)
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    m = np.zeros((n, pool), dtype=np.int8)
    for t, d in enumerate(draws):
        for k in d.main_numbers:
            m[t, k - 1] = 1
    return m


def _cooccurrence_upper(
    m: npt.NDArray[np.int8], iu: tuple[npt.NDArray[np.intp], npt.NDArray[np.intp]]
) -> npt.NDArray[np.float64]:
    """Upper-triangle co-occurrence vector: C_ij = #{draws with both i,j} for i<j."""
    cooc = m.T.astype(np.int64) @ m.astype(np.int64)  # (50,50), diagonal = counts
    return cooc[iu].astype(np.float64)


# ---------------------------------------------------------------------------
# Curveball swap-randomization (njit hot loop)
# ---------------------------------------------------------------------------

@njit(cache=True)
def _curveball_trades(m: npt.NDArray[np.int8], n_trades: int) -> None:
    """In-place `n_trades` curveball trades on the binary matrix `m` (mutates `m`).

    One trade: draw two distinct rows r1, r2; the columns where they DIFFER form the
    swappable pool (shared elements stay). The pool is randomly redistributed: as many
    "1"s go to r1 as it originally had → row and column sums preserved, pairing broken.
    RNG: numba's global state (seeded by `_seed_numba` before the call).
    """
    n_rows, n_cols = m.shape
    diff = np.empty(n_cols, dtype=np.int64)  # scratch: indices of differing columns
    for _ in range(n_trades):
        r1 = np.random.randint(n_rows)
        r2 = np.random.randint(n_rows)
        if r1 == r2:
            continue
        count = 0       # how many columns differ
        a_ones = 0      # how many of them belonged to r1 (that many "1"s return to r1)
        for c in range(n_cols):
            v1 = m[r1, c]
            if v1 != m[r2, c]:
                diff[count] = c
                if v1 == 1:
                    a_ones += 1
                count += 1
        if count == 0:
            continue
        # Fisher-Yates on diff[0:count]
        for i in range(count - 1, 0, -1):
            j = np.random.randint(i + 1)
            tmp = diff[i]
            diff[i] = diff[j]
            diff[j] = tmp
        # the first a_ones differing columns → r1, the rest → r2
        for idx in range(count):
            c = diff[idx]
            if idx < a_ones:
                m[r1, c] = 1
                m[r2, c] = 0
            else:
                m[r1, c] = 0
                m[r2, c] = 1


@njit(cache=True)
def _seed_numba(seed: int) -> None:
    """Seeds numba's global RNG (deterministic null for DoD-6)."""
    np.random.seed(seed)


def _permutation_cooccurrence(
    m0: npt.NDArray[np.int8],
    iu: tuple[npt.NDArray[np.intp], npt.NDArray[np.intp]],
    n_perm: int,
    burn_in: int,
    thin: int,
    seed: int,
) -> npt.NDArray[np.float64]:
    """Matrix (n_perm, n_pairs) of co-occurrences under the curveball null (chain + thinning)."""
    _seed_numba(seed)
    m = m0.copy()
    _curveball_trades(m, burn_in)
    n_pairs = iu[0].shape[0]
    out = np.empty((n_perm, n_pairs), dtype=np.float64)
    for b in range(n_perm):
        _curveball_trades(m, thin)
        out[b] = _cooccurrence_upper(m, iu)
    return out


# ---------------------------------------------------------------------------
# Co-occurrence test
# ---------------------------------------------------------------------------

def cooccurrence_test(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    burn_in: int | None = None,
    thin: int | None = None,
    seed: int = 0,
) -> TestResult:
    """Permutation co-occurrence test over pairs (preregistration §5c).

    H0: main numbers ~ uniform-iid (no joint pair structure beyond what the margins force).
    reject_h0 ⇔ p_value(max-pair) < alpha.

    Statistic = max_ij (O_ij − E_ij)/sqrt(E_ij), null = curveball (preserves both margins).
    E_ij and the null distribution from `n_perm` reshuffles. p = (1+#{perm ≥ obs})/(n_perm+1).
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"cooccurrence_test requires >=2 draws, got {n}")
    m0 = _incidence_matrix(draws)
    iu = np.triu_indices(m0.shape[1], k=1)  # upper triangle of the pool (from data: EJ=50/MM=80)
    obs = _cooccurrence_upper(m0, iu)

    burn = burn_in if burn_in is not None else max(DEFAULT_BURN_FACTOR * n, DEFAULT_BURN_MIN)
    th = thin if thin is not None else max(DEFAULT_THIN_FACTOR * n, 1)
    perm = _permutation_cooccurrence(m0, iu, n_perm, burn, th, seed)

    # E_ij = expected co-occurrence under the null (mean over permutations).
    e = perm.mean(axis=0)
    safe = e > 0.0
    sd = np.sqrt(np.where(safe, e, 1.0))  # sqrt(E) as scale (Poisson-like); guard div0

    def _max_z(c: npt.NDArray[np.float64]) -> float:
        return float(np.where(safe, (c - e) / sd, 0.0).max())

    max_obs = _max_z(obs)
    max_perm = np.array([_max_z(perm[b]) for b in range(n_perm)])
    p_max = (1 + int(np.sum(max_perm >= max_obs))) / (n_perm + 1)

    # Location of the strongest pair (1-based numbers) — diagnostic.
    z_obs = np.where(safe, (obs - e) / sd, 0.0)
    top = int(np.argmax(z_obs))
    pair = (int(iu[0][top]) + 1, int(iu[1][top]) + 1)

    return TestResult(
        test_name="cooccurrence_maxpair",
        statistic=max_obs,
        p_value=p_max,
        reject_h0=bool(p_max < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_perm": n_perm,
            "top_pair": pair,              # strongest pair (i,j), 1-based
            "top_pair_z": float(z_obs[top]),
            "h0": "main pool uniform-iid (no joint pair structure)",
            "null": "curveball swap-randomization (margins preserved)",
        },
    )


def cooccurrence_detector(
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    burn_in: int | None = None,
    thin: int | None = None,
    base_seed: int = 20260531,
) -> Detector:
    """Factory for a detector matching `calibration.Detector` (the W3/W4 harness interface).

    Determinism (DoD-6): each instance is a PURE FUNCTION of `draws`. The curveball seed
    comes from a digest of the contents of `draws` (the main-number matrix) ⊕ `base_seed`, so
    the result depends solely on (draws, base_seed) — not on call order.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _incidence_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed_int = int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)
        seed = seed_int & 0xFFFFFFFF  # numba np.random.seed expects uint32
        return cooccurrence_test(
            draws, n_perm=n_perm, alpha=alpha, burn_in=burn_in, thin=thin, seed=seed
        )

    return detector
