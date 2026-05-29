# PROJECT_BRIEF.md — DriftScope

> **Architectural contract.** Decyzje w tym dokumencie są *permanent patterns* — zmiana wymaga explicit re-review przed dotknięciem kodu.
>
> **Status:** ready-for-handoff (Claude Code CLI) · **Tier:** MEDIUM · **Język brief'u:** PL/EN mix

---

## 0. Flagi i konwencje

- **Compute Execution Policy** (§6) zastępuje generic "Hardware Transcendence Stack" — realny bottleneck = CPU permutation overhead. `HARDWARE_PUSH_CATALOG.md` aplikuje **selektywnie**: **Oś 0 (Environment Sanity)** i **Oś 3 (Compilation — Numba JIT na CPU)** pozostają aktywne; Osie 1–2, 4–7 nie aplikują (brak GPU, brak modeli neural, brak VRAM budget).
- **Anti-goal guard:** każda decyzja sprawdzona pod SEED_IDEA §5A.1–4 (no naive frequency, no hallucinated signal, no wrapper, no gambling-app framing) i §5B.1–4 (no premise pivot).
- **Permanent pattern (Piotr's template):** `pyproject.toml` jako single source of truth; `artifacts/` na root; `@dataclass Config` per moduł dla standalone CLI; `db/queries.py` zamiast Repository pattern (solo dev); PowerShell 5.1 compatible; zmiany w istniejących plikach, nie patch-documenty.
- **Global determinism:** `BASE_SEED=42` (deklarowany w `.env.example` i `core/config.py`). Wszystkie strumienie RNG derive z `np.random.SeedSequence(BASE_SEED)`.

---

## 1. Wizja i Elevator Pitch

**Elevator pitch (recruiter quant/research, 25 sek):**
DriftScope to research-grade audit framework dla detekcji niestacjonarności w strumieniach dyskretnych procesów *z założenia* uniform. Trzy **komplementarne filary** (classical stationarity tests + kernel two-sample test na wektorach częstości + syntetyczna kalibracja DriftSim) konwergują na wnioski; każde "found" musi przejść shuffle test, FDR correction i specification curve analysis, zanim wyląduje w raporcie. Flagship case study — EuroJackpot z dwoma znanymi change-pointami 2014/2022 jako ground truth — istnieje, żeby udowodnić, że detektor *w ogóle działa*, zanim oceniony zostanie jakikolwiek subtelniejszy wzorzec. Framework jest reusable: NIST RNG test data, kryptograficzne PRNG, financial random-walk hypotheses są naturalnymi targetami stretch.

**Sub-tagline (README, ≤15 słów):**
> *Stationarity audit framework for streaming discrete processes — with calibrated detector hallucination rates.*

**Recruiter category:** *Methodological tooling for hypothesis testing on streaming data.* NIE "ML prediction project".

---

## 2. 10-Second Hook

**Konkretna scena (≤10 sek):**
Użytkownik otwiera README/repo. Pierwszy element widoczny w viewport: **animowana "permutation race" — trzy panele obok siebie**, pre-rendered jako `.webm` (autoplay, loop, muted, playsinline).

- **Panel 1 (Real):** EuroJackpot stream, oś czasu 2012→2026, czerwone markery na 2014-10-10 i 2022-03-25 (znane change-pointy). Bayesian online CP "konsumuje" datapoint po datapoint, p-value spada do <0.001 na obu change-pointach.
- **Panel 2 (Uniform RNG control):** ten sam framework na `secrets.randbelow(50)` — detektor nie zapala niczego, p-value zostaje w noise. **To jest visceral proof of non-hallucination.**
- **Panel 3 (Shuffled real):** real stream z permutowaną kolejnością — detektor traci change-pointy.

**Główny "wow":** trzy panele bok w bok pokazują, że detektor *odpowiada na rzeczywistą strukturę czasową*, a nie generuje sygnał. Real → detection. Uniform → null. Shuffled → null.

**Custom design system:** minimal. Color palette: 3 kolory (real = `#0EA5E9` blue, control = `#94A3B8` slate, change-point marker = `#EF4444` red). Typography: JetBrains Mono dla liczb/p-values, Inter dla narracji. **Brak ikon/emoji w README** (anti-scam signal). Logo: scope-wise odrzucone z MVP.

**Biblioteka:** `matplotlib.animation.FuncAnimation` → `ffmpeg-python` → `.webm` (VP9, target 2–5 MB). Embed:

```html
<video src="docs/hook.webm" autoplay loop muted playsinline controlsList="nodownload"></video>
```

GitHub renderuje `<video>` natywnie w MD.

**Pierwsze 3 zdania README (finalna wersja):**
> *DriftScope is a stationarity audit framework for streaming discrete-valued processes. The flagship case study is EuroJackpot — a process designed to be uniform-random, where the empirical question is whether any detectable deviation from uniformity exists. The project is methodological in nature; it neither claims nor seeks to predict lottery outcomes in any actionable sense.*

---

## 3. Stack technologiczny — z uzasadnieniem każdego wyboru

| Warstwa | Wybór | Wersja | Uzasadnienie |
|---|---|---|---|
| Język/runtime | **Python 3.10** | 3.10.x | Dojrzały ekosystem stat; znany Piotrowi |
| Stationarity tests | **statsmodels** | 0.14.x | ADF (H₀: unit root), KPSS (H₀: trend stationarity — komplementarne, nie redundantne), ACF/PACF |
| Change-point detection | **ruptures** | 1.1.9+ | CUSUM, Pelt, Binseg — cross-check vs Bayesian CP |
| Bayesian online CP | **własna implementacja Adams-MacKay 2007** | — | Generative model: Dirichlet-Multinomial conjugate (zob. `preregistration_v2.md` §2). ~150 LOC + property-based tests |
| Spectral analysis | **scipy.signal** | 1.13.x | Welch periodogram, Lomb-Scargle |
| Kernel methods (MMD) | **scikit-learn** kernels + custom MMD | sklearn 1.4.x | `pairwise_kernels` jako primitive; MMD ~80 LOC. Input space: frequency vectors p ∈ Δ⁴⁹ per sliding window (NIE raw draws). RBF na simplex z bandwidth z training-window only. ⚠️ Asymptotic stability przy N=200 UNVERIFIED — empirical calibration vs shuffled null w W4 PoC. |
| Permutation engine | **Numba JIT** (selektywnie) + `joblib.Parallel` (nad konfigami) | Numba 0.65.x | `@njit(cache=True)` tylko gdzie profilowanie pokaże >2× zysk (MMD permutation core priorytetowo, BCPD inner loop opcjonalnie). NumPy sequential default dla prostych testów. Realistyczne: 2.7× dla simple, 10–30× dla MMD O(N²). |
| Multiple testing | `statsmodels.stats.multitest` | 0.14.x | Benjamini-Hochberg FDR (primary), Storey q-values (secondary sanity, Family A only) |
| Data manipulation | **Polars** | 1.x | Type-safe, modern stack signal. MVP: ~958 rows (real seed CSV, 2012–2026); framework dla NIST RNG (10⁶+) stretch |
| Data ingestion | `httpx` + `selectolax` + `tenacity` | — | Scraper z eurojackpot.org archive (brak publicznego API z kluczem). Cached CSV jako Tier-1 fallback w `data/seed/eurojackpot_history.csv` |
| Storage — raw/cleaned data | **Parquet** (`pyarrow`) | — | Zstd compression. Frequency vectors jako `pl.List(pl.Float64)` (Arrow nested list) |
| Storage — permutation results | **Parquet shards per worker** | `pyarrow` | `artifacts/permutations/{test}/{regime}/worker_{id}.parquet`. Reduce w Polars LazyFrame `scan_parquet(glob).collect()`. Zero-contention writes, naturalny checkpoint |
| Storage — metadata | **SQLite** (małe append-only) | stdlib | `artifacts/regime_meta.sqlite` dla regime_meta + calibration_runs (single-writer pattern). NIE primary cache |
| Data versioning | **`git lfs`** + `scripts/archive.py` | git-lfs 3.x | `git lfs track "*.parquet"` + SHA-256 manifest zawartości logicznej (sorted ORDER BY) |
| Config | **Pydantic Settings** v2 + `.env` | 2.x | `core/config.py` |
| Data validation | **Pydantic** v2 | 2.x | `DrawRecord` z `Field(ge=1, le=50)` (main) / `Field(ge=1, le=12)` (euron). Fail-fast przy ingestion |
| Runtime guards | **`core/guards.py`** + `psutil` | stdlib + psutil | ~40 LOC: `@with_timeout(seconds)`, `assert_memory_below(gb)` dekoratory dla entry points |
| CLI | **Typer** | 0.12.x | Type-hinted, `--resume` flag dla checkpointed runs |
| Static viz (paper) | **matplotlib** | 3.9.x | Publikowalne, deterministyczne. Animation export → `.webm` via ffmpeg |
| Interactive viz | **Plotly** (static HTML) | latest | Embed w Quarto report. Streamlit jako W9+ stretch |
| Report | **Quarto** | 1.5+ | Reproducible markdown→HTML/PDF. Fallback: `jupyter nbconvert` |
| Testing | **pytest** + `hypothesis` | latest | `pytest.approx(rel=0.05, abs=1e-3)` w conftest dla stochastycznych testów |
| Code quality | **ruff** + **mypy --strict** | latest | mypy strict dla `methodology/` |
| Package layout | **`pyproject.toml`** + `src/driftscope/` | PEP 621 | `pip install driftscope` |

**§3-alt — explicit rejected:**
- **mapie / conformal p-values** — kategorycznie nieaplikowalne (mapie do conformal *prediction* intervals/sets, nie do testów exchangeability/stationarity).
- **JAX dla MMD vectorization** — DLL risk na Win11, ROI marginalny przy N≤500.
- **R / Julia hybrid** — polyglot mnoży env risk, recruiter signal niejednoznaczny.
- **Rust PyO3 permutation engine** — bookmark na W5 Decision Gate jeśli Numba niewystarczająca, NIE commitment.
- **DVC** — overhead nieproporcjonalny dla <2GB; binary blob anti-pattern dla SQLite.
- **SQLite jako primary permutation cache** — N writers + WAL → `database is locked`.
- **lifelines (survival analysis)** — odrzucone dla `recurrence.py`. Ciągnie pandas (zakazane — §0/konwencje) + scipy + autograd dla jednej funkcji (Nelson-Aalen). NA estimator = `cumsum(d_i / n_i)`, ~20 LOC NumPy — implementacja własna zgodna z anti-goal §12 ("nie wrapper"). EVT/Gumbel via `scipy.stats.gumbel_r`.

---

## 4. Architektura

### 4.1 Struktura katalogów

```
driftscope/
├── pyproject.toml
├── README.md                   # public-facing, 3-sentence disarmer first
├── PROJECT_BRIEF.md            # ten plik
├── .env.example                # zob. niżej (7 kluczy)
├── data/
│   └── seed/
│       └── eurojackpot_history.csv  # committed; zob. schema niżej
├── scripts/
│   ├── archive.py              # SHA-256 manifest generator
│   └── manual_import.py        # CSV upload fallback
├── docs/
│   ├── report.html             # Quarto output, primary demo
│   └── hook.webm               # 10-second hook animation
├── src/driftscope/
│   ├── __init__.py
│   ├── cli.py                  # Typer entrypoint, --resume support
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (paths, BASE_SEED, scraper timeouts)
│   │   ├── types.py            # DrawRecord (Pydantic), RegimeSpec, TestResult
│   │   ├── seeds.py            # make_worker_seeds(base, n) → list[SeedSequence]
│   │   └── guards.py           # @with_timeout, assert_memory_below
│   ├── ingestion/
│   │   ├── lotto_scraper.py    # httpx + selectolax, eurojackpot.org archive
│   │   └── regime_split.py     # 2014/2022 split logic
│   ├── methodology/
│   │   ├── preregistration_v1.md  # SUPERSEDED przez v2 (history)
│   │   ├── preregistration_v2.md  # ACTIVE — frozen choices + revision log
│   │   ├── h1_classical.py     # ADF, KPSS, Bayesian online CP, Welch, ACF
│   │   ├── k4_mmd.py           # Gaussian RBF on frequency vectors
│   │   ├── permutation.py      # shuffle test core (Numba selektywnie)
│   │   ├── block_bootstrap.py  # alternative null
│   │   ├── multiple_testing.py # BH FDR + Storey (family-aware)
│   │   ├── specification.py    # spec curve: 3 windows × 3 bandwidths = 9 points
│   │   └── recurrence.py       # gap test (permutation-calibrated) + Nelson-Aalen + EVT max-gap (W6)
│   ├── driftsim/
│   │   ├── planted_signals.py  # 5 signals concretely defined (zob. §5 Krok 5)
│   │   ├── null_uniform.py     # honest null generator
│   │   └── calibration.py      # sensitivity/specificity curves
│   ├── db/
│   │   ├── schema.sql          # regime_meta, calibration_runs (małe tabele)
│   │   ├── schema_validation.py# Pydantic models per tabela
│   │   └── queries.py          # safe_insert(table, model) + query funcs
│   ├── reporting/
│   │   ├── plots_static.py     # matplotlib (paper + .webm) + animate_bocpd_posterior()
│   │   ├── plots_interactive.py# Plotly (HTML embedded w Quarto)
│   │   ├── disagreement.py     # detector disagreement protocol
│   │   └── report.qmd          # Quarto source
│   └── adaptive/               # opcjonalny, self-value <20% scope
│       └── honest_watchlist.py # generate ONLY when DoD-1..5 pass
├── tests/
│   ├── conftest.py             # pytest.approx defaults
│   ├── test_environment.py     # Numba on Win11 + numpy 2.x sanity
│   ├── test_h1_invariants.py
│   ├── test_mmd_properties.py
│   ├── test_permutation_null.py
│   ├── test_driftsim_calibration.py
│   ├── test_recurrence.py
│   └── test_disagreement.py
├── artifacts/                  # git-lfs tracked
│   ├── raw_draws.parquet
│   ├── regime_{1,2,3}.parquet
│   ├── permutations/{test}/{regime}/worker_{id}.parquet  # sharded
│   ├── regime_meta.sqlite      # physical sink dla db/ access layer
│   ├── driftsim_runs/
│   ├── calibration_curves/
│   └── artifacts_manifest.json # SHA-256 manifest
├── notebooks/                  # exploratory, NIE part of pipeline
└── demo/                       # Streamlit app (W9+ stretch)
    └── app.py
```

**Preregistration versioning:** `preregistration_v2.md` to **active** wersja (`v1` superseded [2026-05-29] — zob. v2 §0 revision_reason). Każda metodologiczna korekta po Decision Gate tworzy `preregistration_v{N}.md` z polem `revision_reason: <text>`. Symlink/copy ostatniej jako aktywnej jest opcjonalna; explicit numbering wystarczy.

**Schemat `data/seed/eurojackpot_history.csv` (ISO 8601 daty, UTF-8, header w pierwszej linii):**

```csv
draw_date,main_1,main_2,main_3,main_4,main_5,euron_1,euron_2
2012-03-23,12,18,28,32,44,4,7
2014-10-10,3,7,12,29,41,4,9
...
```

- `draw_date`: `YYYY-MM-DD` (ISO 8601).
- `main_1..main_5`: integers 1–50, ascending (sorted at scrape time).
- `euron_1..euron_2`: integers 1–12 (outer bound). Valid range per reżim: **1–8 (R1, do 2014-10-03)**, **1–10 (R2, 2014-10-10→2022-03-18)**, **1–12 (R3, od 2022-03-25)**. `regime_split.py` mapuje valid range po dacie; `DrawRecord` waliduje outer bound 1–12. Rozszerzenie support euronumerów = positive control (zob. §10 DoD-1).

**Schemat `.env.example` (7 kluczy):**

```env
BASE_SEED=42
SCRAPER_USER_AGENT="DriftScope/0.1 (research; contact: <email>)"
SCRAPER_REQUEST_TIMEOUT_SEC=30
SCRAPER_RATE_LIMIT_DELAY_SEC=2
ARTIFACTS_DIR=./artifacts
DATA_SEED_PATH=./data/seed/eurojackpot_history.csv
LOG_LEVEL=INFO
```

Wszystkie ładowane przez `core/config.py` (Pydantic Settings).

### 4.2 Moduły — graf zależności (DAG)

```
ingestion ──► core.types ──► methodology ──► reporting
                  ▲              │              ▲
                  │              ▼              │
              driftsim ────────► db (sink) ─────┘
                  │
                  ▼
              adaptive (only-if DoD-1..5 pass)
```

**Konwencje:** `methodology/` to pure functions na `DrawRecord` sequences — nie zna ingestion ani reporting. `db/` jest **terminalnym sinkiem na poziomie kodu** (access layer: `queries.py`, `schema_validation.py`); fizyczne persistence to pliki w `artifacts/` (Parquet shards + `regime_meta.sqlite`). Reporting czyta przez `db/queries.py`, nie bezpośrednio z plików.

### 4.3 Przepływ danych (end-to-end)

```
eurojackpot.org archive (scraper) → ingestion/lotto_scraper.py
       │  (fallback Tier-1: data/seed/eurojackpot_history.csv)
       │  (fallback Tier-2: scripts/manual_import.py)
       ▼
artifacts/raw_draws.parquet
       │
       ▼
regime_split.py → artifacts/regime_{1,2,3}.parquet
       │
       ├──► methodology/h1_classical.py    ──┐
       ├──► methodology/k4_mmd.py           ─┤
       └──► driftsim/calibration.py         ─┤
                                              ▼
                       parquet shards: artifacts/permutations/{test}/{regime}/worker_{id}.parquet
                                              │  (Polars LazyFrame reduce)
                                              ▼
                       multiple_testing.py (family-aware FDR) + specification.py
                                              │
                                              ▼
                       reporting/{disagreement.py, plots, report.qmd}
                                              │
                                              ▼
                              adaptive/honest_watchlist.py (IFF DoD-1..5 pass)
```

---

## 5. Pipeline przetwarzania — krok po kroku

**Krok 0 — Data acquisition + power preview**
*(`scripts/manual_import.py`, `notebooks/00_power_preview.ipynb`)*

Cached CSV jako primary source dla pierwszego uruchomienia (committed do repo). Scraper jako live update mechanism.

**W0.1 — Scraper probe (research sub-task, mandatory pierwszy krok):** ręczna inspekcja struktury HTML `eurojackpot.org/archive` (lub odpowiednika), zidentyfikowanie selektorów CSS dla tabeli wyników + paginacji. Output: krótka notatka `scripts/scraper_selectors.md` z 3-5 selektorami (`table.results tbody tr`, `td.date`, `td.numbers`, itp.). DOPIERO PO TYM implementacja `lotto_scraper.py`.

Analytic power preview via `statsmodels.stats.power.GofChisquarePower` dla effect sizes {0.01, 0.02, 0.05, 0.10}. **Mandatory** — informuje czy DriftSim ma w ogóle szansę detect i jakie effect sizes można obronić w Negative Result Plan. Zrealizowane: `notebooks/00_power_preview.py`. **Wynik W0:** testy biegną per-reżim (real n = R1:133, R2:389, R3:436; total 958), więc binding constraint to n per-reżim, NIE pooled. δ=0.01 (najmniejszy pre-reg) jest per-reżim NIEwykrywalny globalnym GoF (power R1≈0.10, R2≈0.25, R3≈0.29); MDE @80% global ≈ 0.016–0.030 per reżim.

**Krok 1 — Ingestion** (`ingestion/lotto_scraper.py`)
Pull z eurojackpot.org archive page (selektory z W0.1). Cache do `artifacts/raw_draws.parquet`. Retry z exponential backoff (`tenacity`). **Validation:** `DrawRecord` Pydantic model fail-fast przy malformed data. Cadence: manual + wtorek/piątek wieczorem.

**Krok 2 — Regime split** (`ingestion/regime_split.py`)
Trzy parquet'y per reżim reguł: pre-2014-10-10, 2014-10-10→2022-03-25, post-2022-03-25. Każdy reżim traktowany jako oddzielny proces dla validation.

**Krok 3 — H1 Classical Baseline** (`methodology/h1_classical.py`)

Minimum sufficient subset:
- **ADF** — H₀: unit root (non-stationarity)
- **KPSS** — H₀: trend stationarity (komplementarne do ADF — różna H₀ daje pełniejszy obraz)
- **Bayesian online CP** (Adams-MacKay 2007, own impl) — generative model: Dirichlet-Multinomial conjugate (frequency vector p ~ Dir(α=1) prior, predictive posterior aktualizowana per draw). Zwraca **pełną macierz run-length posterior `P(R_t)`** (forward-pass, do ~958×958 ≈ 7 MB pooled; per-reżim mniejsza) — wymagane dla animacji W8 (surprise `S_t = -log P(x_t | R_{t-1})`)
- **Welch periodogram** + **Lomb-Scargle** — periodicity
- **Autocorrelation + PACF** — memory effect

CUSUM zachowany jako classical backup do Bayesian CP (cross-check via `ruptures` PELT).

**Krok 4 — K4-MMD Kernel Two-Sample Test** (`methodology/k4_mmd.py`)

**Input space:** frequency vector `p ∈ Δ⁴⁹` per sliding window N=200, reprezentowany jako `pl.List(pl.Float64)` w Parquet. **NIE** raw draw sequences. RBF kernel z bandwidth = median heuristic obliczanej **wyłącznie na training window** (anti-leakage). Pre-registered w `preregistration_v2.md`. Asymptotic theory via Gretton et al. 2012.

⚠️ Stability przy N=200 UNVERIFIED — W4 PoC: empirical calibration vs shuffled null, threshold pass = false positive rate ≤ 7.5% (preregistration_v2.md §3, granica dwustronna wokół α=0.05).

**Krok 4b — Recurrence / gap analysis** (`methodology/recurrence.py`, W6)

Czas (liczba losowań) między kolejnymi wystąpieniami danej liczby. Pod nullem uniform-iid gap ~ Geometric(q), q = 5/50 dla puli głównej.

- **Gap goodness-of-fit:** odchylenie empirycznego rozkładu gapów od Geometric(q) per liczba per reżim. ⚠️ **NIE analityczny KS** — test Kołmogorowa-Smirnowa jest nieważny dla rozkładów dyskretnych (błędnie skalibrowane p-value). Statystyka kalibrowana przez istniejący silnik permutacyjny (Krok 6), zgodnie z mandatem Krok 5 ("żaden test nie raportuje p-value bez własnej kalibracji").
- **Nelson-Aalen cumulative hazard** per liczba: liniowość skumulowanego hazardu = stała intensywność = zgodność z uniform. Wizualny artefakt diagnostyczny. Implementacja własna (~20 LOC NumPy, `cumsum(d_i/n_i)`), bez `lifelines` (zob. §3-alt).
- **EVT max-gap:** maksymalny gap w sekwencji ma asymptotycznie rozkład Gumbela (gapy geometryczne leżą w domenie przyciągania Gumbela). Test wykrywający odstające "uśpione" liczby.
- Zasilanie Family B FDR (zob. Krok 7).

**Krok 5 — DriftSim Calibration** (`driftsim/`)

**Concrete 5 planted signals:**
1. **Frequency shift** — pojedyncza liczba ma p = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}
2. **Autocorrelation lag-1** — `P(x_t = k | x_{t-1} = k) = (1/50) + ρ`, ρ ∈ {0.05, 0.10, 0.15, 0.20}
3. **Linear trend** — `p_k(t) = p_k + β·(t/T)`, β kalibrowane dla 4 effect sizes
4. **Weekly seasonality** — różne p dla wtorek vs piątek (cycle period = 2 draws). ⚠️ **Tylko R3:** EuroJackpot losował wyłącznie w piątki do marca 2022; wtorki dodano dopiero w R3. Generator wstrzykuje ten sygnał **wyłącznie w reżimach z ≥2 dniami losowań** (realnie tylko R3). W R1/R2 kontrast Tue/Fri nie istnieje fizycznie → scenariusz degeneruje do uniform null.
5. **Pair correlation** — liczby `i, j` współwystępują częściej, lift ∈ {1.1, 1.2, 1.5, 2.0}

**Generacja datasetów:** 5 patterns × 4 effect sizes = **20 planted scenarios per regime** + 1 uniform null scenario = **21 datasetów per regime**. × 3 regimes = **63 unikalne datasety**. **Datasety są shared across tests** — każdy H1 test + MMD ewaluowany na każdym datasecie (nie 21 × N_tests datasetów). Count 63 zachowany: w R1/R2 scenariusze signal #4 (weekly seasonality) degenerują do uniform null — zajmują slot datasetu i pełnią rolę **dodatkowego negative control** (detektor nie powinien tam nic znaleźć).

Output: sensitivity/specificity curves per test per regime, jako `.parquet` + `.html`. **Mandatory:** żaden test nie raportuje p-value na real data bez własnej kalibracji.

**Krok 6 — Permutation testing** (`methodology/permutation.py`)

- **Shuffle test core (DoD-2):** permutacje porządku losowań, 10⁴ permutacji per (test, regime, kernel_config).
- **Block bootstrap** (`block_bootstrap.py`) — alternative null zachowujący krótkozasięgowe korelacje (block size ∈ {5, 10, 20}).
- Wzorzec: `@njit(cache=True)` wewnętrzny loop (selektywnie); `joblib.Parallel` **nad konfigami** `(test, regime, kernel_config, seed_offset)` — NIGDY nad pojedynczymi permutacjami. Output: parquet shards per worker.
- **Stratyfikowana permutacja (R3):** w reżimie z dwoma dniami losowań permutacja domyślnie zachowuje etykietę dnia (Tue/Fri), żeby null nie konfundował planted signal #4 (weekly seasonality). W R1/R2 (tylko piątek) bez efektu.
- **Seedy:** `core.seeds.make_worker_seeds(BASE_SEED, n_workers)` zwraca `list[SeedSequence]`; każdy worker spawnuje własny `np.random.default_rng(seed_seq)` — gwarancja non-correlated streams.

**Krok 7 — Multiple testing correction** (`methodology/multiple_testing.py`)

**Family-aware FDR (α=0.05):**
- **Family A (global time-series tests):** 4 testy (ADF, KPSS, Bayesian CP, Welch) × 3 regimes = **12 hipotez**. **Benjamini-Hochberg** + Storey q-values jako secondary sanity.
- **Family B (per-number tests):** 50 numbers × 3 testy (chi-squared, exact binomial, gap goodness-of-fit z Kroku 4b) × 3 regimes = **450 hipotez**. **Benjamini-Yekutieli** jako primary — ważny przy dowolnej strukturze zależności (zliczenia 5/50 są ujemnie skorelowane, gapy współzależne), gdzie założenie PRDS dla BH jest niepewne; BH jako secondary. Storey odrzucony (niestabilny przy dominującym null).

**Krok 8 — Specification curve** (`methodology/specification.py`)

2 parametry × 3 wartości = **9-point spec curve** per signal:
- window size N ∈ {100, 200, 400}
- bandwidth ∈ {0.5×, 1×, 2×} median heuristic

Jeśli reported signal znika przy minor specification change (>2/9 points trace p>0.05) → unstable, **nie raportowany** w final report.

**Krok 9 — Reporting** (`reporting/`)

Quarto report (`report.qmd`) z embedded Python chunks. Plotly figury → HTML embedded; matplotlib → PDF appendix + `.webm` hook export. Negative result framing first-class.

**Krok 9.1 — Disagreement Protocol** (`reporting/disagreement.py`)

Dla każdego candidate signal, klasyfikacja per zgodność filarów (H1 / MMD / DriftSim):
- **3/3 zgodność** → "fully convergent signal", reported as primary finding.
- **2/3 zgodność** → "convergent signal", reported w main section.
- **1/3 zgodność** → "single-pillar signal, requires DriftSim power context" — reported z explicit warning + power curve.
- **0/3** → "no signal" section.

To operacjonalizuje DoD-4.

**Krok 10 — Adaptive watchlist** (`adaptive/`, opcjonalny, self-value <20% scope)

Wykonuje się TYLKO jeśli ≥1 wzorzec przeszedł DoD-1..5 z FDR<0.05. W przeciwnym razie zwraca `None` z explicit message "no signal above detection threshold".

---

## 6. Compute Execution Policy

### 6.1 Resource budget per etap

| Etap | RAM peak | Disk | CPU time (12C/16T) | Notes |
|---|---|---|---|---|
| Ingestion (scraper) | <100 MB | <5 MB | 30 s – 5 min | Rate-limited (2s/request), ~958 draws (2012–2026) |
| Regime split | <200 MB | <10 MB | <5 s | Polars lazy |
| H1 single run | <500 MB | — | 1–10 s | Per regime per test |
| MMD single config | <800 MB | — | 5–60 s | Kernel matrix 500×500 max |
| Simple permutation test (ADF, chi², 10⁴ perms) | <500 MB | 1–5 MB shard | <10 s | Numba seq scaling |
| MMD permutation test (10⁴ perms) | <2 GB | 5–20 MB shard | 1–15 min | Numba JIT na hot loop ROI |
| DriftSim full sweep (63 unique datasets gen) | <3 GB | 100–300 MB | 1–3 h | Shared across tests |
| **Full test×dataset evaluation pipeline** | <4 GB | 200–500 MB | **4–10 h** | Wszystkie tests × wszystkie datasets × 10⁴ perms |
| Polars LazyFrame reduce (merge shards → results) | <2 GB | <50 MB | **5–15 min** | `scan_parquet(glob).group_by(...).collect()` |
| Specification curve sweep (9 points) | <1 GB | <20 MB | 30–60 min | Po reduce |
| Quarto render | <1 GB | <50 MB output | <5 min | — |

**VRAM budget:** N/A — pipeline CPU-only.
**Total disk budget:** ~1.5–2 GB. git-lfs handles, no remote config required for MVP.

### 6.2 CPU Transcendence Stack (aplikowane Osie z HARDWARE_PUSH_CATALOG)

| Oś / Technika | Implementacja | Impact | Status |
|---|---|---|---|
| **Oś 0 — Environment** | Pre-flight `test_environment.py` (Numba on Win11 + numpy 2.x) | Fail-fast w W1 | ✓ |
| **Oś 3 — Compilation** | Numba JIT selektywnie (MMD hot loop, BCPD inner) | 2.7× simple, 10–30× MMD | ✓ PoC verified |
| Parallelism | `joblib.Parallel(backend='loky')` nad konfigami (NIGDY nad permami) | ~10–12× na 12 cores | ✓ Win11-safe |
| Caching | Parquet shards per worker → Polars LazyFrame reduce | Re-run skip = ∞× (`--resume`) | ✓ |
| Algorithmic | Importance sampling permutations dla rzadkich p-values | 2–5× przy long tail | ⚠️ tylko jeśli baseline >6 h |
| Algorithmic | Analytic null (asymptotic χ²) jako sanity check | — | ✓ cross-check, NIE zastępstwo |
| Vectorization | Polars group-by zamiast pandas apply | 5–30× | ✓ |
| I/O | Parquet + zstd | 5–10× faster read | ✓ |
| Build-time cloud | Colab/Kaggle dla independent cross-environment re-run | Reproducibility signal | ⚠️ optional |

### 6.3 Build-time tasks

| Zadanie | Gdzie | Output | Fallback |
|---|---|---|---|
| DriftSim full calibration sweep | Lokalnie overnight | `artifacts/driftsim_runs/*.parquet` | Kaggle CPU 30h/tydzień |
| 10⁴ permutation final run | Lokalnie overnight, raz przed milestone | Parquet shards | Colab CPU independent re-run |
| Specification curve sweep (9 points) | Lokalnie | `artifacts/specification_curves.parquet` | — |
| Quarto report render | Lokalnie (lub GitHub Actions docelowo) | `docs/report.html`, `docs/report.pdf` | `jupyter nbconvert` |
| Static demo (Plotly HTML) | Lokalnie → GitHub Pages | `docs/report.html` | — |
| HF Spaces demo (Streamlit, W9+ stretch) | GitHub Action → HF Hub | Streamlit app | — |

**Build-time artifact smoke tests** (`tests/test_artifacts_smoke.py`):

| Artefakt | Path glob | 1-line smoke test |
|---|---|---|
| DriftSim runs | `artifacts/driftsim_runs/*.parquet` | `assert pl.scan_parquet('...').select(pl.count()).collect().item() > 0` |
| Permutation shards | `artifacts/permutations/*/*/*.parquet` | `assert len(glob.glob('...')) >= EXPECTED_SHARDS` |
| Spec curve | `artifacts/specification_curves.parquet` | `assert 'p_value' in pl.read_parquet('...').columns` |
| Report | `docs/report.html` | `assert os.path.getsize('...') > 1024` |

Wykonanie kolejności: (1) DriftSim sweep → (2) permutation runs → (3) spec curve sweep → (4) Quarto render.

### 6.4 Runtime fallbacki kaskadowe

1. **Permutation engine speed:**
   - A: Numba JIT + joblib nad konfigami (default)
   - B: pure NumPy + joblib nad konfigami (jeśli Numba broken — `test_environment.py`)
   - C: scipy.stats analytic approximation z explicit "approximate p-value, dependence-untested" flag w raporcie

2. **Storage permutation results:**
   - A: Parquet shards per worker (default)
   - B: JSONL append-only per worker (debugging)

3. **Long pipeline interruption:**
   - A: `cli.run --resume` skips configs with existing shards (default)
   - B: Manual restart from last shard timestamp

4. **Data source availability:**
   - A: Live scraper z eurojackpot.org
   - B: `data/seed/eurojackpot_history.csv` (committed)
   - C: Manual CSV upload via `scripts/manual_import.py`

5. **Quarto render:**
   - A: Quarto 1.5+ (default)
   - B: `jupyter nbconvert` → HTML
   - C: Markdown + manual matplotlib `.png` embedding

6. **HF Spaces demo (W9+):**
   - A: Streamlit on HF Spaces (free tier)
   - B: Static `docs/report.html` na GitHub Pages
   - C: Render.com embedded Plotly HTML

### 6.5 Composability check

| Para technik | Status | Notes |
|---|---|---|
| Numba JIT × joblib.Parallel (nad konfigami) | ✓ | PoC verified; `@njit(cache=True)` picklable wrapper |
| Numba JIT × Polars | ✓ | Konwersja via `.to_numpy()` przed JIT hot path |
| Parquet shards × joblib parallel writes | ✓ | Każdy worker pisze do własnego pliku — zero contention |
| SQLite × append-only single-writer (regime_meta) | ✓ | Tylko CLI main process pisze; tabela mała |
| git-lfs × parquet | ✓ | LFS handles binary; deterministic via sorted CSV hash |
| Pydantic Settings × `.env` | ✓ | Permanent pattern |
| Quarto × Polars | ✓ | Python chunks via jupyter kernel |
| `matplotlib.animation` × ffmpeg → .webm | ✓ | Standard pipeline; VP9 codec for GitHub `<video>` rendering |
| `pl.List(pl.Float64)` × MMD frequency vectors | ✓ | Arrow native nested list; Polars `.list.eval()` for elementwise ops |

---

## 7. Roadmap: MVP → Portfolio-ready → Open-source-ready

### 7.1 Week-by-week

| Tydzień | Cel | Deliverable | DoD spełnione |
|---|---|---|---|
| **W0** (8h) | Data + power preview | Scraper probe (W0.1: selektory) → live scraper PoC; cached CSV committed; analytic power preview notebook | — |
| **W1** (30h) | Environment + H1 core + DoD-1 | `test_environment.py` green; ADF + KPSS + Bayesian CP detect 2014/2022 blind; skeleton committed | DoD-1a, DoD-1b |
| **W2** (32h) | DriftSim part I | 5 planted signal generators × 4 effect sizes; uniform null; unit tests; 63 datasetów wygenerowane | — |
| **W3** (32h) | DriftSim part II — calibration | Sensitivity/specificity curves per H1 test per regime; first artifacts under git-lfs | DoD-5 (foundation) |
| **W4** (24h) | K4-MMD core | MMD impl on frequency vectors; pre-registered choices w `preregistration_v2.md`; PoC: asymptotic stability at N=200 vs shuffled null | DoD-4 (foundation) |
| **W5 — DECISION GATE** (16h) | Triangulation check | H1 + MMD detect planted signals z power >70%? **TAK** → W6. **NIE** → Plan B (§7.3) | DoD-3 |
| **W6** (24h) | Rigor layer | Family-aware FDR (A: 12 BH, B: 450 BY); `recurrence.py` (gap/Nelson-Aalen/EVT, permutation-calibrated); 9-point spec curve; Storey sanity Family A | DoD-2 (full) |
| **W7** (24h) | Reporting + adaptive + disagreement | Quarto draft; `disagreement.py`; watchlist module; README disarmer | DoD-6 |
| **W8** (20h) | Polish MVP | Final README; static plots; `.webm` hook export; **BOCPD posterior animation** (`P(R_t)` run-length heatmap + surprise `S_t`); static `docs/report.html` na GitHub Pages | MVP complete |
| **W9** (16h) | Portfolio polish | Recruiter executive summary (1 page PDF); spec curve sweep documented; (stretch: Streamlit demo) | Portfolio-ready |
| **W10** (20h, opcjonalny) | Open-source readiness | CI/CD (GitHub Actions); CONTRIBUTING.md; pyproject installable; semver v0.1.0 | OS-ready |

### 7.2 Power Analysis & Negative Result Plan

**Status: co-primary deliverable** (NIE fallback). Niezależnie od wyniku detekcji, tabela *"minimum detectable effect size @ 80% power"* per test per reżim jest pierwszorzędnym produktem naukowym. Przy realnym n=958 (per-reżim 133/389/436; główna liczba ~13–44 wystąpień per reżim) moc dla subtelnych biasów jest z założenia ograniczona — potwierdzone w `notebooks/00_power_preview.py`. Skwantyfikowanie tej granicy JEST wkładem, a wynik null jest publikowalny przy explicit framing.

Jeśli żaden detektor nie znajduje sygnału przy FDR<0.05, raport zawiera explicit sekcję **"Power Analysis & Detection Limits"**:
- Plot: power vs effect size z DriftSim, per test, per regime.
- Tabela: "minimum detectable effect size at 80% power" per test.
- Conclusion: "n per-reżim (133–436) jest insufficient dla effect sizes <X" — to JEST publishable wynik (np. δ=0.01 globalnie niewykrywalny per-reżim).

Negative result NIE jest porażką projektu — jest *rigor signal* przy explicit framing.

### 7.3 Plan B (Tydzień 5 fail)

Z SWOT TOP 1: jeśli H1 + MMD nie wykrywają planted signals → projekt staje się "framework for measuring detector hallucination rates in supposedly memoryless processes". Framing z §1 ("calibrated detector hallucination rates") jest *kompatybilny* z Plan B — ta sama narracja, bez positive result section. README disarmer niezmieniony.

### 7.4 Definition of "ready" per tier

**MVP (W0–W8):** wszystkie DoD-1..6 spełnione, raport Quarto dostępny, repo clean, README z disarmerem.

**Portfolio-ready (W9):** + recruiter executive summary (1 page PDF), + `.webm` hook embedded w README, + static demo na GitHub Pages.

**Open-source-ready (W10):** + GitHub Actions CI (test + lint + Quarto render), + CONTRIBUTING.md, + plug-in interface dla custom DriftSim signal generators (stretch: NIST RNG case), + semver tag v0.1.0, + Zenodo DOI.

---

## 8. Risk Register + Mitigation

| # | Ryzyko | Typ | Prawd. | Impact | Mitygacja | Trigger detekcji |
|---|---|---|---|---|---|---|
| R1 | Hallucination (detektor "znajduje" sygnał, którego nie ma) | Methodological | M | **CRITICAL** | Shuffle test obligatory + family-aware FDR + spec curve + DriftSim + 3-panel hook (uniform RNG control) + Disagreement Protocol | p-value <0.05 na real ALE także na ≥1 shuffled fold |
| R2 | Statistical power <30% dla subtle signals przy n per-reżim (133/389/436) | Methodological | H | M | W0 power preview (DONE, `notebooks/00_power_preview.py` — potwierdza δ=0.01 niewykrywalny per-reżim); explicit power analysis; Negative Result Presentation Plan | Power curve z W0 + DriftSim |
| R3 | Specification curve overfitting | Methodological | L | M | Pre-registered space (`preregistration_v{N}.md`); ograniczone 9 points | Diff preregistration z final config |
| R4 | "Lotto-scam" first impression u recruitera | Portfolio | M | H | 3-sentence disarmer; methodological framing; no emojis; 3-panel hook z uniform control | Recruiter feedback post-launch |
| R5 | "Stack za prosty" | Portfolio | M | M | Spec curve + DriftSim + Numba/Polars + family-aware FDR | Self-assessment W8 |
| R6 | 8-10 tyg overrun | Scope | H | M | DriftSim (W2-3) fixed time-box; Plan B safe landing; W10 opcjonalne | Behind schedule W3 lub W5 |
| R7 | DriftSim calibration sweep > overnight | Scope/compute | M | M | Numba JIT W1 sanity; checkpointing via shards; Colab CPU backup | Single config >30 min w W2 |
| R8 | Numba on Win11 issues | Środowisko | Very Low | H | PoC verified 2026-05-17; fallback do pure NumPy | `import numba` fails |
| R9 | Bayesian online CP own impl buggy | Methodological | M | M | Dirichlet-Multinomial spec w preregistration; property-based tests; cross-check vs ruptures PELT | Disagreement >10% z PELT |
| R10 | Gambling addiction ethical concern | Etyczne | L | H | README disclaim §1; no "predict your numbers" framing; honest-None return | — |
| R11 | Scraper ToS violation lub site change | Legal/Tech | M | M | ToS review w W0; cached CSV jako Tier-1 fallback; manual CSV upload Tier-2 | Scraper fail or ToS change |
| R12 | MMD asymptotic instability at N=200 | Methodological | M | M | W4 PoC: empirical calibration vs shuffled null; pass threshold = FPR ≤ 7.5% (preregistration_v2.md §3); PRZED W5 Decision Gate | FPR >7.5% w shuffled |
| R13 | Gap test: analityczny KS nieważny dla rozkładów dyskretnych (błędne p-value) | Methodological | M | M | Statystyka gap kalibrowana permutacyjnie (Krok 4b via Krok 6), NIGDY `scipy.stats.kstest`; Family B przez Benjamini-Yekutieli (zależność) | KS p-value rozbiega się z permutacyjnym >0.02 |

---

## 9. Szacunki czasowe per faza (godziny netto)

| Faza | Min | Realistyczne | Max |
|---|---|---|---|
| W0 — Data + power preview | 6 h | 8 h | 12 h |
| W1 — Env + H1 core + DoD-1 | 20 h | 30 h | 40 h |
| W2 — DriftSim part I | 24 h | 32 h | 44 h |
| W3 — DriftSim calibration | 24 h | 32 h | 44 h |
| W4 — K4-MMD core + N=200 PoC | 16 h | 24 h | 32 h |
| W5 — Decision Gate + iteration | 12 h | 16 h | 24 h |
| W6 — Rigor layer | 16 h | 24 h | 32 h |
| W7 — Reporting + adaptive + disagreement | 18 h | 24 h | 32 h |
| W8 — Polish MVP | 12 h | 20 h | 28 h |
| **TOTAL MVP (W0–W8)** | **148 h** | **210 h** | **288 h** |
| W9 — Portfolio polish | 12 h | 16 h | 24 h |
| W10 — OS readiness (opcjonalne) | 12 h | 20 h | 28 h |
| **TOTAL 10-week** | **172 h** | **246 h** | **340 h** |

---

## 10. DoD Mapping

| DoD | Komponent walidujący | Pass criterion |
|---|---|---|
| DoD-1a — Positive control (euronumery) | H1 stationarity tests na strumieniu euronumerów | Detekcja rozszerzenia puli: 1–8 (R1) → 1–10 (R2, od 2014-10-10) → 1–12 (R3, od 2022-03-25). Pojawienie się liczb 9/10 oraz 11/12 = znana zmiana support → detektor MUSI zapalić |
| DoD-1b — Blind CP (positive control) | Bayesian online CP + CUSUM na euronumerach | Top-2 ranked change-points pokrywają się z 2014-10-10 i 2022-03-25 (±30 dni) **przed** ręcznym sprawdzeniem |
| DoD-1c — Negative control (główne 1–50) | te same detektory na strumieniu 5/50 | Pula główna NIE zmieniła się w 2014 ani 2022 → detektor nie powinien rankować CP w tych datach. Spurious CP na głównych liczbach = hallucination signal (wiąże z R1) |
| DoD-2 — Shuffle test rigor | `methodology/permutation.py` | False-positive rate w shuffled data ≤ α=0.05 ± Monte Carlo error |
| DoD-3 — Multiple testing correction | `methodology/multiple_testing.py` | Family-aware: BH w Family A (12 hyp), Benjamini-Yekutieli w Family B (450 hyp) — osobno |
| DoD-4 — Complementary pillars | H1 + MMD + DriftSim via `reporting/disagreement.py` | Każdy reported signal classified per Disagreement Protocol (§5 Krok 9.1): 3/3, 2/3, 1/3, lub 0/3 |
| DoD-5 — Honest predictor (kalibracja) | `driftsim/calibration.py` | Adaptive watchlist generuje output IFF passed DoD-1..4; w przeciwnym razie None |
| DoD-6 — Reproducibility | `core/seeds.py` + git-lfs + GitHub Action | Cold-machine re-run produces bit-identical SHA-256 hash z `ORDER BY (test, regime, seed)` CSV eksportu (nie binarki SQLite) z committed `BASE_SEED=42` |

---

## 11. Open Questions z SEED_IDEA — resolution

| Pytanie SEED_IDEA | Status | Resolution |
|---|---|---|
| §7A.1 — DoD-1 blind protocol sufficient? | RESOLVED | Ranking change-pointów *przed* porównaniem z 2014/2022 |
| §7A.2 — Paradygmat redefinujący target | DEFERRED to W10+ stretch | TDA jako post-MVP |
| §7B.5 — Hardware Transcendence? | PARTIALLY RESOLVED | Oś 0 + Oś 3 (Numba) aplikują; reszta nie |
| §7C.6 — Statistical power przy n per-reżim | RESOLVED | W0 power preview DONE (real n=958, per-reżim 133/389/436) + DriftSim curves; Negative Result Presentation Plan |
| §7C.7 — Update cadence per komponent | RESOLVED | Online auditor per-draw; H1 per-draw 1-10s; MMD weekly; DriftSim once + per milestone |
| §7C.8 — Honest augmentation | RESOLVED | Within-draw permutations odrzucone (operacja tożsamościowa dla frequency vector). Block bootstrap jako alternative null |
| §7D.9–10 — Framing scam-disarm | RESOLVED | 3-sentence disarmer + 3-panel hook z uniform RNG control |
| §7E.11 — Blind-spot question | ADDRESSED | Negative Result Presentation Plan jako first-class deliverable |

---

## 12. Anti-goals guard

- ☑ **Nie naive frequency** — H1 minimum sufficient: ADF + KPSS + Bayesian CP + Welch + ACF, każdy z permutation-based istotnością.
- ☑ **Nie hallucinated signal** — DoD-2 (shuffle test) obligatory; family-aware FDR; spec curve mandatory; DriftSim power context; Disagreement Protocol; uniform RNG control panel w hook.
- ☑ **Nie wrapper na cudzy model** — własna implementacja Bayesian CP (Dirichlet-Multinomial), własny MMD (~80 LOC), własny DriftSim.
- ☑ **Nie "gwarantowana wygrana"** — README §1 explicit disclaim; adaptive module honest-None; framing methodological.
- ☑ **Nie pivot z premise** — EuroJackpot pozostaje flagship case study; NIST RNG, kryptograficzne PRNG jako stretch §1.
- ☑ **Nie ograniczenie do Pythona z definicji** — R/Julia/Rust rozważone i odrzucone z explicit uzasadnieniem (§3-alt).

---

## PoC Results — Krok 6 (2026-05-17)

**Środowisko:** Python 3.10.13 | numpy 2.2.5 | numba 0.65.1 | joblib 1.5.3 | Win11 | i5-12500H (12C/16T)

### Warianty testowane

| Wariant | Opis | Wynik |
|---|---|---|
| A — NumPy sequential | 1000 perms, 1 core, full loop | **0.06 s → 15 879 perms/s** |
| B — NumPy + joblib per-perm | 1000 callbacków, wszystkie rdzenie | 0.99 s → 1 010 perms/s (**16× wolniej niż A**) |
| C — Numba JIT (1-core) | JIT cały loop, 1000 perms | **0.02 s → 43 094 perms/s** |
| C' — Numba JIT + joblib nad configs | 8 jobów × 125 perms, wszystkie rdzenie | 1.89 s → 530 perms/s (overhead joblib dominuje dla małych jobów) |

### Kluczowe wnioski

1. **Numba JIT (loop-level) = 2.71× szybsze niż NumPy sequential.** Dla 10k perms × 1 config: NumPy ~0.63 s, Numba ~0.23 s.
2. **joblib per-perm (Wariant B) jest WOLNIEJSZE niż sequential.** Process-spawn overhead + serialization dominuje dla krótkich callbacków.
3. **Poprawny wzorzec:** `@njit` kontroluje wewnętrzny loop, `joblib.Parallel` operuje nad konfiguracjami (`(test, regime, kernel_config, seed_offset)`), nie nad pojedynczymi permutacjami:

```python
@njit(cache=True)
def run_all_perms(draws, n_perms, start_seed):
    ...

Parallel(n_jobs=-1)(
    delayed(run_all_perms)(draws, n_perms, seed_offset)
    for seed_offset in config_seeds
)
```

4. **Szacunek pełnej pipeline (10⁴ perms × 150 configs):** Numba JIT + joblib over configs daje ~0.8 h (konserwatywnie z overhead). Mieści się w overnight limicie.

5. **Numba 0.65.1 na Win11 + numpy 2.x:** zweryfikowane, działa. R8 zmniejszone do Very Low.

### Decision

✅ Wariant C działa, pipeline w overnight limicie. Przejście do W7 (cross-review).

---

**Akceptacja:** ten brief jest *contract* — każda zmiana decyzji wymaga update commit'u z rationale. Drobne tactical changes (lib version bump w tym samym major) OK bez review; architectural changes wymagają explicit re-review.

**Handoff:** ten plik jest gotowy do przekazania Claude Code CLI jako root-level architectural contract obok `CLAUDE.md`. Pierwsze pytanie Code do tego brief'u powinno brzmieć: *"Czy rozpoczynamy od W0.1 (scraper probe + manual selector inspection w `scripts/scraper_selectors.md`), czy od pyproject.toml scaffolding?"* — odpowiedź: **W0.1 pierwszy (research blocker), pyproject.toml + struktura katalogów w tej samej sesji po zidentyfikowaniu selektorów.**
