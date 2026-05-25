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
DRIFTSCOPE — AUDYT ARCHITEKTURY & BRIEFU
Solo dev · RTX 3050 4GB · 32GB RAM · Win11 · 8–10 tygodni
1. BŁĘDY FAKTYCZNE
Każdy zarzut z cytatem z briefu + konkretna alternatywa
1.1. mapie użyte poza swoim paradygmatem
Cytat: „Conformal inference: mapie 0.8.x | Pure-Python, sklearn-compatible, Vovk-style conformal p-values” (§3 Stack)
Cytat: „Conformal p-values (Vovk, via mapie) jako uzupełnienie tradycyjnych p-values” (§5 Krok 8)
Problem: mapie implementuje conformal prediction (predykcja przedziałów/setów z gwarancją pokrycia), a nie testowanie hipotez o stacjonarności. „Vovk-style conformal p-values” w mapie to p-values w kontekście predykcji (monotoniczność, validity dla ML), nie testy statystyczne dla szeregów czasowych ani change-point detection. Nie istnieje w mapie moduł do testowania hipotez o jednorodności rozkładu czy stacjonarności.
Alternatywa: Usunąć mapie. Jeśli conformal testy są wymagane, zaimplementować ręcznie conformal test dla dwupróbkowego problemu (np. podstawowy split-CV z conformal p-values według Vovka 2005) lub zrezygnować z tego filaru — FDR + permutation test wystarczą.
1.2. Przestrzeń hipotez 600-testowa to metodologiczny nonsense
Cytat: „Hypothesis space explicit: 50 numbers × 4 test families × 3 regimes = 600 hipotez (pre-registered, no post-hoc additions)” (§5 Krok 7)
Problem: ADF, KPSS, Bayesian CP, Welch, ACF to testy szeregów czasowych (jedno- lub wielowymiarowych). Nie testują one „50 numbers” osobno — one testują cały strumień lub jego wycinek. „50 numbers” sugeruje testy zgodności (goodness-of-fit) per liczba (np. chi-squared czy binomial test), które nie są wymienione w H1. Mieszanie testów stacjonarności (time-series) z testami zgodności w jedną przestrzeń FDR jest błędne — testy ADF/CP na binarnym szeregu „czy padła liczba 1” są nieadekwatne, a FDR zakłada strukturę zależności, której tu nie da się sensownie modelować (suma częstości = 1, więc testy per liczba są silnie zależne).
Alternatywa: Rozdzielić na dwie niezależne rodziny:
Rodzina A (globalna): 1 szereg czasowy × 4 testy stacjonarności × 3 regimes = 12 hipotez.
Rodzina B (per-number): 50 liczb × 2 testy zgodności (chi-squared, exact binomial) × 3 regimes = 300 hipotez.
FDR osobno w każdej rodzinie.
1.3. SQLite hash jako miara reprodukowalności
Cytat: „Cold-machine re-run produces bit-identical SQLite hashes z committed seeds” (§10 DoD-6)
Problem: SQLite nie gwarantuje bit-identical plików przy tych samych danych. Różne wersje SQLite, stan auto_vacuum, alokacja wolnych stron (freelist), kolejność rowid mogą zmienić binarną reprezentację. Hashowanie pliku .sqlite to anty-pattern w reproducibility engineering.
Alternatywa: Eksportować wyniki do deterministycznego formatu (CSV lub Parquet z deterministic ORDER BY) i hashować zawartość logiczną (np. sha256 z posortowanych rekordów), nie plik binarny.
1.4. Within-draw permutations to operacja tożsamościowa
Cytat: „Within-draw permutations: 5!=120× dla głównych liczb, 2!=2× dla euronumerów — jako augmentation, NIE jako null” (§5 Krok 6)
Problem: EuroJackpot to sampling without replacement. Permutacja kolejności wylosowanych liczb w obrębie jednego losowania (np. [3,12,25] → [25,3,12]) nie zmienia zbioru wylosowanych liczb. W kontekście analizy częstości (która jest celem projektu) ta operacja jest tożsamościowa. Nie jest to augmentation, tylko redundantne przetasowanie etykiet w zbiorze.
Alternatywa: Usunąć. Jeśli augmentation potrzebne, użyć block bootstrap na poziomie strumienia losowań (zachowuje strukturę czasową).
1.5. Szacunki wydajności po PoC są nieinternalizowane
Cytat: „Numba JIT + joblib nad konfiguracjami | ~0.8h (konserwatywnie, overhead)” (PoC Results, tabela szacunkowa)
Cytat: „5–30 min per config” (§6.1 Resource budget)
Problem: PoC pokazuje 43 094 perms/s na 1 core (1000 perms w 0.02 s). Dla 150 konfiguracji × 10k perms = 1.5M perms. Na 12 rdzeniach to teoretycznie ~3–5 sekund plus overhead serializacji. Szacunek 0.8 h = 2880 s jest przeszacowany o rząd wielkości (~500–1000×). Autor nie internalizuje własnych wyników PoC.
Alternatywa: Zaktualizować tabelę:
Proste testy (chi-squared, ADF): <<1 min per config.
MMD z dużą macierzą kernelową: 5–30 min per config.
Rozdzielić szacunki per typ testu.
1.6. Nieaktualny wzorzec joblib w §6.2
Cytat: „Parallelism: Process pool nad permutation seeds | joblib.Parallel(backend='loky') | ~12× na 12 cores | ✓ Win11-safe” (§6.2 CPU Transcendence Stack)
Problem: PoC wyraźnie stwierdza: „Wariant B — NumPy + joblib per-perm ... 16x wolniej niz A! ... Wzorzec z pierwotnego briefu jest bledny”. Mimo to §6.2 wciąż promuje „process pool nad permutation seeds” jako zielony checkmark.
Alternatywa: Poprawić §6.2: „joblib.Parallel nad niezależnymi konfiguracjami (test_name, regime, kernel_config), NIGDY nad pojedynczymi permutacjami”.
1.7. Quarto jako zależność systemowa
Cytat: „Report: Quarto 1.5+ | Reproducible markdown→HTML/PDF” (§3 Stack)
Problem: Quarto to zewnętrzne narzędzie systemowe (poza PyPI), wymagające Pandoc, często TeX dla PDF, i na Windows ma historię problemów z PATH. Dla solo dev w 8 tygodni to jest zbędny single point of failure.
Alternatywa: Uczynić Jupyter + nbconvert primary (już jest w fallbackach w §6.4). Quarto jako Tier-2 opcjonalny na W9+ jeśli czas zostanie.
1.8. „Lotto OpenAPI” prawdopodobnie nie istnieje
Cytat: „Lotto OpenAPI ... Cache do raw_draws.parquet. Retry z exponential backoff (tenacity). API key z .env” (§5 Krok 1)
Problem: Nie istnieje publiczne, centralne REST API dla EuroJackpot z historycznymi danymi i kluczem API. Różne kraje (DE, PL, NL) publikują wyniki jako HTML/CSV scraping. Założenie istnienia „OpenAPI” z kluczem API blokuje start projektu.
Alternatywa: Przygotować gotowy CSV z historycznymi danymi (publicznie dostępne z eurojackpot.org, lotto.de) jako seed artifact. Dodać scraper (httpx + BeautifulSoup) jako backup. Usunąć LOTTO_API_KEY z .env.
2. SŁABE PUNKTY ARCHITEKTURY
2.1. Parquet + SQLite + DVC dla 1500 rekordów — architecture astronaut
Cytat: „Storage — raw/cleaned data: Parquet (pyarrow)”, „Storage — permutation results: SQLite”, „DVC 3.x” (§3 Stack)
Problem: 1500 losowań EuroJackpot to ~50 KB w CSV. Parquet to overkill. DVC dla <2 GB artifacts to overhead (setup, remote, lock files) przewyższający korzyści dla solo dev.
Alternatywa: CSV/JSON dla raw data (human-readable, git-friendly bez LFS). SQLite opcjonalnie tylko dla permutation cache jeśli przekroczy 100k rekordów. DVC usunąć — zastąpić artifacts/ w .gitignore + ręczne backupy.
2.2. Polars dla mikro-datasetu
Cytat: „Polars 1.x | Type-safe, ~5–30× szybsze niż pandas dla group-by/window ops, recruiter signal 'modern stack'” (§3 Stack)
Problem: Dla 1500 rekordów różnica Polars vs pandas to mikrosekundy vs milisekundy — niezauważalna. Polars wprowadza learning curve, problemy z interop (matplotlib, plotly, pytest fixtures) i „nowoczesny” kod, który recruiter i tak nie zauważy w 1500-wierszowym dataset.
Alternatywa: Pandas jako primary. Polars jako opcjonalny „stretch” w notebooks/ jeśli w przyszłości dane urosną (NIST RNG).
2.3. Pydantic + Typer + Streamlit + Quarto = stack creep
Cytat: „Config: Pydantic Settings v2 + .env”, „CLI: Typer 0.12.x”, „Interactive viz: Plotly + Streamlit”, „Report: Quarto 1.5+” (§3 Stack)
Problem: Rdzeń metodologiczny to ~300 LOC (Bayesian CP + MMD + permutation). Dodanie 5 frameworków/systemów zwiększa powierzchnię awarii i czas konfiguracji o 20–30% całego budżetu.
Alternatywa:
Config: dataclass + os.environ (20 LOC, zero deps).
CLI: argparse (stdlib, 30 LOC).
Streamlit: static Plotly HTML jako primary demo.
Quarto: Jupyter + nbconvert.
2.4. db/queries.py to nadmiarowa abstrakcja
Cytat: „db/queries.py zamiast Repository pattern (solo dev)” (§0 Flagi)
Problem: Nawet queries.py to unnecessary layer dla SQLite z 3 tabelami i solo dev. SQLAlchemy Core lub plain sqlite3 wystarczą.
Alternatywa: Usunąć warstwę db/. Użyć plain sqlite3 w methodology/permutation.py (zapis wyników) lub CSV sharded per config.
2.5. MMD z RBF na danych kategorycznych
Cytat: „Gaussian RBF + polynomial kernels. Sliding window N=200 kontra DriftSim baseline” (§5 Krok 4)
Problem: MMD z RBF kernel zakłada przestrzeń metryczną R 
d
  . Liczby lotto (1–50) to etykiety kategoryczne — porządek liczb nie ma znaczenia fizycznego (7 nie jest „bliżej” 8 niż 49). „Median heuristic” dla bandwidth na kategorycznych danych jest pozbawiony sensu.
Alternatywa: Użyć kernela dla danych kategorycznych (np. Hamming kernel dla zbiorów 5 liczb, Jaccard kernel) lub zrezygnować z MMD na rzecz testów permutacyjnych na poziomie strumienia (np. chi-squared sliding window z permutation null).
2.6. Triangulation bez wspólnego celu pomiaru
Cytat: „DoD-4: Cross-architecture consistency | H1 ↔ MMD ↔ DriftSim triangulation | Każdy reported signal widziany przez ≥2 z 3 filarów” (§10)
Problem: H1 testuje stacjonarność w czasie (czy parametry procesu się zmieniają). MMD to two-sample test (czy dwa fragmenty mają ten sam rozkład). DriftSim to generator danych. To są trzy ortogonalne rzeczy. MMD wykrywa różnicę rozkładów między reżimami, ale nie „stacjonarność” w sensie H1. Triangulation wymaga pomiaru tego samego zjawiska różnymi metodami.
Alternatywa: Zdefiniować jasno:
H1: stacjonarność strumienia w czasie.
MMD: homogeniczność rozkładów między reżimami (inna hipoteza).
DriftSim: kalibracja czułości detektora.
Nie nazywać tego „triangulation” — to są komplementarne, nie redundantne filary.
2.7. SQLite concurrent writes bez mechanizmu synchronizacji
Cytat: „SQLite × parallel writes | ⚠️ | WAL mode mandatory; jeden writer pool, multiple readers. Schemat zaprojektowany pod append-only.” (§6.5 Composability)
Problem: Brief wspomina „jeden writer pool”, ale nie ma takiego modułu w architekturze (db/ ma tylko schema.sql i queries.py). Przy joblib.Parallel z 12 procesami każdy próbujący INSERT do SQLite, nawet z WAL, wystąpią „database is locked” błędy. SQLite obsługuje dokładnie jednego writera.
Alternatywa: Użyć JSONL per process (każdy proces zapisuje do własnego pliku) + merge na końcu. Lub zaimplementować multiprocessing.Queue z dedykowanym writer procesem.
3. LEPSZE ALTERNATYWY
(Streszczenie z powyższego, posegregowane priorytetem)
Table
Priorytet	Element	Obecny stan	Alternatywa
P0	mapie / conformal	Źle użyty	Usunąć. Zastąpić BH-FDR + Bonferroni sanity.
P0	Przestrzeń 600 hipotez	Nonsens metodologiczny	Rozdzielić: 12 hipotez globalnych + 300 per-number. FDR osobno.
P0	SQLite hash	Anty-pattern	Hashuj zawartość logiczną (CSV), nie plik binarny.
P1	Parquet/DVC/Polars	Overkill dla 1500 rows	CSV + pandas. DVC → .gitignore.
P1	Pydantic/Typer/Quarto	Stack creep	dataclass/argparse/Jupyter.
P1	MMD RBF	Nieadekwatny kernel	Hamming/Jaccard kernel lub chi-squared sliding window.
P2	Within-draw perm	Operacja tożsamościowa	Usunąć. Block bootstrap jako sanity.
P2	Quarto primary	Zewnętrzny dep	Jupyter + nbconvert primary.
P2	„Lotto OpenAPI”	Prawdopodobnie nie istnieje	Gotowy CSV + scraper backup.
4. BRAKUJĄCE ELEMENTY
4.1. Model generatywny dla Bayesian CP
Cytat: „Bayesian online CP (Adams-MacKay 2007, own impl) ~150 LOC” (§3 Stack)
Brak: BCPD wymaga modelu generatywnego p(x 
t
​
 ∣θ) . Dla lotto (5 z 50 bez zwracania + 2 z 12) nie jest to trywialne — czy model to Multinomial dla częstości? Czy Hypergeometric dla całych losowań? Czy 50 niezależnych Bernoulli? Decyzja wpływa na całą metodologię.
Dodać: Sekcję w methodology/preregistration.md z definicją modelu (np. Dirichlet-Multinomial dla częstości).
4.2. Pre-computed power analysis
Cytat: „Statistical power <30% dla subtle signals przy n=1500” (§8 Risk Register)
Brak: Nie ma oszacowania mocy dla konkretnego testu i efektu przed W1. Przy n=1500  i zmianie p=0.1→0.11  — czy chi-squared to wykryje? To trzeba wiedzieć przed napisaniem kodu.
Dodać: Analytic power analysis (np. statsmodels.stats.power) lub krótka symulacja w W0 (przed W1).
4.3. Definicja 5 planted signals
Cytat: „5 planted patterns × 4 effect sizes” (§5 Krok 5)
Brak: Nie ma listy wzorców. Bez tej listy W2-W3 nie mogą ruszyć.
Dodać: Definicje: (1) zmiana p  jednej liczby, (2) autokorelacja w czasie, (3) trend liniowy w częstościach, (4) sezonowość (np. cykl tygodniowy), (5) zmiana korelacji między liczbami.
4.4. Negative result artifact
Cytat: „Negative result framing first-class — README mówi explicit 'if no signal found, this is also a result'” (§5 Krok 9)
Brak: Nie ma planu jak zaprezentować negative result jako wartościowy. Samo zdanie w README to za mało dla recruitera.
Dodać: Sekcję w raporcie: „Power Analysis & Detection Limits” z wykresem power vs effect size z DriftSim pokazującym, że n=1500  nie wystarcza dla efektów <5% .
4.5. Moduł block bootstrap
Cytat: „Block bootstrap — alternative null zachowujący krótkozasięgowe korelacje” (§5 Krok 6)
Brak: Wzmianka w pipeline, ale brak w strukturze katalogów (methodology/ nie zawiera block_bootstrap.py).
Dodać: methodology/block_bootstrap.py lub usunąć z pipeline jeśli out of scope.
5. UX / 10-SECOND HOOK
5.1. Animacja Plotly to over-investment
Cytat: „Pierwszy element widoczny w viewport: animowana 'permutation race' — dwie wertykalne osie... 15-sekundowa pętla, autoplay, no sound” (§2)
Problem: Plotly z >500 frames często zacina się w przeglądarkach. Stworzenie płynnej animacji z dwoma panelami, licznikiem p-value i 1500 punktami to 4–8 h pracy dla efektu „gimmick”. Dla recruitera quant/research ważniejszy jest rigor niż animacja lotto.
Alternatywa: Statyczny obraz: scatter timeline + histogram p-value z shuffled data. GIF z 5 klatkami (matplotlib.animation) zamiast interaktywnego Plotly. Oszczędność: 6h.
5.2. Risk „lotto-scam” jest realny i niewystarczająco zaadresowany
Cytat: „3-sentence disarmer w README; methodological category framing; no emojis/casual tone” (§8 Risk R4)
Problem: Nawet z disarmerem, flagship case study = lotto to instant red flag dla części recruiterów. Animacja lotto wzmacnia to wrażenie.
Alternatywa: Zmienić 10-second hook na DriftSim calibration curve (power vs effect size) jako pierwszy obrazek. EuroJackpot wspomnieć dopiero w sekcji „Case Studies”. Framing: „Framework for calibrating stationarity detectors”, nie „Lotto audit”.
5.3. Streamlit demo na HF Spaces — ryzyko timeout
Cytat: „Streamlit dla HF Spaces demo” (§3 Stack)
Problem: HF Spaces free tier = CPU + 2GB RAM. Permutation test czy DriftSim w Streamlit może timeoutować przy 10k perms.
Alternatywa: Static HTML report z embedded Plotly jako primary demo. Streamlit tylko jako „interactive explorer” jeśli czas zostanie na W9.
6. RYZYKA — CZY SZACUNKI SĄ REALISTYCZNE?
6.1. W1 optymistyczny o ~50%
Cytat: „W1 — Env + H1 core + DoD-1: Min 16h | Realistic 24h | Max 32h” (§9)
Problem: Scaffolding 15+ modułów, pyproject.toml, test_environment.py, Numba sanity, ADF, Bayesian CP 150 LOC z testami, DoD-1b blind detection (wymaga gotowych danych). To realistycznie 30–40 h, nie 24h.
Mitigation: Dodać W0 (data acquisition + EDA, 8h) przed W1. Albo zwiększyć W1 do 32h realistic.
6.2. W6 to potencjalny sinkhole
Cytat: „W6 — Rigor layer: Min 20h | Realistic 28h | Max 40h | mapie + specification curve = nowy material” (§9)
Problem: mapie nie pasuje (Błąd 1.1). Spec curve dla 600 hipotez to explosion kombinatoryczny. Storey q-values przy wszystkich nullach są niestabilne. To może pożreć 40h+ i dać nieopublikowalne wyniki.
Mitigation: Uprościć W6: BH-FDR + Bonferroni sanity. Usunąć mapie. Spec curve tylko dla głównych parametrów (window size, bandwidth), nie dla wszystkich hipotez.
6.3. W8–W10 = scope creep
Cytat: „W8: Polish MVP | W9: Portfolio polish | W10: OS readiness” (§7.1)
Problem: 3 tygodnie „polish” przy 8-tygodniowym MVP to 37% budżetu na niekrytyczne rzeczy. CI/CD, CONTRIBUTING.md, semver dla projektu z 1 dev to overhead.
Mitigation: Połączyć W8–W9 w 1 tydzień. W10 jako post-MVP stretch (opcjonalny).
6.4. Plan B to trudniejszy cel niż Plan A
Cytat: „Plan B jest zawsze akceptowalny... framework for measuring detector hallucination rates” (§7.3)
Problem: Jeśli detektory nie wykrywają planted signals (prawdopodobne przy n=1500 ), to „framework for measuring hallucination rates” wymaga udowodnienia, że dane są null i że FPR jest kontrolowany. To jest metodologicznie trudniejsze niż wykrycie sygnału.
Mitigation: Zaakceptować Plan B jako primary goal. Skalibrować detektor na DriftSim tak, aby FPR był kontrolowany — to jest wynik. Positive result to bonus.
7. AUDYT KATALOGU HARDWARE
Cytat: „HARDWARE_PUSH_CATALOG.md formalnie nie aplikuje (CPU-only, modele <100 MB RAM, brak ML neural)” (§0)
7a. Czy zastosowano kompozycję spójną z katalogiem?
Werdykt: Katalog nie aplikuje — słuszna decyzja briefu. Projekt to klasyczna statystyka (NumPy/SciPy), nie AI/ML. Jedyna technika z katalogu zastosowana sensownie to Numba JIT (analog Osi 3 — Compilation/JIT dla CPU).
7b. Techniki HEAVILY relevantne, ale niezastosowane?
Werdykt: Brak. Projekt nie używa GPU, modeli neuronowych, kwantyzacji, offloadingu. Katalog nie ma tu zastosowania.
7c. Techniki zastosowane, ale niepasujące?
Werdykt: mapie (Oś 7 / Oś 4 okolicznościowo) — biblioteka ML do conformal prediction, użyta w projekcie statystycznym poza swoim paradygmatem. To jedyny „wyciek” ML-stacku do statystyki.
7d. Czy PoC Results uzasadniają dodaną złożoność?
Werdykt: PoC uzasadniają Numba JIT i pokazują, że pipeline jest szybki. Nie uzasadniają: Polars, DVC, Quarto, Streamlit, Pydantic, Typer, SQLite jako primary. Te są dodane dla „recruiter signal” lub „template compliance”, nie dla potrzeb obliczeniowych.
7e. Failure modes z katalogu — które realnie zagrażają?
Table
Failure Mode	Zagraża?	Uzasadnienie
F9 — Colab timeout w trakcie DriftSim	TAK	Jeśli DriftSim na Colab Free bez checkpointów co 30 min.
F10 — Build-time → runtime gap	TAK	DVC + Quarto + SQLite mogą mieć różne wersje na Colab vs lokalnie.
F12 — Driver/DLL Conflict	NIE	Brak CUDA/CuDNN w pipeline.
F3, F5, F11	NIE	Brak PyTorch modeli, TensorRT, DirectML.
8. SOURCE VERIFICATION
Table
Twierdzenie w briefu	Status	Uzasadnienie / Link
*„Numba JIT × joblib.Parallel	✓	Numba functions są picklable; loky backend OK”* (§6.5)	⚠️ UNVERIFIED — needs PoC test	Numba z cache=True na Windows + spawn może mieć problemy z pickle. Wymaga testu w W1.
*„SQLite × parallel writes	⚠️	WAL mode mandatory; jeden writer pool”* (§6.5)	⚠️ UNVERIFIED — needs PoC test	WAL pozwala na concurrent reads, ale nie concurrent writes. „Jeden writer pool” wymaga implementacji, której nie ma w architekturze.
*„mapie × statsmodels	✓	Mapie jest sklearn-compatible; integration via numpy arrays”* (§6.5)	⚠️ UNVERIFIED — needs PoC test	Technicznie prawda, ale nie uzasadnia użycia w kontekście testowania hipotez.
*„Quarto × Polars	✓	Quarto wykonuje Python chunks; Polars dla data prep”* (§6.5)	✓ Community-confirmed	Quarto obsługuje Python via Jupyter engine.
„ruptures 1.1.9+ — najszerszy zestaw algorithmów CP w Pythonie” (§3)	✓ Community-confirmed	ruptures dokumentuje PELT, Binseg, CUSUM, etc.
„Adams-MacKay 2007 ~150 LOC” (§3)	⚠️ UNVERIFIED — needs PoC test	Brak publicznego PoC w briefie. 150 LOC to zaniżony szacunek jeśli model generatywny dla danych dyskretnych ma być poprawny.
„Polars 1.x ~5–30× szybsze niż pandas” (§3)	✓ Community-confirmed	Benchmarky Polars (docs.pola.rs) potwierdzają.
„DVC > git-LFS dla rigor signal” (§3)	⚠️ UNVERIFIED — needs PoC test	Dla <2GB git-LFS wystarcza. DVC ma overhead setupu nieproporcjonalny do korzyści.
„EuroJackpot z dwoma znanymi change-pointami 2014/2022” (§1)	⚠️ UNVERIFIED — needs source	Wymaga weryfikacji dat zmiany reguł EuroJackpot w oficjalnych źródłach (eurojackpot.org, lotto.de).
„Storey q-values jako secondary cross-check” (§5 Krok 7)	⚠️ UNVERIFIED — needs PoC test	Storey wymaga estymacji π 
0
​
  , niestabilnej przy 600 testach i wszystkich nullach. Brak parametru lambda w briefie.
PODSUMOWANIE WYKONAWCZE
Table
Kategoria	Liczba zarzutów	Priorytet P0
Błędy faktyczne	8	4 (mapie, 600 hipotez, SQLite hash, within-draw perm)
Słabe punkty architektury	7	2 (MMD RBF, SQLite writes)
Brakujące elementy	5	2 (model generatywny, power analysis)
Ryzyka czasowe	4	1 (W6 sinkhole)
Najbardziej palące:
Usunąć mapie i conformal p-values — to błąd kategoryczny.
Naprawić przestrzeń hipotez — 600 testów to nonsense metodologiczny.
Uprościć stack — CSV zamiast Parquet/DVC, pandas zamiast Polars, argparse zamiast Typer, Jupyter zamiast Quarto (primary).
Zmienić 10-second hook z animacji lotto na wykres kalibracji DriftSim — uniknie „scam vibe”.
Czy brief jest gotowy do handoffu?
Nie. Wymaga poprawki P0-P1 (zwłaszcza §3 Stack, §5 Krok 6-8, §10 DoD) przed napisaniem pierwszej linii kodu. Obecna wersja prowadzi do 20–30% czasu zmarnowanego na naprawę błędnych założeń w tygodniach 4–6.