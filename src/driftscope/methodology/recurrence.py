"""Recurrence / gap analysis (W6, preregistration §5b).

Czas (liczba losowan) miedzy kolejnymi wystapieniami danej liczby. Pod nullem uniform-iid
gap ~ Geometric(q), q = 5/50 = 0.1 dla puli glownej. Ten modul testuje TEMPORALNA strukture
pojawiania sie liczb — wymiar ortogonalny do marginesu (chi²) i do wspolwystapien (§5c).

**Co wykrywa, a co NIE (kluczowa wlasciwosc nulla):** null = permutacja KOLEJNOSCI losowan
(draw-order shuffle). Permutacja zachowuje LICZNOSC kazdej liczby → test WARUNKUJE na
marginesie. Skutek:
- WYKRYWA clumping/runs (autocorr): liczba reapearuje szybciej niz Geometric → nadmiar
  krotkich gapow; shuffle to niszczy → obserwowane w ogonie nulla.
- WYKRYWA periodycznosc / niestacjonarnosc arrivali (seasonality, trend) — uklad gapow
  odbiega od wymienialnego.
- SLEPY na freq_shift (czysto marginalny): wyzsza liczebnosc daje krotsze gapy, ALE shuffle
  ma te sama liczebnosc → null tez przesuniety → marginal skonditionowany out. To CECHA:
  marginal lapie chi², recurrence dokłada wymiar temporalny.

**Statystyka (KS vs Geometric, permutacyjnie kalibrowana):** per liczba D_k = KS distance
empirycznego CDF gapow od Geometric(q). ⚠️ NIE analityczny p-value KS (niewazny dla
rozkladow dyskretnych — preregistration §5b). Omnibus = **max_k D_k** (jak max-pair w §5c),
null = draw-order shuffle (max_k D_k per shuffle), lokalizacja: najbardziej anomalna liczba.
p = (1 + #{maxD_perm ≥ maxD_obs})/(n_perm+1).

Dodatkowo (diagnostyka §5b, NIE silnik decyzji):
- **Nelson-Aalen** cumulative hazard per liczba — liniowosc (nachylenie ≈ q) = stala
  intensywnosc = zgodnosc z uniform.
- **EVT max-gap** — maksymalny gap ma asymptotycznie rozklad Gumbela (gapy geometryczne
  w domenie przyciagania Gumbela); p-value Gumbel jako sanity dla skrajnie dlugich przerw.

Determinizm (DoD-6): detektor jest CZYSTA FUNKCJA wejscia — seed shuffle z hash draws.
Zasila Family B FDR (§5).
"""
from __future__ import annotations

import hashlib
from typing import Callable

import numpy as np

from driftscope.core.types import DrawRecord, TestResult

_MAIN_POOL_SIZE = 50
_MAIN_DRAW = 5
_Q_MAIN = _MAIN_DRAW / _MAIN_POOL_SIZE  # 0.1 — P(liczba w jednym losowaniu) pod uniform

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05

Detector = Callable[[list[DrawRecord]], TestResult]


# ---------------------------------------------------------------------------
# Gapy
# ---------------------------------------------------------------------------

def _incidence_matrix(draws: list[DrawRecord]) -> np.ndarray:
    """Binarna macierz (n_draws, 50): M[t, k]=1 ⇔ liczba (k+1) w losowaniu t."""
    n = len(draws)
    m = np.zeros((n, _MAIN_POOL_SIZE), dtype=np.int8)
    for t, d in enumerate(draws):
        for k in d.main_numbers:
            m[t, k - 1] = 1
    return m


def number_gaps(draws: list[DrawRecord], number: int) -> np.ndarray:
    """Gapy (w losowaniach) miedzy kolejnymi wystapieniami `number` (1-based).

    Gap = roznica indeksow losowan kolejnych wystapien (>=1). Zwraca [] gdy liczba
    pojawia sie < 2 razy (brak gapu).
    """
    col = _incidence_matrix(draws)[:, number - 1]
    return _gaps_from_column(col)


def _gaps_from_column(col: np.ndarray) -> np.ndarray:
    """Gapy z binarnej kolumny wystapien (1D 0/1)."""
    pos = np.flatnonzero(col)
    if pos.size < 2:
        return np.empty(0, dtype=np.int64)
    return np.diff(pos).astype(np.int64)


def _ks_vs_geometric(gaps: np.ndarray, q: float) -> float:
    """KS distance empirycznego CDF gapow od Geometric(q) na {1,2,...}.

    Geometric CDF: F(g) = 1 − (1−q)^g dla g >= 1. Wariant dwustronny (gorny i dolny
    skok empirycznego CDF). Zwraca 0.0 dla < 2 gapow (brak sygnalu).
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


def _max_ks_over_numbers(m: np.ndarray, q: float) -> tuple[float, int]:
    """(max_k D_k, argmax_k) po wszystkich 50 liczbach dla macierzy incydencji `m`."""
    best_d = 0.0
    best_k = 0
    for k in range(_MAIN_POOL_SIZE):
        d = _ks_vs_geometric(_gaps_from_column(m[:, k]), q)
        if d > best_d:
            best_d = d
            best_k = k
    return best_d, best_k


# ---------------------------------------------------------------------------
# Nelson-Aalen cumulative hazard (diagnostyka §5b)
# ---------------------------------------------------------------------------

def nelson_aalen(gaps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Estymator Nelson-Aalen skumulowanego hazardu z gapow (~20 LOC, bez lifelines).

    Traktuje gapy jako czasy zdarzen (recurrence). Hazard krokowy w czasie t = liczba
    zdarzen w t / liczba "at risk" (gapy >= t). Zwraca (times, cumhaz) — schodkowa funkcja.
    Pod uniform-iid skumulowany hazard rosnie ~liniowo z nachyleniem q/(1−q)·... ≈ stala
    intensywnosc; krzywizna sygnalizuje niestacjonarnosc intensywnosci.
    """
    if gaps.size == 0:
        return np.empty(0), np.empty(0)
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


def nelson_aalen_linearity_deviation(gaps: np.ndarray) -> float:
    """Maks. odchylenie skumulowanego hazardu od prostej (0,0)→(t_max, H_max).

    0 = idealnie liniowy (stala intensywnosc, zgodne z uniform); rosnie przy krzywiznie
    (zmienna intensywnosc). Czysta liczba diagnostyczna, NIE testowana permutacyjnie tutaj.
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
# EVT max-gap (Gumbel, diagnostyka §5b)
# ---------------------------------------------------------------------------

def evt_max_gap_pvalue(gaps: np.ndarray, q: float) -> tuple[int, float]:
    """(max_gap, p-value) skrajnie dlugiej przerwy wg asymptotyki Gumbela.

    Dla gapow ~ Geometric(q), maksimum z m gapow ma w przyblizeniu rozklad maks.
    rozkladu geometrycznego: P(max <= x) ≈ (1 − (1−q)^x)^m. p-value = P(max >= obs)
    = 1 − (1 − (1−q)^(obs−1))^m (uzywa obs−1 dla prawego ogona, konserwatywnie).
    Sanity dla pojedynczej skrajnej przerwy; NIE zastepuje testu KS.
    """
    if gaps.size == 0:
        return 0, 1.0
    m = gaps.size
    obs = int(gaps.max())
    # P(pojedynczy gap >= obs) = (1−q)^(obs−1); P(max < obs) = (1 − (1−q)^(obs−1))^m
    tail_single = (1.0 - q) ** (obs - 1)
    p = 1.0 - (1.0 - tail_single) ** m
    return obs, float(min(max(p, 0.0), 1.0))


# ---------------------------------------------------------------------------
# Test recurrence (gap GoF, permutacyjnie kalibrowany)
# ---------------------------------------------------------------------------

def gap_recurrence_test(
    draws: list[DrawRecord],
    q: float = _Q_MAIN,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
) -> TestResult:
    """Permutacyjny test struktury temporalnej gapow (preregistration §5b).

    H0: pojawienia kazdej liczby sa wymienialne w czasie (uklad iid). Statystyka omnibus
    = max_k KS(gapy_k, Geometric(q)); null = permutacja kolejnosci losowan (zachowuje
    licznosci → warunkuje na marginesie). reject_h0 ⇔ p < alpha. Lokalizuje najbardziej
    anomalna liczbe (top_number, 1-based).
    """
    n = len(draws)
    if n < 4:
        raise ValueError(f"gap_recurrence_test wymaga >=4 losowan, otrzymano {n}")
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
            "top_number": k_obs + 1,   # najbardziej anomalna liczba (1-based)
            "h0": "per-number arrivals exchangeable in time (uniform-iid)",
            "null": "draw-order permutation (counts preserved → conditions on marginal)",
        },
    )


def recurrence_detector(
    q: float = _Q_MAIN,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    base_seed: int = 20260531,
) -> Detector:
    """Fabryka detektora zgodnego z `calibration.Detector` (interfejs harnessu W3/W4/W6).

    Determinizm (DoD-6): czysta funkcja `draws` — seed permutacji z digestu zawartosci
    `draws` ⊕ `base_seed` (jak k4_mmd / cooccurrence).
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _incidence_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed = (int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF
        return gap_recurrence_test(draws, q=q, n_perm=n_perm, alpha=alpha, seed=seed)

    return detector
