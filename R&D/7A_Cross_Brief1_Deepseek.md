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
AUDYT KRYTYCZNY — PROJECT_BRIEF.md (DriftScope)
Solo dev | RTX 3050 4GB | 32GB RAM | Win11 | Cel: portfolio + narzędzie

1. BŁĘDY FAKTYCZNE
#	Cytat z briefu	Problem	Dowód / kontrprzykład
F1	§3 Stack: "Numba JIT + joblib.Parallel" (bez zastrzeżenia)	Brief sam w PoC Results §12 udowadnia, że joblib nad pojedynczymi permutacjami jest 16x wolniejszy niż NumPy sequential. Poprawny wzorzec (joblib nad konfigami) nie jest opisany w §3.	PoC Results: *"Wariant B — NumPy + joblib per-perm ... 0.99s → 1 010 perms/s (16x wolniej niz A!)"*
F2	§6.1: "Permutation test (1 config × 10⁴ perms) ... 5–30 min"	Dla prostych statystyk (chi-squared, ADF) to przeszacowanie o 2–3 rzędy wielkości. PoC pokazuje: 10k permutacji = 0.23s (Numba) lub 0.63s (NumPy).	PoC Results: "NumPy seq (bez parallelism) ... ~0.0h (praktycznie chwila)"
F3	§3: "Numba 0.59.x"	PoC używa 0.65.1 z powodu numpy 2.x. Brief sam każe zaktualizować, ale nie zmienia pyproject.toml w briefie.	PoC Results: "Numba 0.65.1 zamiast 0.59.x z briefu — numpy 2.x wymaga nowszego numba"
F4	§4.3: Przepływ danych — "Lotto OpenAPI → ingestion/lotto_client.py"	Lotto OpenAPI nie istnieje publicznie (komercyjne API wymaga umowy, ToS często zabraniają publikacji). Brief w R11 przyznaje ryzyko ToS, ale pipeline zakłada to jako default.	R11: "Lotto API ToS violation — Legal — M" — ale brak fallbacku w głównym przepływie.
F5	§6.2: "Numba JIT na permutation kernel ... 10–50× speedup vs pure NumPy"	PoC pokazuje 2.71× (43k vs 15.9k perms/s). 10–50× to typowe dla operacji O(N²) z pętlami, nie dla prostego shuffle+statistic.	PoC Results: *"Numba JIT (1-core) ... 43 094 perms/s vs NumPy 15 879 perms/s = 2.71x"*
F6	§6.4: Fallback C — "scipy.stats analytic approximation" dla permutation test	To logiczny błąd: przybliżenie asymptotyczne nie zastępuje permutation testu, gdy H0 jest "exchangeability". Może dawać bardzo mylne p-values dla małych N lub skorelowanych danych. Brief traktuje to jako równorzędny fallback.	Brak cytatu z literatury — standardowe ostrzeżenie: "Asymptotic approximations may be highly anti-conservative under dependence" (Davison & Hinkley 1997).
2. SŁABE PUNKTY ARCHITEKTURY
2.1 Over-engineered: Numba dla prostych statystyk
Cytat: §3 — "Permutation engine: Numba JIT + joblib.Parallel"

Problem: PoC pokazuje, że NumPy sequential daje 15 879 perms/s, a Numba 43k perms/s. Dla 10k permutacji różnica = 0.4 sekundy. Zysk nie wart ryzyka (R8: Win11 compatibility, F12-style DLL issues). Numba dodaje:

Zależność z wąskim oknem wersji (numpy 2.x → Numba 0.65+)

@njit narzuca restrykcje (brak Python objects, brak debuggera)

Dłuższy czas importu (~0.5s)

Alternatywa: numpy.random.permutation + wektoryzacja. Dla MMD (gdzie faktycznie jest O(N²)) — wtedy Numba ma sens. Dla reszty — nie.

2.2 Over-engineered: DVC dla 1500 rekordów
Cytat: §4.1 — "artifacts/ ... DVC-tracked" i §6.5 — "DVC × SQLite — not diff-friendly"

Problem: Brief sam przyznaje, że DVC + SQLite to problem. Dla zbioru 1500 wierszy (raw_draws.parquet < 1 MB) i kilkuset MB cache'u permutacji, git lfs lub nawet zwykły git add wystarczy. DVC wprowadza:

Konieczność dvc pull przed każdym uruchomieniem

Ryzyko "detached HEAD" dla artifactów

Kolejny plik konfiguracyjny (dvc.yaml) do utrzymania

Alternatywa: git lfs dla plików >5 MB, pytest --regenerate do odtwarzania cache'u. Jeśli chodzi o reprodukowalność — wystarczy commitować seed i skrypt.

2.3 Under-engineered: Brak checkpointingu dla długich pipeline'ów
Cytat: §6.1 — "Full pipeline overnight ... 6–18 h"

Problem: Przy 18h biegu, awaria w godzinie 17 = utrata całego wyniku. Brief nie definiuje:

Checkpoint co N permutacji (zapisz częściowe SQLite)

Wznowienie po przerwaniu (resume z ostatniego seeda)

Heartbeat logging (czy pipeline w ogóle żyje)

Alternatywa: dask.distributed z fire_and_forget=False i periodic client.persist(). Ale dla prostej wersji: zapis po każdej konfiguracji + flag --resume-from.

2.4 Under-engineered: Brak incrementalnego przetwarzania dla nowych losowań
Cytat: §5 Krok 1 — "Pull all historical draws" i "Cadence: manual + wtorek/piątek wieczorem"

Problem: Po każdym nowym losowaniu (2x/tydzień) pipeline przebiegnie wszystkie testy od nowa (18h). Nikt nie będzie tego robił ręcznie co tydzień. Brak logiki "incremental update" — tylko nowe daty powinny być przetwarzane.

Alternatywa: last_processed_date w SQLite, pipeline tylko dla dat > last_processed. Dla testów change-point — re-run tylko od ostatniego znanego CP.

2.5 Niespójność: CPU-only vs załączony HARDWARE_PUSH_CATALOG
Cytat: §6.1 — "VRAM budget: N/A — pipeline CPU-only"

Problem: Brief załącza katalog w całości dedykowany optymalizacji AI/ML na GPU (RTX 3050, CUDA, TensorRT, quantization). Z 8 osi katalogu, tylko Oś 0 (Environment) i fragment Osi 7 (ONNX Runtime CPU) mają zastosowanie. Reszta to martwy ciężar kontekstowy dla LLM, który może sugerować niepotrzebne techniki (np. offloading, distillation).

Alternatywa: Usunąć załącznik lub dodać wyraźną sekcję "Katalog nie aplikuje — projekt CPU-only" na początku briefu.

3. LEPSZE ALTERNATYWY (dla każdego zarzutu)
Problem	Alternatywa	Uzasadnienie
Numba dla prostych statystyk (F5, 2.1)	NumPy + wektoryzacja, Numba tylko dla MMD (gdzie kernel matrix 500×500).	2.71× speedup nie wart ryzyka. Dla MMD różnica będzie większa (O(N²) vs O(N)), tam Numba ma sens.
DVC (2.2)	git lfs + pytest --regenerate	Dla 2 GB artifactów git-lfs wystarcza. Reprodukowalność przez pytest --randomly-seed=42.
Brak checkpointingu (2.3)	Zapis co 10% konfiguracji do SQLite + --resume w CLI.	18h → max 1.8h straty przy awarii.
Brak incremental update (2.4)	last_updated timestamp; pipeline różnicowy dla nowych dat.	2x/tydzień → 15 minut zamiast 18h.
HARDWARE_PUSH nieaplikowalny (2.5)	Usuń załącznik lub dodaj "ONLY SECTION 0 (Environment) APPLIES".	Eliminuje ryzyko, że LLM zaproponuje CUDA/offloading.
Lotto API może nie istnieć (F4)	Scraper ze statycznej strony (np. eurojackpotresults.com) + manual CSV jako primary.	API jest ryzykowne ToS-wise. Publiczne strony z historią są bezpieczniejsze.
Asymptotic fallback dla permutation (F6)	Usuń fallback C — zostaw tylko A (Numba) i B (NumPy).	Asymptotyczne p-values dla zależnych danych = kłamstwo.
4. BRAKUJĄCE ELEMENTY
#	Element	Dlaczego potrzebny	Propozycja
B1	Stop-loss / abort criteria	Projekt ma 10 tygodni, ale brak progu "project fails, archive and move on".	Jeśli w W5 (Decision Gate) power <30% dla planted signals → archiwizacja jako "negative result framework" i koniec.
B2	CI/CD pipeline dla testów (MVP, nie W10)	Portfolio bez CI to red flag dla rekrutera.	GitHub Actions: pytest + mypy + ruff na każdym pushu.
B3	Logging i monitoring	18h pipeline bez logów = czarna skrzynka.	structlog z zapisem do logs/pipeline_YYYYMMDD.jsonl; heartbeat co 5 minut.
B4	Disaster recovery dla API LOTTO	Jeśli API zniknie, projekt traci case study.	Dwa źródła: official API (jeśli działa) + scraped backup (codzienny cron).
B5	Testy end-to-end (nie tylko unit)	Brief ma testy per moduł, ale nie sprawdza, czy cli.py --full-pipeline przechodzi.	tests/test_e2e.py z mockowanym API i małym zbiorem (100 draws).
B6	Resource monitoring	Brief szacuje RAM/CPU, ale nie ma kodu, który to weryfikuje.	memory_profiler w tests/test_environment.py — fail jeśli >4 GB RAM.
5. UX / 10-SECOND HOOK — REALISTYCZNY CZY ROBI WRAŻENIE?
Cytat: "animowana 'permutation race' — dwie wertykalne osie obok siebie. Lewa: real EuroJackpot stream ... Prawa: shuffled version"

5.1 Realizm techniczny: ✅ działa
Plotly z frames i 1500 punktów → OK.

Eksport do HTML embed → OK.

15s pętla bez dźwięku → OK.

5.2 Czy zrobi wrażenie na recruiterze? ⚠️ średnio
Problem 1: Hook pokazuje, że detektor znajduje znane change-pointy (2014, 2022). Recruiter może pomyśleć: "Overfitting do dat, które autor znał przed uruchomieniem" — mimo że brief ma DoD-1b (blind detection). Ale hook tego nie pokazuje.

Problem 2: Recruiter z quant finance może zauważyć, że EuroJackpot to bardzo słaby test — proces jest de facto uniform (jak twierdzi brief). Jeśli detektor znajduje change-pointy tam, gdzie ich nie ma (2014 zmiana reguł euronumerów to prawdziwy change-point, więc OK), ale dla uniform processu detektor powinien nie znajdować niczego. Hook nie pokazuje false positive rate na uniform null.

Lepszy hook:

Trzy panele: (1) real EuroJackpot, (2) true uniform RNG (np. secrets.randbelow), (3) shuffled real.

Real pokazuje 2 change-pointy.

Uniform RNG pokazuje 0 change-pointów (z p-value >0.05).

Shuffled pokazuje 0.

Wtedy widać, że detektor nie halucynuje.

5.3 Ryzyko "scam framing" (R4)
Mimo 3-zdań disarmera w README, hook z loterią (nawet jako case study) może być triggerem dla rekruterów z firm etycznych (fintech, healthcare). Alternatywa: użyj innego case study jako domyślnego w hooku (np. NIST RNG test suite), a EuroJackpot jako "stretch goal" w dalszej części README.

6. RYZYKA — CZY SZACUNKI CZASOWE REALISTYCZNE?
6.1 Ogólna ocena: OPTIMISTYCZNE o ~30–50%
Cytat: §9 — "TOTAL MVP 132–266 h, realistyczne 188 h"

Dlaczego zbyt optymistyczne:

Czynnik	Brief zakłada	Realistyczne
Nauka Polars (nowy stack)	0 h (wzmianka o "type-safe", brak czasu na onboarding)	8–16 h (różnice w API vs pandas)
Numba debug na Win11	W1 sanity check (R8 — Low risk)	PoC działał, ale każda zmiana typu danych = crash. 4–8 h na debug.
DVC setup	dvc.yaml jako część W1	4–8 h (remote config, pipeline stages, .gitignore dance)
Quarto + Python chunks	"reproducible markdown" — zero czasu	4–8 h (setup, embedded Python, cross-platform paths)
mapie (conformal)	W6 — 20–28 h na "rigor layer"	Samo mapie może być 8 h, ale integracja z istniejącymi testami — kolejne 8 h.
Specification curve	Nowy koncept dla autora (Simonsohn 2020)	16–24 h (implementacja, testy, wizualizacja)
Cross-platform (Win/Linux)	Brak wzmianki	Jeśli kiedykolwiek trafi na GitHub Actions (Linux), ścieżki, line endings, Numba caching — 8–16 h.
Skorygowany szacunek: realistyczne 280–350 h (MVP). Dla 5h/dzień = 14–18 tygodni.

6.2 Ryzyko specyficzne dla sprzętu (RTX 3050 4GB)
Projekt jest CPU-only, więc GPU nieużywane. Jednak:

Ryzyko	Prawd.	Impact	Mitygacja
Numba JIT na i5-12500H (12C/16T) — throttling termiczny przy długim biegu	M	M	Monitor temp (psutil), zapis co 10%, przerwa jeśli >90°C
32GB RAM — OK, ale permutacje + SQLite + Polars mogą przekroczyć przy równoległości	L	M	joblib z max_nbytes=None dla shared memory, inaczej swap.
Win11 + Polars + Numba — konflikt z antywirusem (real-time scanning .pyc)	M	L	Dodaj repo do wykluczeń Windows Defender.
7. AUDYT KATALOGU (HARDWARE_PUSH_CATALOG.md)
7a) Czy zastosowano kompozycję spójną z katalogiem?
NIE — katalog dotyczy AI/ML na GPU, projekt jest CPU-only bez ML. Kompozycja jest niespójna:

Katalog zakłada model >1 GB, quantization, offloading, distillation. Brief: "modele <100 MB RAM, brak ML neural".

Katalog nie zawiera Numba, Polars, joblib — głównych technik briefu.

Jedyna wspólna oś to Oś 0 (Environment) — pin wersji, conda env, pre-flight test.

Wniosek: Załącznik jest wprowadzający w błąd — sugeruje, że projekt potrzebuje optymalizacji GPU, podczas gdy brief deklaruje CPU-only.

7b) Techniki HEAVILY relevantne, ale niezastosowane
Technika z katalogu	Dlaczego relevantna	Brak w briefie
Oś 0 — Pre-flight environment test	Brief ma test_environment.py — OK, ale nie testuje Numba na Win11 z numpy 2.x.	Dodaj test: import numba; numba.jit(lambda x: x+1)(1)
Oś 5 — Caching (vector DB)	Brief używa SQLite jako cache'u permutacji — to jest de facto "vector DB" dla statystyk.	Zastosowane (w formie uproszczonej).
Oś 6 — Build-time cloud (Colab/Kaggle)	DriftSim calibration (3–8 h) i permutation runs (18 h) mogą być uruchomione w chmurze, zwalniając laptop.	Brief wspomina Colab jako fallback, nie jako primary. Dla overnight runs Colab T4 może być szybszy niż i5-12500H (który throttluje).
Oś 7 — ONNX Runtime (CPU)	Dla MMD kernel matrix, ONNX może przyspieszyć (choć marginalnie).	Nie zastosowane.
7c) Techniki zastosowane, ale niepasujące
Technika z briefu	Dlaczego niepasująca do katalogu
Numba JIT	Katalog nie wymienia Numba — skupia się na PyTorch/TensorRT. Numba jest techniką CPU, nie "hardware push".
joblib.Parallel	Katalog ignoruje CPU parallelism — zakłada, że bottleneck to VRAM, nie CPU.
Polars	Katalog nie dotyczy dataframes.
DVC	Katalog nie ma sekcji o data versioning.
7d) Czy PoC Results uzasadniają dodaną złożoność?
NIE — PoC pokazuje, że NumPy sequential jest 0.06s na 1000 permutacji. Dla 10k permutacji to 0.6s. Numba daje 0.23s. Zysk 0.37 sekundy na konfigurację.

Dla 150 konfiguracji (szacunek z briefu: 50 numbers × 4 test families × 3 regimes = 600, ale część to H1, część MMD — przyjmijmy 150 MMD + 450 prostych):

Bez Numba: 450 × 0.6s = 4.5 min (dla prostych) + MMD (gdzie Numba ma sens) = może 2h.

Z Numba: 450 × 0.23s = 1.7 min.

Zysk = 3 minuty na całym pipeline'ie. Koszt: ryzyko kompatybilności, debug, dłuższy import.

Werdykt: Numba nie jest uzasadniona dla prostych statystyk. Dla MMD — tak (O(N²) kernel matrix). Brief powinien warunkowo stosować Numba tylko w k4_mmd.py.

7e) Failure modes z katalogu — które realnie zagrażają?
Failure mode	Czy zagraża?	Uzasadnienie
F9 — Colab session timeout	⚠️ Pośrednio	Brief nie używa Colab jako primary, ale jeśli ktoś uruchomi tam pipeline (z fallbacku) bez checkpointingu — straci pracę. Brief nie definiuje checkpointingu.
F10 — Build-time → runtime gap	✅ TAK	Brief używa DVC, SQLite, Parquet. Przy przenoszeniu z Win11 na GitHub Actions (Ubuntu) — ścieżki, line endings, binary SQLite mogą być różne. Brak testu cross-platform.
F12 — Driver/DLL Conflict	❌ NIE	Projekt nie używa CUDA, więc F12 nie dotyczy.
F5 — DirectML vs CUDA mismatch	❌ NIE	CPU-only.
F2 — Fragmentacja VRAM	❌ NIE	CPU-only.
8. SOURCE VERIFICATION (kompatybilność technik)
Twierdzenie z briefu	Weryfikacja	Status
"Numba functions są picklable jako wrapped Python" (§6.5 Composability)	Numba jitowane funkcje domyślnie nie są picklowalne. Działają z joblib tylko jeśli użyto @njit(cache=True) i funkcja nie ma closure. PoC użył delayed(run_all_perms) — zakładam, że to działało, ale nie ma gwarancji na wszystkich platformach.	⚠️ UNVERIFIED — wymaga testu: pickle.dumps(numba.jit(lambda x: x+1))
"Polars 1.x ... 5–30× szybsze niż pandas"	Potwierdzone w benchmarkach Polars (H2O.ai). Ale dotyczy operacji group-by/join na dużych danych (>1M wierszy). Dla 1500 wierszy różnica jest pomijalna.	✅ TRUE (ale irrelevant dla scale)
*"mapie 0.8.x ... sklearn-compatible"*	Dokumentacja mapie potwierdza zgodność z sklearn API.	✅ VERIFIED
"Quarto wykonuje Python chunks; Polars dla data prep"	Quarto 1.5+ wspiera Python przez jupyter kernel. Polars działa w Quarto.	✅ VERIFIED
"SQLite × parallel writes — WAL mode mandatory"	Dokumentacja SQLite: WAL pozwala na concurrent readers + jeden writer. Ale joblib.Parallel z backend='loky' może otworzyć wiele writerów → sqlite3.OperationalError. Brief zakłada "jeden writer pool, multiple readers" — ale nie implementuje tego.	⚠️ UNVERIFIED — wymaga testu z 4 writerami jednocześnie.
PODSUMOWANIE — TOP 3 KRYTYCZNE ZMIANY PRZED STARTEM
Usuń Numba dla prostych statystyk — zostaw tylko dla MMD (gdzie faktycznie jest O(N²)). Użyj NumPy sequential jako baseline. Zyskasz prostotę, stracisz 0.37s na konfigurację.

Zamień DVC na git-lfs + pytest --regenerate — DVC to overkill dla 2 GB, a brief sam przyznaje problem z SQLite + DVC.

Dodaj checkpointing i resume — 18h pipeline bez wznowienia po awarii to proszenie się o katastrofę. Zapisuj częściowe wyniki co 10% konfiguracji.

Usuń HARDWARE_PUSH_CATALOG z załączników lub dodaj wyraźną adnotację *"SEKCJA 0 (ENVIRONMENT) TYLKO — RESZTA NIE APLIKUJE (CPU-ONLY)"*.

Zweryfikuj Lotto API — zanim napiszesz lotto_client.py, sprawdź czy w ogóle istnieje publicznie. Przygotuj scraper jako fallback.

Decyzja: Brief jest dobry metodologicznie, ale over-engineered w stacku (Numba, DVC, SQLite jako cache) i optymistyczny czasowo. Po powyższych zmianach nadaje się do realizacji. W obecnej formie — ryzyko porzucenia w W3 z powodu frustracji narzędziami.