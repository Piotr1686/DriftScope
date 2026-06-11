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
- Język komentarzy w kodzie: polski
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
```
DriftScope/
├── pyproject.toml                    # PEP 621, single source of truth wersji
├── .env.example                      # 7 kluczy konfiguracyjnych
├── PROJECT_BRIEF.md                  # architectural contract
├── CLAUDE.md / MEMORY.md / last_session.md
├── poc_permutation_engine.py         # Krok 6 PoC (DONE 2026-05-17)
├── data/
│   └── seed/
│       └── eurojackpot_history.csv   # committed; Tier-1 fallback
├── scripts/
│   ├── smoke_test.py                 # deps import + CPU/GPU check + wersje
│   ├── archive.py                    # SHA-256 manifest generator (git-lfs)
│   └── manual_import.py              # CSV upload fallback (Tier-2)
├── docs/
│   ├── report.html                   # Quarto output (W8)
│   └── hook.webm                     # 10-second hook animation (W8)
├── notebooks/                        # exploratory — NIE part of pipeline
├── demo/
│   └── app.py                        # Streamlit app (W9+ stretch)
├── artifacts/                        # git-lfs tracked (*.parquet)
│   ├── raw_draws.parquet
│   ├── regime_{1,2,3}.parquet
│   ├── permutations/{test}/{regime}/worker_{id}.parquet
│   ├── driftsim_runs/
│   ├── calibration_curves/
│   └── artifacts_manifest.json
├── src/driftscope/
│   ├── __init__.py                   # __version__ = "0.1.0"
│   ├── cli.py                        # Typer entrypoint, --resume
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings (BASE_SEED, paths)
│   │   ├── types.py                  # DrawRecord, RegimeSpec, TestResult
│   │   ├── seeds.py                  # make_worker_seeds(base, n) → list[SeedSequence]
│   │   └── guards.py                 # @with_timeout, assert_memory_below
│   ├── ingestion/
│   │   ├── lotto_scraper.py          # httpx + selectolax + tenacity
│   │   └── regime_split.py           # 2014/2022 split → regime_{1,2,3}.parquet
│   ├── methodology/
│   │   ├── preregistration_v1.md     # SUPERSEDED przez v2 (history)
│   │   ├── preregistration_v2.md     # SUPERSEDED przez v3 (history)
│   │   ├── preregistration_v3.md     # SUPERSEDED przez v4 (history)
│   │   ├── preregistration_v4.md     # SUPERSEDED przez v5 (history)
│   │   ├── preregistration_v5.md     # SUPERSEDED przez v6 (history)
│   │   ├── preregistration_v6.md     # SUPERSEDED przez v7 (history)
│   │   ├── preregistration_v7.md     # ACTIVE — frozen choices + revision log
│   │   ├── cooccurrence.py           # test wspolwystapien par (§5c, curveball null)
│   │   ├── h1_classical.py           # ADF, KPSS, Bayesian CP, Welch, ACF
│   │   ├── k4_mmd.py                 # Gaussian RBF na freq vectors (Δ⁴⁹)
│   │   ├── permutation.py            # shuffle test + @njit(cache=True) hot loop
│   │   ├── block_bootstrap.py        # alternative null (block ∈ {5,10,20})
│   │   ├── multiple_testing.py       # Family A (12, BH) + Family B (450, Benjamini-Yekutieli)
│   │   ├── specification.py          # spec curve 9 points (3 windows × 3 bw)
│   │   └── recurrence.py             # gap test (perm-calibrated) + Nelson-Aalen + EVT (W6)
│   ├── driftsim/
│   │   ├── planted_signals.py        # 5 sygnały × 4 effect sizes = 20 scenarios
│   │   ├── null_uniform.py           # honest null generator (baseline)
│   │   └── calibration.py            # sensitivity/specificity curves
│   ├── reporting/
│   │   ├── plots_static.py           # matplotlib (paper + .webm export)
│   │   ├── plots_interactive.py      # Plotly (HTML w Quarto)
│   │   ├── disagreement.py           # Disagreement Protocol (3/3, 2/3, 1/3, 0/3)
│   │   └── report.qmd                # Quarto source
│   └── adaptive/
│       └── honest_watchlist.py       # TYLKO gdy DoD-1..5 pass; else None
└── tests/
    ├── conftest.py                   # pytest.approx defaults, seed fixtures
    ├── test_environment.py           # Numba + Win11 + numpy 2.x (Oś 0)
    ├── test_vram_invariants.py       # RAM budget niezmienniki (CPU-only)
    ├── test_h1_invariants.py         # ADF/KPSS/CP invariants
    ├── test_mmd_properties.py        # MMD properties + N=200 stability
    ├── test_permutation_null.py      # FPR ≤ α=0.05 ± MC error
    ├── test_driftsim_calibration.py  # planted signal detection
    ├── test_disagreement.py          # Disagreement Protocol logic
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
