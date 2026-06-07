"""Co-occurrence test — wykrywanie struktury LACZNEJ par liczb (W6, preregistration §5c).

Detektory marginalne (chi² §5, MMD §3) sa z zalozenia SLEPE na signal #5 (pair_corr):
para liczb (i,j) wspolwystepuje w jednym losowaniu czesciej niz pod uniform, podczas gdy
KAZDY pojedynczy margines pozostaje ~uniform (W3/W4 — power ≈ FPR). Ten modul domyka luke
dedykowanym testem wspolwystapien.

**Null — swap-randomization (curveball, Strona et al. 2014):** macierz incydencji
losowanie×liczba (n × 50, suma wiersza = 5) jest losowo przetasowywana tak, by zachowac
JEDNOCZESNIE sumy wierszy (5 liczb/losowanie) i sumy kolumn (marginalna czestosc kazdej
liczby), a zlamac TYLKO strukture parowania. To izoluje sygnal laczny od marginalnego —
analityczny Binomial(n, p_pair) jest niewazny przy nie-uniform marginesach (np. pod
freq_shift), wiec null musi byc permutacyjny i warunkowany na marginesach. Lancuch
sekwencyjny (burn-in + thinning, Gotelli 2000; Besag-Clifford serial) — jedna "wymiana"
curveball swapuje wiele elementow naraz, wiec miesza szybciej niz pojedyncze swapy krawedzi.

**Statystyka — max-pair (decyzja W6, korekta §5c):**
  z_ij = (O_ij − E_ij) / sqrt(E_ij),   reject ⇔ max_ij z_ij w prawym ogonie nulla.
E_ij i rozklad nulla z `n_perm` przetasowan curveball (E_ij = srednia wspolwystapien pod
nullem). p-value = (1 + #{maxstat_perm ≥ maxstat_obs})/(n_perm+1).

  **Odrzucona statystyka — suma T = Σ_{i<j}(O−E)²/E (pierwotnie pinowana §5c):** planted
  pair_corr to sygnal RZADKI (jedna para z 1225). (a) Suma rozmywa pojedyncza odchylona
  pare w szumie 1224 par nullowych (null T ~ 1225 ± 49; wklad pojedynczej pary jest rzedu
  kilku jednostek → tonie → power ≈ FPR, ta sama slepota co chi²/MMD). (b) Forma chi² (/E, skala
  Poissona) jest dla wspolwystapien zle skalibrowana — empirycznie FPR ~0.17 na nullu
  (R3, W6). Statystyka EKSTREMALNA max-pair jest wlasciwa dla rzadkiej alternatywy i
  kalibruje sie poprawnie (FPR ≈ α). Argument strukturalny + empiryczny na DriftSim
  (nie data-dredge na realnym EuroJackpot) — ratyfikowany w preregistration_v5.

**Finding W6 (zwalidowany na DriftSim, preregistration_v5):** po przeprojektowaniu
mechanizmu pair_corr na MARGIN-PRESERVING (forced-frac p, marginesy uniform — §6/v5) test
wspolwystapien daje czysta komorke Disagreement Protocol: jest JEDYNYM detektorem lapiacym
ten sygnal. Power (n_trials=50, n_perm=99):
  p:         0.01   0.02   0.05   0.10
  R1 (133):  0.06   0.08   0.80   1.00
  R2 (389):  0.06   0.40   1.00   1.00
  R3 (436):  0.08   0.36   1.00   1.00
Przy p=0.10 (najmocniejszy): chi²=0.06, MMD=0.03 — oba na FPR floor (marginesy zachowane
→ dowodliwie slepe). FPR(null)=0.03. Decision Gate (>70%) spelniony dla p ≥ 0.05 we
wszystkich rezimach (R1@0.05=0.80). p=0.01 ponizej floor wszedzie; p=0.02 floor w R1,
czesciowy w R2/R3. Lokalizacja pary (top_pair) poprawna przy odrzuceniu.

Determinizm (DoD-6): detektor jest CZYSTA FUNKCJA wejscia — rng curveball seedowany z
ZAWARTOSCI `draws` (digest macierzy liczb glownych ⊕ base_seed), jak w `k4_mmd`.

Numba (Os 3): curveball hot loop w `@njit(cache=True)`.
"""
from __future__ import annotations

import hashlib

import numpy as np
import numpy.typing as npt
from numba import njit

from driftscope.core.types import Detector, DrawRecord, TestResult

_MAIN_POOL_SIZE = 50  # pula glowna 1-50
_MAIN_DRAW = 5        # 5 liczb na losowanie (suma wiersza incydencji)

DEFAULT_N_PERM = 999
DEFAULT_ALPHA = 0.05
# Mieszanie lancucha curveball. burn-in proporcjonalny do liczby losowan (rzedy
# wielkosci wg Strona 2014: kilka×n wymian wystarcza); thinning = n wymian/probke.
DEFAULT_BURN_FACTOR = 5   # burn-in = BURN_FACTOR * n_draws (min DEFAULT_BURN_MIN)
DEFAULT_BURN_MIN = 1000
DEFAULT_THIN_FACTOR = 1   # thinning = THIN_FACTOR * n_draws wymian miedzy probkami


# ---------------------------------------------------------------------------
# Macierz incydencji i wspolwystapienia
# ---------------------------------------------------------------------------

def _incidence_matrix(draws: list[DrawRecord]) -> npt.NDArray[np.int8]:
    """Binarna macierz incydencji (n_draws, pool): M[t, k]=1 ⇔ liczba (k+1) w losowaniu t.

    Suma kazdego wiersza = k_drawn (liczby glowne); suma kolumny k = liczebnosc liczby (k+1).
    Szerokosc puli wyprowadzona z rekordow (`draws[0].pool_size`; EJ=50, MM=80).
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
    """Wektor wspolwystapien gornego trojkata: C_ij = #{losowania z obiema i,j} dla i<j."""
    cooc = m.T.astype(np.int64) @ m.astype(np.int64)  # (50,50), diagonala = liczebnosci
    return cooc[iu].astype(np.float64)


# ---------------------------------------------------------------------------
# Curveball swap-randomization (njit hot loop)
# ---------------------------------------------------------------------------

@njit(cache=True)
def _curveball_trades(m: npt.NDArray[np.int8], n_trades: int) -> None:
    """In-place `n_trades` wymian curveball na binarnej macierzy `m` (mutuje `m`).

    Jedna wymiana: losuj dwa rozne wiersze r1, r2; kolumny w ktorych sie ROZNIA tworza
    pule wymienna (elementy wspolne zostaja). Pula jest losowo redystrybuowana: tyle samo
    "1" trafia do r1 ile mial pierwotnie → sumy wierszy i kolumn zachowane, parowanie
    zlamane. RNG: globalny stan numba (zaseedowany przez `_seed_numba` przed wywolaniem).
    """
    n_rows, n_cols = m.shape
    diff = np.empty(n_cols, dtype=np.int64)  # scratch: indeksy roznicych sie kolumn
    for _ in range(n_trades):
        r1 = np.random.randint(n_rows)
        r2 = np.random.randint(n_rows)
        if r1 == r2:
            continue
        count = 0       # ile kolumn sie rozni
        a_ones = 0      # ile z nich nalezalo do r1 (tyle "1" wroci do r1)
        for c in range(n_cols):
            v1 = m[r1, c]
            if v1 != m[r2, c]:
                diff[count] = c
                if v1 == 1:
                    a_ones += 1
                count += 1
        if count == 0:
            continue
        # Fisher-Yates na diff[0:count]
        for i in range(count - 1, 0, -1):
            j = np.random.randint(i + 1)
            tmp = diff[i]
            diff[i] = diff[j]
            diff[j] = tmp
        # pierwsze a_ones roznicych kolumn → r1, reszta → r2
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
    """Seeduje globalny RNG numba (deterministyczny null dla DoD-6)."""
    np.random.seed(seed)


def _permutation_cooccurrence(
    m0: npt.NDArray[np.int8],
    iu: tuple[npt.NDArray[np.intp], npt.NDArray[np.intp]],
    n_perm: int,
    burn_in: int,
    thin: int,
    seed: int,
) -> npt.NDArray[np.float64]:
    """Macierz (n_perm, n_pairs) wspolwystapien pod nullem curveball (lancuch + thinning)."""
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
# Test wspolwystapien
# ---------------------------------------------------------------------------

def cooccurrence_test(
    draws: list[DrawRecord],
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = DEFAULT_ALPHA,
    burn_in: int | None = None,
    thin: int | None = None,
    seed: int = 0,
) -> TestResult:
    """Permutacyjny test wspolwystapien par (preregistration §5c).

    H0: liczby glowne ~ uniform-iid (brak struktury lacznej par ponad to, co wymuszaja
    marginesy). reject_h0 ⇔ p_value(max-pair) < alpha.

    Statystyka = max_ij (O_ij − E_ij)/sqrt(E_ij), null = curveball (zachowuje oba
    marginesy). E_ij i rozklad nulla z `n_perm` przetasowan. p = (1+#{perm ≥ obs})/(n_perm+1).
    """
    n = len(draws)
    if n < 2:
        raise ValueError(f"cooccurrence_test wymaga >=2 losowan, otrzymano {n}")
    m0 = _incidence_matrix(draws)
    iu = np.triu_indices(m0.shape[1], k=1)  # gorny trojkat puli (pool z danych: EJ=50/MM=80)
    obs = _cooccurrence_upper(m0, iu)

    burn = burn_in if burn_in is not None else max(DEFAULT_BURN_FACTOR * n, DEFAULT_BURN_MIN)
    th = thin if thin is not None else max(DEFAULT_THIN_FACTOR * n, 1)
    perm = _permutation_cooccurrence(m0, iu, n_perm, burn, th, seed)

    # E_ij = oczekiwane wspolwystapienie pod nullem (srednia po permutacjach).
    e = perm.mean(axis=0)
    safe = e > 0.0
    sd = np.sqrt(np.where(safe, e, 1.0))  # sqrt(E) jako skala (Poisson-like); guard div0

    def _max_z(c: npt.NDArray[np.float64]) -> float:
        return float(np.where(safe, (c - e) / sd, 0.0).max())

    max_obs = _max_z(obs)
    max_perm = np.array([_max_z(perm[b]) for b in range(n_perm)])
    p_max = (1 + int(np.sum(max_perm >= max_obs))) / (n_perm + 1)

    # Lokalizacja najsilniejszej pary (1-based liczby) — diagnostyka.
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
            "top_pair": pair,              # najsilniejsza para (i,j), 1-based
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
    """Fabryka detektora zgodnego z `calibration.Detector` (interfejs harnessu W3/W4).

    Determinizm (DoD-6): kazda instancja jest CZYSTA FUNKCJA `draws`. Seed curveball
    pochodzi z digestu zawartosci `draws` (macierz liczb glownych) ⊕ `base_seed`, wiec
    wynik zalezy wylacznie od (draws, base_seed) — nie od kolejnosci wywolan.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        mat = _incidence_matrix(draws)
        digest = hashlib.blake2b(mat.tobytes(), digest_size=8).digest()
        seed_int = int.from_bytes(digest, "little") ^ (base_seed & 0xFFFFFFFFFFFFFFFF)
        seed = seed_int & 0xFFFFFFFF  # numba np.random.seed oczekuje uint32
        return cooccurrence_test(
            draws, n_perm=n_perm, alpha=alpha, burn_in=burn_in, thin=thin, seed=seed
        )

    return detector
