# PROJECT_BRIEF.md — DriftScope (v2.0)

> **Architectural contract.** Decyzje w tym dokumencie są *permanent patterns* — zmiana wymaga explicit re-review przed dotknięciem kodu.
>
> **Wersja:** v2.0 · **Status:** ready-for-handoff (Claude Code CLI) · **Tier:** MEDIUM · **Język brief'u:** PL/EN mix
> **Diff vs v1.0:** zob. §Appendix A — Transparency Table na końcu pliku.

---

## 0. Flagi i konwencje

- **Konflikt zaadresowany:** sekcja "Hardware Transcendence Stack" z generic szablonu jest częściowo zastąpiona **Compute Execution Policy** (§6) dla realnego bottleneck'u — CPU permutation overhead. `HARDWARE_PUSH_CATALOG.md` aplikuje **selektywnie**: **Oś 0 (Environment Sanity)** i **Oś 3 (Compilation — Numba JIT na CPU)** pozostają aktywne; Osie 1–2, 4–7 nie aplikują (brak GPU, brak modeli neural, brak VRAM budget).
- **Anti-goal guard:** każda decyzja sprawdzona pod SEED_IDEA §5A.1–4 (no naive frequency, no hallucinated signal, no wrapper, no gambling-app framing) i §5B.1–4 (no premise pivot).
- **Permanent pattern (Piotr's template):** `pyproject.toml` jako single source of truth; `artifacts/` na root; `@dataclass Config` per moduł dla standalone CLI; `db/queries.py` zamiast Repository pattern (solo dev); PowerShell 5.1 compatible; zmiany w istniejących plikach, nie patch-documenty.

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
- **Panel 1 (Real):** EuroJackpot stream, oś czasu 2012→2026, czerwone markery na 2014-10-08 i 2022-03-25 (znane change-pointy). Bayesian online CP "konsumuje" datapoint po datapoint, p-value spada do <0.001 na obu change-pointach.
- **Panel 2 (Uniform RNG control):** ten sam framework na `secrets.randbelow(50)` — detektor nie zapala niczego, p-value zostaje w noise. **To jest visceral proof of non-hallucination.**
- **Panel 3 (Shuffled real):** real stream z permutowaną kolejnością — detektor traci change-pointy.

**Główny "wow":** trzy panele bok w bok pokazują, że detektor *odpowiada na rzeczywistą strukturę czasową*, a nie generuje sygnał. Real → detection. Uniform → null. Shuffled → null. **Lotto-scam disarmer w postaci wizualnej.**

**Custom design system:** minimal. Color palette: 3 kolory (real = `#0EA5E9` blue, control = `#94A3B8` slate, change-point marker = `#EF4444` red). Typography: JetBrains Mono dla wszystkich liczb/p-values, Inter dla narracji. **Brak ikon/emoji w README** (anti-scam signal). Logo: scope-wise odrzucone z MVP.

**Biblioteka:** `matplotlib.animation.FuncAnimation` → `ffmpeg-python` → `.webm` (VP9, ~2-5 MB target). Embed:
```html
<video src="docs/hook.webm" autoplay loop muted playsinline controlsList="nodownload"></video>
```
GitHub renderuje `<video>` natywnie w MD. **NIE Plotly autoplay w iframe** (GitHub blokuje), **NIE GIF z `kaleido`** (50-100 MB), **NIE D3/Three.js** (SWOT K2 — solo dev frontend overrun risk).

**Pierwsze 3 zdania README (finalna wersja):**
> *DriftScope is a stationarity audit framework for streaming discrete-valued processes. The flagship case study is EuroJackpot — a process designed to be uniform-random, where the empirical question is whether any detectable deviation from uniformity exists. The project is methodological in nature; it neither claims nor seeks to predict lottery outcomes in any actionable sense.*

---

## 3. Stack technologiczny — z uzasadnieniem każdego wyboru

| Warstwa | Wybór | Wersja | Uzasadnienie |
|---|---|---|---|
| Język/runtime | **Python 3.10** | 3.10.x | Znany Piotrowi, dojrzały ekosystem stat |
| Stationarity tests | **statsmodels** | 0.14.x | ADF, **KPSS** (restored — przeciwna H₀ niż ADF, NIE redundantne), ACF/PACF |
| Change-point detection | **ruptures** | 1.1.9+ | CUSUM, Pelt, Binseg — cross-check vs Bayesian CP |
| Bayesian online CP | **własna implementacja Adams-MacKay 2007** | — | Generative model: Dirichlet-Multinomial conjugate (zob. `preregistration.md` §2). ~150 LOC + tests. |
| Spectral analysis | **scipy.signal** | 1.13.x | Welch, Lomb-Scargle |
| Kernel methods (MMD) | **scikit-learn** kernels + custom MMD | sklearn 1.4.x | `pairwise_kernels` jako primitive; MMD ~80 LOC. **Input space:** frequency vectors p ∈ Δ⁴⁹ per sliding window (NIE raw draws). RBF na simplex z bandwidth z **training-window only** (anti-leakage). ⚠️ Asymptotic stability przy N=200 UNVERIFIED — empirical calibration vs shuffled null w W4 PoC. |
| Permutation engine | **Numba JIT** (selektywnie) + `joblib.Parallel` (nad konfigami) | Numba 0.65.x | **`@njit(cache=True)` TYLKO gdzie profilowanie pokaże >2× zysk** (MMD permutation core priorytetowo, BCPD inner loop opcjonalnie). NumPy sequential default dla prostych testów (chi-squared, ADF). PoC: 2.7× dla prostych, oczekiwane 10-30× dla MMD O(N²). |
| Multiple testing | `statsmodels.stats.multitest` | 0.14.x | Benjamini-Hochberg FDR (primary), Storey q-values (secondary sanity, 3 LOC) |
| ~~Conformal inference~~ | ~~mapie~~ | ~~—~~ | **USUNIĘTE** (v2.0). `mapie` jest do conformal *prediction* (intervals/sets), nie do testowania hipotez stacjonarności / exchangeability martingales. Conformal p-values jako filar wykreślony z MVP. Specification curve pokrywa robustness signal. |
| Data manipulation | **Polars** | 1.x | Type-safe, modern stack signal. 1500 rows scale TYLKO MVP — framework dla NIST RNG (10⁶+) stretch. |
| Data ingestion | `httpx` + `selectolax` (HTML parsing) + `tenacity` (retry) | — | **Primary: scraper z eurojackpot.org archive** (brak publicznego API z kluczem). Cached CSV jako Tier-1 fallback (committed do `data/seed/eurojackpot_history.csv`). |
| Storage — raw/cleaned data | **Parquet** (`pyarrow`) | — | Zstd compression |
| Storage — permutation results | **Parquet shards per worker** | `pyarrow` | `artifacts/permutations/{test}/{regime}/worker_{id}.parquet`. Merge w reduce phase via Polars LazyFrame. **Zastępuje SQLite jako primary cache** (SQLite WAL nie obsługuje N writers). |
| Storage — metadata | **SQLite** (mała, append-only) | stdlib | `artifacts/regime_meta.sqlite` tylko dla regime_meta + calibration_runs (1 writer pattern OK). |
| Data versioning | **`git lfs` + `scripts/archive.py`** | `git-lfs` 3.x | `git lfs track "*.parquet"` + manifest SHA-256 zawartości logicznej. **DVC usunięte** (v2.0) — overhead nieproporcjonalny dla <2GB; binary blob anti-pattern dla SQLite. |
| Config | **Pydantic Settings** v2 + `.env` | 2.x | Permanent pattern; `core/config.py` |
| Data validation | **Pydantic** v2 | 2.x | `DrawRecord` z `Field(ge=1, le=50)` dla main, `Field(ge=1, le=12)` dla euron. Fail-fast przy ingestion. |
| CLI | **Typer** | 0.12.x | Type-hinted, `--resume` flag dla checkpointed runs |
| Static viz (paper) | **matplotlib** | 3.9.x | Publikowalne, deterministyczne. Animation export via FuncAnimation + ffmpeg → `.webm`. |
| Interactive viz | **Plotly** (static HTML) | latest | Embed w Quarto report. Streamlit **demoted** do Tier-2 (W9+ stretch). |
| Report | **Quarto** | 1.5+ | Reproducible markdown→HTML/PDF. Fallback: `jupyter nbconvert` (zob. §6.4). |
| Testing | **pytest** + `hypothesis` | latest | `pytest.approx(rel=0.05, abs=1e-3)` dla stochastycznych testów. Property-based dla shuffle invariants, MMD symmetry, FDR monotonicity. |
| Code quality | **ruff** + **mypy --strict** | latest | mypy strict dla `methodology/` |
| Package layout | **`pyproject.toml`** + `src/driftscope/` | PEP 621 | `pip install driftscope` |

**§3-alt — odrzucone alternatywy (explicit):**
- **mapie / conformal p-values jako filar** — usunięte (kategoryczny błąd, zob. wyżej).
- **JAX dla MMD vectorization** — F12 risk na Win11, ROI marginalny przy N≤500.
- **R hybrid, Julia, Rust PyO3** — onboarding > budget, recruiter signal niejednoznaczny. Re-evaluation Rust PyO3 w W5 jeśli Numba niewystarczająca (bookmark).
- **DVC** — overhead > benefit dla <2GB; SQLite binary blob anti-pattern.
- **SQLite jako primary permutation cache** — N writers + WAL → `database is locked`.

---

## 4. Architektura

### 4.1 Struktura katalogów

```
driftscope/
├── pyproject.toml
├── README.md                   # public-facing, 3-sentence disarmer first
├── PROJECT_BRIEF.md            # ten plik
├── .env.example                # NO LOTTO_API_KEY (scraper-based)
├── data/
│   └── seed/
│       └── eurojackpot_history.csv  # cached fallback, committed
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
│   │   ├── config.py           # Pydantic Settings
│   │   ├── types.py            # DrawRecord (Pydantic), RegimeSpec, TestResult
│   │   ├── seeds.py            # make_worker_seeds(base, n) → list[SeedSequence]
│   │   └── guards.py           # @with_timeout, assert_memory_below (~40 LOC)
│   ├── ingestion/
│   │   ├── lotto_scraper.py    # httpx + selectolax, eurojackpot.org
│   │   └── regime_split.py     # 2014/2022 split logic
│   ├── methodology/
│   │   ├── preregistration.md  # frozen choices + generative model spec
│   │   ├── h1_classical.py     # ADF, KPSS, Bayesian online CP, Welch, ACF
│   │   ├── k4_mmd.py           # Gaussian RBF on frequency vectors
│   │   ├── permutation.py      # Numba-jit hot loop (selektywnie), shuffle test
│   │   ├── block_bootstrap.py  # alternative null (was missing v1.0)
│   │   ├── multiple_testing.py # BH FDR + Storey q-values, FAMILY-AWARE
│   │   └── specification.py    # spec curve: window ∈ {100,200,400} × bw ∈ {0.5,1,2}×median
│   ├── driftsim/
│   │   ├── planted_signals.py  # 5 signals concretely defined (zob. §5 Krok 5)
│   │   ├── null_uniform.py     # honest null generator
│   │   └── calibration.py      # sensitivity/specificity curves
│   ├── db/
│   │   ├── schema.sql          # regime_meta, calibration_runs (małe tabele)
│   │   ├── schema_validation.py# Pydantic models per tabela
│   │   └── queries.py          # safe_insert(table, model) + query funcs
│   ├── reporting/
│   │   ├── plots_static.py     # matplotlib (paper + .webm export)
│   │   ├── plots_interactive.py# Plotly (HTML embedded w Quarto)
│   │   ├── disagreement.py     # detector disagreement protocol (was missing v1.0)
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
│   └── test_disagreement.py
├── artifacts/                  # git-lfs tracked
│   ├── raw_draws.parquet
│   ├── regime_{1,2,3}.parquet
│   ├── permutations/{test}/{regime}/worker_{id}.parquet  # sharded
│   ├── regime_meta.sqlite
│   ├── driftsim_runs/
│   ├── calibration_curves/
│   └── artifacts_manifest.json # SHA-256 manifest
├── notebooks/                  # exploratory, NIE part of pipeline
└── demo/                       # Streamlit app (W9+ stretch)
    └── app.py
```

### 4.2 Moduły — graf zależności (DAG, db jako sink)

```
ingestion ──► core.types ──► methodology ──► reporting
                  ▲              │              ▲
                  │              ▼              │
              driftsim ────────► db (sink) ─────┘
                  │
                  ▼
              adaptive (only-if DoD-1..5 pass)
```

**Single direction.** `methodology/` nie wie nic o ingestion ani reportingu — pure functions na `DrawRecord` sequences. `db/` jest **terminalnym sinkiem** (append-only) — nie pośredniczy w pipeline'ie, tylko persistuje wyniki dla `reporting/`.

### 4.3 Przepływ danych (end-to-end)

```
eurojackpot.org archive (scraper) → ingestion/lotto_scraper.py
       │  (fallback: data/seed/eurojackpot_history.csv)
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

**Krok 0 — Data acquisition + power preview** (`scripts/manual_import.py`, `notebooks/00_power_preview.ipynb`)
Cached CSV jako primary; scraper jako live update. Analytic power preview via `statsmodels.stats.power.GofChisquarePower` dla effect sizes {0.01, 0.05, 0.10} przy n=1500. **Mandatory przed W1** — informuje czy DriftSim ma w ogóle szansę detect.

**Krok 1 — Ingestion** (`ingestion/lotto_scraper.py`)
Pull z eurojackpot.org archive page. Cache do `raw_draws.parquet`. Retry z exponential backoff. **Validation:** `DrawRecord` Pydantic model, fail-fast przy malformed data. Cadence: manual + wtorek/piątek wieczorem.

**Krok 2 — Regime split** (`ingestion/regime_split.py`)
Trzy parquet'y per reżim reguł: pre-2014-10-08, 2014-10-08→2022-03-25, post-2022-03-25.

**Krok 3 — H1 Classical Baseline** (`methodology/h1_classical.py`)
Minimum sufficient subset:
- **ADF** — H₀: unit root (non-stationarity)
- **KPSS** — H₀: trend stationarity (**przeciwna H₀ niż ADF, NIE redundantne — restored v2.0**)
- **Bayesian online CP** (Adams-MacKay 2007, own impl) — model: Dirichlet-Multinomial conjugate (zob. `preregistration.md`)
- **Welch periodogram** + **Lomb-Scargle**
- **Autocorrelation + PACF**

CUSUM zachowane jako classical backup do Bayesian CP (cross-check via `ruptures` PELT).

**Krok 4 — K4-MMD Kernel Two-Sample Test** (`methodology/k4_mmd.py`)
**Input space:** frequency vector p ∈ Δ⁴⁹ per sliding window N=200, NIE raw draws. RBF kernel z bandwidth = median heuristic obliczanej **wyłącznie na training window** (anti-leakage, fix v2.0). Pre-registered w `preregistration_v1.md` przed Tygodniem 5. Asymptotic theory via Gretton et al. 2012 — ⚠️ stability przy N=200 UNVERIFIED, empirical calibration vs shuffled null w W4 PoC.

**Krok 5 — DriftSim Calibration** (`driftsim/`)

**Concrete 5 planted signals (was missing v1.0):**
1. **Frequency shift** — pojedyncza liczba ma p = 0.10 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}
2. **Autocorrelation lag-1** — `P(x_t = k | x_{t-1} = k) = (1/50) + ρ`, ρ ∈ {0.05, 0.10, 0.15}
3. **Linear trend** — `p_k(t) = p_k + β·t/T`, β kalibrowane dla effect size matching
4. **Weekly seasonality** — różne p dla wtorek vs piątek (cycle period = 2 draws)
5. **Pair correlation** — liczby `i, j` współwystępują częściej, lift = {1.1, 1.2, 1.5}

5 patterns × 4 effect sizes = **20 calibration scenarios per test per regime**. 1 no-planted (uniform null) scenario per regime. Output: sensitivity/specificity curves per test, jako `.parquet` + `.html`. **Mandatory:** żaden test nie raportuje p-value na real data bez własnej kalibracji.

**Krok 6 — Permutation testing** (`methodology/permutation.py`)
- **Shuffle test core (DoD-2):** permutacje porządku losowań, 10⁴ permutacji per test per kernel config per regime.
- ~~Within-draw permutations~~ — **USUNIĘTE (v2.0).** Operacja tożsamościowa dla analizy częstości (sampling without replacement → order doesn't matter dla frequency vector).
- **Block bootstrap** (`methodology/block_bootstrap.py`) — alternative null zachowujący krótkozasięgowe korelacje, jako sanity check.
- Wzorzec: `@njit(cache=True)` wewnętrzny loop (selektywnie, gdzie profile >2×); `joblib.Parallel` **nad konfigami** `(test, regime, kernel_config, seed_offset)`, **NIGDY nad pojedynczymi permutacjami** (PoC W12 Wariant B udowodnił anti-pattern). Output: parquet shards per worker.
- **Seedy:** `core.seeds.make_worker_seeds(base_seed, n_workers)` zwraca `list[SeedSequence]`; każdy worker spawnuje własny `np.random.default_rng(seed_seq)` — gwarancja non-correlated streams (fix v2.0).

**Krok 7 — Multiple testing correction** (`methodology/multiple_testing.py`)
**Family-aware FDR (fix v2.0):**
- **Family A (global time-series tests):** 4 testy (ADF, KPSS, Bayesian CP, Welch) × 3 regimes = **12 hipotez**. BH FDR primary.
- **Family B (per-number goodness-of-fit):** 50 numbers × 2 testy (chi-squared, exact binomial) × 3 regimes = **300 hipotez**. BH FDR osobno.
- Storey q-values jako secondary cross-check w Family A (mała n) — przy Family B Storey może być niestabilne, więc tylko BH.

**Krok 8 — Specification curve** (`methodology/specification.py`)
~~Conformal p-values~~ — **usunięte (v2.0)** (mapie kategoryczny błąd).
**Ograniczona spec curve:** 2 parametry × 3 wartości każdy:
- window size N ∈ {100, 200, 400}
- bandwidth ∈ {0.5×, 1×, 2×} median heuristic

→ 9-point spec curve per signal. Jeśli wynik znika przy minor specification change → unstable, nie raportowane.

**Krok 9 — Reporting** (`reporting/`)
Quarto report z embedded Python chunks. Plotly figury → HTML embedded; matplotlib → PDF appendix + `.webm` hook export. Negative result framing first-class.

**Krok 9.1 — Disagreement Protocol** (`reporting/disagreement.py`, **nowy v2.0**)
Jeśli filar X detect, filar Y nie:
- **2/3 zgodność** → "convergent signal", raportowane jako primary finding.
- **1/3 zgodność** → "single-pillar signal, requires DriftSim power context" — raportowane z explicit warning + power curve z DriftSim.
- **0/3** → no signal section.

DoD-4 ("≥2/3 filarów") teraz operacyjnie zdefiniowane.

**Krok 10 — Adaptive watchlist** (`adaptive/`, opcjonalny, self-value <20% scope)
Wykonuje się TYLKO jeśli ≥1 wzorzec przeszedł DoD-1..5 z FDR<0.05. W przeciwnym razie returns `None` z explicit message.

---

## 6. Compute Execution Policy

### 6.1 Resource budget per etap (zaktualizowane z PoC)

| Etap | RAM peak | Disk | CPU time (12C/16T) | Notes |
|---|---|---|---|---|
| Ingestion | <100 MB | <5 MB | <30 s | Scraper rate-limited |
| Regime split | <200 MB | <10 MB | <5 s | Polars lazy |
| H1 single run | <500 MB | — | 1–10 s | Per regime per test |
| MMD single config | <800 MB | — | 5–60 s | Kernel matrix 500×500 max |
| **Simple permutation test (ADF, chi², 10⁴ perms)** | <500 MB | 1–5 MB shard | **<10 s** | PoC potwierdzone (Numba seq: 0.23s/1k → ~2.3s/10k) |
| **MMD permutation test (10⁴ perms, O(N²) kernel)** | <2 GB | 5–20 MB shard | **1–15 min** | Numba JIT na hot loop daje tu największy zysk |
| **Full pipeline overnight** | <4 GB | 200–500 MB | **2–6 h** (było 6–18) | Realistyczna estymacja po PoC; checkpointing via shards |
| DriftSim full sweep | <3 GB | 100–300 MB | **3–8 h** | 20 scenarios × 3 regimes |
| Quarto render | <1 GB | <50 MB | <5 min | — |

**VRAM budget:** N/A — pipeline CPU-only.
**Total disk budget:** ~1.5–2 GB. git-lfs handles, no remote config required for MVP.

### 6.2 CPU Transcendence Stack (aplikowane Osie z HARDWARE_PUSH_CATALOG)

| Oś | Technika | Lib | Impact | Status |
|---|---|---|---|---|
| **Oś 3 — Compilation** | Numba JIT selektywnie (MMD hot loop, BCPD inner) | `numba` 0.65.x | **2.7× simple, 10-30× MMD** (PoC + estimate) | ✓ Win11 verified (PoC 2026-05-17) |
| **Oś 0 — Environment** | Pre-flight `test_environment.py` na Win11 + numpy 2.x | pytest | Fail-fast | ✓ |
| **Parallelism** | Process pool **nad konfigami** (test, regime, kernel, seed_offset) — NIGDY nad permami | `joblib.Parallel(backend='loky')` | ~10–12× na 12 cores | ✓ Win11-safe |
| **Caching** | Parquet shards per worker → Polars LazyFrame reduce | `pyarrow` + `polars` | Re-run skip = ∞× (--resume flag) | ✓ |
| **Algorithmic** | Importance sampling permutations dla rzadkich p-values | own impl | 2–5× przy długim tail | ⚠️ tylko jeśli baseline >6 h |
| **Algorithmic** | Analytic null (asymptotic χ²) jako sanity check vs permutation | scipy.stats | — | ✓ — *cross-check, NIE zastępstwo* |
| **Vectorization** | Polars group-by zamiast pandas apply | `polars` 1.x | 5–30× na cleanup | ✓ |
| **I/O** | Parquet + zstd | `pyarrow` | 5–10× faster read | ✓ |
| **Build-time cloud** | Colab/Kaggle dla independent cross-environment re-run | Colab/Kaggle | Reproducibility signal, NIE speedup | ⚠️ optional |

### 6.3 Build-time tasks

| Zadanie | Gdzie | Output | Fallback |
|---|---|---|---|
| DriftSim full calibration sweep | Lokalnie overnight | `artifacts/driftsim_runs/*.parquet` | Kaggle CPU 30h/tydzień |
| 10⁴ permutation final run | Lokalnie overnight, raz przed milestone | parquet shards | Colab CPU independent re-run |
| Specification curve sweep (9 points) | Lokalnie | `artifacts/specification_curves.parquet` | — |
| Quarto report render | Lokalnie (lub GitHub Actions docelowo) | `docs/report.html`, `docs/report.pdf` | `jupyter nbconvert` |
| Static demo (Plotly HTML) | Lokalnie → GitHub Pages | `docs/report.html` | — |
| HF Spaces demo (Streamlit, **W9+ stretch**) | GitHub Action → HF Hub | Streamlit app | — |

### 6.4 Runtime fallbacki kaskadowe

1. **Permutation engine speed:**
   - A: Numba JIT + joblib nad konfigami (default)
   - B: pure NumPy + joblib nad konfigami (jeśli Numba broken — `test_environment.py`)
   - C: scipy.stats analytic approximation z explicit "approximate p-value, dependence-untested" flag w raporcie

2. **Storage permutation results:**
   - A: Parquet shards per worker (default, v2.0)
   - B: JSONL append-only per worker (debugging)
   - ~~SQLite~~ — usunięte z fallbacków (N writers anti-pattern)

3. **Long pipeline interruption:**
   - **A:** `cli.run --resume` skips configs with existing shards (default v2.0)
   - **B:** Manual restart from last shard timestamp

4. **Data source availability:**
   - A: Live scraper z eurojackpot.org (tenacity retry 5×, exponential backoff)
   - B: `data/seed/eurojackpot_history.csv` (committed, manually maintained)
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

| Para technik | Kompatybilność | Notes |
|---|---|---|
| Numba JIT × joblib.Parallel (nad konfigami) | ✓ | PoC verified 2026-05-17 (Wariant C); `@njit(cache=True)` picklable wrapper |
| Numba JIT × Polars | ✓ | Konwersja via `.to_numpy()` przed JIT hot path |
| Parquet shards × joblib parallel writes | ✓ | Każdy worker pisze do własnego pliku — zero contention |
| SQLite × append-only single-writer (regime_meta) | ✓ | Tylko CLI main process pisze; tabela mała |
| git-lfs × parquet | ✓ | LFS handles binary; deterministic via sorted ORDER BY content hash |
| Pydantic Settings × `.env` | ✓ | Permanent pattern |
| Quarto × Polars | ✓ | Python chunks via jupyter kernel |
| `matplotlib.animation` × ffmpeg → .webm | ✓ | Standard pipeline; VP9 codec for GitHub `<video>` rendering |

**Brak znanych konfliktów krytycznych po v2.0 fix-up.** Numba 0.65.x na Win11 PoC verified — R8 zmniejszone z L do Very Low.

---

## 7. Roadmap: MVP → Portfolio-ready → Open-source-ready

### 7.1 Week-by-week (zaktualizowane v2.0)

| Tydzień | Cel | Deliverable | DoD spełnione |
|---|---|---|---|
| **W0** (8h, nowy v2.0) | Data + power preview | Cached CSV committed; scraper PoC; analytic power preview notebook | — |
| **W1** (30h) | Environment + H1 core + DoD-1 | `test_environment.py` green; ADF + KPSS + Bayesian CP detect 2014/2022 blind; skeleton committed | DoD-1a, DoD-1b |
| **W2** (32h) | DriftSim part I | 5 planted signal generators (concrete defs from §5 Krok 5) × 4 effect sizes; uniform null; unit tests | — |
| **W3** (32h) | DriftSim part II — calibration | Sensitivity/specificity curves per H1 test per regime; first artifacts under git-lfs | DoD-5 (foundation) |
| **W4** (24h) | K4-MMD core | MMD impl on frequency vectors; pre-registered choices; **PoC: asymptotic stability at N=200 vs shuffled null** | DoD-4 (foundation) |
| **W5 — DECISION GATE** (16h) | Triangulation check | H1 + MMD detect planted signals z power >70%? **TAK** → W6. **NIE** → Plan B (§7.3) | DoD-3 |
| **W6** (24h) | Rigor layer | Family-aware FDR (Family A: 12 hyp, Family B: 300 hyp); spec curve (9 points); Storey sanity | DoD-2 (full) |
| **W7** (24h) | Reporting + adaptive + disagreement protocol | Quarto draft; disagreement.py; watchlist module; README disarmer | DoD-6 |
| **W8** (20h) | Polish MVP | Final README; static plots; `.webm` hook export; static `docs/report.html` na GitHub Pages | MVP complete |
| **W9** (16h) | Portfolio polish | Recruiter executive summary (1 page PDF); spec curve sweep documented; (stretch: Streamlit demo) | Portfolio-ready |
| **W10** (20h, optional) | Open-source readiness | CI/CD (GitHub Actions); CONTRIBUTING.md; pyproject installable; semver v0.1.0 | OS-ready |

### 7.2 Negative Result Presentation Plan (nowe v2.0)

Jeśli żaden detektor nie znajduje sygnału przy FDR<0.05, raport zawiera explicit sekcję **"Power Analysis & Detection Limits"**:
- Plot: power vs effect size z DriftSim, per test, per regime.
- Tabela: "minimum detectable effect size at 80% power" per test.
- Conclusion: "n=1500 jest insufficient dla effect sizes <X" — to JEST publishable wynik.

Negative result NIE jest porażką projektu — jest *rigor signal* przy explicit framing.

### 7.3 Plan B (Tydzień 5 fail)

Z SWOT TOP 1: jeśli H1 + MMD nie wykrywają planted signals → projekt staje się "framework for measuring detector hallucination rates in supposedly memoryless processes". Framing z §1 ("calibrated detector hallucination rates") jest *kompatybilny* z Plan B — ta sama narracja, bez positive result section. README disarmer niezmieniony.

---

## 8. Risk Register + Mitigation (v2.0)

| # | Ryzyko | Typ | Prawd. | Impact | Mitygacja | Trigger detekcji |
|---|---|---|---|---|---|---|
| R1 | Hallucination (detektor "znajduje" sygnał, którego nie ma) | Methodological | M | **CRITICAL** | Shuffle test obligatory + family-aware FDR + spec curve + DriftSim + 3-panel hook (uniform RNG control) | p-value <0.05 na real ALE także na ≥1 shuffled fold |
| R2 | Statistical power <30% dla subtle signals przy n=1500 | Methodological | H | M | W0 power preview; explicit power analysis; Negative Result Presentation Plan | Power curve from W0 + DriftSim |
| R3 | Specification curve overfitting | Methodological | L | M | Pre-registered space (`preregistration_v{N}.md`); ograniczone 9 points | Diff preregistration z final config |
| R4 | "Lotto-scam" first impression u recruitera | Portfolio | M | H | 3-sentence disarmer; methodological framing; no emojis; 3-panel hook z uniform control | Recruiter feedback post-launch |
| R5 | "Stack za prosty" | Portfolio | M | M | Spec curve + DriftSim + Numba/Polars + family-aware FDR | Self-assessment W8 |
| R6 | 8-10 tyg overrun | Scope | H | M | DriftSim (W2-3) fixed time-box; Plan B safe landing; W10 opcjonalne | Behind schedule W3 lub W5 |
| R7 | DriftSim calibration sweep > overnight | Scope/compute | M | M | Numba JIT W1 sanity; checkpointing via shards; Colab CPU backup | Single config >30 min w W2 |
| R8 | Numba on Win11 issues | Środowisko | **Very Low** (was L) | H | PoC verified 2026-05-17; fallback do pure NumPy | `import numba` fails |
| R9 | Bayesian online CP own impl buggy | Methodological | M | M | Dirichlet-Multinomial spec w preregistration; property-based tests; cross-check vs ruptures PELT | Disagreement >10% z PELT |
| R10 | Gambling addiction ethical concern | Etyczne | L | H | README disclaim §1; no "predict your numbers" framing; honest-None return | — |
| R11 | Scraper ToS violation lub site change | Legal/Tech | M (was L) | M | ToS review w W0; cached CSV jako Tier-1 fallback; manual CSV upload Tier-2 | Scraper fail or ToS change |
| ~~R12~~ | ~~DVC complexity~~ | ~~Scope~~ | — | — | **USUNIĘTE (v2.0)** — DVC wykreślone z stack | — |
| **R13** (nowe) | MMD asymptotic instability at N=200 | Methodological | M | M | W4 PoC: empirical calibration vs shuffled null PRZED W5 Decision Gate | False positive rate >10% w shuffled |
| **R14** (nowe) | SQLite hash binary nondeterminism (fixed) | Reproducibility | — | — | **FIXED (v2.0)** — hash CSV z sorted ORDER BY content, nie binarki | — |

---

## 9. Szacunki czasowe per faza (v2.0)

| Faza | Min | Realistyczne | Max | Notes |
|---|---|---|---|---|
| **W0 — Data + power preview (nowy)** | 6 h | 8 h | 12 h | Cached CSV + scraper PoC + power notebook |
| W1 — Env + H1 core + DoD-1 | 20 h | **30 h** (było 24) | 40 h | +KPSS, +DrawRecord validation, scaffolding 15+ modułów |
| W2 — DriftSim part I | 24 h | **32 h** (było 28) | 44 h | Concrete 5 signals nontrivial |
| W3 — DriftSim calibration | 24 h | **32 h** (było 28) | 44 h | |
| W4 — K4-MMD core + N=200 PoC | 16 h | **24 h** (było 20) | 32 h | +empirical asymptotic check |
| W5 — Decision Gate + iteration | 12 h | 16 h | 24 h | |
| W6 — Rigor layer | 16 h | **24 h** (było 28) | 32 h | Mniejszy scope (no mapie, ograniczona spec curve) |
| W7 — Reporting + adaptive + disagreement | 18 h | **24 h** | 32 h | +disagreement.py |
| W8 — Polish MVP | 12 h | **20 h** | 28 h | |
| **TOTAL MVP (W0–W8)** | **148 h** | **210 h** (było 188) | **288 h** | Realistic mid-range |
| W9 — Portfolio polish | 12 h | 16 h | 24 h | HF Spaces (stretch) |
| W10 — OS readiness (opcjonalne) | 12 h | 20 h | 28 h | CI/CD + contribution guide |
| **TOTAL 10-week** | **172 h** | **246 h** (było 224) | **340 h** | |

---

## 10. DoD Mapping (v2.0)

| DoD | Komponent walidujący | Pass criterion |
|---|---|---|
| DoD-1a — Sanity check (euronumbers) | H1 stationarity tests | Detekcja zmian puli euronumerów 2014/2022 |
| DoD-1b — Blind change-point detection | Bayesian online CP + CUSUM | Top-2 ranked change-points pokrywają się z 2014-10-08 i 2022-03-25 (±30 dni) **przed** ręcznym sprawdzeniem |
| DoD-2 — Shuffle test rigor | `methodology/permutation.py` | False-positive rate w shuffled data ≤ α=0.05 ± Monte Carlo error |
| DoD-3 — Multiple testing correction | `methodology/multiple_testing.py` | **Family-aware:** BH FDR w Family A (12 hyp) i Family B (300 hyp) osobno |
| DoD-4 — Complementary pillars (was "triangulation") | H1 + MMD + DriftSim | Każdy reported signal classified per **Disagreement Protocol** (§5 Krok 9.1): convergent / single-pillar / null |
| DoD-5 — Honest predictor (kalibracja) | `driftsim/calibration.py` | Adaptive watchlist generuje output IFF passed DoD-1..4; w przeciwnym razie None |
| DoD-6 — Reproducibility | `core/seeds.py` + git-lfs + GitHub Action | **Cold-machine re-run produces bit-identical hash z `ORDER BY (test, regime, seed)` eksportu CSV** (NIE binarki SQLite) z committed seeds |

---

## 11. Open Questions z SEED_IDEA — resolution

| Pytanie SEED_IDEA | Status | Resolution |
|---|---|---|
| §7A.1 — DoD-1 blind protocol sufficient? | **RESOLVED** | Ranking change-pointów *przed* porównaniem z 2014/2022 |
| §7A.2 — Paradygmat redefinujący target | **DEFERRED** to W10+ stretch | TDA jako post-MVP |
| §7B.5 — Hardware Transcendence? | **PARTIALLY RESOLVED** | Oś 0 + Oś 3 (Numba) aplikują; reszta nie |
| §7C.6 — Statistical power przy n=1500 | **RESOLVED** | W0 power preview + DriftSim curves; Negative Result Presentation Plan |
| §7C.7 — Update cadence per komponent | **RESOLVED** | Online auditor per-draw; H1 per-draw 1-10s; MMD weekly; DriftSim once + per milestone |
| §7C.8 — Honest augmentation | **PARTIALLY RESOLVED** | Within-draw permutations USUNIĘTE (v2.0). Block bootstrap jako alternative null. |
| §7D.9–10 — Framing scam-disarm | **RESOLVED + STRENGTHENED** | 3-sentence disarmer + 3-panel hook z uniform RNG control |
| §7E.11 — Blind-spot question | **ADDRESSED** | Negative Result Presentation Plan jako first-class deliverable |

---

## 12. Anti-goals guard (final v2.0)

- ☑ **Nie naive frequency** — H1 minimum sufficient: ADF + **KPSS** + Bayesian CP + Welch + ACF, każdy z permutation-based istotnością.
- ☑ **Nie hallucinated signal** — DoD-2 (shuffle test) obligatory; family-aware FDR; spec curve mandatory; DriftSim power context; disagreement protocol; uniform RNG control panel w hook.
- ☑ **Nie wrapper na cudzy model** — własna implementacja Bayesian CP (Dirichlet-Multinomial), własny MMD (~80 LOC), własny DriftSim.
- ☑ **Nie "gwarantowana wygrana"** — README §1 explicit disclaim; adaptive module honest-None; framing methodological.
- ☑ **Nie pivot z premise** — DECISION_PROMPT §5B respektowane (NIE zamieniam EuroJackpot na NIST jako primary case mimo sugestii LLM).
- ☑ **Nie ograniczenie do Pythona z definicji** — R/Julia/Rust rozważone i odrzucone z explicit uzasadnieniem (§3-alt).

---

## PoC Results — Krok 6 (2026-05-17, niezmienione w v2.0)

[Zachowane bez zmian — PoC zweryfikował: Numba 0.65.1 + numpy 2.x na Win11 OK; joblib per-perm = anti-pattern; joblib nad konfigami + Numba inner loop = 2.7× simple, oczekiwane 10-30× MMD.]

**Decyzja (§6D WORKFLOW):** ✅ Wariant C działa, pipeline w overnight limicie.

---

## Appendix A — Transparency Table (v1.0 → v2.0)

| # | Zmiana | Sekcja briefu | Źródło zarzutu | Uzasadnienie |
|---|---|---|---|---|
| A1 | Usunięty `mapie` + cały filar conformal p-values | §3 Stack, §5 Krok 8 | Gemini, **Kimi**, Qwen (3 LLM) | Kategoryczny błąd: mapie do conformal *prediction* (intervals/sets), nie hipotez stacjonarności. Filar wykreślony z MVP. |
| B1 | Hook: Plotly autoplay → `matplotlib.animation` → `.webm` via ffmpeg | §2 | **5/5 LLM-ów** | GitHub blokuje iframe Plotly autoplay; `.webm` w `<video>` renderuje natywnie. ~2-5 MB vs 50-100 MB GIF. |
| B2 | Hook: 2 panele → 3 panele (+uniform RNG control) | §2 | DeepSeek | Wzmocnienie "visceral proof of non-hallucination" — real → detect, uniform → null, shuffled → null. |
| C1 | SQLite primary cache → Parquet shards per worker | §3 Stack, §4.1, §4.3, §6.2, §6.3, §6.5 | Gemini, Kimi, DeepSeek | SQLite WAL = 1 writer / N readers; joblib N workers → `database is locked`. Parquet shards = zero contention + naturalny checkpointing. |
| C2 | DVC usunięte → `git lfs` + `scripts/archive.py` (SHA-256 manifest) | §3 Stack, §4.1, §8 (R12 dropped) | **5/5 LLM-ów** | DVC overhead nieproporcjonalny dla <2GB; brief sam przyznawał problem DVC+SQLite. |
| C3 | DoD-6 hash binarki SQLite → hash `ORDER BY` eksport CSV | §10 DoD-6, §8 R14 | Kimi | SQLite binary nondeterministic (auto_vacuum, freelist). Hash logicznej zawartości jest deterministic. |
| D1 | "10-50× Numba speedup" → realistic split (2.7× simple, 10-30× MMD) | §3 Stack, §6.2 | DeepSeek, GPT | PoC pokazał 2.71× dla shuffle+chi². 10-50× to typowe dla O(N²), nie O(N). |
| D2 | Numba 0.59.x → 0.65.x pin | §3 Stack | DeepSeek, Qwen | numpy 2.x wymaga numba≥0.60; PoC potwierdzone 2026-05-17. |
| D3 | §6.2 Parallelism: poprawiony wzorzec "nad konfigami, NIE nad permami" | §6.2 | Kimi | §6.2 wciąż promowało anti-pattern udowodniony w PoC Wariant B (16× wolniej). |
| D4 | §6.1 Resource budget: realistyczne timing po PoC | §6.1 | DeepSeek, Kimi | "5-30 min per config" było ~rząd wielkości za dużo dla prostych testów. |
| D5 | Numba selektywnie (per-function profile), nie globalnie | §3 Stack | DeepSeek | Dla prostych testów zysk 0.4s nie wart ryzyka kompatybilności. Numba ma sens dla MMD O(N²). |
| E1 | KPSS przywrócone obok ADF | §3 Stack, §5 Krok 3 | Qwen | ADF H₀: unit root; KPSS H₀: trend stationarity — komplementarne, NIE redundantne. 3 LOC, zysk diagnostyczny. |
| E2 | "600 hipotez" → Family A (12 global) + Family B (300 per-number), FDR osobno | §5 Krok 7, §10 DoD-3 | Kimi | ADF/CP testują strumień jako całość; chi² per-number to inna rodzina. Mieszanie FDR błędne. |
| E3 | Within-draw permutations usunięte | §5 Krok 6, §11 §7C.8 | Kimi | Sampling without replacement → kolejność wewnątrz draw nie wpływa na frequency vector. Operacja tożsamościowa. |
| E4 | MMD input space explicit: frequency vectors per window | §3 Stack, §5 Krok 4 | Kimi | Klaryfikacja: NIE RBF na raw lotto numbers (kategoryczne), tylko na p ∈ Δ⁴⁹. |
| E5 | "Triangulation" → "Complementary pillars" + Disagreement Protocol | §1, §5 Krok 9.1, §10 DoD-4 | Kimi | H1/MMD/DriftSim mierzą różne aspekty — komplementarne, nie redundantne. Disagreement Protocol operacjonalizuje DoD-4. |
| E6 | MMD bandwidth z training window only (anti-leakage) | §5 Krok 4 | Gemini | Median heuristic z całego okresu = future leakage w streaming setting. |
| E7 | BCPD generative model spec dodany do preregistration | §3 Stack, §5 Krok 3 | Kimi | Adams-MacKay 2007 wymaga `p(x_t\|θ)`. Wybór: Dirichlet-Multinomial conjugate. |
| F1 | `core/seeds.py`: `make_worker_seeds()` zwraca `list[SeedSequence]` | §4.1, §5 Krok 6 | Gemini, Qwen | Fork-correlated streams bez SeedSequence = fałszywe null distribution. Krytyczne dla rigor. |
| F2 | `DrawRecord` jako Pydantic model z `Field(ge=..., le=...)` | §3 Stack, §4.1, §5 Krok 1 | Qwen | Fail-fast vs silent NaN przy malformed scraper response. |
| F3 | `--resume` flag w CLI; parquet shards = naturalny checkpointing | §3 Stack, §6.4 | DeepSeek | 6h pipeline bez resume = utrata pracy przy awarii. |
| F4 | `pytest.approx(rel=0.05, abs=1e-3)` w conftest.py | §3 Stack, §4.1 | Qwen | Stochastyczne testy wymagają tolerance; pytest default exact match = flaky CI. |
| F5 | `core/guards.py` (~40 LOC: @with_timeout, assert_memory_below) | §4.1 | Qwen | Lekki monitor, NIE pełny psutil system. Hang prevention. |
| G1 | "Lotto OpenAPI" → scraper httpx+selectolax + cached CSV | §3 Stack, §4.1, §5 Krok 1 | DeepSeek, Kimi | EuroJackpot brak publicznego API z kluczem. Scraper + cached CSV bezpieczniejsze ToS-wise. |
| H3 | Streamlit demoted do W9+ stretch; primary demo = static HTML | §3 Stack, §7.1 | GPT, Kimi | Static `docs/report.html` na GitHub Pages = mniej maintenance, większa stabilność, brak HF Spaces timeout. |
| H5 | `db/schema_validation.py` + `safe_insert(table, model)` | §4.1 | Qwen | Walidacja schematu przy runtime; brak migration path przy raw SQL. |
| I2 | Storey: tylko Family A; spec curve ograniczone do 2 params × 3 wartości = 9 points | §5 Krok 7, §5 Krok 8 | GPT (modyfikacja) | Storey przy Family B (300 hyp, dużo nullów) niestabilne; spec curve full grid = combinatorial explosion. |
| J1-J4 | Time estimates revised: W1 24→30h, W2 28→32h, W3 28→32h, W4 20→24h, W6 28→24h, W7 24→24h, W8 20→20h | §9 | GPT, DeepSeek, Kimi, Qwen | Konsensus: optymistyczne o ~15-20%; balansowane mniejszym scope (no mapie). Total MVP: 188→210h. |
| J6 | W0 (8h) dodane przed W1 | §7.1 Krok 0, §9 | Kimi, GPT | Power preview + cached CSV mandatory przed scaffoldingiem (blocker dla DriftSim parametrization). |
| K1 | 5 planted signals konkretnie zdefiniowane | §5 Krok 5 | Kimi | "5 planted patterns × 4 effect sizes" bez listy = W2-W3 blocker. |
| K2 | Negative Result Presentation Plan jako section §7.2 | §7.2 (nowy) | GPT, Kimi | "If no signal, this is also a result" w README to za mało — recruiter wymaga concrete plan. |
| K3 | Detector Disagreement Protocol w `reporting/disagreement.py` | §5 Krok 9.1, §10 DoD-4 | GPT | Brak planu dla single-pillar / contradictory detectors. Operacjonalizuje DoD-4. |
| K4 | `methodology/block_bootstrap.py` dodany do struktury | §4.1 | Kimi | Wzmiankowane w pipeline (§5 Krok 6), brakowało w katalogach. |
| L1 | Graf §4.2 przerysowany: db jako sink (terminal node) | §4.2 | Qwen | Oryginalna notacja sugerowała dwukierunkowy przepływ przez db. |
| L2 | `preregistration_v{N}.md` versioning + `revision_reason` field | §5 Krok 4 | Qwen | Sztywna preregistracja blokuje korekcję po DriftSim. Versioning preserves rigor. |
| L3 | MMD asymptotic stability at N=200 → ⚠️ UNVERIFIED, W4 PoC | §3 Stack, §5 Krok 4, §7.1 W4, §8 R13 | GPT | Brief traktował to jako solved (Gretton 2012); finite-sample stability wymaga empirical check. |
| L4 | HARDWARE_PUSH_CATALOG: Oś 0 + Oś 3 aplikują (nie wszystko wyłączone) | §0, §6.2 | GPT, DeepSeek | Środowisko + JIT compilation aplikują na CPU; brief błędnie wyłączał całość. |

**Zarzuty ODRZUCONE (eksplicit):**

| Zarzut | Źródło | Powód odrzucenia |
|---|---|---|
| Polars overkill dla 1500 rekordów | Kimi | Permanent pattern Piotra; framework dla 10⁶+ stretch; recruiter signal "modern stack". |
| Pydantic + Typer = stack creep | Kimi | Permanent pattern z Piotra template (spójność cross-project). |
| Quarto external dependency | Kimi | Fallback B (jupyter nbconvert) już w §6.4; Quarto stabilny na Win11 per prior projects. |
| Lotto-scam vibe wymaga premise pivot | DeepSeek, Kimi | Premise pivot = anti-goal §5B SEED_IDEA. R4 mitigated by 3-panel hook + disarmer. |
| Incremental update dla nowych losowań | DeepSeek | Out of MVP scope (brief §5 Krok 1 explicit "manual + cron opcjonalny"). |
| Adaptive watchlist over-engineered | Gemini | Już oznaczone jako "opcjonalny, self-value <20% scope". |
| Conformal/Storey/spec curve = over-rigor | GPT | Target recruiter to quant/research, nie general — rigor IS signal. Częściowo zaadresowane (mapie usunięte, spec curve ograniczona, Storey demoted). |
| Numba+joblib pickle unverified | DeepSeek, Qwen, Kimi | PoC §12 Wariant C zweryfikował (530-43k perms/s mierzone). |
| W8-W10 = scope creep | Kimi | W10 już opcjonalne; W9 (demo + summary) krytyczne dla portfolio. |
| Stack technical depth recruiter perception | GPT | Quant/research recruiter rozróżnia BH vs Storey — to JEST positioning. |
| Specification curve = academic vanity | GPT | Standard w meta-research, pasuje do "methodological tooling" framing. Scope ograniczony zamiast usunięcia. |
| Change EuroJackpot → NIST jako primary case | DeepSeek, Kimi | Premise pivot (anti-goal §5B). EuroJackpot pozostaje flagship; NIST jako stretch §1. |

---

**Akceptacja:** ten brief jest *contract* — każda zmiana decyzji wymaga update commit'u z rationale. Drobne tactical changes (lib version bump w tym samym major) OK bez review; architectural changes wymagają explicit re-review.

**Handoff:** ten plik jest gotowy do przekazania Claude Code CLI jako root-level architectural contract. Pierwsze pytanie Code do tego brief'u powinno brzmieć: *"Czy rozpoczynamy od W0 (data scraper PoC + cached CSV + power preview), czy od W1 scaffolding `pyproject.toml`?"* — odpowiedź: **W0 pierwszy (8h, mandatory before W1 — data acquisition blocker)**.
