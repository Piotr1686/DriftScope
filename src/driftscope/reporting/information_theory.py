"""Audyt informacyjno-teoretyczny — zlozonosc Lempel-Ziv 1976 (wow opcja #3, reporting layer).

Warstwa reporting/analysis (SUPLEMENT, NIE methodology/): detektor nie jest 4. filarem
Disagreement Protocol — ten pozostaje 3-filarowy (h1/mmd/cooccurrence, DoD-4=3/3, §6.5).
Jak `prng_benchmark` i `disagreement`, modul jest suplementem non-prereg (NIE podlega
dyscyplinie preregistration §0) — patrz pamiec `audit-framework-wow-options`.

**Idea:** prawdziwie losowa sekwencja jest NIESCISLIWA. Odchylenie od uniform-iid wnosi
strukture (powtarzalne podciagi) → NIZSZA zlozonosc algorytmiczna. Mierzymy ja kanoniczna
zlozonoscia produkcji Lempel-Ziv 1976 (Kaspar-Schuster 1987) — czysty algorytm, zero
zaleznosci od wersji kompresora (DoD-6 trywialny, cytowalny). bz2 ratio dolaczamy jako
intuicyjny cross-check w `metadata` (NIE wchodzi do `reject_h0`).

**Null — order-shuffle (margin-conditioned):** strumien = sklejone CHRONOLOGICZNIE bloki
posortowanych 5 liczb glownych. Null permutuje KOLEJNOSC blokow (losowan), zachowujac
(a) marginal (multiset symboli = czestosci liczb) oraz (b) wewnatrz-losowaniowe
wspolwystapienia (blok 5 liczb nienaruszony) — a lamiac TYLKO strukture MIEDZY-losowaniowa
(period / autocorr). Dzieki temu IT jest KOMPLEMENTARNY: slepy na czysty marginal (chi²/MMD
go lapia) i na joint wewnatrz losowania (co-occurrence go lapie), czuly na strukture
SEKWENCYJNA, ktorej zadna z trzech rodzin nie celuje wprost.

**Statystyka:** zlozonosc surowa c(obs). Struktura → c NIZSZA → lewy ogon nulla:
  p = (1 + #{c_perm ≤ c_obs}) / (n_perm + 1),   reject_h0 ⇔ p < alpha.
`statistic` raportuje zlozonosc ZNORMALIZOWANA c_norm = c · ln(L) / (L · ln(a)) (a=alfabet,
L=dlugosc; → ~1 dla losowego) — monotoniczna w c, wiec p ten sam.

Determinizm (DoD-6): detektor jest CZYSTA FUNKCJA wejscia — rng order-shuffle seedowany z
digestu zawartosci `draws` (macierz liczb glownych) ⊕ base_seed, jak w `cooccurrence`.

Numba (Os 3): kanoniczny parse LZ76 w `@njit(cache=True)` (czysta funkcja int-tablicy).
"""
from __future__ import annotations

import bz2
import hashlib
import math

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult

_MAIN_POOL_SIZE = 50  # alfabet: liczby glowne 1-50
_MAIN_DRAW = 5        # 5 liczb na losowanie (rozmiar bloku)

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05
_DEFAULT_BASE_SEED = 20260607


# ---------------------------------------------------------------------------
# Kodowanie strumienia
# ---------------------------------------------------------------------------

def _main_blocks(draws: list[DrawRecord]) -> npt.NDArray[np.int32]:
    """Macierz (n_draws, 5) POSORTOWANYCH liczb glownych w porzadku chronologicznym.

    Wiersz t = blok losowania t. Splaszczenie `.ravel()` daje strumien dlugosci 5·n nad
    alfabetem 1-50; permutacja wierszy = order-shuffle zachowujacy bloki (null).
    """
    n = len(draws)
    blocks = np.empty((n, _MAIN_DRAW), dtype=np.int32)
    for t, d in enumerate(draws):
        blocks[t] = np.sort(np.asarray(d.main_numbers, dtype=np.int32))
    return blocks


# ---------------------------------------------------------------------------
# Zlozonosc Lempel-Ziv 1976 (njit hot loop)
# ---------------------------------------------------------------------------

@njit(cache=True)
def lz76_complexity(s: npt.NDArray[np.int32]) -> int:
    """Kanoniczna zlozonosc produkcji Lempel-Ziv 1976 (Kaspar-Schuster 1987).

    Liczba fraz w rozbiorze samo-produkujacym sekwencje lewostronnie. Granice:
    1 ≤ c ≤ n. Ciag staly → c=2; ciag o samych roznych symbolach → c=n; struktura
    (powtorzenia) → c maleje. RNG niezalezne (czysta funkcja `s`).
    """
    n = s.shape[0]
    if n <= 1:
        return n
    c = 1
    lp = 1     # dlugosc juz sparsowanego prefiksu
    i = 0      # wskaznik porownania w historii
    k = 1      # dlugosc biezacego dopasowania
    k_max = 1  # najdluzsze dopasowanie dla biezacej frazy
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


def _normalized_complexity(c: int, length: int) -> float:
    """Znormalizowana zlozonosc c_norm = c · ln(L) / (L · ln(a)) (→ ~1 dla losowego)."""
    if length <= 1:
        return float(c)
    return c * math.log(length) / (length * math.log(_MAIN_POOL_SIZE))


def _bz2_ratio(s: npt.NDArray[np.int32]) -> float:
    """Stosunek kompresji bz2: len(bz2(bajty)) / len(bajty). Wartosci 1-50 mieszcza sie w uint8."""
    raw = s.astype(np.uint8).tobytes()
    return len(bz2.compress(raw, compresslevel=9)) / len(raw)


# ---------------------------------------------------------------------------
# Test informacyjno-teoretyczny
# ---------------------------------------------------------------------------

def information_test(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Permutacyjny test zlozonosci Lempel-Ziv 1976 (suplement IT, order-shuffle null).

    H0: liczby glowne ~ uniform-iid (brak struktury SEKWENCYJNEJ ponad marginal + joint
    wewnatrz losowania). reject_h0 ⇔ p_value(c, lewy ogon) < alpha.

    Null = permutacja kolejnosci blokow losowan (zachowuje marginal i wspolwystapienia,
    lamie strukture miedzy-losowaniowa). p = (1+#{c_perm ≤ c_obs})/(n_perm+1).
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"information_test wymaga >=2 losowan, otrzymano {n}")

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
        statistic=_normalized_complexity(c_obs, length),
        p_value=p_lz,
        reject_h0=bool(p_lz < alpha),
        metadata={
            "alpha": alpha,
            "n_draws": n,
            "n_perm": n_perm,
            "lz76_raw": int(c_obs),
            "lz76_norm": _normalized_complexity(c_obs, length),
            "bz2_ratio": bz2_obs,      # cross-check (intuicyjny; NIE wchodzi do reject_h0)
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
    """c_obs + rozklad nulla zlozonosci LZ76 (order-shuffle) — do wizualizacji / raportu.

    Zwraca (zlozonosc obserwowana, tablica `n_perm` zlozonosci pod permutacja blokow).
    Ten sam null co `information_test`; wydzielone dla warstwy demo/reporting (histogram
    obs vs null), bez dublowania logiki shuffle.
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"lz76_null_distribution wymaga >=2 losowan, otrzymano {n}")
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
    """Fabryka detektora zgodnego z `core.types.Detector` (interfejs harnessu W3/W4).

    Determinizm (DoD-6): kazda instancja jest CZYSTA FUNKCJA `draws`. Seed order-shuffle
    pochodzi z digestu zawartosci `draws` (macierz liczb glownych) ⊕ `base_seed`, wiec
    wynik zalezy wylacznie od (draws, base_seed) — jak w `cooccurrence_detector`.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        blocks = _main_blocks(draws)
        digest = hashlib.blake2b(blocks.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return information_test(draws, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
