# last_session.md

**Sesja:** 2026-06-07 · ~21:00-22:30
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 0e04caf @ master (origin zsynchronizowany; state commity 33a71d6→… lokalne)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Zaplanować + zaimplementować Multi Multi (20/80) jako DRUGĄ grę — „second real-world case
study: large-alphabet, high-frequency NEGATIVE control + scale stress-test".** Decyzja gry
zamknięta (research zmian reguł — zob. MEMORY.md [2026-06-07 sesja 3]): MM wybrane (alfabet 80,
najdłuższy strumień 2×/dzień, P=20/80=0.25 najbardziej odmienne od EJ); Lotto/Keno odrzucone;
ŻADNA gra nie daje positive control → MM to czysty negative control + stress-test.

**Kroki implementacji (kolejność):**
1. **Data source + scraper** — historia MM. Sprawdzić wzorzec CSV `wynikilotto.net.pl`
   (jak EJ `data/seed/eurojackpot_history.csv`) lub `lotto.pl`. `ingestion/mm_scraper.py`
   (lub uogólnić `lotto_scraper`); Tier-1 seed CSV committed. Format: data + 20 liczb 1–80.
2. **Uogólnienie `DrawRecord` (`core/types.py`)** — model zmiennej długości (np. generyczny
   `numbers: list[int]` + `pool_size` + `k_drawn`), zachowując back-compat EJ (`main_1..5`,
   `euron_1..2`). To dotyka WIELU modułów — patrz krok 3.
3. **Parametryzacja stałych pool=50/k=5 (PRZEKROJOWY pass, NIE bolt-on)** — audyt + parametryzacja
   w: `pipeline` (`_MAIN_POOL_SIZE`, `_P_NUMBER_PRESENT=5/50`), `methodology/{cooccurrence,
   k4_mmd (wymiar wektora częstości Δ⁴⁹→Δ⁷⁹), permutation, recurrence, multiple_testing,
   block_bootstrap}`, `reporting/information_theory`, `driftsim`. **Defaulty = wartości EJ →
   zero regresji** (zweryfikować pełnym suite przed dodaniem MM).
4. **Runner negative-control-only** — MM NIE pasuje do `run_audit` (brak reżimów = brak zmiany
   reguł; brak pola „euron"). Ścieżka jak `prng_benchmark`: 3 filary (BOCPD main / MMD / cooc) +
   Family B na strumieniu MM. Lokalizacja prawdopodobnie `reporting/` (POZA prereg §0, precedens
   PRNG/disagreement). Oczekiwany wynik: **all-clear (honest null na innej grze)**.
5. **Sekcja w `report.qmd`** — „Second real-world case study: Multi Multi" symetrycznie do
   sekcji 5 PRNG: tabela wyników (oczekiwane clear) + nota o skali (n, alfabet 80) + re-render
   `docs/{report,index}.html` + grep przed kopiowaniem.
6. **Walidacja** — FPR/kalibracja sanity przy pool=80; pełny suite green; ruff + mypy --strict;
   ew. update README (tabela case-studies + test count).

**Dyscyplina prereg:** spodziewane BRAK rewizji prereg §0 (te same testy/nulle/progi; parametr
P_present to własny uniform MM, NIE zmiana metodologii EJ; warstwa reporting/data poza §0 jak PRNG).
POTWIERDZIĆ przy planowaniu — jeśli cokolwiek dotyka zamrożonej decyzji statystycznej EJ → rewizja.

**Uczciwe zastrzeżenia (NIE pomijać):** (a) uogólnienie to realna robota przekrojowa, nie „inny
DrawRecord source" jednolinijkowo; (b) MM = negative control only (brak positive control); (c) NIE
dodawać Lotto/Keno — jedna gra, koniec (unik scope creep); (d) rebrand MM 2009 / +losowania =
eksploracyjne non-controls, nie ground truth.

---

## Co zrobiono w tej sesji

- ✓ **Kolumna „IT (LZ) p" per-regime w `report.qmd`** (`bfa6731`): R1=0.535/R2=0.855/R3=0.620
  wszystkie clear; suplement (NIE 4. filar; DoD-4=3/3); re-render docs.
- ✓ **Pełny rewrite `README.md`** (`822cb36`) wg briefu 5-modeli (lejek, 2× Mermaid, sformułowania
  uczciwościowe, sprostowania metryk: RAM ~210 MB nie 4 GB, LZ76 0.700 nie 0.75).
- ✓ **Archiwum briefu+recenzji** → `docs/research/readme_rewrite/` (`0e04caf`).
- ✓ **Weryfikacja po /end:** live Pages deploy `0e04caf` = success (run 27102934312), docs serwują
  tabelę IT per-regime; Mermaid składniowo czysty (brak silent-break chars; wizualne potwierdzenie
  = rzut oka usera na front repo).
- ✓ **Research drugiej gry + DECYZJA Multi Multi** (zob. MEMORY.md [2026-06-07 sesja 3]).
- ✓ **State commit** `33a71d6` (poprz. zapis sesji). Ten zapis = kolejny state commit.

## Co zostało (backlog sesji — wszystko OPCJONALNE / stretch)

- ⟳ **Implementacja Multi Multi** (NASTĘPNY KROK) — główny kierunek następnej sesji.
- ⟳ Wizualne potwierdzenie renderu Mermaid na froncie repo (rzut oka usera).
- ⟳ Push state commitów (origin na `0e04caf`; 33a71d6+ lokalne) — do decyzji.
- ⟳ Pages na `actions/deploy-pages` (Node20-warning) — stretch CI.
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.

## Aktywne pliki

- (następna sesja) `core/types.py`, `ingestion/mm_scraper.py` (nowy), `methodology/*` (parametryzacja
  pool/k), `pipeline.py`, `reporting/` (runner MM + sekcja report.qmd), `data/seed/` (MM CSV)
- `README.md`, `MEMORY.md` (wpisy sesja 2 + sesja 3)
- ACTIVE prereg = **v7** (bez zmian — MM to reusability/reporting + parametryzacja, spodziewane poza §0)

## Otwarte pytania

- **Źródło danych MM** — czy `wynikilotto.net.pl` ma CSV MM (jak EJ) czy trzeba `lotto.pl` API/scrape.
- **Kształt uogólnionego `DrawRecord`** — generyczny `numbers+pool_size+k_drawn` vs osobny typ MM.
- **Render Mermaid na GitHubie** — wizualne potwierdzenie (sandbox nie pokaże JS-render).
- **Czy projekt „skończony"?** — rdzeń TAK; MM to świadome rozszerzenie reusability na 2. realną grę.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-07 sesja 3] DECYZJA: druga gra = Multi Multi** —
  research zmian reguł MM/Lotto/Keno (brak positive control w żadnej), uzasadnienie wyboru MM
  (alfabet 80/skala/dystynktywność), zakres uogólnienia pool=50/k=5 (przekrojowy), plan.
