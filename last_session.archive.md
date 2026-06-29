## ═══ Sesja zarchiwizowana [2026-06-29 18:40] ═══

# last_session.md

**Sesja:** 2026-06-27 · ~21:30-21:50
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 7a4010d @ master (zsynchronizowany z origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Strategiczna decyzja: framework „done" (Ścieżka A) vs pivot predykcyjny vs polish.**
Brak twardego zadania technicznego w kolejce — wszystkie rekomendowane kroki
portfolio-readiness domknięte. Konkretne opcje do wyboru przy następnym /start:
(a) profile README + pinned repo na koncie GitHub (poza tym repo); (b) ostrożny
redakcyjny K4 README (re-weight „What I built" wyżej, bez psucia lejka);
(c) stretch techniczny (np. analiza pary (10,25) z R2, streaming MMD z roadmapy).

Kontekst: po wgraniu social preview i dwujęzycznym README projekt jest w pełni
domknięty jako portfolio (Ścieżka A). Następna sesja to wybór kierunku, nie
kontynuacja taska — dlatego brak pojedynczego „pliku do edycji".

---

## Co zrobiono w tej sesji

- ✓ **Social preview WGRANY** (user, web-UI) — domknięty ostatni rekomendowany krok portfolio-readiness z 2026-06-26. `docs/assets/social_preview.png` aktywny jako Open Graph card.
- ✓ **Dwujęzyczny README** (`7a4010d`): `README.md` (kanoniczny EN) przepisany + `README.pl.md` (tłumaczenie 1:1) NOWY — układ Neural-Mosaic: przełącznik języka, 6 badge'y, hero (social_preview), ToC, **parytet 20 sekcji**, kotwice PL z polskimi znakami.
- ✓ **Nowe sekcje wyciągnięte Z KODU:** Configuration (8 kluczy `.env.example`), Usage (flagi CLI z `cli.py`), Requirements (stack z `pyproject`). Liczba testów **278** zweryfikowana `pytest --collect-only`.
- ✓ **Weryfikacja LZ76/bz2** — opis w README zgodny z `reporting/information_theory.py` (bz2 = cross-check w metadata, NIE w reject_h0). Nic nie poprawiano.
- ✓ **Push** — oba commity (`5d9ccbb` session-state + `7a4010d` README) → origin/master; repo synced 0/0.

## Co zostało (backlog sesji)

- ⟳ Profile README + pinned repo na koncie GitHub (poza tym repo).
- ⟳ K4 ostrożny re-weight README (opcjonalne, redakcyjne — świadomie pominięte 2026-06-26).
- ⟳ Hygiena Pages-deploy Node20 (wymaga scope `workflow`; niski ROI).
- ⟳ Stretche techniczne: analiza pary (10,25) z R2, pełna piątka RNG (zrobione), streaming MMD (roadmap).
- ⟳ Strategiczne: framework „done" (Ścieżka A) vs pivot predykcyjny (`project_pivot_prediction.md`).

## Aktywne pliki

- ZMIENIONE (committed, pushed): `README.md` (przepisany EN), `README.pl.md` (NOWY), `MEMORY.md` (wpis [2026-06-27]).
- ACTIVE prereg = **v7** (bez zmian — docs/meta-only, zero methodology).

## Otwarte pytania

- Brak blokujących. Repo w pełni zsynchronizowane, working tree czyste.
- Strategiczne (nie blokuje): kierunek następnej sesji — Ścieżka A „done" vs polish vs stretch vs pivot.

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-27]** — dwujęzyczny README EN/PL (układ Neural-Mosaic), social preview wgrany, sekcje Configuration/Usage/Requirements z kodu, weryfikacja LZ76/bz2, parytet 20 sekcji, kotwice PL. HEAD=`7a4010d`, pushed.
- Agent-memory: bez nowego wpisu (realizacja w pełni zapisana w repo + MEMORY.md projektu).

## ═══ Sesja zarchiwizowana [2026-06-27 21:50] ═══

# last_session.md

**Sesja:** 2026-06-26 · ~20:40-21:35
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** a345fb4 @ master (zsynchronizowany z origin/master, CI green)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Wgrać social preview ręcznie:** GitHub repo → **Settings → (General) → Social preview →
Edit → Upload an image** → wybrać `docs/assets/social_preview.png` (1280×640, już w repo).

Kontekst: to JEDYNY pozostały rekomendowany krok portfolio-readiness, którego nie da się
zautomatyzować — GitHub nie ma API (REST/GraphQL) do social preview, to funkcja wyłącznie
web-UI. Mój token `gh` (scope `repo`) zrobił już wszystko inne (About, Release v0.1.0, push).
Po wgraniu: framework + portfolio w pełni domknięte.

Alternatywnie (opcjonalne, do decyzji): (a) ostrożny wariant **K4** — podciągnąć skondensowane
„What I built" wyżej w README (bez re-orderingu lejka); (b) przygotować `deploy-pages.yml`
do ręcznego pusha (hygiena Node20 — wymaga scope `workflow`, którego token nie ma; niski ROI).

---

## Co zrobiono w tej sesji

- ✓ **Adwersarialny audyt README** — 3 agenci (fact-check / sceptyk statystyczny / krytyk klarowności). Werdykt: liczby solidne (cała tabela PRNG zgodna z `report.html`), ale overclaim przez przemilczenie + redundancja.
- ✓ **Korekty NAPRAWCZE N1–N7** (`a80e1ce`): ujawniony top-1 CP 2015-01-23 (aftershock); „independent"→„complementary"; Benjamini-Yekutieli „arbitrary dependence"; caveat mocy R1 n=133; licznik 278; crypto-bullet jako negative control; „bit-identical" zawężone do pinned env.
- ✓ **Polish KLAROWNOŚCI K1/K3/K7/K8** (`df9c05d`): skrócony hard-gate, 6→3 domeny, quickstart, roadmap. K2/K4/K5/K6 świadomie pominięte.
- ✓ **Portfolio-readiness batch:** About przez `gh` (opis+homepage+12 topiców, było puste); `pyproject` metadane (`05570e9`: urls/keywords/classifiers — naprawiona gotcha TOML zagnieżdżenia `dependencies`); **Release v0.1.0** (tag+notes); social card 1280×640 (`c6420bf`); CONTRIBUTING + issue/PR templates (`a345fb4`).
- ✓ Wszystkie 5 commitów wypchnięte na origin/master; CI zielone (run `28261897434`).

## Co zostało (backlog sesji)

- ⟳ **Social preview upload** (ręczne, user — patrz NASTĘPNY KROK). Jedyny pozostały rekomendowany item.
- ⟳ K4 ostrożny re-weight README (opcjonalne, redakcyjne).
- ⟳ Hygiena Pages-deploy Node20 (wymaga scope `workflow`; niski ROI, świadomie odłożone).
- ⟳ Profile README + pinned repo na koncie GitHub (poza tym repo).
- ⟳ Strategiczne: framework „done" (Ścieżka A) vs pivot predykcyjny (`project_pivot_prediction.md`).

## Aktywne pliki

- ZMIENIONE (committed, pushed): `README.md` (N1–N7 + K1/K3/K7/K8), `pyproject.toml` (urls/keywords/classifiers), `docs/assets/social_preview.png` (NOWY), `CONTRIBUTING.md` (NOWY), `.github/PULL_REQUEST_TEMPLATE.md` + `.github/ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml` (NOWE)
- ACTIVE prereg = **v7** (bez zmian — reporting/docs/meta-only)

## Otwarte pytania

- Brak blokujących. Social preview czeka na ręczne wgranie (limit GitHuba, nie uprawnień).
- Strategiczne: czy robić ostrożny K4, czy framework „done".

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-26]** — adwersarialny audyt README, korekty N1–N7, polish K1/K3/K7/K8, batch portfolio-readiness (About/Release/pyproject/social/community-health), oraz finding dostępu `gh` (scope `repo` tak / `workflow` nie; social preview = BRAK API GitHub). HEAD=`a345fb4`, pushed.
- Agent-memory: bez nowego wpisu (realizacja w pełni zapisana w repo + MEMORY.md projektu).

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
