## ═══ Sesja zarchiwizowana [2026-06-26 21:35] ═══

# last_session.md

**Sesja:** 2026-06-14 · 21:00-21:45
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** bfa5754 @ master (zsynchronizowany z origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Ostatni merytoryczny stretch (mini-study pary 10,25) domknięty — brak narzuconego
następnego kroku.** Framework (Ścieżka A) kompletny i opublikowany. Jedyny pozostały
konkretny item techniczny to **zaakceptowany dług hygieniczny Pages-deploy** (Opcja 1,
świadomie odłożona w tej sesji jako złe ryzyko/zysk):

- Przełączyć GitHub Pages source z „Deploy from branch /docs" na **„GitHub Actions"** +
  własny workflow `actions/deploy-pages` (+`actions/upload-pages-artifact`), by wyciszyć
  Node20-deprecation annotation we wbudowanym `pages-build-deployment` (używa wewnętrznie
  `checkout@v4`/`upload-artifact@v4`). To **kosmetyka** (warning, nie failure) tykająca
  żywy deployment → realne ryzyko zepsucia opublikowanej strony za zerowy zysk merytoryczny.
  Zob. MEMORY [2026-06-06] gotcha Pages-deploy.

Kontekst: tej sesji wybrano Opcję 2 z trzech kandydatów (mini-study) i ją domknięto;
Opcja 3 = „framework done" pozostaje w pełni uprawniona. Alternatywnie — pivot
predykcyjny (zob. agent-memory `project_pivot_prediction.md`), jeśli kierunek się zmieni.

---

## Co zrobiono w tej sesji

- ✓ **PUSH zaległego commitu sesyjnego** (`da3b50d..d716f09`) — stan `/end` z poprzedniej sesji wypchnięty na origin.
- ✓ **Mini-study pary (10,25) w R2 — Opcja 2** (`bfa5754`, pushed). Reporting/docs-only, prereg v7 nietknięty, zero zmian logiki `src/`:
  - Odtworzono deterministycznie jedyną flagę negative-controlu: R2 (n=389) współwystąpienia → para **(10,25)**, p=0.024@999 / 0.010@199, z≈4.6. R1/R3 clear (`R1 0/3 · R2 1/3 · R3 0/3`).
  - Analiza „clean cell": O=9 vs E≈2.19, ale marginesy niewinne (#10=28 najrzadsza, z_marg=−1.84; #25=38 średnia, z_marg=−0.15) → czysto łączna anomalia. Para stabilna względem n_perm. Expected-rate P≈14% na ≥1 flagę w 3 reżimach.
  - Deliverable: (1) nota `docs/research/2026-06-14_r2_cooccurrence_pair_10_25.md` (PL, pełna anatomia + argument dlaczego FDR strukturalnie nie potwierdza → 1/3, nie finding). (2) `report.qmd §4` data-driven chunk `r2-cooccurrence-pair` (nazywa parę + liczy marginesy z `report`/`draws`, p NIE hardcoded). (3) re-render `docs/{index,report}.html` (grep-zweryfikowany przed kopią).
- ✓ Walidacja: render OK (ostrzeżenia SSL avgMonFltProxy/cdn.plot.ly = znany fallback proxy AVG); commit + push, drzewo czyste, origin zsynchronizowany.

## Co zostało (backlog sesji)

- ⟳ **Hygiena Pages-deploy (opcjonalna, zaakceptowany dług):** source → „GitHub Actions" + `actions/deploy-pages` (wycisza Node20 annotation). Świadomie odłożona — złe ryzyko/zysk.
- ⟳ Stretche domknięte: pełna piątka RNG, demo Streamlit, IT supplement, MM gra 2, mini-study R2 — Ścieżka A kompletna.
- ⟳ Strategiczne (nie blokujące): czy framework „done", czy pivot predykcyjny (`project_pivot_prediction.md`).

## Aktywne pliki

- ZMIENIONE (committed, pushed): `src/driftscope/reporting/report.qmd` (§4 chunk),
  `docs/{index,report}.html` (re-render), `docs/research/2026-06-14_r2_cooccurrence_pair_10_25.md` (NOWY)
- ACTIVE prereg = **v7** (bez zmian — reporting/docs-only)

## Otwarte pytania

- Brak blokujących. Mini-study (Opcja 2) domknięty zgodnie z decyzją usera.
- Strategiczne: framework „done" (Ścieżka A) vs hygiena Pages-deploy vs pivot predykcyjny.

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-14] Mini-study pary (10,25) w R2** —
  konkretyzacja jedynej flagi negative-controlu, „clean cell", dlaczego 1/3 nie finding,
  expected-rate 14%, deliverable (nota + §4 chunk + re-render). HEAD=`bfa5754`, pushed.
- Agent-memory: bez nowego wpisu (czysta realizacja zaplanowanego stretcha, w pełni zapisana w repo).

## ═══ Sesja zarchiwizowana [2026-06-14 21:45] ═══

# last_session.md

**Sesja:** 2026-06-13 · 21:00-22:50 (sesja 2)
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** da3b50d @ master (zsynchronizowany z origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Cały backlog z 2026-06-13 domknięty — brak narzuconego następnego kroku.**
Najbardziej naturalny kandydat: **decyzja, czy przełączyć GitHub Pages na source
"GitHub Actions" + własny `actions/deploy-pages`**, by wyciszyć Node20-deprecation
annotation we wbudowanym `pages-build-deployment` (używa wewnętrznie `checkout@v4`/
`upload-artifact@v4`). To jedyny znany otwarty „dług hygieniczny" CI (zob. MEMORY
[2026-06-06] gotcha Pages-deploy). Alternatywnie: analiza pary (10,25) z R2 (single-pillar
co-occurrence 1/3) jako mini-study, albo zostawić framework jako domknięty (Ścieżka A).

Kontekst: framework (Ścieżka A) jest kompletny i opublikowany; ta sesja zamknęła dwa
findingi code-review + trzy polish. Nie ma „następnego kroku roadmapy" — pozostałe pozycje
to opcjonalne stretche/hygiena, nie zobowiązania.

---

## Co zrobiono w tej sesji

- ✓ **PUSH zaległego commitu sesyjnego** (`79c03e9..4fd16f9`) — stan z poprzedniej sesji wypchnięty na origin.
- ✓ **Sub-Finding #1: granularność Family B dla EJ-`'real'` w §5** (`adb7e74`) — decyzja usera = **full-stream (50) + caveat**, NIE per-reżim. Caveat (EN) w `report.qmd §5` + nota docstring `run_battery` + zdanie w README. Re-render `docs/{index,report}.html` (grep-zweryfikowany przed kopią). Reporting-only, prereg v7 nietknięty.
- ✓ **Finding #2 → README** (`d2abd12`) — akapit „Why we do not hard-gate on ≥2/3" (analog `report.qmd §4`, strukturalna ślepota na 1/3). README-only, bez re-renderu.
- ✓ **Polish 1: ruff `scripts/{check_api_key,smoke_test}.py`** (`90e4e38`) — 3× I001 (auto-fix) + 1× F841 (`data = check(...)`→`check(...)`). Pre-existing dług sprzątnięty.
- ✓ **Polish 2: exec summary 1×A4** — ZWERYFIKOWANE headless Edge `--print-to-pdf` → `/Type /Page` = 1 strona. Verify-only.
- ✓ **Polish 3: BOCPD cross-walidacja progu pool=80 @ n=5000** (`da3b50d`) — p95=**0.3314 = identyczne z n=2000** (Δ=0.0000), FPR@0.34=0.04. Length-invariance potwierdzona (prereg v6 §0). Komentarz w `h1_classical.py`.
- ✓ **Polska wersja README (prywatna, POZA repo)** — `D:\Programming_Projects\zz_INNE\README_PL\README.md` (383 linie). Nagłówek HTML = prywatna/nieoficjalna; niewersjonowana.
- ✓ Walidacja: ruff+mypy --strict na dotkniętych plikach czyste; wszystkie 4 commity na origin/master, drzewo czyste.

## Co zostało (backlog sesji)

- ⟳ **Hygiena Pages-deploy (opcjonalna):** przełączyć Pages source na „GitHub Actions" + `actions/deploy-pages`, by wyciszyć Node20 annotation w `pages-build-deployment` (nasz `ci.yml` już zbumpowany).
- ⟳ **Analiza pary (10,25)** z R2 (single-pillar co-occurrence 1/3) — opcjonalne mini-study, NIE finding (nie przeszło bramki konwergencji+FDR).
- ⟳ Stretche domknięte: pełna piątka RNG, demo Streamlit, IT supplement, MM gra 2 — Ścieżka A kompletna.

## Aktywne pliki

- ZMIENIONE (committed, pushed): `src/driftscope/reporting/{prng_benchmark.py,report.qmd}`,
  `src/driftscope/methodology/h1_classical.py`, `README.md`, `docs/{index,report}.html`,
  `scripts/{check_api_key,smoke_test}.py`
- POZA REPO (prywatne): `D:\Programming_Projects\zz_INNE\README_PL\README.md`
- ACTIVE prereg = **v7** (bez zmian — reporting/docs/style-only)

## Otwarte pytania

- Brak nierozstrzygniętych. Oba findingi (#1 full-stream, #2 honest-disclosure) i sub-decyzja Family B zamknięte decyzją usera.
- Strategiczne (nie blokujące): czy framework jest „done" (Ścieżka A), czy podejmować opcjonalne hygiena/stretche?

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-13 sesja 2]** — sub-Finding #1 full-stream+caveat,
  Finding #2→README, 3 polish (ruff/exec-1A4/BOCPD length-invariance), polska wersja README poza repo.
  HEAD=`da3b50d`, pushed. Highlight: BOCPD p95(n=5000)=p95(n=2000)=0.3314 (Δ=0.0000) — empiryczne domknięcie length-invariance prereg v6 §0.

## ═══ Sesja zarchiwizowana [2026-06-13 22:50] ═══

# last_session.md

**Sesja:** 2026-06-13 · 11:30-12:30
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 79c03e9 @ master (zsynchronizowany z origin/master, CI green)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Podjąć DECYZJĘ na Finding code-review #1 z 2026-06-11: polityka werdyktu wiersza
`klass='real'` (EuroJackpot) w benchmarku §5 — czy `family_b_per_number_pvalues`
powinno być regime-split.** Konkretnie: benchmark PRNG (`reporting/prng_benchmark.py`,
`run_battery`) liczy Family B na PEŁNYM strumieniu EJ (full-stream), podczas gdy główny
pipeline robi to per-reżim (R1/R2/R3, BY pooled /150). Pytanie: ujednolicić EJ-real
w benchmarku do per-reżim (spójność z headline) czy zostawić full-stream z caveat
w prozie? (Reporting-only, bez prereg.)

Kontekst: werdykt OR→Disagreement (#1) i honest-disclosure 1/3 (#2) ZROBIONE w tej sesji
(`e553820`/`79c03e9`). Pozostała sub-decyzja granularności Family B dla wiersza 'real' —
zaparkowana, bo wymaga rozstrzygnięcia user (spójność vs prostota benchmarku).

---

## Co zrobiono w tej sesji

- ✓ **PUSH zaległości** — 14 commitów taska struktury (`7ed0ca6..38aec30`) wypchnięte,
  CI green (`27461790549`).
- ✓ **Doc-sync** (`e890b08`) — liczniki testów 266/268→272/274 (README:49/223/316 +
  `executive_summary.html:213`), docstring `run_multimulti_audit` „all-clear"→„clear",
  kwalifikator naive-OR w `calibrate_mmd_pool.py:3`.
- ✓ **Finding #1** (`e553820`) — `BenchmarkRow.flagged` OR → **Disagreement ≥2 z {Family B,
  MMD, co-occurrence}**, IT non-voting (nowe `core_votes`). Spójne z `MultiMultiAuditRow`
  + prozą §5. Sensitivity zachowana (bias=2, period=3; n=600 i n=1500). Przy n=1500
  wartości Verdict bez zmian (usuwa kruchość specificity, nie headline). 4 testy regresyjne.
  Komentarz MM `:47` zaktualizowany.
- ✓ **Finding #2** (`e553820`, `report.qmd §4`) — honest-disclosure: sygnał widoczny tylko
  jednej rodzinie (pair_corr→cooc) = 1/3; twarda reguła ≥2/3 byłaby strukturalnie ślepa;
  bramka watchlisty = FDR primary + konwergencja ≥1 (NIE hard ≥2/3). Bez zmian kodu.
- ✓ **Re-render Pages** (`79c03e9`) — `report.qmd` (§4+§5) → quarto → `docs/index.html`+
  `report.html`, zweryfikowane grep-em PRZED kopią (per-reżim, /150, period(50), webm). CI green.
- ✓ Liczniki podbite 274→278 (po +4 testach). Walidacja: pytest **276/2skip**, ruff+mypy --strict czyste, CI 2× green.
- ✓ Pamięć: projektowy MEMORY.md wpis [2026-06-13]; agent-memory gotcha `cd`→podwojone ścieżki.

## Co zostało (backlog sesji)

- ⟳ **NASTĘPNY KROK:** decyzja #1 — granularność Family B dla wiersza EJ-'real' w §5 (full-stream vs per-reżim).
- ⟳ Dług ruff `scripts/{check_api_key,smoke_test}.py` (4×: I001 + unused `data`) —
  pre-existing, POZA scope CI; sprzątnąć przy pracy w tych plikach.
- ⟳ Wizualny check exec summary Ctrl+P = 1×A4; cross-check kalibracji BOCPD n=5000 pool=80.
- ⟳ Stretche: pełna piątka RNG domknięta; demo Streamlit zbudowane — Ścieżka A kompletna.

## Aktywne pliki

- ZMIENIONE (commited): `src/driftscope/reporting/{prng_benchmark,multimulti_audit,report.qmd}.py/.qmd`,
  `tests/test_prng_benchmark.py`, `README.md`, `docs/{executive_summary,index,report}.html`,
  `scripts/{multimulti_audit,calibrate_mmd_pool}.py`
- ACTIVE prereg = **v7** (bez zmian — reporting-only, methodology/ nietknięte)

## Otwarte pytania

- Finding #1 (sub-decyzja): wiersz EJ 'real' w benchmarku §5 — Family B full-stream czy per-reżim?
- Finding #2 domknięty prozą; czy dodać analogiczny akapit do README (obecnie tylko report.qmd §4)?

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-13]** push zaległości + doc-sync +
  Finding #1 (werdykt PRNG OR→Disagreement ≥2) + Finding #2 (honest-disclosure 1/3),
  HEAD=`79c03e9`, pushed, CI green. Gotcha narzędziowy `cd`→podwojone ścieżki.
- Agent-memory: `bash-cd-persists-doubled-paths.md` (feedback).

## ═══ Sesja zarchiwizowana [2026-06-13 12:27] ═══

# last_session.md

**Sesja:** 2026-06-11 · sesja 2 (wieczór)
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 7348fee @ master (NIEpushowane — 13 commitów przed origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**`git push origin master` + weryfikacja CI**, potem domknąć pending doc-sync
z drugiego taska. Konkretnie:
1. `git push origin master` (wyśle 13 commitów: 9 strukturalnych z tej sesji
   `74bd82d..7348fee` + 4 wcześniejsze niepushowane `3e70fef`/`448fd1a`/`f8a8d06`/`6313461`).
   Push HTTPS przez credential manager (bez promptu wg historii).
2. Sprawdzić CI: `gh run list --branch master --limit 3 --json status,conclusion,headSha`
   lub `gh run watch --exit-status`. **UWAGA:** czytać X/✓ per krok, NIE polegać na
   „exit 0" powiadomienia tła. CI scope = `ruff check src tests` + `mypy src` + `pytest`
   (scripts/ POZA scope → 4 pre-existing ruff w scripts/ NIE wywalą CI).
3. Po zielonym CI: domknąć **pending doc-sync z code-review** (osobny task, NIE ruszany
   w tej sesji): liczniki testów 266/268 → **272/274** w `README.md:49,223,316` +
   `docs/executive_summary.html:213`; docstring `multimulti_audit.py:96` „all-clear"→„clear";
   `calibrate_mmd_pool.py:3` kwalifikator naive-OR. (Pełna lista MEMURY.md [2026-06-11].)

Kontekst: task struktury repo WYKONANY i ZWALIDOWANY (pytest 272/2skip, ruff src/tests
+ mypy czyste, wheel zweryfikowany), ale user odłożył push na jutro. Push to jedyna
niezrobiona pozycja DoD taska (kryterium „CI green na pushu").

---

## Co zrobiono w tej sesji

- ✓ **TASK_REPO_STRUCTURE_OPUS48.md WYKONANY** — 9 commitów strukturalnych
  `74bd82d..7348fee`. Decyzje usera (AskUserQuestion): F2=manifest SHA-256,
  F8=minimal (exclude *.md z wheel), F7=zostaw scraper_selectors, F9=CITATION.cff/F10=nie.
  - **F3** py.typed (PEP 561); **F4a** poc→notebooks/ +ref README; **F4b**
    universal-session→docs/templates/ (snake_case); **F6** test_api_key→check_api_key
    (audyt: zero sekretu); **F5** R&D/→docs/research/rd_archive/ (30 plików snake_case
    + README mapujący); **F8-min** exclude `**/*.md` z wheel; **F2** kontraktowa rewizja
    git-lfs→manifest SHA-256 (PROJECT_BRIEF §0 nota + 6 linii sync, CLAUDE.md DoD-6);
    **F1** drzewo CLAUDE.md przepisane 1:1 z git ls-files; **F9** CITATION.cff.
- ✓ **Walidacja DoD taska:** pytest **272 passed / 2 skipped** (zero regresji),
  `ruff check src tests` + `mypy src` czyste, **wheel zbudowany** (py.typed=True, *.md=0,
  prereg=brak), `git --follow` zachowuje historię przenosin.
- ✓ Pamięć: root MEMORY.md wpis **[2026-06-11 sesja 2]** (pełne hashe/decyzje/walidacja/dług).

## Co zostało (backlog sesji)

- ⟳ **NASTĘPNY KROK:** push 13 commitów + CI check + pending doc-sync (zob. wyżej).
- ⟳ **Pending doc-sync z code-review** (drugi task, sekcja 6 „Poza zakresem" struktury):
  liczniki 266/268→272/274, docstring all-clear→clear, kwalifikator calibrate_mmd_pool.
- ⟳ Findingi code-review wymagające DECYZJI: #1 polityka werdyktu `klass='real'` §5
  (OR→Disagreement?); #2 udokumentować ślepotę ≥2/3 na sygnały 1/3-strukturalne.
- ⟳ Dług ruff `scripts/{check_api_key,smoke_test}.py` (4×: I001 + unused `data`) —
  pre-existing, POZA scope CI; do sprzątnięcia przy pracy w tych plikach (zmiana semantyki).
- ⟳ Wizualny check exec summary Ctrl+P = 1×A4; cross-check kalibracji BOCPD n=5000 pool=80.

## Aktywne pliki

- ZMIENIONE (commited): `pyproject.toml` (py.typed pkg + wheel exclude), `CLAUDE.md`
  (DoD-6 + drzewo 1:1), `PROJECT_BRIEF.md` (rewizja §0 lfs→manifest), `README.md`
  (poc path), `CITATION.cff` (NOWY), `src/driftscope/py.typed` (NOWY)
- PRZENIESIONE: `notebooks/poc_permutation_engine.py`, `docs/templates/universal_session_setup_prompt.md`,
  `scripts/check_api_key.py`, `docs/research/rd_archive/` (30+README)
- ACTIVE prereg = **v7** (bez zmian — task strukturalny, methodology/ nietknięte poza wheel-exclude)

## Otwarte pytania

- Kiedy push? (user: jutro). Czy bundlować pending doc-sync w ten sam push czy osobno.
- Finding #1: wiersz EJ 'real' w benchmarku §5 → Disagreement czy OR z caveat?

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-11 sesja 2] TASK_REPO_STRUCTURE WYKONANY** —
  9 commitów, decyzje F2/F7/F8/F9, walidacja, F2 rewizja kontraktowa lfs→manifest, dług ruff scripts/.

## ═══ Sesja zarchiwizowana [2026-06-11 23:50] ═══

# last_session.md

**Sesja:** 2026-06-11 · ~20:45-22:00 (wznowiona po przerwanym /code-review z limitu sesji)
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** f8a8d06 @ master (task struktury repo; LOKALNE — niepushowane: 3e70fef, 448fd1a, f8a8d06 + commit stanu)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Naprawić 4 findingi doc-sync z code-review JEDNYM commitem `docs:` i dopiero potem
push na origin/master + check CI** (`gh run list --branch master --limit 3 --json
status,conclusion,headSha`):
1. Liczniki testów 266/268 → **272 passed / 274 collected**: `README.md:49` ("266 passing"),
   `:223` ("266 passing / 268 collected"), `:316` ("268 tests") oraz
   `docs/executive_summary.html:213` ("268 tests · CI green"). Źródło prawdy: żywy
   `pytest --collect-only -q`.
2. Docstring `run_multimulti_audit` (`src/driftscope/reporting/multimulti_audit.py:96`):
   "Oczekiwany: all-clear" → "Oczekiwany: clear (Disagreement; samotny filar 1/3 = clear)".
3. `scripts/calibrate_mmd_pool.py:3`: dopisać kwalifikator "(FLAG pod ówczesnym werdyktem
   naive-OR, zmienionym w 3e70fef na Disagreement >=2/3)".
4. Opcjonalnie w tym samym commicie: `report.qmd:366` — drukować werdykt MM z kodu
   (`mm.core_fraction` + `mm.disagreement.label` + `mm.verdict` w chunku linie 347-355,
   wzór = sekcja 3 EJ) zamiast statycznej prozy; wymaga re-renderu Quarto → jeśli za drogie
   teraz, przenieść do backlogu.

Kontekst: code-review max na `3e70fef` zakończony — fix poprawny, push NIEBLOKOWANY, ale
punkty 1-3 to dokładnie ta klasa dryfu liczników/dokumentacji, którą naprawiał `7ed0ca6`;
push bez nich od razu reintrodukuje rozjazd na publicznym Pages. Pełna lista 15 findingów
w MEMORY.md [2026-06-11].

---

## Co zrobiono w tej sesji

- ✓ **NASTĘPNY KROK z poprz. sesji DOMKNIĘTY — lokalny `/code-review max` na diffie
  `origin/master..HEAD` (3e70fef)** zamiast retry ultra (który padł na timeout):
  - Pełny pipeline: 9 finderów (5 correctness + 3 cleanup + altitude) → dedup 22→15
    kandydatów → weryfikacja per-kandydat (Phase 2) → sweep (Phase 3, +4) → **finalny
    raport 15 findingów** (ranking w rozmowie; skondensowane w MEMORY.md).
  - **Werdykt: fix poprawny, push nieblokowany.** Top: (1) wiersz EJ 'real' w §5 nadal
    OR → możliwy "EuroJackpot FLAG" po aktualizacji seed CSV; (2) koszt ≥2/3 = ślepota
    nagłówka na defekty strukturalnie-1/3 (pair_corr, constant-bias); (3) 4 szybkie
    doc-sync (liczniki, all-clear, calibrate, report.qmd §6).
  - Sesja przerwana limitem w Phase 2 (2 weryfikatorów padło) — wznowiona bezszwowo.
- ✓ **Review struktury repo + `TASK_REPO_STRUCTURE_OPUS48.md`** (`f8a8d06`): samowystarczalny
  task dla Opus 4.8 — findingi F1-F11 (P0: drzewo CLAUDE.md mocno nieaktualne, martwa
  deklaracja git-lfs bez .gitattributes, brak py.typed; P1: root clutter + `R&D/`;
  P2: scripts + prereg v1-v6 w wheel [DECYZJA USERA]), struktura docelowa, kolejność
  commitów ze STOP-ami, kryteria DoD. Fundamenty (src-layout, PEP 621, CI) ocenione OK.
- ✓ Pamięć: root MEMORY.md wpis **[2026-06-11]** (wyniki review + task struktury).

## Co zostało (backlog sesji)

- ⟳ **NASTĘPNY KROK:** 4× doc-sync → commit `docs:` → push (3e70fef..stan) → CI check.
- ⟳ Findingi code-review wymagające DECYZJI (nie ruszać bez usera):
  - #1: polityka werdyktu dla `klass='real'` w benchmarku §5 (OR → Disagreement?
    dotyka `prng_benchmark.py:57`, `report.qmd:299`, `scripts/prng_benchmark.py:85`,
    `demo/app.py:150`).
  - #2: udokumentować/zmitygować ślepotę ≥2/3 na sygnały 1/3-strukturalne (zdanie
    w docstringu/raporcie; ew. eskalacja przy q<<α w Family B).
- ⟳ Findingi cleanup (przy okazji następnej pracy w tych plikach): walidacja `--window>0`
  + help dla `--alpha`; `DisagreementVerdict.is_convergent` zamiast magic `>=2`;
  testy wiringu filarów (asercje `agreeing`, lone-cooc, mmd+cooc); CSV '1/3' Excel-data;
  alias `core_fraction`; duplikacje prozy ≥2/3 i formatowania Family B.
- ⟳ **TASK_REPO_STRUCTURE_OPUS48.md** — odpalić jako osobne zadanie (Opus 4.8); decyzje
  usera w kroku 7 taska (F2 git-lfs vs manifest, F8 prereg w wheel).
- ⟳ Wizualny check exec summary Ctrl+P = 1×A4 (z poprz. sesji, ryzyko ~zero).
- ⟳ Cross-check kalibracji BOCPD n=5000 pool=80 (opcjonalny — próg length-invariant).

## Aktywne pliki

- `TASK_REPO_STRUCTURE_OPUS48.md` (NOWY — `f8a8d06`)
- Czytane (review, bez zmian): `src/driftscope/reporting/{multimulti_audit,disagreement,prng_benchmark}.py`,
  `scripts/multimulti_audit.py`, `tests/test_generic_pool_invariants.py`, `report.qmd`,
  `README.md`, `pyproject.toml`, `.gitignore`, `.github/workflows/ci.yml`
- ACTIVE prereg = **v7** (bez zmian — sesja czysto review/docs)

## Otwarte pytania

- Finding #1: czy wiersz EJ 'real' w benchmarku ma przejść na Disagreement (spójność) czy
  zostać na OR z caveat w prozie (prostota)? — decyzja przy domykaniu findingów.
- Task struktury: kiedy odpalić Opus 4.8 i które decyzje F2/F8 user wybiera.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-11] CODE-REVIEW max 3e70fef** — werdykt,
  15 findingów (pełne ścieżki/linie), 4× doc-sync przed pushem, task struktury `f8a8d06`.
