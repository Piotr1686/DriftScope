```
Druga (ostatnia) runda. Skup się na:
1. Czy zmiany z R1 są spójne i nie tworzą konfliktów?
2. Czy coś źle zaimplementowane (np. zmieniono model,
   ale nie zaktualizowano VRAM budgetu)?
3. Czy szacunki czasowe nadal realistyczne po zmianach?

NIE powtarzaj zarzutów z R1. NIE proponuj fundamentalnych zmian.
Format: zwięzły raport (max 100 linii).
```


ODPOWIEDŹ:
Raport konsystencji DriftScope v2.0 — Runda 2 (final)
1. Werdykt ogólny
Zmiany z R1 są w >95% spójne i konflikt-free. Usunięcie conformal p-values, wymiana SQLite→Parquet, 3-panel hook, family-aware FDR, KPSS restore, Disagreement Protocol oraz realistyczne Numba speedupy są konsekwentnie odzwierciedlone w stacku, architekturze, pipeline, DoD i risk register. Nie wykryto „dziur” typu „usunięto komponent, ale zostawiono jego zależność w innym module”.
2. Wykryte niespójności / niedociągnięcia (4 punkty)
Table
#	Lokalizacja	Problem	Waga
N1	§4.1 struktura katalogów vs §5 Krok 4 / Appendix A L2	W drzewie jest methodology/preregistration.md, ale brief wymaga versioning preregistration_v{N}.md + pole revision_reason. Brak spójności nazewnictwa.	Niska
N2	§5 Krok 5 vs §6.1 (DriftSim resource budget)	§5: „20 calibration scenarios per test per regime”. §6.1: „20 scenarios × 3 regimes”. To sugeruje 60 total, podczas gdy „per test” implikuje znacznie więcej (przy 3+ testach). Budget 3–8h może być niedoszacowany jeśli „per test” jest literalne.	Niska-Średnia
N3	§6.1 (Full pipeline overnight)	Szacunek 2–6h nie uwzględnia explicit czasu na reduce/merge Polars LazyFrame z shardów oraz family-aware FDR (Family B = 300 hyp). Przy 10⁴ permutacji × 3 regimes × 2 families merge może dodać 10–20 min, ale przy overnight to marginalne.	Niska
N4	§4.1 core/guards.py	W brief jest „~40 LOC”, ale w §3 Stack nie ma tego modułu w tabeli (brak wpisu w stacku). Nie jest to konflikt, ale brak explicit traceability.	Kosmetyczna
3. Compute / VRAM — spójność ze zmianami modelu
VRAM budget = N/A w §6.1 jest spójne z §0 (Osie 1–2, 4–7 nie aplikują, brak GPU) i z usunięciem mapie/conformal (nie wymagały GPU, ale ich usunięcie nie wpływa na VRAM).
Numba JIT selektywnie — w §3, §6.2, §6.4 fallback B, §8 R8 (Very Low) oraz §12 PoC wszystkie wskazują na ten sam model: JIT tylko tam gdzie profile >2×, z fallbackiem do pure NumPy. Brak sprzecznych sygnałów.
Parquet shards × joblib — w §3, §4.3, §6.2, §6.4, §6.5, §8 R14 wszędzie spójnie: zero-contention writes, deterministic hash via sorted CSV, SQLite relegowane tylko do metadata single-writer.
4. Szacunki czasowe — realistyczność po zmianach
Table
Tydzień	Zmiana vs v1.0	Ocena realistyczności
W0	+8h (nowy)	Scraper PoC + CSV + power preview. Realistyczne (scraper to <4h, reszta to notebook).
W1	+6h (24→30)	15+ modułów scaffolding + KPSS restore + Bayesian CP + test_environment.py. Napięte ale realistyczne (~4h/dzień).
W2	+4h (28→32)	5 concrete signals × 4 effect sizes + unit tests. OK — concrete definicje eliminują oscylację designu.
W3	+4h (28→32)	Kalibracja + pierwsze artefakty git-lfs. OK.
W4	+4h (20→24)	MMD + N=200 PoC. OK — empirical asymptotic check to ~4-6h sam w sobie.
W6	-4h (28→24)	Usunięcie mapie + spec curve ograniczona do 9 pkt + Storey tylko Family A. Realistyczne — netto prostszy scope.
W7	0 (24→24)	+disagreement.py + watchlist. OK — disagreement to ~4-6h jeśli H1/MMD już działają.
W8	0 (20→20)	Polish + webm + README. OK, ale render .webm (ffmpeg) + GitHub Pages deploy to 4-6h, reszta to docs.
Total MVP 210h — spójny ze wzrostem scope o W0 i konkretyzacją DriftSim, zrównoważonym optymalizacją W6. Dla MEDIUM tier i solo dev — realistyczny mid-range.
5. DoD — spójność ze zmianami R1
DoD-1b (blind CP): spójny z §5 Krok 3 i §7.1 W1.
DoD-2 (shuffle test): spójny z §5 Krok 6 i usunięciem within-draw permutations.
DoD-3 (family-aware FDR): spójny z §5 Krok 7 (Family A/B split) i §10.
DoD-4 (triangulation → complementary pillars): spójny z Disagreement Protocol w §5 Krok 9.1 i §4.1 disagreement.py.
DoD-6 (reproducibility): spójny z core/seeds.py, git-lfs, Parquet shards, hash CSV zamiast SQLite (fix v2.0 zastosowany w §10).
6. Rekomendacje (drobne, non-fundamental)
N1: Ujednolicić nazwę w §4.1 na preregistration_v1.md (lub dodać adnotację, że preregistration.md to symlink do aktualnej wersji).
N2: W §6.1 doprecyzować, czy „20 scenarios × 3 regimes” = 60 datasetów (shared across tests), czy per-test runs. Jeśli per-test, budget 3–8h może być tight.
N3: Dodać 15–30 min do §6.1 „Full pipeline” na Polars LazyFrame reduce z shardów — conservative estimate.
N4: Dodać core/guards.py do §3 Stack (kosmetyczne, ale zamyka traceability).
Podsumowanie: Brief jest gotowy do handoffu. Zmiany z R1 są wdrożone konsekwentnie, szacunki czasowe realistyczne, a compute policy spójna z CPU-only constraint.
