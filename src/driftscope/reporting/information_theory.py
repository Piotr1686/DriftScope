"""Information-theoretic audit — Lempel-Ziv 1976 complexity (wow option #3, reporting layer).

A reporting/analysis layer (a SUPPLEMENT, NOT methodology/): this detector is not a 4th
Disagreement Protocol pillar — that stays three-way (h1/mmd/cooccurrence, DoD-4=3/3, §6.5).
Like `prng_benchmark` and `disagreement`, the module is a non-prereg supplement (NOT subject
to the preregistration §0 discipline) — see the `audit-framework-wow-options` memory.

**Idea:** a truly random sequence is INCOMPRESSIBLE. A deviation from uniform-iid introduces
structure (repeating substrings) → LOWER algorithmic complexity. We measure it with the
canonical Lempel-Ziv 1976 production complexity (Kaspar-Schuster 1987) — a pure algorithm, no
dependence on a compressor version (DoD-6 trivial, citable). We attach the bz2 ratio as an
intuitive cross-check in `metadata` (it does NOT enter `reject_h0`).

**Null — order-shuffle (margin-conditioned):** the stream = the CHRONOLOGICALLY concatenated
blocks of the sorted 5 main numbers. The null permutes the ORDER of blocks (draws), preserving
(a) the marginal (the symbol multiset = number frequencies) and (b) within-draw co-occurrences
(the block of 5 numbers untouched) — breaking ONLY the between-draw structure
(period / autocorr). This makes IT COMPLEMENTARY: blind to a pure marginal (chi²/MMD catch it)
and to the within-draw joint (co-occurrence catches it), sensitive to the SEQUENTIAL structure
that none of the three families targets directly.

**Statistic:** the raw complexity c(obs). Structure → lower c → the left tail of the null:
  p = (1 + #{c_perm ≤ c_obs}) / (n_perm + 1),   reject_h0 ⇔ p < alpha.
`statistic` reports the NORMALIZED complexity c_norm = c · ln(L) / (L · ln(a)) (a=alphabet,
L=length; → ~1 for random) — monotonic in c, so the p is the same.

Determinism (DoD-6): the detector is a PURE FUNCTION of the input — the order-shuffle rng is
seeded from a digest of the `draws` contents ⊕ base_seed, as in `cooccurrence`.

Numba (Axis 3): the canonical LZ76 parse in `@njit(cache=True)` (a pure function of an int array).
"""
from __future__ import annotations

import bz2
import hashlib
import math

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult

_MAIN_POOL_SIZE = 50  # alphabet: main numbers 1-50
_MAIN_DRAW = 5        # 5 numbers per draw (block size)

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05
_DEFAULT_BASE_SEED = 20260607


# ---------------------------------------------------------------------------
# Stream encoding
# ---------------------------------------------------------------------------

def _main_blocks(draws: list[DrawRecord]) -> npt.NDArray[np.int32]:
    """Matrix (n_draws, k) of the SORTED main numbers in chronological order.

    Row t = the block of draw t. Flattening with `.ravel()` gives a stream of length k·n over
    the alphabet 1-pool; permuting rows = an order-shuffle preserving blocks (the null).
    The block width k is derived from the records (EJ=5, MM=20).
    """
    n = len(draws)
    k = len(draws[0].main_numbers) if draws else _MAIN_DRAW
    blocks = np.empty((n, k), dtype=np.int32)
    for t, d in enumerate(draws):
        blocks[t] = np.sort(np.asarray(d.main_numbers, dtype=np.int32))
    return blocks


# ---------------------------------------------------------------------------
# Lempel-Ziv 1976 complexity (njit hot loop)
# ---------------------------------------------------------------------------

@njit(cache=True)
def lz76_complexity(s: npt.NDArray[np.int32]) -> int:
    """Canonical Lempel-Ziv 1976 production complexity (Kaspar-Schuster 1987).

    The number of phrases in the self-producing left-to-right parse. Bounds:
    1 ≤ c ≤ n. A constant sequence → c=2; a sequence of all distinct symbols → c=n; structure
    (repetitions) → c decreases. RNG-independent (a pure function of `s`).
    """
    n = s.shape[0]
    if n <= 1:
        return n
    c = 1
    lp = 1     # length of the already-parsed prefix
    i = 0      # comparison pointer in the history
    k = 1      # length of the current match
    k_max = 1  # longest match for the current phrase
    while True:
        if s[i + k - 1] == s[lp + k - 1]:
            k += 1
            if lp + k > n:
                c += 1
                break
        else:
            if k > k_max:
                k_max = k
            i += 1
            if i == lp:
                c += 1
                lp += k_max
                if lp + 1 > n:
                    break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    return c


def _normalized_complexity(c: int, length: int, alphabet: int = _MAIN_POOL_SIZE) -> float:
    """Normalized complexity c_norm = c · ln(L) / (L · ln(a)) (→ ~1 for random).

    `alphabet` = the symbol pool size (EJ=50, MM=80) derived from the records.
    """
    if length <= 1:
        return float(c)
    return c * math.log(length) / (length * math.log(alphabet))


def _bz2_ratio(s: npt.NDArray[np.int32]) -> float:
    """bz2 compression ratio: len(bz2(bytes)) / len(bytes). Values 1-50 fit in uint8."""
    raw = s.astype(np.uint8).tobytes()
    return len(bz2.compress(raw, compresslevel=9)) / len(raw)


# ---------------------------------------------------------------------------
# Information-theoretic test
# ---------------------------------------------------------------------------

def information_test(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Permutation test of Lempel-Ziv 1976 complexity (IT supplement, order-shuffle null).

    H0: the main numbers ~ uniform-iid (no SEQUENTIAL structure beyond the marginal + the
    within-draw joint). reject_h0 ⇔ p_value(c, left tail) < alpha.

    Null = permuting the order of draw blocks (preserves the marginal and co-occurrences,
    breaks the between-draw structure). p = (1+#{c_perm ≤ c_obs})/(n_perm+1).
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"information_test requires >=2 draws, got {n}")

    pool = draws[0].pool_size  # symbol alphabet (EJ=50, MM=80)
    blocks = _main_blocks(draws)
    obs_stream = blocks.ravel()
    length = obs_stream.shape[0]
    c_obs = lz76_complexity(obs_stream)
    bz2_obs = _bz2_ratio(obs_stream)

    rng = np.random.default_rng(seed)
    n_le_c = 0       # #{c_perm ≤ c_obs}
    n_le_bz2 = 0     # #{bz2_perm ≤ bz2_obs} — cross-check
    for _ in range(n_perm):
        perm_stream = blocks[rng.permutation(n)].ravel()
        if lz76_complexity(perm_stream) <= c_obs:
            n_le_c += 1
        if _bz2_ratio(perm_stream) <= bz2_obs:
            n_le_bz2 += 1

    p_lz = (1 + n_le_c) / (n_perm + 1)
    p_bz2 = (1 + n_le_bz2) / (n_perm + 1)

    return TestResult(
        test_name="lz76_sequential",
        statistic=_normalized_complexity(c_obs, length, pool),
        p_value=p_lz,
        reject_h0=bool(p_lz < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_perm": n_perm,
            "lz76_raw": int(c_obs),
            "lz76_norm": _normalized_complexity(c_obs, length, pool),
            "bz2_ratio": bz2_obs,      # cross-check (intuitive; does NOT enter reject_h0)
            "bz2_p": p_bz2,
            "h0": "main pool uniform-iid (no sequential structure)",
            "null": "order-shuffle (draw-block permutation; margins + joint preserved)",
        },
    )


def lz76_null_distribution(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    seed: int = 0,
) -> tuple[int, npt.NDArray[np.int64]]:
    """c_obs + the LZ76 complexity null distribution (order-shuffle) — for visualization / report.

    Returns (the observed complexity, an array of `n_perm` complexities under block permutation).
    The same null as `information_test`; split out for the demo/reporting layer (obs vs null
    histogram), without duplicating the shuffle logic.
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"lz76_null_distribution requires >=2 draws, got {n}")
    blocks = _main_blocks(draws)
    c_obs = lz76_complexity(blocks.ravel())
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=np.int64)
    for b in range(n_perm):
        null[b] = lz76_complexity(blocks[rng.permutation(n)].ravel())
    return c_obs, null


def information_detector(
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    base_seed: int = _DEFAULT_BASE_SEED,
) -> Detector:
    """Factory for a detector conforming to `core.types.Detector` (the W3/W4 harness interface).

    Determinism (DoD-6): each instance is a PURE FUNCTION of `draws`. The order-shuffle seed
    comes from a digest of the `draws` contents (the main-number matrix) ⊕ `base_seed`, so the
    result depends solely on (draws, base_seed) — as in `cooccurrence_detector`.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        blocks = _main_blocks(draws)
        digest = hashlib.blake2b(blocks.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return information_test(draws, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
