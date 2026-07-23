# CLAUDE.md — DriftScope

## Kontekst projektu
- **Projekt:** DriftScope — research-grade audit framework dla detekcji niestacjonarności w strumieniach dyskretnych procesów z założenia uniform. Flagship case study: EuroJackpot z known change-pointami 2014-10-10 i 2022-03-25 jako ground truth (positive control = euronumery; negative control = główne liczby 1-50). Framework jest reusable: NIST RNG, kryptograficzne PRNG, financial random-walk są naturalnymi stretch targets.
- **Typ:** CLI Tool / Scientific Research Framework (Methodology)
- **Stack (pinned wersje krytyczne):**
  - Python 3.10.x (fixed)
  - `numba==0.65.1` — PINNED (zweryfikowane Win11 + numpy 2.x, 2026-05-17; fallback: pure NumPy)
  - `numpy>=2.2,<3.0` — wymagany numpy 2.x dla numba 0.65.x
  - `statsmodels>=0.14,<0.15` — ADF/KPSS/BH FDR
  - `ruptures>=1.1.9,<2.0` — PELT cross-check dla Bayesian CP
  - `scipy>=1.13,<2.0` — scipy.signal (Welch, Lomb-Scargle)
  - `scikit-learn>=1.4,<2.0` — pairwise_kernels dla MMD
  - `polars>=1.0,<2.0` — type-safe data manipulation (NIE pandas)
  - `pydantic>=2.0,<3.0` + `pydantic-settings>=2.0,<3.0`
  - `typer>=0.12,<0.13` — CLI z --resume
  - `matplotlib>=3.9,<4.0` — static viz + .webm animation
  - `plotly` (latest) — interactive HTML charts
  - `httpx>=0.27` + `selectolax>=0.3` + `tenacity>=8.0` — scraper
  - `pyarrow>=16.0` — Parquet I/O (Zstd compression)
  - `psutil>=5.9` — RAM guards
  - Dev: `pytest>=8.0`, `hypothesis>=6.0`, `ruff>=0.4`, `mypy>=1.10`
- **Środowisko:** Windows 11, Miniconda (Python 3.10), VS Code
- **Cel bieżący:** W0 — Data + power preview (scraper probe → cached CSV → analytic power)

## Zasady pracy
- Zawsze sprawdzaj MEMORY.md przed podjęciem decyzji architektonicznej
- Nie duplikuj rozwiązań już opisanych w MEMORY.md
- Przy każdej nowej sesji: zacznij od /start
- Przy zakończeniu sesji: zawsze wywołaj /end
- W trakcie dłuższej pracy rób checkpointy przez /save
- Język komunikacji: polski (chyba że user napisze po angielsku)
- PROJECT_BRIEF.md to **architectural contract** — każda zmiana decyzji wymaga explicit update commit z rationale
- Każda zmiana w `methodology/` wymaga update `preregistration_v{N}.md` z polem `revision_reason`

## Konwencje projektu
- Nazewnictwo plików: snake_case (Python)
- Język komentarzy w kodzie: **angielski** (decyzja i18n 2026-07-23; wcześniej polski — migracja legacy w toku, `notebooks/` świadomie poza zakresem)
- Styl commitów: conventional commits (feat:, fix:, refactor:, docs:, chore:)
- Linter/formatter: ruff (wszystko) + mypy --strict (priorytetowo dla `methodology/`)
- Package layout: `pyproject.toml` + `src/driftscope/` (PEP 621)
- Config: Pydantic Settings v2 + `.env` (`BASE_SEED=42` globalny determinizm)
- Storage: Parquet + Zstd (`artifacts/`) + CSV (seed/wyniki) — persystencja w pełni plikowa (warstwa SQLite `db/` usunięta 2026-06-06, nigdy nie zmaterializowana; zob. PROJECT_BRIEF.md §0 rewizja)
- Testowanie stochastyczne: `pytest.approx(rel=0.05, abs=1e-3)` (globalnie w conftest.py)
- **Nigdy:**
  - Repository pattern (gdyby zaszła potrzeba dostępu do DB → `db/queries.py`; w DriftScope persystencja plikowa, brak warstwy DB)
  - `pandas.apply` (użyj Polars)
  - joblib nad pojedynczymi permutacjami (joblib TYLKO nad konfigami `(test, regime, kernel_config, seed_offset)`)
  - JAX (DLL risk na Win11)
  - R/Julia/Rust (chyba że Numba niewystarczająca po Decision Gate W5)

## Hardware Transcendence Stack

> Dotyczy DriftScope: **Oś 0 + Oś 3 aktywne.** Reszta HARDWARE_PUSH_CATALOG nie aplikuje
> (pipeline CPU-only, brak modeli neural, VRAM budget N/A).

| Oś / Technika | Implementacja | Impact | Status |
|---|---|---|---|
| **Oś 0 — Environment** | `tests/test_environment.py` (Numba Win11 + numpy 2.x sanity) | Fail-fast W1 | ✓ PoC verified |
| **Oś 3 — Compilation** | `@njit(cache=True)` selektywnie (MMD hot loop, BCPD inner) | 2.7× simple / 10–30× MMD | ✓ PoC verified |
| Parallelism | `joblib.Parallel(backend='loky')` nad konfiguracjami | ~10–12× na 12 cores | ✓ Win11-safe |
| Caching | Parquet shards per worker → Polars LazyFrame reduce | Re-run skip = ∞× (`--resume`) | ✓ |
| Vectorization | Polars group-by zamiast pandas apply | 5–30× | ✓ |
| I/O | Parquet + Zstd compression | 5–10× faster read | ✓ |
| Algorithmic | Importance sampling (tylko gdy baseline >6h) | 2–5× long tail | ⚠️ jeśli potrzeba |
| Build-time cloud | Colab/Kaggle dla cross-env re-run | Reproducibility signal | ⚠️ opcjonalne |

**PoC (Krok 6, 2026-05-17):** Numba JIT = 2.71× vs NumPy sequential. joblib per-perm = 16× WOLNIEJSZE — NIGDY joblib nad pojedynczymi permutacjami.

## Sprzęt / Budżet obliczeniowy

| Zasób | Wartość | Uwagi |
|---|---|---|
| CPU | i5-12500H (12C/16T) | `joblib.Parallel(n_jobs=-1)` → ~10–12× |
| RAM | 32GB DDR4 | Peak pipeline ~4 GB (DriftSim full sweep) |
| GPU | RTX 3050 Laptop 4 GB VRAM | **Nieużywane** — pipeline CPU-only |
| VRAM budget | N/A | Brak modeli neural; VRAM ≤3.5 GB (constraint nieaktywny) |
| batch_size | 1 (default dla komponentów z batch API) | |
| Overnight budget | ~18h | DriftSim full sweep (4–10h) mieści się w limicie |

**Budżet RAM per etap (§6.1 PROJECT_BRIEF.md):**

| Etap | RAM peak | CPU time | Notes |
|---|---|---|---|
| Ingestion (scraper) | <100 MB | 30s–5 min | Rate-limited 2s/req |
| H1 single run | <500 MB | 1–10 s | Per regime per test |
| MMD single config | <800 MB | 5–60 s | Kernel matrix 500×500 max |
| Simple permutation (10⁴) | <500 MB | <10 s | Numba sequential |
| MMD permutation (10⁴) | <2 GB | 1–15 min | Numba JIT hot loop |
| DriftSim full sweep | <3 GB | 1–3 h | 63 unique datasets |
| Full pipeline eval | <4 GB | 4–10 h | Wszystkie tests × datasets × 10⁴ perms |
| Polars LazyFrame reduce | <2 GB | 5–15 min | `scan_parquet(glob).collect()` |

## Pliki stanu sesji
- **MEMORY.md**               — długoterminowa pamięć projektu (czytaj na /start)
- **last_session.md**         — stan ostatniej sesji + punkt odniesienia git (czytaj na /start, pisz na /end)
- **last_session.archive.md** — archiwum 5 ostatnich sesji (bezpiecznik /end; powstaje przy pierwszym /end)

## Komendy dostępne w tym projekcie
| Komenda    | Kiedy używać                        | Co robi                                          |
|------------|-------------------------------------|--------------------------------------------------|
| `/start`   | Na początku każdej sesji            | Czyta MEMORY.md + last_session.md; sanity-check  |
| `/save`    | Checkpoint w trakcie pracy          | Aktualizuje last_session.md (sesja trwa)         |
| `/recover` | Przed /end lub po chaotycznej pracy | Audyt zmian od punktu odniesienia; lista napraw  |
| `/end`     | Na końcu sesji                      | Weryfikacja → archiwizacja → nadpis + MEMORY     |
| `/status`  | Szybki podgląd (bez modyfikacji)    | Wyświetla aktualny stan z last_session.md        |

## Struktura katalogów

> Drzewo zsynchronizowane z `git ls-files` 1:1 [2026-06-11]. Katalogi czysto
> archiwalne (`docs/research/rd_archive/`, `docs/research/readme_rewrite/`) zwinięte
> do licznika + pointera (mają własne README) — reszta wyliczona plik po pliku.

```
DriftScope/
├── pyproject.toml                    # PEP 621, single source of truth wersji
├── .env.example                      # klucze konfiguracyjne
├── .gitignore
├── PROJECT_BRIEF.md                  # architectural contract
├── README.md                         # front door (publiczny)
├── LICENSE                           # MIT
├── CLAUDE.md                         # instrukcje projektu (ten plik)
├── MEMORY.md                         # długoterminowa pamięć projektu
├── last_session.md                   # stan ostatniej sesji
├── last_session.archive.md           # archiwum 5 ostatnich sesji
├── WORKFLOW.md                       # workflow sesyjny
├── HARDWARE_PUSH_CATALOG.md          # meta-katalog technik (linkowany wyżej)
├── TASK_REPO_STRUCTURE_OPUS48.md     # task refaktoryzacji struktury (2026-06-11)
├── .claude/commands/                 # skille sesyjne: start/save/recover/end/status.md
├── .github/workflows/ci.yml          # CI: ruff + mypy --strict + pytest (ubuntu, py3.10)
├── data/seed/
│   ├── eurojackpot_history.csv       # committed; Tier-1 fallback (958 losowań)
│   ├── multimulti_history.csv        # committed; gra 2 (16827 losowań, pool=80)
│   ├── powerball_history.csv         # World Lottery Audit (ścieżka A); + _bonus_ wariant
│   ├── megamillions_history.csv      # World Lottery Audit (ścieżka A); + _bonus_ wariant
│   ├── drand_beacon.csv              # ścieżka B2; 2678 rund drand (32 B/runda)
│   ├── nist_beacon.csv               # ścieżka B2; 1339 pulsów NIST (64 B/puls)
│   ├── randao_missed_slots.csv       # ścieżka B3; pominięte sloty (skan CZĘŚCIOWY, --resume)
│   └── randao_scan_meta.json         # ścieżka B3; mianowniki + cursor skanu (complete=False)
├── scripts/
│   ├── smoke_test.py                 # deps import + CPU check + wersje
│   ├── archive.py                    # SHA-256 manifest generator
│   ├── manual_import.py              # CSV upload fallback (Tier-3)
│   ├── check_api_key.py              # probe klucza developers.lotto.pl (← test_api_key)
│   ├── convert_mm_seed.py            # konwerter źródłowego CSV Multi Multi → seed
│   ├── calibrate_bocpd_threshold.py  # kalibracja progu BOCPD per-pole (null)
│   ├── calibrate_mmd_pool.py         # kalibracja FPR MMD per pool (np. 80)
│   ├── multimulti_audit.py           # CLI runner audytu MM (gra 2)
│   ├── prng_benchmark.py             # CLI PRNG benchmark (reusability showcase)
│   ├── fetch_beacons.py              # CLI: cache digestów drand/NIST (B2)
│   ├── fetch_beacon_chain.py         # CLI: skan zajętości slotów Ethereum, --resume (B3)
│   ├── randao_audit.py               # CLI: audyt withholdingu RANDAO (B3)
│   └── scraper_selectors.md          # nota W0.1 (deliverable kontraktu — zob. PROJECT_BRIEF)
├── docs/                             # GitHub Pages source (Deploy from branch /docs)
│   ├── index.html                    # landing
│   ├── report.html                   # Quarto output (kanoniczny raport)
│   ├── executive_summary.html        # 1-pager rekruterski (W9)
│   ├── templates/
│   │   └── universal_session_setup_prompt.md   # (← root)
│   └── research/
│       ├── external/
│       │   └── 2026-05-27_eurojackpot_take_rate.md
│       ├── readme_rewrite/           # brief + 5 recenzji README (6 plików)
│       └── rd_archive/               # archiwum cross-review R&D (30 plików + README mapujący)
├── notebooks/                        # exploratory — NIE part of pipeline
│   ├── 00_power_preview.py           # W0 power preview
│   └── poc_permutation_engine.py     # Krok 6 PoC (← root, DONE 2026-05-17)
├── demo/
│   └── app.py                        # Streamlit (off-stack, optional-dep `demo`)
├── artifacts/                        # manifest SHA-256 trackowany; binaria ignorowane (rewizja [2026-06-11])
│   ├── .gitkeep
│   └── artifacts_manifest.json       # SHA-256 manifest (DoD-6); *.parquet odtwarzalne przez --resume
├── src/driftscope/
│   ├── __init__.py                   # __version__ = "0.1.0"
│   ├── py.typed                      # marker PEP 561 (mypy --strict konsumentom)
│   ├── cli.py                        # Typer entrypoint (driftscope run)
│   ├── pipeline.py                   # orkiestrator run_audit (integracja DoD-1..6, regime-aware)
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings (BASE_SEED, paths)
│   │   ├── types.py                  # DrawRecord (unified pool/k), Detector alias, TestResult
│   │   ├── seeds.py                  # make_worker_seeds(base, n) → list[SeedSequence]
│   │   └── guards.py                 # @with_timeout, assert_memory_below
│   ├── ingestion/
│   │   ├── lotto_scraper.py          # httpx + selectolax + tenacity; load_seed_csv / load_generic_seed_csv
│   │   ├── regime_split.py           # 2014/2022 split → regime_{1,2,3} (warstwa danych)
│   │   ├── rng_streams.py            # PRNG: MT19937/Xorshift/ChaCha20/AES-CTR-DRBG + defekty
│   │   ├── beacon_streams.py         # B2: drand/NIST jako BitStream (finite, bez ziarna)
│   │   └── beacon_chain.py           # B3: zajętość slotów Ethereum, limiter AIMD, --resume
│   ├── methodology/
│   │   ├── preregistration_v1.md     # SUPERSEDED przez v2 (history)
│   │   ├── preregistration_v2.md     # SUPERSEDED przez v3 (history)
│   │   ├── preregistration_v3.md     # SUPERSEDED przez v4 (history)
│   │   ├── preregistration_v4.md     # SUPERSEDED przez v5 (history)
│   │   ├── preregistration_v5.md     # SUPERSEDED przez v6 (history)
│   │   ├── preregistration_v6.md     # SUPERSEDED przez v7 (history)
│   │   ├── preregistration_v7.md     # ACTIVE — frozen choices + revision log
│   │   ├── h1_classical.py           # ADF, KPSS, BOCPD (compute_bocpd_curve), Welch, ACF
│   │   ├── k4_mmd.py                 # Gaussian RBF na freq vectors (Δⁿ)
│   │   ├── cooccurrence.py           # test współwystąpień par (§5c, curveball null)
│   │   ├── permutation.py            # shuffle test + @njit(cache=True) hot loop (DoD-2)
│   │   ├── block_bootstrap.py        # alternative null (block ∈ {5,10,20})
│   │   ├── multiple_testing.py       # Family A (BH) + Family B (Benjamini-Yekutieli)
│   │   ├── specification.py          # spec curve 9 points (3 windows × 3 bw)
│   │   └── recurrence.py             # gap test (perm-calibrated) + Nelson-Aalen + EVT
│   ├── driftsim/
│   │   ├── planted_signals.py        # 5 sygnałów × 4 effect sizes = 63 datasety
│   │   ├── null_uniform.py           # honest null generator (+ generic pool)
│   │   └── calibration.py            # sensitivity/specificity curves + chi2
│   ├── reporting/
│   │   ├── plots_static.py           # matplotlib (paper + .webm export)
│   │   ├── plots_interactive.py      # Plotly (HTML w Quarto)
│   │   ├── disagreement.py           # Disagreement Protocol (3/3, 2/3, 1/3, 0/3) (DoD-4)
│   │   ├── information_theory.py     # suplement LZ76 (NIE 4. filar)
│   │   ├── prng_benchmark.py         # bateria reusability (PRNG ground-truth)
│   │   ├── multimulti_audit.py       # runner gra 2 (Multi Multi, negative control)
│   │   ├── lottery_audit.py          # runner World Lottery Audit (ścieżka A)
│   │   ├── randao_audit.py           # B3: audyt withholdingu (pozycja pominięć w epoce)
│   │   └── report.qmd                # Quarto source
│   └── adaptive/
│       └── honest_watchlist.py       # TYLKO gdy DoD-3 (FDR) + DoD-4 pass; else None (DoD-5)
└── tests/                            # 28 plików test_*.py + conftest (macierz DoD-1..6 + reporting + reuse)
    ├── conftest.py                   # pytest.approx defaults, seed fixtures
    ├── test_environment.py           # Numba + Win11 + numpy 2.x (Oś 0)
    ├── test_vram_invariants.py       # RAM budget niezmienniki (CPU-only)
    ├── test_h1_invariants.py         # ADF/KPSS/BOCPD invariants
    ├── test_mmd_properties.py        # MMD properties + stability
    ├── test_cooccurrence.py          # co-occurrence (curveball, max-pair)
    ├── test_permutation_null.py      # FPR ≤ α=0.05 ± MC error (DoD-2)
    ├── test_block_bootstrap.py       # moving block bootstrap null
    ├── test_multiple_testing.py      # Family A/B FDR (DoD-3)
    ├── test_specification.py         # spec curve 9 punktów
    ├── test_recurrence.py            # gap + Nelson-Aalen + EVT
    ├── test_driftsim_calibration.py  # planted signal detection
    ├── test_disagreement.py          # Disagreement Protocol logic (DoD-4)
    ├── test_honest_watchlist.py      # honest gate → None (DoD-5)
    ├── test_reproducibility.py       # seeds + pure-function reseed + manifest (DoD-6)
    ├── test_pipeline.py              # run_audit end-to-end (pos/neg control)
    ├── test_regime_split.py          # granice reżimów + Parquet determinizm
    ├── test_rng_streams.py           # PRNG streams + defekty (favor/period)
    ├── test_beacon_streams.py        # B2: cache digestów, wyczerpanie, determinizm bez ziarna
    ├── test_randao_audit.py          # B3: czułość/swoistość + moc + integralność skanu
    ├── test_lottery_audit.py         # ścieżka A: replikacja PB/MM
    ├── test_prng_benchmark.py        # bateria reusability
    ├── test_generic_pool_invariants.py  # loader + wyprowadzanie pool z rekordów (gra 2)
    ├── test_information_theory.py     # LZ76 suplement (komplementarność)
    ├── test_plots_static.py          # figury matplotlib (ścieżki/suffix)
    ├── test_plots_interactive.py      # figury Plotly (struktura + HTML)
    ├── test_demo_smoke.py            # Streamlit AppTest headless
    ├── test_cli.py                   # CLI driftscope run
    └── test_artifacts_smoke.py       # artifact path + content smoke tests
```

## Roadmap (tygodnie)
- **W0** — Data + power preview (scraper probe, cached CSV, analytic power)
- **W1** — Environment + H1 core + DoD-1 (test_environment.py green, ADF/KPSS/Bayesian CP)
- **W2** — DriftSim part I (5 planted signals × 4 effect sizes = 63 datasets)
- **W3** — DriftSim calibration (sensitivity/specificity curves)
- **W4** — K4-MMD core (MMD on frequency vectors, N=200 PoC vs shuffled null)
- **W5** — Decision Gate (H1+MMD detect planted signals power >70%?)
- **W6** — Rigor layer (family-aware FDR, spec curve 9 points)
- **W7** — Reporting + adaptive + disagreement protocol
- **W8** — Polish MVP (.webm hook, GitHub Pages)
- **W9** — Portfolio polish (executive summary PDF)
- **W10** — Open-source readiness (opcjonalne)

## DoD Mapping
| DoD | Komponent walidujący | Pass criterion |
|---|---|---|
| DoD-1a | H1 stationarity tests | Detekcja zmian puli euronumerów 2014/2022 |
| DoD-1b | Bayesian CP + CUSUM (euronumery) | Top-2 CP pokrywają 2014-10-10 (±60 dni — data-CP ≈2014-11-28) i 2022-03-25 (±30 dni) blind; główne 1-50 = negative control (brak CP) |
| DoD-2 | `methodology/permutation.py` | FPR w shuffled data ≤ α=0.05 ± MC error |
| DoD-3 | `methodology/multiple_testing.py` | Family-aware FDR (A: 12, BH; B: 450, Benjamini-Yekutieli) |
| DoD-4 | `reporting/disagreement.py` | Każdy signal classified: 3/3, 2/3, 1/3, 0/3 |
| DoD-5 | `driftsim/calibration.py` | Adaptive watchlist zwraca None gdy DoD-1..4 fail |
| DoD-6 | `core/seeds.py` + SHA-256 manifest | Cold-machine re-run = bit-identical SHA-256 CSV |
