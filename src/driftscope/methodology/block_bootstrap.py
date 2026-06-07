"""Block bootstrap — alternatywny null zachowujacy zaleznosc krotkozasiegowa (W6).

Permutacyjny null (`permutation.py`, `recurrence.py`) zaklada PELNA wymienialnosc (iid) —
shuffle niszczy CALA strukture szeregowa. Moving block bootstrap (MBB) jest alternatywnym,
bardziej KONSERWATYWNYM nullem: resampluje nakladajace sie BLOKI kolejnych losowan, wiec
zachowuje zaleznosc w obrebie bloku (dlugosci `block_size`), a losowo laczy bloki. Sygnal
ktory przebija ten null NIE jest wyjasniony zaleznoscia krotkozasiegowa skali `block_size`.

Block size ∈ {5, 10, 20} (pre-registered). Statystyka domyslna = lag-1 serial overlap
(ta sama co `permutation.serial_overlap_test`) → bezposrednie porownanie obu nulli:
- shuffle (permutation): bardzo czuly na autocorr (lag-1) — power ~1.0.
- block bootstrap: ABSORBUJE lag-1 w obrebie bloku → niska power na autocorr (cecha:
  rozroznia zaleznosc krotkozasiegowa od dluzszego zasiegu). Luka shuffle−block = sygnatura
  zasiegu zaleznosci. Na nullu iid oba daja FPR ≈ α.

Determinizm (DoD-6): detektor czysta funkcja `draws` (seed z hash). njit hot loop (Os 3).
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
    """Null lag-1 overlap pod moving block bootstrap (njit hot loop).

    Kazda replika: skleja ceil(n/block_size) nakladajacych sie blokow dlugosci `block_size`
    (losowy start ∈ [0, n−block_size]), bierze pierwsze n indeksow, liczy sredni overlap
    kolejnych losowan w tej resamplowanej kolejnosci.
    """
    np.random.seed(seed)
    n = mat.shape[0]
    kd = mat.shape[1]  # rozmiar losowania (EJ=5, MM=20)
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
    """Test zaleznosci szeregowej z nullem moving block bootstrap (alternatywny null).

    H0: struktura szeregowa wyjasniona zaleznoscia w obrebie blokow dlugosci `block_size`.
    Statystyka = lag-1 serial overlap. reject_h0 ⇔ p < alpha (prawy ogon — overlap przebija
    null blokowy). Bardziej konserwatywny niz shuffle dla zaleznosci skali ≤ block_size.
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"block_bootstrap_test wymaga >=4 losowan, otrzymano {n}")
    if block_size < 1 or block_size > n:
        raise ValueError(f"block_size={block_size} poza [1, n={n}]")
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
    """Fabryka detektora zgodnego z `calibration.Detector`. Pure-function reseed (DoD-6)."""
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _main_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return block_bootstrap_test(
            draws, block_size=block_size, n_boot=n_boot, alpha=alpha, seed=seed
        )

    return detector
