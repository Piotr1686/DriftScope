"""Shuffle test core — kanoniczny silnik permutacyjny (W6, DoD-2).

Wzorzec (PoC Krok 6, 2026-05-17): `@njit(cache=True)` kontroluje CALY wewnetrzny loop
permutacji; `joblib.Parallel` (gdy trzeba) nad KONFIGURACJAMI (test, regime, kernel, seed),
NIGDY nad pojedynczymi permutacjami (16× wolniejsze — MEMORY.md).

**Statystyka MUSI zalezec od KOLEJNOSCI** — permutujemy porzadek losowan, wiec statystyka
niezmiennicza na permutacje wierszy (np. globalne chi² zliczen) jest degeneracyjna (identyczna
dla kazdej permutacji → p=1). Kanoniczny order-dependent test: **lag-1 serial overlap** —
srednia liczba wspolnych liczb miedzy kolejnymi losowaniami |S_t ∩ S_{t+1}|. Pod iid losowania
sa niezalezne; autocorr (boost liczb z poprzedniego losowania) podnosi overlap → prawy ogon.
Shuffle kolejnosci zachowuje marginesy, lamie strukture szeregowa → czysty null (DoD-2).

`permutation_pvalue` to wspolny prymityw (1 + #{null ≥ obs})/(B+1) — konserwatywny estymator
Monte Carlo (E[FPR] ≤ α). Determinizm (DoD-6): detektor czysta funkcja `draws` (seed z hash).
"""
from __future__ import annotations

import hashlib
from typing import Callable

import numpy as np
from numba import njit

from driftscope.core.types import DrawRecord, TestResult

_MAIN_DRAW = 5
DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05

Detector = Callable[[list[DrawRecord]], TestResult]


def permutation_pvalue(observed: float, null_stats: np.ndarray) -> float:
    """Jednostronny (prawy ogon) p-value Monte Carlo: (1 + #{null ≥ obs})/(B + 1).

    `+1` w liczniku i mianowniku → estymator dowodliwie konserwatywny (E[FPR] ≤ α pod H0),
    nigdy nie zwraca 0. Wspolny prymityw dla wszystkich testow permutacyjnych frameworka.
    """
    b = null_stats.size
    ge = int(np.sum(null_stats >= observed))
    return (1 + ge) / (b + 1)


def _main_matrix(draws: list[DrawRecord]) -> np.ndarray:
    """Macierz (n, 5) liczb glownych (1-based)."""
    return np.array([d.main_numbers for d in draws], dtype=np.int64)


@njit(cache=True)
def _mean_lag1_overlap(mat: np.ndarray) -> float:
    """Srednia liczba wspolnych liczb miedzy kolejnymi losowaniami (order-dependent)."""
    n = mat.shape[0]
    if n < 2:
        return 0.0
    total = 0
    for t in range(n - 1):
        c = 0
        for a in range(_MAIN_DRAW):
            for b in range(_MAIN_DRAW):
                if mat[t, a] == mat[t + 1, b]:
                    c += 1
        total += c
    return total / (n - 1)


@njit(cache=True)
def _shuffle_overlap_null(mat: np.ndarray, n_perm: int, seed: int) -> np.ndarray:
    """Null lag-1 overlap pod permutacja KOLEJNOSCI (njit hot loop — wzorzec PoC)."""
    np.random.seed(seed)
    n = mat.shape[0]
    idx = np.arange(n)
    out = np.empty(n_perm, dtype=np.float64)
    for k in range(n_perm):
        # Fisher-Yates na idx
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
            for a in range(_MAIN_DRAW):
                for b in range(_MAIN_DRAW):
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
    """Permutacyjny test zaleznosci szeregowej (lag-1 overlap; DoD-2).

    H0: kolejnosc losowan wymienialna (iid). Statystyka = sredni overlap kolejnych losowan;
    null = permutacja kolejnosci. reject_h0 ⇔ p < alpha (prawy ogon — nadmiarowy overlap).
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"serial_overlap_test wymaga >=4 losowan, otrzymano {n}")
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
    """Fabryka detektora zgodnego z `calibration.Detector`. Pure-function reseed (DoD-6)."""
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _main_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return serial_overlap_test(draws, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
