## ═══ Sesja zarchiwizowana [2026-06-07 23:18] ═══

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


## ═══ Sesja zarchiwizowana [2026-06-07 21:51] ═══

# last_session.md

**Sesja:** 2026-06-07 · ~11:00-12:10
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 9c2dc2f @ master (origin: 99b4dea — patrz niżej)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Rozszerzyć per-regime sekcję w `src/driftscope/reporting/report.qmd` o kolumnę „IT (LZ) p"
na realnym EuroJackpot (R1/R2/R3)** — pokazać, że suplement IT czyta negative control jako
clear również pod kątem SEKWENCYJNYM (czwarty, niezależny obiektyw obok 3 filarów). Konkretnie:
w chunku raportu per-regime wywołać `information_detector()(draws_regime)` dla każdego reżimu i
dodać kolumnę z `p_value`; oczekiwane wartości wysokie (~clear), jak negative control 1-50.

Kontekst: IT pozostaje SUPLEMENTEM, NIE wchodzi do `classify()` / Disagreement Protocol
(DoD-4=3/3 nienaruszone). To domyka narrację „honest null" o sekwencyjny wymiar bez zmiany
kontraktu. Czysty stretch reporting — brak ścieżki krytycznej (framework Ścieżka A domknięty).

---

## Co zrobiono w tej sesji

- ✓ **Naprawa rozjazdów z /start:** dotrackowany `artifacts/{.gitkeep,artifacts_manifest.json}`
  (DoD-6 deliverable; poprz. sesja błędnie uznała „ignored"), odpięty `settings.local.json` od
  gita (`git rm --cached` + `.gitignore`) — koniec perpetualnego churnu allowlisty. Commity
  `7d73cb2`, `28ad0ca`, `1162bc4`. Push origin.
- ✓ **Faza A — detektor IT** (`reporting/information_theory.py`): złożoność Lempel-Ziv 1976
  (`@njit cache=True`) + bz2 cross-check; null **order-shuffle** (permutacja bloków losowań →
  zachowuje marginal+joint, łamie strukturę między-losowaniową). Komplementarny: ślepy na
  freq_shift/pair_corr, czuły na autocorr/period. `information_detector` = czysta funkcja (DoD-6,
  digest-seed jak cooccurrence). 10 testów (FPR≤α, power autocorr, ślepota freq_shift, determinizm).
- ✓ **Faza A.2 — integracja baterii PRNG:** kolumna IT (`it_reject`/`it_p`) w `prng_benchmark.py`
  (src+scripts), `report.qmd`. IT zapala się WYŁĄCZNIE na `+period(50)` (p≈0.01), milczy na
  good/crypto/bias i realnym EuroJackpot (p≈0.75).
- ✓ **Faza B — demo Streamlit** (`demo/app.py`, był stub): 3 zakładki (detection matrix /
  entropy-lens LZ76 / Turing test), grupa optional-dep `demo`. Buildery czyste, `st.*` pod
  `render()`/`__main__`. Smoke test + `AppTest` headless (0 wyjątków). Streamlit 1.58 zainstalowany.
- ✓ **Walidacja:** ruff + mypy strict (`src`+`demo`, 34 plików) clean; **260 passed / 2 skipped**.
- ✓ **Commity + push:** `e60b888` (IT), `99b4dea` (demo) → origin. README + root MEMORY.md
  zaktualizowane; `9c2dc2f` (docs readme) — patrz niżej co do push.

## Co zostało (backlog sesji)

- ⟳ **Kolumna IT per-regime w report.qmd** — NASTĘPNY KROK.
- ⟳ Pages na `actions/deploy-pages` (usuwa Node20-warning) — stretch CI.
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.
- ⚠ **`9c2dc2f` (docs readme) i commit stanu sesji NIEWYPCHNIĘTE** — origin na `99b4dea`.
  Push pozostawiony do decyzji (zob. Otwarte pytania).

## Aktywne pliki

- `src/driftscope/reporting/information_theory.py` (nowy) + `tests/test_information_theory.py`
- `src/driftscope/reporting/prng_benchmark.py`, `scripts/prng_benchmark.py`, `report.qmd` (kolumna IT)
- `demo/app.py` (nowy) + `tests/test_demo_smoke.py`; `pyproject.toml` (mypy override + grupa demo)
- `README.md`, `MEMORY.md` (root, wpis Architektura [2026-06-07])
- ACTIVE prereg = **v7** (bez zmian — IT jest suplementem poza prereg)

## Otwarte pytania

- **Wypchnąć `9c2dc2f` (docs readme) + commit stanu sesji?** origin stoi na `99b4dea`
  (feature'y już tam są). Brak ścieżki krytycznej; do decyzji na starcie następnej sesji.
- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) praktycznie TAK; IT i demo
  to zrealizowane wow-stretche. Pozostałe pozycje to czyste stretche.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-07] ✓ IT supplement (LZ76) + demo Streamlit** —
  decyzja suplement-nie-filar, reporting/ poza prereg, order-shuffle null, walidacja, integracja.
- Pamięć agenta: `it_supplement_lz76.md` (+ wpis w indeksie MEMORY.md agenta).

## ═══ Sesja zarchiwizowana [2026-06-07 12:10] ═══

# last_session.md

**Sesja:** 2026-06-06 · ~21:50-22:15
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** a24b684 @ master (origin zsynchronizowany)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Stretch (opcjonalny): przełączyć GitHub Pages na deploy przez `actions/deploy-pages`.**
Konkretnie: utworzyć `.github/workflows/pages.yml` (job `build` z `actions/upload-pages-artifact@v3`
wskazującym `docs/` + job `deploy` z `actions/deploy-pages@v4`, `permissions: pages:write,
id-token:write`, trigger `push` na `master` przy zmianie `docs/**`), następnie w Settings → Pages
zmienić Source z „Deploy from a branch" na „GitHub Actions". Cel: usunięcie jedynego pozostałego
ostrzeżenia Node20 z wbudowanego `pages-build-deployment`.

Kontekst: główny cel projektu (framework audytowy, Ścieżka A) jest **praktycznie domknięty** —
DoD-1..6, reporting, CI, Pages, pełna piątka PRNG, db/ cleanup i W9 executive summary wszystkie
gotowe, wypchnięte i zweryfikowane na żywo. To zadanie to czysty polish CI; nie ma ścieżki
krytycznej. Równorzędne alternatywy: demo Streamlit, analiza pary (10,25), `information_theory.py`.

---

## Co zrobiono w tej sesji

- ✓ **NASTĘPNY KROK z poprz. sesji DOMKNIĘTY — live Pages zweryfikowane:** run
  `pages-build-deployment` `27072126882` → **success**, `headSha=0b3271179e...` (= `0b32711`,
  commit z W9 executive summary). Weryfikacja przez `gh run list/view --json` (sandbox blokuje HTTPS).
- ✓ **Live URL potwierdzony przez WebFetch:** `executive_summary.html` serwuje pełny one-pager
  (heading + kluczowe linie zgadzają się z W9). Callout „executive summary" obecny w wdrożonym
  `docs/index.html:2229` → linkuje do `executive_summary.html`.
- ✓ **Push zaległego `a24b684`** (commit zapisu sesji z poprz. `/end`, niewypchnięty) →
  `origin/master` zsynchronizowany (`0b32711..a24b684`).
- ✓ **`artifacts/` potwierdzone jako celowo git-ignored** (`git check-ignore` exit 0) — nie wymaga akcji.

## Co zostało (backlog sesji — wszystko OPCJONALNE / stretch)

- ⟳ Pages na `actions/deploy-pages` (usuwa Node20-warning) — NASTĘPNY KROK.
- ⟳ demo Streamlit (`demo/app.py` stub, off-stack).
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.
- ⟳ `information_theory.py` (LZ76/MDL) — absent, stretch.

## Aktywne pliki

- (brak zmian w kodzie/docs w tej sesji — sesja czysto weryfikacyjna)
- `last_session.md` + `last_session.archive.md` — stan sesji (ten commit)
- ACTIVE prereg = **v7** (bez zmian — sesja non-methodology)

## Otwarte pytania

- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) **praktycznie TAK**.
  Wszystkie długi polish (db/ kontrakt, W9) zamknięte, wdrożone i zweryfikowane na żywo.
  Pozostałe pozycje to czyste stretche bez ścieżki krytycznej.

## Do MEMORY.md (przeniesiono)

Brak nowych wpisów — sesja czysto weryfikacyjna (potwierdzenie deployu `0b32711`), bez decyzji
architektonicznych ani rozwiązań trudnych problemów. Wynik „live Pages OK" jest efemeryczny,
nie wymaga trwałej pamięci.

## ═══ Sesja zarchiwizowana [2026-06-06 22:15] ═══

# last_session.md

**Sesja:** 2026-06-06 · ~20:50-21:35
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 0b32711 @ master (pushed → origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Zweryfikować live GitHub Pages po push `0b32711`:** że landing
`https://piotr1686.github.io/DriftScope/` serwuje callout „executive summary" ORAZ że
`https://piotr1686.github.io/DriftScope/executive_summary.html` ładuje się (200 + treść
one-pagera). Sandbox blokuje HTTPS (curl exit 35) → weryfikować przez
`gh run list --workflow=pages-build-deployment` + `gh run view <id>` (status success,
headSha=0b32711), lub poprosić usera o rzut oka na URL. Jeśli OK → projekt praktycznie domknięty.

Kontekst: oba wstrzymane punkty z poprz. sesji (db/ cleanup + W9) WYKONANE i wypchnięte w tej
sesji. Pozostała tylko potwierdzenie deployu (async po push) — analogicznie jak weryfikowano
Pages po PR#2/#3 w poprzednich sesjach. Opcjonalny stretch po weryfikacji: przełączyć Pages
na source „GitHub Actions" + własny `actions/deploy-pages` (usuwa Node20-warning z wbudowanego
`pages-build-deployment`).

---

## Co zrobiono w tej sesji

- ✓ **db/ cleanup + sync kontraktu (commit `d2048e5`, pushed):** `git rm -r src/driftscope/db/`
  (4 puste stuby, zero importów). Kontrakt zsynchronizowany z kodem: PROJECT_BRIEF.md (nota
  rewizji §0 z `revision_reason`, §3 storage→Parquet/CSV inline, §4.1 drzewo, §4.2 DAG→`artifacts/`,
  §4.3 data-flow, §10 synergy, DoD-6) + CLAUDE.md (Storage/Nigdy/drzewo/lfs-glob) + `scripts/archive.py`
  (martwy glob `*.sqlite`). Walidacja: 246 passed / 2 skip, mypy --strict src czyste (32 pliki), ruff czyste.
- ✓ **W9 executive summary (commit `0b32711`, pushed):** `docs/executive_summary.html` — standalone
  print-friendly 1-page one-pager (recruiter TL;DR, odrębny od `report.html`). `@media print` → 1 strona
  A4 (zweryfikowane headless Edge → PDF page-count=1). Linki: README + callout w `report.qmd`. Re-render
  Quarto → `docs/{index,report}.html` (plotly via CDN; AVG-proxy build-fetch fail nieszkodliwy).
- ✓ **Push:** `5c2237d..0b32711` → `origin/master` (2 commity).
- ✓ **Pamięć:** projektowy MEMORY.md — db/ finding oznaczony ✓ RESOLVED + wpis ✓ W9 ZBUDOWANY
  (gotcha print-fit, docs/ ręcznie kopiowane, render gotcha). Pamięć agenta: nowy wpis
  `powershell-git-commit-heredoc-gotcha.md`.

## Co zostało (backlog sesji — wszystko OPCJONALNE / stretch)

- ⟳ Weryfikacja live Pages po push (NASTĘPNY KROK).
- ⟳ Pages na `actions/deploy-pages` (usuwa Node20-warning) — opcjonalne.
- ⟳ demo Streamlit (`demo/app.py` stub, off-stack).
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.
- ⟳ `information_theory.py` (LZ76/MDL) — absent, stretch.

## Aktywne pliki

- `docs/executive_summary.html` — nowy one-pager (`0b32711`)
- `docs/{index,report}.html` — re-render z callout (`0b32711`)
- `src/driftscope/reporting/report.qmd` — callout do executive summary (`0b32711`)
- `README.md` — link executive summary (`0b32711`)
- `PROJECT_BRIEF.md` + `CLAUDE.md` + `scripts/archive.py` — sync kontraktu po usunięciu db/ (`d2048e5`)
- ACTIVE prereg = **v7** (bez zmian — sesja non-methodology)

## Otwarte pytania

- **Live Pages po deploy** — czy `pages-build-deployment` na `0b32711` = success i URL serwuje
  one-pager + callout (deploy async po push).
- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) praktycznie TAK; oba ostatnie
  długi polish (db/ kontrakt + W9) zamknięte. Pozostałe pozycje to czyste stretche.

## Do MEMORY.md (przeniesiono)

Projektowy MEMORY.md: db/ FINDING → ✓ RESOLVED (opis wykonania) + nowy wpis **[2026-06-06 sesja 2]
✓ W9 executive summary ZBUDOWANY** (gotcha print-fit headless-Edge, docs/ ręcznie kopiowane = brak
render-stepu w CI, render gotcha AVG-proxy plotly→CDN). Pamięć agenta:
`powershell-git-commit-heredoc-gotcha.md` (`-m @'...'@` wycieka `@` → używać `git commit -F <plik>`).

## ═══ Sesja zarchiwizowana [2026-06-06 21:30] ═══

# last_session.md

**Sesja:** 2026-06-06 · ~10:40-11:55
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 5c2237d @ master

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**[CZEKA NA DECYZJĘ USERA — dwie rekomendowane pozycje, obie wstrzymane]**

**(1) db/ cleanup** — usunąć `src/driftscope/db/` (puste stuby, zero użycia w src/tests) ORAZ
zsynchronizować kontrakt: update CLAUDE.md (drzewo) + PROJECT_BRIEF.md (linie 13/72/145-148/
169/219/443/546 — w tym narracja data-flow §219 „Reporting czyta przez db/queries.py") z polem
rationale „access layer SQLite nigdy nie zmaterializował się; persystencja Parquet/CSV; kontrakt==kod".
**(2) W9 executive summary** — zbudować jako print-friendly standalone HTML one-pager (Quarto→HTML
+ print-CSS, eksport Ctrl+P→PDF); LaTeX niedostępny, prawdziwy PDF wymagałby ryzykownego `quarto
install tinytex`.

Kontekst: rdzeń projektu domknięty (DoD-1..6 + reporting + CI + Pages + pełna piątka PRNG).
Obie pozycje to polish/uczciwość kontraktu, nie ścieżka krytyczna. db/ wstrzymane bo usunięcie =
rewizja kontraktu w 8+ miejscach (decyzja prezentacyjna usera). W9 wstrzymane bo format (HTML vs
PDF) zależy od akceptacji ryzyka tinytex.

---

## Co zrobiono w tej sesji

- ✓ **PRNG benchmark — pełna piątka (PR#4 `5c2237d`, squash-merge):** `AESCtrDrbgStream`
  (AES-256 CTR jako DRBG, szkielet NIST SP 800-90A) + defekt **period-truncation**
  (`draws_from_stream(period=p)` — krótki cykl powtarzany → zamrożone częstości → over-dispersion).
  favor/period wykluczają się; `period=None` = zachowanie bit-identyczne (zero regresji).
- ✓ **Money run n=1500:** good/crypto(ChaCha20+AES)/real → clear; **bias(7) → FLAG wąski**
  (Family B 1/50 + MMD); **period(50) → FLAG szeroki (3/3 filary: Family B 27/50 + MMD + cooc)**.
  Framework **rozróżnia typ defektu**. Sensitivity ✓ Specificity ✓.
- ✓ **Walidacja:** suite **246 passed / 2 skip** (+7), ruff(src/tests)+mypy --strict czyste,
  CI ubuntu zielone 2m53s, `docs/` re-render (Quarto), Pages deploy success. README 2+2+2 + 246.
- ✓ **Diagnoza db/** — rozbieżność kontrakt↔implementacja zidentyfikowana (NIE wykonano cleanup).
- ✓ **Diagnoza toolchain** — LaTeX/tinytex niedostępny (executive PDF).
- ✓ **Pamięć:** 3 wpisy **[2026-06-06]** w MEMORY.md (PR#4, db/ finding, toolchain LaTeX).

## Co zostało (backlog sesji — wszystko OPCJONALNE / stretch)

- ⟳ **db/ cleanup + rewizja kontraktu** (NASTĘPNY KROK (1), czeka na decyzję).
- ⟳ **W9 executive summary HTML one-pager** (NASTĘPNY KROK (2), czeka na decyzję formatu).
- ⟳ demo Streamlit (`demo/app.py` stub, off-stack).
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.
- ⟳ `information_theory.py` (LZ76/MDL) — absent, stretch.
- ⟳ Node20 na wbudowanym `pages-build-deployment` (przełączyć na `actions/deploy-pages`) — opcjonalne.

## Aktywne pliki

- `src/driftscope/ingestion/rng_streams.py` — AESCtrDrbgStream + period defekt (`5c2237d`)
- `src/driftscope/reporting/prng_benchmark.py` + `scripts/prng_benchmark.py` — 2+2+2 + `--period` (`5c2237d`)
- `tests/test_rng_streams.py` + `tests/test_prng_benchmark.py` — +7 testów (`5c2237d`)
- `src/driftscope/reporting/report.qmd` + `README.md` + `docs/{index,report}.html` — sekcja 5 (`5c2237d`)
- (PENDING) `src/driftscope/db/*` — kandydat do usunięcia; `CLAUDE.md` + `PROJECT_BRIEF.md` — rewizja kontraktu
- ACTIVE prereg = **v7** (bez zmian — sesja non-methodology)

## Otwarte pytania

- **db/ — usunąć czy zostawić „deferred"?** Rekomendacja: usunąć + zsynchronizować kontrakt
  (uczciwość kontrakt↔kod > martwe stuby dla portfolio). Decyzja prezentacyjna usera.
- **W9 PDF czy HTML?** Rekomendacja: HTML one-pager (zero ryzyka LaTeX). PDF tylko jeśli user
  zaakceptuje ryzyko `quarto install tinytex` (SSL przez AVG-proxy).
- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) praktycznie tak.

## Do MEMORY.md (przeniesiono)

3 wpisy **[2026-06-06]** w MEMORY.md: (1) PRNG pełna piątka PR#4 + gotcha Pages-deploy Node20,
(2) FINDING db/ rozbieżność kontrakt↔impl + rekomendacja (DECYZJA PENDING), (3) toolchain
LaTeX niedostępny + rekomendacja HTML one-pager dla W9.

