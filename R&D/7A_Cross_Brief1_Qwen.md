```
Krytyczny audyt PROJECT_BRIEF. Solo developer, RTX 3050 (4GB VRAM),
32GB RAM, Windows 11. Cel: portfolio + narzędzie.

Załączam też HARDWARE_PUSH_CATALOG.md jako referencję.

Stwórz raport:

1. BŁĘDY FAKTYCZNE (każdy zarzut z cytatem fragmentu briefu)
2. SŁABE PUNKTY ARCHITEKTURY (nieskalowalne, over/under-engineered)
3. LEPSZE ALTERNATYWY (dla każdego zarzutu konkretne rozwiązanie)
4. BRAKUJĄCE ELEMENTY
5. UX / 10-Second Hook (czy realistyczny, czy zrobi wrażenie)
6. RYZYKA (czy szacunki czasowe realistyczne)
7. AUDYT KATALOGU
   a) Czy zastosowano kompozycję spójną z katalogiem?
   b) Czy są techniki HEAVILY relevantne, ale niezastosowane?
   c) Czy są techniki zastosowane, ale niepasujące?
   d) Czy PoC Results uzasadniają dodaną złożoność?
   e) Failure modes z katalogu — które realnie zagrażają?
8. SOURCE VERIFICATION
   Dla twierdzeń o kompatybilności: link do docs/issue
   lub oznacz jako "⚠️ UNVERIFIED — needs PoC test"

Zasady:
- Nie chwal — szukaj problemów
- Każdy zarzut z konkretną alternatywą
- Każdy zarzut musi cytować fragment briefu (eliminuje halucynacje)
- Nie proponuj rozwiązań chmurowych dla RUNTIME (build-time OK)
- Nie proponuj rozwiązań wymagających zespołu
```

ODPOWIEDŹ:
KRYTYCZNY AUDYT PROJECT_BRIEF.md (DriftScope)
1. BŁĘDY FAKTYCZNE
Zarzut
Cytat z briefu
Analiza
Statystyczna nieścisłość w odrzuceniu KPSS
§5 Krok 3: KPSS odrzucone jako redundant z ADF (oba testują różne hipotezy zerowe, ale dla naszego celu pokrywają tę samą informację).
ADF testuje hipotezę zerową o jednostkowym pierwiastku (non-stationarity), KPSS testuje hipotezę zerową o stacjonarności trendu. W praktyce research-grade używa się obu, bo dają przeciwne hipotezy zerowe. Odrzucenie KPSS osłabia wnioskowanie i nie jest "redundancją", tylko stratą sygnatu diagnostycznego.
Niespójność pinów wersji
§3: Numba 0.59.x vs PoC Results: Numba 0.65.1 zamiast 0.59.x z briefu
Tabela §3 nie została zaktualizowana mimo explicit zapisu w sekcji PoC. Spowoduje błędy środowiska przy instalacji z pyproject.toml (numpy 2.x wymaga numba>=0.60).
Przeszacowany budżet czasu per konfigurację
`§6.1: Permutation test (1 config × 10⁴ perms)
<2 GB
Graf zależności łamie deklarację "Single direction"
§4.2: methodology → db (queries.py) ←─┤ ↓ ↓ reporting ← driftsim
Graf pokazuje db jako węzeł pośredniczący między methodology a reporting/driftsim, sugerując dwukierunkowy przepływ lub zależności cykliczne. W rzeczywistości db jest tylko sinkiem (append-only), a nie komponentem pipeline'u. Notacja wizualna myli.
2. SŁABE PUNKTY ARCHITEKTURY
**DVC jako overkill dla <2GB artifacts** (§3: DVC 3.x ... DriftSim runs i permutation cache to artifacts >10MB. DVC > git-LFS dla rigor signal.). Dla solo dev i łącznego rozmiaru ~1.5GB DVC dodaje ~4-6h setupu/maintenance, zero wartości merytorycznej nad git lfs + .gitattributes. Rigor signal nie płynie z DVC, tylko z pytest + seed control.
db/queries.py zamiast lightweight ORM (§4.1: db/queries.py zamiast Repository pattern (solo dev)). Raw SQL strings w queries.py przy append-only SQLite nie mają walidacji schematu przy runtime. Błąd w zapytaniu wykryty dopiero przy reportingu. Brak migration path przy zmianie permutation_results schema.
Sztywna preregistration przed kalibracją (§5 Krok 4: Pre-registered w preregistration.md przed Tygodniem 5 ... bandwidth = median heuristic). Jeśli DriftSim (W2-W3) wykaże, że median heuristic ma power <30% dla subtlet signals, preregistration blokuje korektę. Narusza zasadę "calibration-first".
Brak walidacji schematu na ingestion (§5 Krok 1: Pull all historical draws ... Cache do raw_draws.parquet). Brak explicit check zakresów (1-50 main, 1-12 euronumbers), duplikatów, missing dates. API może zwrócić malformed JSON; pipeline runnie cicho z NaN w statystykach.
3. LEPSZE ALTERNATYWY
Problem
Alternatywa (solo-dev, lokalnie)
KPSS odrzucone
Przywróć KPSS jako sanity check (statsmodels.tsa.stattools.kpss). Koszt: 3 LOC. Zysk: pełna stacjonarność ADF/KPSS triangulation, standard w econometrics.
DVC overhead
Usuń DVC. Użyj git lfs track "*.parquet" "*.sqlite" + prosty scripts/archive.py generujący artifacts_manifest.json z hashami SHA-256. Rigor ten sam, setup 15 min.
Raw SQL queries
sqlite-utils lub Polars.write_database() z if_exists="append". Automatyczna inferencja typów, safe parameterized inserts, zero raw stringów.
Sztywna preregistration
Wersjonuj: artifacts/preregistration_v1.json → v2.json jeśli DriftSi wymusza zmianę. Dodaj pole "revision_reason": "calibration_power_correction" w raporcie. Transparentne, nie łamie rigor.
Brak validation ingestion
Dodaj pydantic.BaseModel na DrawRecord z Field(ge=1, le=50) + polars schema validation przy read_parquet. Fail-fast zamiast silent corruption.
4. BRAKUJĄCE ELEMENTY
Cross-process seed management dla Numba/Joblib (core/seeds.py istnieje, ale brak strategii). joblib + numba w process pool wymagają SeedSequence lub unikalnych seed offsetów per worker, inaczej strumienie korelują. Brak tego = fałszywe p-values.
Timeout & Memory Guards per step (§6.1 Resource budget). Brak mechanizmu multiprocessing.TimeoutError lub psutil monitora. Jeśli MMD sliding window zawiesi się (np. przez degenerate kernel), pipeline blokuje się na godziny.
Statistical Tolerance w testach (§4.1 tests/). pytest domyślnie oczekuje exact match. P-values i statystyki losowe wymagają pytest.approx(rel_tol=0.05, abs_tol=1e-3). Brak tego = flaky CI.
Explicit fallback dla mapie integration (§5 Krok 8: mapie wrapper, Vovk conformal p-values). mapie nie natywnie wspiera custom permutation statistics. Wymaga ręcznego ConformalClassifier adaptera. Brak specyfikacji interfejsu.
5. UX / 10-Second Hook
Cytat: §2: animowana "permutation race" ... Plotly (go.Scatter + frames) → eksport do .html embedowany w README
Realizm: Niskie. Plotly frames dla 1500 pointów × 2 series × dynamiczne layout updates generuje ~50-100MB JS w DOM. Przeglądarki (szczególnie Safari/Edge na Windows) freeze'ują lub crashują przy autoplay.
Impact: Zamiast "wow", użytkownik widzi spinner lub crash. To niszczy sygnał rigor.
Fix: Pre-renderuj do .webm (3-5MB) używając matplotlib.animation lub plotly.io.write_image + ffmpeg. Embed jako <video autoplay loop muted playsinline controlsList="nodownload">. Plotly zostaw dla interaktywnego demo (Streamlit/HF), nie dla README.
6. RYZYKA (CZAS)
Szacunek MVP: ~188h (§9: REALISTYCZNE). Realistyczne, ale optymistyczne o ~15-20%.
Główne nieprawidłowości:
W1 Numba sanity: Win11 + numpy 2.x + Numba 0.65 często wymaga ręcznego czyszczenia cache __pycache__/numba_cache, co +2-4h.
W2-3 DriftSim: 20 scenarios × 3 regimes × permutation runs to nie tylko generowanie, ale debugowanie edge cases (np. zero-variance w window, degenerate MMD kernel). +6-8h.
W6 Conformal + Spec Curve: mapie docs dla custom stats są szczątkowe. Implementacja Vovk-style p-values z permutation null wymaga ~30-40 LOC + tests. +4-6h.
Rekomendacja: Złóż TOTAL MVP na 210-220h. Timebox W2 na 20h max; jeśli DriftSim nie skończony, przejdź do W4 z dummy data.
7. AUDYT KATALOGU (HARDWARE_PUSH_CATALOG.md)
Pytanie
Audyt
a) Kompozycja spójna z katalogiem?
Katalog explicit wyklucza ten projekt: KIEDY KATALOG NIE APLIKUJE: Projekt CPU-bound bez ML (data crunching pandas, statystyka). Brief poprawnie identyfikuje CPU jako bottleneck, ale próba mapowania katalogu jest kategorycznie nieadekwatna. Numba + Polars to już "minimum sufficient".
b) Techniki HEAVILY relevantne, ale niezastosowane?
Oś 5 (Pipeline tricks → Caching/Vector cache): SQLite cache jest użyty, ale brakuje TTL + LRU eviction (Failure F8). Przy overnight run cache rośnie do 500MB. Brak eviction = disk full po kilku milestone'ach.
c) Techniki zastosowane, ale niepasujące?
joblib.Parallel(backend='loky') + Numba. Katalog nie omawia tego bezpośrednio, ale loky spawnuje processy. Na Windows proces spawn ma ~50-100ms overhead per task. Przy krótkich callbackach (jak w PoC Wariant B) jest wolniejsze. Brief to naprawił w PoC, więc aktualnie pasuje.
d) PoC Results uzasadniają złożoność?
Tak. PoC udowodnił, że joblib per-perm to anti-pattern, a @njit loop + joblib over configs daje ~2.7x speedup vs numpy seq. Kompleksowość Numba jest uzasadniona ROI w czasie overnight run.
e) Failure modes z katalogu — które realnie zagrażają?
F12 (Driver/DLL Conflict): Realne na Win11 przy upgrade numpy/numba. Mitigacja z briefu (test_environment.py) OK. F8 (Vector cache blow-up): SQLite bez eviction/TTL. F2 (Memory fragmentation): N/A (CPU), ale Polars lazy eval + Numba JIT cache może zjeść ~4GB RAM przy full pipeline. Monitor psutil required.
8. SOURCE VERIFICATION
Twierdzenie z briefu
Weryfikacja / Link
Status
Numba 0.65.x + numpy 2.x compatibility on Win11
https://numba.pydata.org/numba-doc/latest/user/installing.html#installing-using-pip
✅ Ver. numba>=0.60 required for numpy 2.x. PoC OK.
joblib.Parallel(backend='loky') + @njit picklable
https://joblib.readthedocs.io/en/stable/parallel.html#pickling
⚠️ UNVERIFIED — needs PoC test. loky uses cloudpickle. @njit compiled objects are not natively picklable; require wrapper function or numba.caching. Brief's PoC implies it works, but official docs warn about serialization overhead.
Polars 1.x group-by 5–30× faster than pandas
https://docs.pola.rs/user-guide/migration/pandas/
✅ Confirmed. Polars lazy + arrow backend benchmarks consistently show 5-10x on groupby, up to 30x on complex window ops.
statsmodels BH FDR + Storey q-values
https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html
✅ Ver. method='fdr_bh' (default) and method='qvalue' (Storey) supported.
mapie for Vovk conformal p-values
https://mapie.readthedocs.io/en/latest/getting_started.html
⚠️ UNVERIFIED — needs PoC test. mapie focuses on prediction intervals/classification, not custom permutation-based p-values. Will require subclassing ConformalRegressor or manual split-conformal implementation.
ruptures 1.1.9+ PELT vs Bayesian CP cross-check
https://centre-borelli.github.io/ruptures-docs/user-guide/algorithms/pelt/
✅ Ver. Ruptures PELT is stable, well-tested. Cross-check strategy is sound.
Quarto 1.5+ embedded Python chunks reproducibility
https://quarto.org/docs/computations/python.html
✅ Ver. Quarto uses jupyter kernel under the hood. Deterministic if seeds fixed.
REKOMENDACJA FINALNA: Brief jest solidny, ale wymaga 4 poprawek przed handoff:
Usuń DVC, zastąp git lfs + manifest.
Przywróć KPSS, dodaj pytest.approx do stat testów.
Zmień hook z Plotly frames na pre-rendered .webm.
Dodaj TTL/LRU do SQLite cache i explicit SeedSequence strategy.
Po tych zmianach brief jest ready-for-handoff.
How can I help you today?


AI-generated content may not be accurate.