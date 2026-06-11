# PROJECT_BRIEF.md — DriftScope

> **Architectural contract.** Decyzje w tym dokumencie są *permanent patterns* — zmiana wymaga explicit re-review przed dotknięciem kodu.
>
> **Wersja:** v1.0 · **Status:** ready-for-handoff (Claude Code CLI) · **Tier:** MEDIUM · **Język brief'u:** PL/EN mix (zgodnie z konwencją Piotra)

---

## 0. Flagi i konwencje

- **Konflikt zaadresowany:** sekcja "Hardware Transcendence Stack" z generic szablonu jest pominięta zgodnie z `DECISION_PROMPT` §6.5. Zastąpiona **Compute Execution Policy** (§6 niżej) o identycznej strukturze, ale dla realnego bottleneck'u — CPU permutation overhead. `HARDWARE_PUSH_CATALOG.md` formalnie nie aplikuje (CPU-only, modele <100 MB RAM, brak ML neural).
- **Anti-goal guard:** każda decyzja niżej sprawdzona pod SEED_IDEA §5A.1–4 (no naive frequency, no hallucinated signal, no wrapper, no gambling-app framing) i §5B.1–4 (no premise pivot).
- **Permanent pattern (Piotr's template):** `pyproject.toml` jako single source of truth dependencies; `artifacts/` na root (nie `models/`); `@dataclass Config` per moduł dla standalone CLI; `db/queries.py` zamiast Repository pattern (solo dev); PowerShell 5.1 compatible (no `&&`); zmiany w istniejących plikach, nie patch-documenty.

---

## 1. Wizja i Elevator Pitch

**Elevator pitch (recruiter quant/research, 25 sek):**
DriftScope to research-grade audit framework dla detekcji niestacjonarności w strumieniach dyskretnych procesów *z założenia* uniform. Trzy niezależne filary (klasyczne testy + kernel two-sample test + syntetyczna kalibracja) triangulują wnioski; każde "found" musi przejść shuffle test, FDR correction i specification curve analysis, zanim wyląduje w raporcie. Flagship case study — EuroJackpot z dwoma znanymi change-pointami 2014/2022 jako ground truth — istnieje, żeby udowodnić, że detektor *w ogóle działa*, zanim oceniony zostanie jakikolwiek subtelniejszy wzorzec. Framework jest reusable: NIST RNG test data, kryptograficzne PRNG, financial random-walk hypotheses są naturalnymi targetami stretch.

**Sub-tagline (README, ≤15 słów):**
> *Stationarity audit framework for streaming discrete processes — with calibrated detector hallucination rates.*

**Recruiter category:** *Methodological tooling for hypothesis testing on streaming data.* NIE "ML prediction project".

## 2. 10-Second Hook

**Konkretna scena (≤10 sek):**
Użytkownik otwiera README/repo. Pierwszy element widoczny w viewport: **animowana "permutation race"** — dwie wertykalne osie obok siebie. Lewa: real EuroJackpot stream, oś czasu 2012→2026, czerwone markery na 2014-10-08 i 2022-03-25 (znane change-pointy). Prawa: shuffled version tego samego streamu. Pod spodem licznik p-value Bayesian online CP w real-time, jak detektor "konsumuje" datapoint po datapoint. Real stream zapala oba change-pointy z p<0.001; shuffled stream zostaje w noise. **15-sekundowa pętla, autoplay, no sound.**

**Główny "wow":** *visceral proof of non-hallucination*. W jednej animacji widać, że detektor *odpowiada na rzeczywistą strukturę*, a nie generuje sygnał. To jest "lotto-scam disarmer" w postaci wizualnej, nie tekstowej.

**Custom design system:** minimal. Color palette: 3 kolory (real = `#0EA5E9` blue, shuffled = `#94A3B8` slate, change-point marker = `#EF4444` red). Typography: JetBrains Mono dla wszystkich liczb/p-values, Inter dla narracji. **Brak ikon/emoji w README** (anti-scam signal). Logo: opcjonalne, scope-wise odrzucone z MVP.

**Biblioteka:** Plotly (`go.Scatter` + `frames` dla animacji) → eksport do `.html` embedowany w README przez `<details>` lub bezpośrednio jako GIF z `kaleido`. **NIE D3 custom, NIE Three.js** (SWOT K2 warning — solo dev frontend overrun risk).

**Pierwsze 3 zdania README (finalna wersja, do publikacji):**
> *DriftScope is a stationarity audit framework for streaming discrete-valued processes. The flagship case study is EuroJackpot — a process designed to be uniform-random, where the empirical question is whether any detectable deviation from uniformity exists. The project is methodological in nature; it neither claims nor seeks to predict lottery outcomes in any actionable sense.*

## 3. Stack technologiczny — z uzasadnieniem każdego wyboru

| Warstwa | Wybór | Wersja | Uzasadnienie |
|---|---|---|---|
| Język/runtime | **Python 3.10** | 3.10.x | Znany Piotrowi, dojrzały ekosystem stat (§4 SEED_IDEA). Polyglot odrzucony — patrz §3-alt niżej. |
| Stationarity tests | **statsmodels** | 0.14.x | ADF, KPSS, ACF/PACF — kanon klasyczny, peer-reviewed implementations |
| Change-point detection | **ruptures** | 1.1.9+ | CUSUM, Pelt, Binseg — najszerszy zestaw algorithmów CP w Pythonie |
| Bayesian online CP | **własna implementacja Adams-MacKay 2007** | — | Lib `bayesian_changepoint_detection` jest stale (last update 2018, no type hints, no tests). Własna ~150 LOC, peer-readable, testable. |
| Spectral analysis | **scipy.signal** | 1.13.x | Welch, Lomb-Scargle (dla nieregularnych grids) — standard |
| Kernel methods (MMD) | **scikit-learn** kernels + custom MMD | sklearn 1.4.x | `pairwise_kernels` jako primitive; MMD jako ~80 LOC custom z testami unit (Gretton et al. 2012 reference). PyTorch GPU acceleration **odrzucone** — N≤500, brak ROI. |
| Permutation engine | **Numba JIT** + `joblib.Parallel` | Numba 0.59.x | Hot kernel: index generation + statistic computation. 10–50× speedup vs pure NumPy. Onboarding +5 dni (akceptowalne — to dominujący compute cost projektu). **Rust/PyO3 odrzucone** — +2 tyg onboarding, ROI nie udowodniony przy n=1500. |
| Multiple testing | `statsmodels.stats.multitest` | 0.14.x | Benjamini-Hochberg FDR (primary), Storey q-values (secondary jako sanity) |
| Conformal inference | **mapie** | 0.8.x | Pure-Python, sklearn-compatible, Vovk-style conformal p-values |
| Data manipulation | **Polars** | 1.x | Type-safe, ~5–30× szybsze niż pandas dla group-by/window ops, recruiter signal "modern stack". Pandas zachowane tylko jako interop z pytest fixtures/legacy notebooks. |
| Data ingestion | `httpx` + `tenacity` (retry) | — | Sync (1 call/dzień), backoff exponential |
| Storage — raw/cleaned data | **Parquet** (`pyarrow`) | — | 1500 punktów × 3 reżimy — overkill dla SQLite jako primary store |
| Storage — permutation results | **SQLite** | stdlib | 10⁵–10⁶ rekordów z indeksami po `(test_name, regime, kernel_config, seed)` — natywny query path |
| Data versioning | **DVC** | 3.x | DriftSim runs i permutation cache to artifacts >10MB. DVC > git-LFS dla rigor signal. |
| Config | **Pydantic Settings** v2 + `.env` | 2.x | Per Piotr's template; `core/config.py` jako single config loader |
| CLI | **Typer** | 0.12.x | Type-hinted, auto-help, recruiter-friendly nad argparse |
| Static viz (paper) | **matplotlib** | 3.9.x | Publikowalne, deterministyczne |
| Interactive viz | **Plotly** + **Streamlit** | latest stable | Streamlit dla HF Spaces demo. **Gradio odrzucone** — gorsza kontrola layoutu dla calibration curves; **D3/Observable/Three.js odrzucone** (SWOT K2: solo dev overrun). |
| Report | **Quarto** | 1.5+ | Reproducible markdown→HTML/PDF. Embedded Python chunks. Recruiter-grade artifact. |
| Testing | **pytest** + `hypothesis` | latest | Property-based testing dla shuffle invariants, MMD symmetry, FDR monotonicity |
| Code quality | **ruff** + **mypy --strict** | latest | Single linter (ruff zastępuje flake8+isort+pyupgrade); mypy strict dla `methodology/` module |
| Package layout | **`pyproject.toml`** + `src/driftscope/` layout | PEP 621 | Single source of truth, installable as `pip install driftscope` |

**§3-alt — odrzucone alternatywy (explicit, żeby uniknąć drift'u w dev):**
- **JAX dla MMD vectorization:** odrzucone. F12-class risk na Win11 (DLL hell + jaxlib wheels niestabilne), ROI marginalny przy N≤500. SWOT explicit warning.
- **R hybrid (changepoint, kernlab):** odrzucone mimo metodologicznej dojrzałości. Polyglot setup mnoży env risk, recruiter signal niejednoznaczny (R = data analyst, nie ML engineer).
- **Julia:** odrzucone — recruiter signal "scientific computing depth", ale onboarding (Piotr: zero godzin Julia) zjada 2 tyg z 6–8 tyg budget'u.
- **Rust PyO3 permutation engine:** odrzucone *na MVP*. Re-evaluation po Tygodniu 5 (Decision Gate) jeśli Numba okaże się niewystarczająca. Bookmark, nie commitment.

## 4. Architektura

### 4.1 Struktura katalogów

```
driftscope/
├── pyproject.toml              # single source of truth deps
├── README.md                   # public-facing, 3-sentence disarmer first
├── PROJECT_BRIEF.md            # ten plik
├── .env.example                # LOTTO_API_KEY=...
├── dvc.yaml                    # DriftSim + permutation runs as DVC stages
├── src/driftscope/
│   ├── __init__.py
│   ├── cli.py                  # Typer entrypoint
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (paths, seeds, API key)
│   │   ├── types.py            # dataclasses: DrawRecord, RegimeSpec, TestResult
│   │   └── seeds.py            # global RNG management (reproducibility)
│   ├── ingestion/
│   │   ├── lotto_client.py     # httpx + tenacity wrapper na Lotto OpenAPI
│   │   └── regime_split.py     # 2014/2022 split logic
│   ├── methodology/
│   │   ├── preregistration.md  # frozen kernel/test choices BEFORE final runs
│   │   ├── h1_classical.py     # ADF, Bayesian online CP, Welch, ACF
│   │   ├── k4_mmd.py           # Gaussian RBF + polynomial MMD
│   │   ├── permutation.py      # Numba-jit shuffle test core
│   │   ├── multiple_testing.py # BH FDR + Storey q-values
│   │   ├── conformal.py        # mapie wrapper, Vovk conformal p-values
│   │   └── specification.py    # specification curve analysis (Simonsohn 2020)
│   ├── driftsim/
│   │   ├── planted_signals.py  # 5 wzorców × 4 effect sizes
│   │   ├── null_uniform.py     # honest null generator
│   │   └── calibration.py      # sensitivity/specificity curves
│   ├── db/
│   │   ├── schema.sql          # permutation_results, calibration_runs, regime_meta
│   │   └── queries.py          # query functions (NIE Repository class)
│   ├── reporting/
│   │   ├── plots_static.py     # matplotlib (paper-grade)
│   │   ├── plots_interactive.py# Plotly (demo-grade)
│   │   └── report.qmd          # Quarto source
│   └── adaptive/               # self-value (§6.2 SEED_IDEA, <20% scope)
│       └── honest_watchlist.py # generate ONLY when DoD-1..5 pass
├── tests/
│   ├── test_environment.py     # CI sanity — Numba on Win, Polars version, etc.
│   ├── test_h1_invariants.py   # property-based via hypothesis
│   ├── test_mmd_properties.py  # symmetry, positivity, kernel matrix shape
│   ├── test_permutation_null.py# shuffle distribution → uniform p-values
│   └── test_driftsim_calibration.py
├── artifacts/                  # DVC-tracked
│   ├── raw_draws.parquet
│   ├── regime_{1,2,3}.parquet
│   ├── permutation_cache.sqlite
│   ├── driftsim_runs/
│   └── calibration_curves/
├── notebooks/                  # exploratory, NIE part of pipeline
└── demo/                       # Streamlit app for HF Spaces
    └── app.py
```

### 4.2 Moduły — graf zależności

```
ingestion  →  core.types  ←  methodology
                ↓               ↓
              db (queries.py) ←─┤
                ↓               ↓
             reporting ← driftsim (calibration)
                ↓
             adaptive (only-if-passes DoD-1..5)
```

**Single direction.** `methodology/` nie wie nic o ingestion ani reportingu — pure functions na `DrawRecord` sequences. Testable in isolation.

### 4.3 Przepływ danych (end-to-end)

```
Lotto OpenAPI
   │  (httpx + tenacity, 1 call/dzień, manual trigger lub cron)
   ▼
ingestion/lotto_client.py  →  artifacts/raw_draws.parquet
   │
   ▼
regime_split.py  →  artifacts/regime_{1,2,3}.parquet
   │
   ├─→ methodology/h1_classical.py  ──┐
   ├─→ methodology/k4_mmd.py         ─┤→  db/queries.py  →  permutation_cache.sqlite
   └─→ driftsim/calibration.py        ─┘                       │
                                                                ▼
                                            multiple_testing.py + conformal.py + specification.py
                                                                │
                                                                ▼
                                                  reporting/{plots,report.qmd}
                                                                │
                                                                ▼
                                               adaptive/honest_watchlist.py (IFF DoD-1..5 pass)
```

## 5. Pipeline przetwarzania — krok po kroku

**Krok 1 — Ingestion** (`ingestion/lotto_client.py`)
Pull all historical draws z Lotto OpenAPI. Cache do `raw_draws.parquet`. Retry z exponential backoff (`tenacity`). API key z `.env` (NIGDY w repo). Cadence: manual + wtorek/piątek wieczorem (cron opcjonalny).

**Krok 2 — Regime split** (`ingestion/regime_split.py`)
Trzy parquet'y per reżim reguł: pre-2014-10-08, 2014-10-08→2022-03-25, post-2022-03-25. Każdy traktowany jako **oddzielny proces** dla validation (3 osobne calibration runs); join tylko dla regime-aware testów change-point detection.

**Krok 3 — H1 Classical Baseline** (`methodology/h1_classical.py`)
Minimum sufficient subset:
- **ADF** — stationarity test (statsmodels `adfuller`)
- **Bayesian online CP** (Adams-MacKay 2007, own impl) — change-point detection
- **Welch periodogram** + **Lomb-Scargle** — periodicity detection
- **Autocorrelation + PACF** — memory effect

KPSS *odrzucone* jako redundant z ADF (oba testują różne hipotezy zerowe, ale dla naszego celu pokrywają tę samą informację). CUSUM zachowane jako classical backup do Bayesian CP (cross-check).

**Krok 4 — K4-MMD Kernel Two-Sample Test** (`methodology/k4_mmd.py`)
Gaussian RBF + polynomial kernels. **Pre-registered** w `methodology/preregistration.md` przed Tygodniem 5 — bandwidth = median heuristic (no data-dredging). Sliding window N=200 kontra DriftSim baseline. Asymptotyczna teoria via Gretton et al. 2012.

**Krok 5 — DriftSim Calibration** (`driftsim/`)
- 5 planted patterns × 4 effect sizes (δ ∈ {0.01, 0.02, 0.05, 0.10} relative do uniform p=0.1) = **20 calibration scenarios** per test per regime.
- 1 no-planted (uniform null) scenario per regime.
- Output: sensitivity/specificity curves per test, jako `.parquet` + `.html` (Plotly).
- **Mandatory:** żaden test nie raportuje p-value na real data, dopóki ma własną kalibrację z DriftSim.

**Krok 6 — Permutation testing** (`methodology/permutation.py`)
- **Shuffle test core (DoD-2):** permutacje porządku losowań, 10⁴ permutacji per test per kernel config per regime.
- **Within-draw permutations:** 5!=120× dla głównych liczb, 2!=2× dla euronumerów — jako augmentation, NIE jako null (kolejność wewnątrz nie ma znaczenia fizycznego).
- **Block bootstrap** — alternative null zachowujący krótkozasięgowe korelacje, jako sanity check przeciwko shuffle test.
- Numba JIT na hot loop generation+statistic; joblib.Parallel na CPU cores; SQLite cache (seed → result).

**Krok 7 — Multiple testing correction** (`methodology/multiple_testing.py`)
Benjamini-Hochberg FDR jako primary (α=0.05). Storey q-values jako secondary cross-check. Hypothesis space explicit: 50 numbers × 4 test families × 3 regimes = 600 hipotez (pre-registered, no post-hoc additions).

**Krok 8 — Conformal & Specification curve** (`methodology/{conformal,specification}.py`)
Conformal p-values (Vovk, via `mapie`) jako uzupełnienie tradycyjnych p-values. Specification curve analysis: wszystkie reasonable parameter combinations (window sizes, kernel bandwidths, FDR thresholds) → wykres p-value distribution. Jeśli wynik znika przy minor specification change → unstable, nie raportowane.

**Krok 9 — Reporting** (`reporting/`)
Quarto report (`report.qmd`) z embedded Python chunks. Plotly figury → HTML. Matplotlib figury → PDF dla paper-style appendix. Negative result framing first-class — README mówi explicit "if no signal found, this is also a result".

**Krok 10 — Adaptive watchlist** (`adaptive/`, opcjonalny, self-value <20% scope)
Wykonuje się TYLKO jeśli ≥1 wzorzec przeszedł DoD-1..5 z FDR<0.05. W przeciwnym razie returns `None` z explicit message "no signal above detection threshold". **Nie wymyśla sygnału.**

## 6. Compute Execution Policy

> *Sekcja zastępująca generic "Hardware Execution Policy" zgodnie z DECISION_PROMPT §6.5. Realny bottleneck = CPU permutation overhead, nie VRAM.*

### 6.1 Resource budget per etap

| Etap | RAM peak | Disk | CPU time (12C/16T) | Notes |
|---|---|---|---|---|
| Ingestion | <100 MB | <5 MB raw | <30 s | Single API call ≤1500 records |
| Regime split | <200 MB | <10 MB per regime | <5 s | Polars lazy frame |
| H1 single run | <500 MB | — | 1–10 s | Per regime per test family |
| MMD single config | <800 MB | — | 5–60 s | Kernel matrix 500×500 max |
| Permutation test (1 config × 10⁴ perms) | <2 GB | 5–20 MB SQLite | **5–30 min** | Numba JIT, all cores |
| **Full pipeline overnight** | <4 GB | 200–500 MB | **6–18 h** | All tests × kernels × regimes × 10⁴ perms |
| DriftSim full sweep | <3 GB | 100–300 MB | **3–8 h** | 20 scenarios × 3 regimes × calibration runs |
| Quarto render | <1 GB | <50 MB output | <5 min | — |

**VRAM budget:** N/A — pipeline CPU-only. RTX 3050 4GB VRAM nie używane.
**Total disk budget (all artifacts):** ~1.5–2 GB. Mieści się na lokalnym SSD bez problemu; DVC remote opcjonalny.

### 6.2 CPU Transcendence Stack

> *Forma identyczna jak Hardware Transcendence Stack w generic szablonie, treść = CPU/compute, nie VRAM.*

| Oś | Technika | Lib | Impact | Status |
|---|---|---|---|---|
| **Compilation** | Numba JIT na permutation kernel | `numba` 0.59 | 10–50× speedup vs pure NumPy | ⚠️ Win11 — test in W1 |
| **Parallelism** | Process pool nad permutation seeds | `joblib.Parallel(backend='loky')` | ~12× na 12 cores | ✓ Win11-safe |
| **Caching** | Permutation results indexed by seed | SQLite + B-tree on (test, regime, seed) | Re-run skip = ∞× | ✓ |
| **Algorithmic** | Importance sampling permutations dla rzadkich p-values | own impl | 2–5× przy długim tail | ⚠️ tylko jeśli baseline >12 h |
| **Algorithmic** | Analytic null (asymptotic χ²) jako sanity check vs permutation | scipy.stats | — | ✓ — *as cross-check, nie zastępstwo* |
| **Vectorization** | Polars group-by zamiast pandas apply | `polars` 1.x | 5–30× na cleanup steps | ✓ |
| **I/O** | Parquet z compression `zstd` zamiast CSV | `pyarrow` | 5–10× faster read | ✓ |
| **Build-time cloud** | Overnight final runs na Colab Free CPU | Colab | Wolniej niż lokalnie (12C i5 > Colab CPU) — **tylko jako redundancy**, nie speedup | ⚠️ |
| **Build-time cloud** | Kaggle 30h/tydzień CPU dla independent re-run | Kaggle | Reproducibility cross-environment | ⚠️ |

### 6.3 Build-time tasks

| Zadanie | Gdzie | Output | Fallback |
|---|---|---|---|
| DriftSim full calibration sweep | **Lokalnie overnight** (i5-12500H > Colab CPU) | `artifacts/driftsim_runs/*.parquet` | Kaggle CPU 30h/tydzień |
| 10⁴ permutation final run | Lokalnie overnight, raz przed każdym milestone | `artifacts/permutation_cache.sqlite` | Colab CPU jako independent re-run dla cross-validation |
| Specification curve full sweep | Lokalnie | `artifacts/specification_curves.parquet` | — |
| Quarto report render | Lokalnie (lub GitHub Actions docelowo) | `docs/report.html`, `docs/report.pdf` | Manual `quarto render` |
| HF Spaces demo deploy | GitHub Action push → HF Hub | demo (Streamlit) | Manual push |

**Reguła kierunkowa:** local-first dla wszystkiego co Numba-friendly (i5-12500H z 12 cores bije Colab CPU). Cloud TYLKO dla cross-validation (independent re-run różny seed/order → ten sam wynik = rigor signal).

### 6.4 Runtime fallbacki kaskadowe

**A → B → C dla każdego krytycznego komponentu:**

1. **Permutation engine speed:**
   - A: Numba JIT + joblib (default)
   - B: pure NumPy + joblib (jeśli Numba broken na Win z jakiegoś powodu — patrz `tests/test_environment.py`)
   - C: scipy.stats analytic approximation z explicit "approximate p-value" flag w raporcie

2. **Storage permutation results:**
   - A: SQLite (default)
   - B: Parquet sharded per test_name (jeśli SQLite locking issues przy parallel writes)
   - C: Plain JSONL append-only (debugging)

3. **Lotto API availability:**
   - A: Live API pull (tenacity retry 5×, exponential backoff)
   - B: Cached `raw_draws.parquet` (last successful pull)
   - C: Manual CSV upload (`scripts/manual_import.py`) — for total API outage

4. **Quarto render:**
   - A: Quarto 1.5+ (default)
   - B: Plain `jupyter nbconvert` → HTML (if Quarto install fails)
   - C: Markdown + manual matplotlib `.png` embedding

5. **HF Spaces demo:**
   - A: Streamlit on HF Spaces (free tier)
   - B: Render.com static site z embedded Plotly HTML
   - C: GitHub Pages z static HTML report

### 6.5 Composability check

| Para technik | Kompatybilność | Notes |
|---|---|---|
| Numba JIT × joblib.Parallel | ✓ | Numba functions są picklable jako wrapped Python; `loky` backend OK |
| Numba JIT × Polars | ✓ | Konwersja via `.to_numpy()` przed JIT hot path |
| SQLite × parallel writes | ⚠️ | WAL mode mandatory; jeden writer pool, multiple readers. Schemat zaprojektowany pod append-only. |
| DVC × SQLite | ⚠️ | DVC traktuje SQLite jako binary blob — nie diff-friendly. **Mitygacja:** SQLite jako artifact (DVC track), nie source-of-truth (parquet jest). |
| Pydantic Settings × `.env` | ✓ | Per Piotr's template, sprawdzone w poprzednich projektach |
| Streamlit × Plotly | ✓ | Native support, no friction |
| Quarto × Polars | ✓ | Quarto wykonuje Python chunks; Polars dla data prep |
| mapie × statsmodels | ✓ | Mapie jest sklearn-compatible; integration via numpy arrays |

**Brak znanych konfliktów krytycznych.** Numba na Windows 11 jest jedynym ⚠️ — sanity test w Tygodniu 1.

---

## 7. Roadmap: MVP → Portfolio-ready → Open-source-ready

### 7.1 Week-by-week

| Tydzień | Cel | Deliverable | DoD spełnione |
|---|---|---|---|
| **W1** | Environment + H1 core + DoD-1a/1b | `test_environment.py` green; ADF + Bayesian CP detect 2014/2022 change-points blind; project skeleton committed | DoD-1a, DoD-1b |
| **W2** | DriftSim part I | Planted signal generators (5 types × 4 effect sizes); uniform null generator; unit tests | — |
| **W3** | DriftSim part II — calibration | Sensitivity/specificity curves per H1 test per regime; first artifacts under DVC | DoD-5 (foundation) |
| **W4** | K4-MMD core | MMD impl + pre-registered kernel choices in `preregistration.md`; comparison z H1 na shuffled data | DoD-4 (foundation) |
| **W5 — DECISION GATE** | Triangulation check | H1 + MMD detect planted signals z DriftSim z power >70%? **TAK** → W6. **NIE** → Plan B (patrz §8.4) | DoD-3 |
| **W6** | Rigor layer | FDR (BH primary, Storey secondary); conformal p-values via mapie; specification curve analysis | DoD-2 (full) |
| **W7** | Reporting + adaptive | Quarto report draft; honest watchlist module (returns None if no signal); README disarmer | DoD-6 |
| **W8** | Polish MVP | Final README; static plots polished; demo Streamlit prototype | MVP complete |
| **W9** | Portfolio polish | HF Spaces demo deploy; recruiter-facing summary; specification curve full sweep documented | Portfolio-ready |
| **W10** | Open-source readiness | CI/CD (GitHub Actions); contribution guide; pyproject.toml as installable; semantic version v0.1.0 | OS-ready |

### 7.2 Definition of "ready" per tier

**MVP (W1–W8):** wszystkie DoD-1..6 spełnione, raport Quarto dostępny, repo clean, README z disarmerem. Wystarczające do "look at my GitHub" w aplikacji.

**Portfolio-ready (W9):** + HF Spaces interactive demo, + recruiter-facing executive summary (1 page PDF), + 10-second hook GIF embedded w README. Wystarczające do "tu jest mój flagship project".

**Open-source-ready (W10):** + GitHub Actions CI (test + lint + Quarto render), + CONTRIBUTING.md, + plug-in interface dla custom DriftSim signal generators (stretch: NIST RNG case), + semver tag v0.1.0, + Zenodo DOI dla cytowalności.

### 7.3 Plan B (Tydzień 5 fail)

Z SWOT TOP 1: *"Jeśli H1 + MMD nie wykrywają planted signals w tygodniu 5 → projekt staje się 'framework for measuring detector hallucination rates in supposedly memoryless processes'."*

**Decyzja:** Plan B jest **zawsze akceptowalny**, nie tylko jako fallback. Framing z §1 ("calibrated detector hallucination rates" jako pozycja na rynku tooling'u) jest *kompatybilny* z Plan B — to ta sama narracja, tylko bez positive result section w raporcie. **README disarmer pozostaje niezmieniony.**

## 8. Risk Register + Mitigation

| # | Ryzyko | Typ | Prawd. | Impact | Mitygacja | Trigger detekcji |
|---|---|---|---|---|---|---|
| R1 | Hallucination (detektor "znajduje" sygnał, którego nie ma) | Methodological | M | **CRITICAL** | Shuffle test obligatory + FDR + specification curve + DriftSim calibration | p-value <0.05 na real ALE także na ≥1 shuffled fold |
| R2 | Statistical power <30% dla subtle signals przy n=1500 | Methodological | H | M | Explicit power analysis w README; effect size threshold documented; negative result first-class | Power curve from DriftSim |
| R3 | Specification curve overfitting | Methodological | L | M | Pre-registered specification space w `preregistration.md` przed final run | Diff `preregistration.md` z final config |
| R4 | "Lotto-scam" first impression u recruiter'a | Portfolio | M | H | 3-sentence disarmer w README; methodological category framing; no emojis/casual tone | Recruiter feedback (post-launch) |
| R5 | "Stack za prosty" dla quant recruitera | Portfolio | M | M | Conformal + specification curve + DriftSim infrastructure jako "rigor signal"; Numba/Polars jako modern stack signal | Self-assessment review W8 |
| R6 | 6-8 tyg overrun | Scope | H | M | DriftSim (W2-3) jako biggest unknown, fixed time-box; Plan B jako safe landing | Behind schedule W3 lub W5 |
| R7 | DriftSim calibration sweep > overnight | Scope/compute | M | M | Numba JIT W1 sanity check; effect size sweep narrower if needed; Colab CPU as backup | Single config >30 min w W2 |
| R8 | Numba on Win11 install issues | Środowisko | L | H | `test_environment.py` w W1; fallback do pure NumPy z explicit speed hit warning | `import numba` fails |
| R9 | Bayesian online CP own implementation buggy | Methodological | M | M | Property-based tests (`hypothesis`); cross-check vs `ruptures` PELT na same data | Disagreement >10% z PELT |
| R10 | Gambling addiction ethical concern | Etyczne | L | H | README explicit disclaim §1; no "predict your numbers" framing anywhere; adaptive module returns None when honest | — |
| R11 | Lotto API ToS violation | Legal | L | M | ToS review w W1 BEFORE pull; jeśli restricted, switch to public scraped historical data | ToS review |
| R12 | DVC complexity > rigor benefit | Scope | M | L | Allow demote to plain `git lfs` if DVC eats >4h setup | Setup >4h |

## 9. Szacunki czasowe per faza (godziny netto)

| Faza | Min | Realistyczne | Max | Notes |
|---|---|---|---|---|
| W1 — Env + H1 core + DoD-1 | 16 h | 24 h | 32 h | Numba sanity to wildcard |
| W2 — DriftSim part I | 20 h | 28 h | 40 h | Largest uncertainty |
| W3 — DriftSim calibration | 20 h | 28 h | 40 h | |
| W4 — K4-MMD core | 16 h | 20 h | 30 h | Custom MMD ~80 LOC core, reszta = tests |
| W5 — Decision Gate + iteration | 12 h | 16 h | 24 h | |
| W6 — Rigor layer | 20 h | 28 h | 40 h | mapie + specification curve = nowy material |
| W7 — Reporting + adaptive | 16 h | 24 h | 32 h | |
| W8 — Polish MVP | 12 h | 20 h | 28 h | |
| **TOTAL MVP** | **132 h** | **188 h** | **266 h** | ~5h/dzień × 8 tyg × 5 dni = 200h — realistic mid-range |
| W9 — Portfolio polish | 12 h | 16 h | 24 h | HF Spaces deploy + summary |
| W10 — OS readiness | 12 h | 20 h | 28 h | CI/CD + contribution guide |
| **TOTAL 10-week** | **156 h** | **224 h** | **318 h** | |

## 10. DoD Mapping (z SEED_IDEA §7A.1 + DECISION_PROMPT)

| DoD | Komponent walidujący | Pass criterion |
|---|---|---|
| DoD-1a — Sanity check (euronumbers) | H1 stationarity tests | Detekcja zmian puli euronumerów 2014/2022 w częstościach 9, 10, 11, 12 |
| DoD-1b — Blind change-point detection | Bayesian online CP + CUSUM | Top-2 ranked change-points pokrywają się z 2014-10-08 i 2022-03-25 (±30 dni) **przed** ręcznym sprawdzeniem |
| DoD-2 — Shuffle test rigor | `methodology/permutation.py` | False-positive rate w shuffled data ≤ α=0.05 ± Monte Carlo error |
| DoD-3 — Multiple testing correction | `methodology/multiple_testing.py` | Benjamini-Hochberg FDR primary, Storey q-values secondary; hypothesis space pre-registered |
| DoD-4 — Cross-architecture consistency | H1 ↔ MMD ↔ DriftSim triangulation | Każdy reported signal widziany przez ≥2 z 3 filarów |
| DoD-5 — Honest predictor (kalibracja) | `driftsim/calibration.py` | Adaptive watchlist generuje output IFF passed DoD-1..4; w przeciwnym razie None |
| DoD-6 — Reproducibility | `core/seeds.py` + DVC + GitHub Action | Cold-machine re-run produces bit-identical SQLite hashes z committed seeds |

## 11. Open Questions z SEED_IDEA — resolution

| Pytanie SEED_IDEA | Status | Resolution |
|---|---|---|
| §7A.1 — DoD-1 blind protocol sufficient? | **RESOLVED** | Tak; ranking change-pointów *przed* porównaniem z 2014/2022 dat (zob. `methodology/h1_classical.py` API) |
| §7A.2 — Paradygmat radykalnie redefiniujący target | **DEFERRED** to W10+ stretch | TDA (persistence landscapes na Takens embedding) jako post-MVP exploration. Specification curve analysis już dodaje math depth bez wybuchu scope'u. |
| §7B.5 — Hardware Transcendence? | **RESOLVED — NIE** | CPU-only architecture; sekcja zastąpiona §6 |
| §7C.6 — Statistical power przy n=1500 | **RESOLVED** | Power analysis w `driftsim/calibration.py` jako mandatory output; documented w README |
| §7C.7 — Update cadence per komponent | **RESOLVED** | Online auditor: per-draw; H1: per-draw 1-10s; MMD: co tydzień; DriftSim: jednorazowo + co milestone re-run |
| §7C.8 — Honest augmentation | **RESOLVED** | Within-draw permutations (5! main, 2! eurons) jako augmentation; shuffle test jako null; block bootstrap jako alternative null |
| §7D.9–10 — Framing scam-disarm | **RESOLVED** | 3-sentence disarmer w README jako §2 niżej; methodological category framing |
| §7E.11 — Blind-spot question | **ADDRESSED** | *"Czy projekt mierzy negative result rigor-ously?"* — Tak, via DriftSim calibration curves które *muszą* zostać opublikowane niezależnie od positive/negative result na real data |

## 12. Anti-goals guard (final)

Każda decyzja w tym brief'ie sprawdzona pod:

- ☑ **Nie naive frequency** — H1 minimum sufficient subset to ADF + Bayesian CP + Welch + ACF, każdy z permutation-based istotnością.
- ☑ **Nie hallucinated signal** — DoD-2 (shuffle test) obligatory; FDR primary; specification curve mandatory; adaptive watchlist returns None gdy DoD-1..5 nie spełnione.
- ☑ **Nie wrapper na cudzy model** — własna implementacja Bayesian online CP, własny MMD (~80 LOC), własny DriftSim, własny conformal integration.
- ☑ **Nie "gwarantowana wygrana"** — README §1 explicit disclaim; adaptive module wraz z honest-None return; framing methodological, nie predictive.
- ☑ **Nie pivot z premise** — DECISION_PROMPT §5B respektowane; brief nie tłumaczy że losowanie jest niezależne (premise jest w SEED_IDEA §11 Reality Check).
- ☑ **Nie ograniczenie do Pythona z definicji** — alternatywy R/Julia/Rust rozważone i odrzucone z explicit uzasadnieniem (§3-alt), nie z lenistwa.

---

## PoC Results — Krok 6 (2026-05-17)

**Srodowisko:** Python 3.10.13 | numpy 2.2.5 | numba 0.65.1 | joblib 1.5.3 | Win11 | i5-12500H (12C/16T)

> Numba 0.65.1 zamiast 0.59.x z briefu — numpy 2.x wymaga nowszego numba. Zaktualizowac pin w pyproject.toml.

### Warianty testowane

| Wariant | Opis | Wynik |
|---------|------|-------|
| A — NumPy sequential | 1000 perms, 1 core, pelny loop | **0.06s → 15 879 perms/s** |
| B — NumPy + joblib per-perm | 1000 callbackow, wszystkie rdzenie | 0.99s → 1 010 perms/s (16x wolniej niz A!) |
| C — Numba JIT (1-core) | JIT caly loop 1000 perms | **0.02s → 43 094 perms/s** |
| C — Numba JIT + joblib configs | 8 jobow x 125 perms, wszystkie rdzenie | 1.89s → 530 perms/s (overhead joblib dominuje dla malych jobow) |

### Kluczowe wnioski

**1. Numba JIT (loop-level) = 2.71x szybsze niz NumPy sequential.**
Dla 10k perms x 1 konfiguracja: NumPy = ~0.63s, Numba = ~0.23s (szacunek z 1k skalowany x10).

**2. joblib per-perm (Wariant B) jest WOLNIEJSZE niz sequential.**
Process-spawn overhead + serialization dominuje dla krotkich callbackow.
Wzorzec z pierwotnego briefu (`Parallel` nad indywidualnymi permutacjami) jest bledny.

**3. Poprawny wzorzec: Numba kontroluje wewnetrzny loop, joblib nad konfigami.**
```
# PRAWIDLOWO:
@njit(cache=True)
def run_all_perms(draws, n_perms, start_seed):  # JIT caly loop
    ...

Parallel(n_jobs=-1)(
    delayed(run_all_perms)(draws, n_perms, seed_offset)
    for seed_offset in config_seeds              # joblib nad konfiguracjami
)
```

**4. Szacunek pelnej pipeline (10k perms x 150 konfiguracji):**

| Wzorzec | Szacunek |
|---------|----------|
| NumPy seq (bez parallelism) | ~0.0h (praktycznie chwila) |
| NumPy + joblib per-perm (bledny) | ~0.4h |
| Numba JIT + joblib nad konfiguracjami | ~0.8h (konserwatywnie, overhead) |

Wszystkie warianty mieszcza sie w overnight limicie (18h). **Brief byl zbyt pesymistyczny** — szacunek 5-30 min per config dotyczy bardziej zlozonej statystyki (MMD sliding window), nie prostego chi-squared. Numba szczegolnie oplacalna dla operacji O(N^2) (MMD).

### Poprawki do briefu

1. **§3 Stack — wersja Numba:** 0.65.x (nie 0.59.x) — wymagane przez numpy 2.x.
2. **§5 Pipeline — Krok 6 Permutation:** zmieniony wzorzec `@njit` — caly loop wewnatrz JIT, `joblib.Parallel` nad niezaleznymi konfigami (test_name, regime, kernel_config), nie nad pojedynczymi permutacjami.
3. **§6.1 Resource budget:** szacunek "5-30 min per config" dla prostych testow (chi-squared, ADF) jest przeszacowany — faktycznie sekundy. 5-30 min moze byc realistyczne dla MMD z duza macierza kernelowa.
4. **R8 ryzyko Numba Win11:** ZWERYFIKOWANE — Numba 0.65.1 dziala na Win11 z numpy 2.x. Ryzyko R8 zmniejszone z L do Very Low.

### Decyzja (§6D WORKFLOW)

**Stan: ✅ Wariant C dziala, pipeline w overnight limicie.**

Przejsc do Kroku 7 (cross-review briefu) z uwzglednieniem poprawek powyzej.

---

**Akceptacja:** ten brief jest *contract* — każda zmiana decyzji wymaga update commit'u z rationale. Drobne tactical changes (lib version bump w tym samym major) OK bez review; architectural changes (Numba → Rust, MMD → neural variant, target → non-EuroJackpot przed Tygodniem 10) wymagają explicit re-review.

**Handoff:** ten plik jest gotowy do przekazania Claude Code CLI jako root-level architectural contract. Pierwsze pytanie Code do tego brief'u powinno brzmieć: *"Czy rozpoczynamy od `test_environment.py` w W1, czy od scaffolding `pyproject.toml` + struktury katalogów?"* — odpowiedź: **scaffolding pierwszy, environment test drugi w tej samej sesji**.
