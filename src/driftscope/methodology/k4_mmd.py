"""K4-MMD Kernel Two-Sample Test (W4).

Maximum Mean Discrepancy (Gretton et al. 2012) na frequency vectors p ∈ Δ⁴⁹
liczonych per sliding window (preregistration_v3 §3). Test dwuprobkowy: czy dwa
zbiory wektorow czestosci pochodza z tego samego rozkladu.

**Framing (decyzja W4, 2026-05-31):** §3 pinuje input space (Δ⁴⁹ per okno),
kernel (Gaussian RBF), bandwidth (median heuristic, anti-leakage), prog FPR ≤ 7.5%
— ale NIE pinuje, co jest X a co Y dla pojedynczego strumienia. Wybor: **homogenicznosc
do uniform** — X = okna obserwowanego strumienia, Y = okna swiezo wygenerowanego
uniform 5/50 (`generate_uniform_draws`, ten sam n). Test odrzuca, gdy rozklad okiennych
wektorow czestosci obserwacji odbiega od uniform. Lapie freq_shift (przesuniecie
sredniej), trend (przesuniecie globalne) i autocorr (nadmierna dyspersja okien);
z zalozenia SLEPY na pair_corr (joint, marginal ~uniform) → motywuje test wspolwystapien
W6. Wybor frameingu jest detalem implementacyjnym (poza prereg §3); zmiana metody
(kernel/input/bandwidth) wymagalaby preregistration_v4.

**Window vs realne n:** §3 mowi N=200, §4 spec curve N ∈ {100,200,400}. To dotyczy
PELNEGO realnego strumienia (~958 losowan). W DriftSim kalibracji per-rezim n jest male
(R1=133/R2=389/R3=436 < 200), wiec okno jest mniejsze i zadane parametrem `window`.
Adaptacja rozmiaru proby, NIE zmiana metody.

Numba (Os 3): permutacyjny null liczony w `@njit(cache=True)` hot loop nad pre-policzona
macierza Grama (PoC: 10–30× dla MMD). joblib NIGDY nad pojedynczymi permutacjami.

RBF/odleglosci sa liczone recznie (`_pairwise_sq_dists`/`_rbf_gram`) zamiast sklearn
`pairwise_kernels` (mimo wskazania w CLAUDE.md) — CELOWO: macierz Grama trafia wprost do
njit hot loop, brak importu sklearn na sciezce goracej i zero ryzyka regresji liczbowej.
"""
from __future__ import annotations

import hashlib
from typing import Callable

import numpy as np
from numba import njit

from driftscope.core.types import DrawRecord, TestResult
from driftscope.driftsim.null_uniform import Regime, generate_uniform_draws

_MAIN_POOL_SIZE = 50  # pula glowna 1-50 → frequency vector p ∈ Δ⁴⁹

# Domyslne parametry. WINDOW=200 = wartosc §3 dla pelnego strumienia; kalibracja
# per-rezim nadpisuje na mniejsze (n < 200). Brak DEFAULT_STEP: `step` jest WYMAGANY
# w `sliding_frequency_vectors` — domyslny krok byl footgunem (overlap → FPR~1.0).
DEFAULT_WINDOW = 200
DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05

Detector = Callable[[list[DrawRecord]], TestResult]


# ---------------------------------------------------------------------------
# Frequency vectors p ∈ Δ⁴⁹
# ---------------------------------------------------------------------------

def _main_matrix(draws: list[DrawRecord]) -> np.ndarray:
    """Macierz (n_draws, 5) liczb glownych (1-based). MMD czyta tylko pule glowna."""
    return np.array([d.main_numbers for d in draws], dtype=np.int64)


def frequency_vector(draws: list[DrawRecord]) -> np.ndarray:
    """Marginalny wektor czestosci p ∈ Δ⁴⁹ (suma=1) puli glownej dla zbioru losowan."""
    return _block_frequency(_main_matrix(draws))


def _block_frequency(main_block: np.ndarray) -> np.ndarray:
    """Wektor czestosci (50,) dla bloku liczb glownych (w, 5); normalizowany do sumy 1."""
    counts = np.bincount(main_block.ravel() - 1, minlength=_MAIN_POOL_SIZE).astype(float)
    total = counts.sum()
    return counts / total if total > 0 else counts


def sliding_frequency_vectors(
    draws: list[DrawRecord],
    window: int,
    step: int,
) -> np.ndarray:
    """Wektory czestosci Δ⁴⁹ z przesuwajacego sie okna `window` (krok `step`).

    Zwraca macierz (n_windows, 50). Kazdy wiersz = marginalna czestosc puli glownej
    w jednym oknie kolejnych losowan.

    `step` jest WYMAGANY (bez domyslnej wartosci): pod permutacyjnym nullem MMD
    (`mmd_permutation_test`) okna musza byc NIENAKLADAJACE sie (step >= window), inaczej
    korelacja okien lamie wymienialnosc → FPR~1.0. Brak domyslnego kroku wymusza
    swiadomy wybor.

    Raises:
        ValueError: gdy `window` > liczba losowan lub `window`/`step` <= 0.
    """
    if window <= 0 or step <= 0:
        raise ValueError(f"window i step musza byc > 0 (window={window}, step={step})")
    mains = _main_matrix(draws)
    n = mains.shape[0]
    if window > n:
        raise ValueError(f"window={window} > liczba losowan={n} — okno sie nie miesci")
    vectors = [
        _block_frequency(mains[start : start + window])
        for start in range(0, n - window + 1, step)
    ]
    return np.asarray(vectors, dtype=float)


# ---------------------------------------------------------------------------
# Gaussian RBF + median heuristic
# ---------------------------------------------------------------------------

def _pairwise_sq_dists(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Macierz kwadratow odleglosci euklidesowych ||a_i - b_j||² (clip do >= 0)."""
    aa = np.sum(A * A, axis=1)[:, None]
    bb = np.sum(B * B, axis=1)[None, :]
    return np.maximum(aa + bb - 2.0 * A @ B.T, 0.0)


def median_heuristic(X: np.ndarray) -> float:
    """Bandwidth σ = mediana parami odleglosci euklidesowych w X (Gretton 2012).

    Anti-leakage (§3): liczona WYLACZNIE na training window (przekazany X = obserwacja),
    nigdy na polaczonym X∪Y. Degeneracja (mediana 0 — np. identyczne wektory) → 1.0.
    """
    if X.shape[0] < 2:
        return 1.0
    sq = _pairwise_sq_dists(X, X)
    iu = np.triu_indices(X.shape[0], k=1)
    dist = np.sqrt(sq[iu])
    med = float(np.median(dist))
    return med if med > 0.0 else 1.0


def _rbf_gram(A: np.ndarray, B: np.ndarray, bandwidth: float) -> np.ndarray:
    """Macierz Grama Gaussian RBF: k(a,b) = exp(-||a-b||² / (2σ²))."""
    return np.exp(-_pairwise_sq_dists(A, B) / (2.0 * bandwidth * bandwidth))


def mmd_rbf_squared(X: np.ndarray, Y: np.ndarray, bandwidth: float) -> float:
    """Nieobciazony estymator MMD² (Gretton 2012, eq. 3) z Gaussian RBF.

    Wyklucza diagonale (i≠j) w skladnikach within-sample. Moze byc lekko ujemny
    (wlasnosc estymatora nieobciazonego), gdy X i Y pochodza z tego samego rozkladu.
    """
    m, n = X.shape[0], Y.shape[0]
    if m < 2 or n < 2:
        raise ValueError(f"MMD² wymaga >=2 obserwacji w kazdej probie (m={m}, n={n})")
    k_xx = _rbf_gram(X, X, bandwidth)
    k_yy = _rbf_gram(Y, Y, bandwidth)
    k_xy = _rbf_gram(X, Y, bandwidth)
    term_xx = (k_xx.sum() - np.trace(k_xx)) / (m * (m - 1))
    term_yy = (k_yy.sum() - np.trace(k_yy)) / (n * (n - 1))
    term_xy = k_xy.sum() / (m * n)
    return float(term_xx + term_yy - 2.0 * term_xy)


# ---------------------------------------------------------------------------
# Permutacyjny null — Numba hot loop (Os 3) nad pre-policzona macierza Grama
# ---------------------------------------------------------------------------

@njit(cache=True)
def _mmd2_permuted(gram: np.ndarray, perm: np.ndarray, m: int) -> float:
    """Nieobciazony MMD² dla podzialu zadanego permutacja `perm` indeksow puli Z=[X;Y].

    Pierwsze `m` indeksow perm → X', reszta → Y'. Indeksuje pre-policzona macierz `gram`
    (L×L), wiec kernel liczony jest raz, a kazda permutacja to tylko sumowanie.
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
def _permutation_null(gram: np.ndarray, perms: np.ndarray, m: int) -> np.ndarray:
    """Rozklad null MMD² dla `perms.shape[0]` permutacji etykiet (hot loop)."""
    n_perm = perms.shape[0]
    out = np.empty(n_perm, dtype=np.float64)
    for p in range(n_perm):
        out[p] = _mmd2_permuted(gram, perms[p], m)
    return out


def mmd_permutation_test(
    X: np.ndarray,
    Y: np.ndarray,
    n_perm: int = DEFAULT_N_PERM,
    rng: np.random.Generator | None = None,
    bandwidth: float | None = None,
    alpha: float = DEFAULT_ALPHA,
) -> TestResult:
    """Test MMD² z permutacyjnym (shuffled) nullem etykiet okien.

    H0: X i Y pochodza z tego samego rozkladu. Null przez przemieszanie etykiet
    polaczonej puli Z=[X;Y] (Gretton 2012 §8). p-value = (1 + #{null >= obs}) / (n_perm+1)
    (konserwatywny estymator z +1, MC-poprawny).

    OSTRZEZENIE (wymienialnosc): null zaklada, ze L=m+n wierszy X∪Y jest WYMIENIALNYCH
    pod H0. Dla wektorow z okien oznacza to okna NIENAKLADAJACE sie (step >= window) —
    okna nakladajace sie sa skorelowane within-sample, lamia wymienialnosc i daja FPR~1.0.
    Funkcja NIE jest w stanie sama wykryc nakladania (dostaje tylko macierze) — odpowiada
    za to caller (zob. `mmd_uniform_detector`).

    Args:
        X: (m, d) — frequency vectors obserwacji (training; zrodlo bandwidth). m >= 2.
        Y: (n, d) — frequency vectors referencji. n >= 2.
        n_perm: liczba permutacji etykiet.
        rng: generator NumPy (jedyne zrodlo losowosci); None → default_rng().
        bandwidth: σ RBF; None → median_heuristic(X) (anti-leakage, §3).
        alpha: prog odrzucenia.

    Raises:
        ValueError: gdy m < 2 lub n < 2 (estymator nieobciazony dzieli przez m*(m-1)).
    """
    if rng is None:
        rng = np.random.default_rng()
    m, n = X.shape[0], Y.shape[0]
    if m < 2 or n < 2:
        raise ValueError(
            f"MMD² wymaga >=2 okien w kazdej probie (m={m}, n={n}); "
            "zwieksz n_draws lub zmniejsz window."
        )
    if bandwidth is None:
        bandwidth = median_heuristic(X)  # anti-leakage: tylko training window (X)

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
# Detector dla calibration.py (framing: homogenicznosc do uniform)
# ---------------------------------------------------------------------------

def mmd_uniform_detector(
    window: int = 25,
    step: int | None = None,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    ref_regime: Regime = "R2",
    base_seed: int = 20260531,
) -> Detector:
    """Fabryka detektora MMD zgodnego z interfejsem `calibration.Detector`.

    Test: MMD²(okna obserwacji, okna uniform reference). Referencja generowana
    `generate_uniform_draws` o tej samej dlugosci co obserwacja (symetryczna
    wymienialnosc pod nullem → czysta kalibracja FPR). Pula glowna jest niezalezna
    od rezimu (zawsze 5/50), wiec `ref_regime` nie wplywa na wektory czestosci.

    **Okna NIENAKLADAJACE sie (step = window) — wymagane dla kalibracji.** Null testu
    to permutacja etykiet polaczonej puli okien, ktora zaklada WYMIENIALNOSC jednostek.
    Okna nakladajace sie (step < window) sa silnie skorelowane (within-X) i niezalezne
    miedzy strumieniami (X⊥Y) → wymienialnosc zlamana → obserwowane MMD² systematycznie
    > null permutacyjny → FPR ~1.0 (zmierzone empirycznie W4, 2026-05-31). Dlatego `step`
    domyslnie = `window` i `step < window` jest ZABRONIONE. ("sliding window" z §3 nie
    pinuje kroku; FPR ≤ 7.5% z §3 wymaga non-overlap pod tym nullem.)

    Domyslny `window=25` (step=25): kalibracja na realnym n daje FPR ≤ 7.5% we wszystkich
    rezimach (R1 n=133 → 5 okien, R2 → 15, R3 → 17). Dla pelnego strumienia (~958) uzyj
    `window=200` (§3). R1 (n=133) jest na granicy danych dla MMD okiennego — power nizsza.

    Determinizm (DoD-6): detektor jest CZYSTA FUNKCJA wejscia. rng kazdego wywolania
    jest seedowany deterministycznie z ZAWARTOSCI `draws` (digest macierzy liczb glownych
    ⊕ `base_seed`), wiec wynik zalezy wylacznie od (draws, base_seed) — NIE od kolejnosci
    czy liczby wczesniejszych wywolan. Dwie swieze instancje detektora na tym samym
    `draws` daja identyczny p-value; rozne `draws` → niezalezne strumienie. Seed z hash
    obserwacji nie wprowadza biasu: referencja pozostaje uniform niezaleznie od seeda,
    a odwzorowanie seed→probka jest nieskorelowane z odchyleniem obserwacji.
    """
    actual_step = window if step is None else step
    if actual_step < window:
        raise ValueError(
            f"step={actual_step} < window={window}: okna nakladajace sie lamia "
            "wymienialnosc permutacyjna → FPR ~1.0. Uzyj step >= window (non-overlap)."
        )

    def detector(draws: list[DrawRecord]) -> TestResult:
        n = len(draws)
        n_windows = (n - window) // actual_step + 1 if n >= window else 0
        if n_windows < 2:
            raise ValueError(
                f"n_draws={n} daje {n_windows} okien przy window={window}/step={actual_step}; "
                "MMD wymaga >=2 okien — zwieksz n_draws lub zmniejsz window."
            )
        # Seed czysto z zawartosci draws (⊕ base_seed) → detektor reprodukowalny niezaleznie
        # od kolejnosci wywolan (DoD-6). digest 8B macierzy liczb glownych.
        digest = hashlib.blake2b(_main_matrix(draws).tobytes(), digest_size=8).digest()
        seed_int = int.from_bytes(digest, "little")
        rng = np.random.default_rng(np.random.SeedSequence([base_seed, seed_int]))

        reference = generate_uniform_draws(n, ref_regime, rng)
        x = sliding_frequency_vectors(draws, window, actual_step)
        y = sliding_frequency_vectors(reference, window, actual_step)
        result = mmd_permutation_test(x, y, n_perm=n_perm, rng=rng, alpha=alpha)
        return result.model_copy(
            update={"metadata": {**result.metadata, "window": window, "step": actual_step}}
        )

    return detector
