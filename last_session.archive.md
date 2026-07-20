## ═══ Sesja zarchiwizowana [2026-07-20 23:22] ═══

# last_session.md

**Sesja:** 2026-07-19/20 · przedłużona (audyt bojowy + World Lottery Audit + i18n)
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 6cd9f8d @ master (zsynchronizowany z origin/master, CI zielone)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Ścieżka B: adapter `BeaconStream` (RANDAO/drand/NIST) — research źródeł danych + implementacja.**
Zacznij od researchu API: Ethereum RANDAO (beacon chain `randao_mix` per epoka — beaconcha.in
API lub bezpośrednio z beacon node), drand (League of Entropy, publiczne REST API) i NIST
Randomness Beacon jako kontrole crypto-clean. Zaprojektuj `BeaconStream` wg protokołu
`BitStream` z `src/driftscope/ingestion/rng_streams.py` (patrz `MT19937Stream`/`ChaCha20Stream`
jako wzorzec adaptera), potem `draws_from_stream` bez zmian. Cel: audyt manipulowalności
RANDAO (proposer withholding) tą samą baterią co PRNG benchmark.

Kontekst: user zdecydował (2026-07-19) na wdrożenie „w boju" DriftScope = ścieżka A (World
Lottery Audit) + B (RANDAO) sekwencyjnie, po odrzuceniu 9 linków AI/Kaggle usera jako
metodologicznie nieadekwatnych (brak struktury k-z-N z uniform nullem). **Ścieżka A w pełni
SHIPPED tej sesji** (dane + kalibracja + runner + raport + push + CI zielone) — zob.
MEMORY.md [2026-07-19]. B jest logicznym następnym krokiem na tej samej infrastrukturze.

---

## Co zrobiono w tej sesji

- ✓ **Dokończony Batch 5 i18n** — `tests/` 20 plików PL→EN (`7b992a7`), 277 pass, ruff clean.
- ✓ **Audyt generalizowalności kodu** — potwierdzono ~85% reużywalności frameworka poza EJ
  (pool_size w 13 plikach, progi per-pool, szablon runnera = multimulti_audit).
- ✓ **Odrzucone 9 linków AI/Kaggle usera** (metodologicznie nieadekwatne) + wybrana ścieżka
  A+B (World Lottery Audit → RANDAO), zapisane w pamięci agenta.
- ✓ **A1 — dane:** oficjalne CSV z data.ny.gov (Powerball 1968 losowań, Mega Millions 2520
  losowań) → `scripts/convert_ny_lottery.py` → seedy w `data/seed/` (`ad741e8`).
- ✓ **A2 — kalibracja:** coverage warm-up `ceil((N/k)·H_N)` dla pul k=5 (domyślny `N//K`
  rażąco nie pokrywał transientu coupon-collector); progi BOCPD pool 69→0.49, 75→0.39.
- ✓ **A3 — runner:** `reporting/lottery_audit.py` + CLI + 5 testów (`5dd9942`). **WYNIK: 4/4
  udokumentowanych zmian matrycy wykryte blind (day-zero MM 2013, shrink 2017 złapany przez
  Family B, PB 2015 near-miss p=0.065), 0 spurious onsetów.**
- ✓ **A4 — raport:** sekcja 7 `report.qmd` (live chunk) + tabele README EN/PL + re-render
  `docs/` (webm+plotly zweryfikowane) + push + CI ubuntu zielone 2m25s (`6cd9f8d`).
- ✓ Suite końcowa: **284 collected (282 pass / 2 skip)**.

## Co zostało (backlog sesji)

- ⟳ **Ścieżka B (RANDAO/beacony)** — patrz NASTĘPNY KROK powyżej. Nierozpoczęte.
- ⟳ **Migracja i18n — reszta:** `scripts/` (Batch 6, ~10 plików, teraz +2 nowe: `convert_ny_lottery.py`
  już EN, `lottery_audit.py` już EN), flip konwencji `CLAUDE.md` („Język komentarzy: polski"→EN),
  `preregistration_v7.md` → EN, `demo/app.py` (opcjonalne). `notebooks/` świadomie poza zakresem.
- ⟳ Stretch A (NIE weszły do raportu): strumienie bonus (k=1, cooc N/A dla pojedynczej liczby),
  UK Lotto (licencja mirrorów pełnej historii TBD — oficjalne archiwum tylko ~180 dni),
  rodzynki rygoru (Bułgaria 2009, RPA 2020 single-event fallacy, moc na fraud Tiptona).

## Aktywne pliki

- NOWE (committed, pushed): `scripts/convert_ny_lottery.py`, `data/seed/{powerball,megamillions}_{,bonus_}history.csv`,
  `src/driftscope/reporting/lottery_audit.py`, `scripts/lottery_audit.py`, `tests/test_lottery_audit.py`,
  `src/driftscope/methodology/h1_classical.py` (`_MAIN_REJECT_THRESHOLD_BY_POOL` +69/+75).
- ZMIENIONE: `report.qmd` (nowa sekcja 7, Reproducibility→8), `README.md`/`README.pl.md`
  (sekcja World Lottery Audit + test count 279→284), `docs/report.html`/`docs/index.html` (re-render).
- ZROBIONE wcześniej w sesji: `tests/*.py` (20 plików, i18n).
- DO ZROBIENIA (i18n): `scripts/*` (reszta), `CLAUDE.md`, `preregistration_v7.md`, `demo/app.py`.

## Otwarte pytania

- Brak blokujących. Repo zsynchronizowane, working tree czyste (poza plikami stanu tej sesji),
  CI zielone na `6cd9f8d`.
- UK Lotto do ścieżki A: czy szukać mirrora z pełną historią (merseyworld / Kaggle) i
  weryfikować licencję, czy zostawić PB+MM jako wystarczający dowód replikacji?

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-07-19]** — World Lottery Audit (Ścieżka A)
  SHIPPED: dane real (data.ny.gov), coverage warm-up dla pul k=5, runner z onset-based
  localization + kontrastem Family B, 4/4 zdarzeń wykrytych blind, 0 spurious. Asymetria
  BOCPD (natychmiastowy na nowy symbol, ślepy na wycofanie) jako finding komplementarności
  na realnym ground truth. Gotcha SSL (AVG MITM) — `httpx verify=ssl.create_default_context()`.
  HEAD=`6cd9f8d`, pushed, CI zielone.
- Agent-memory: [Battle deployment A+B](battle_deployment_a_plus_b.md) zaktualizowany o wyniki A.

## ═══ Sesja zarchiwizowana [2026-07-20 21:49] ═══

# last_session.md

**Sesja:** 2026-06-29 · ~przedłużona (audyt + migracja EN)
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 4ed01bb @ master (zsynchronizowany z origin/master)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Kontynuuj migrację PL→EN — Batch 3: `driftsim/` + `adaptive/` + `pipeline.py` (docstringi/komentarze).**
Konkretnie przetłumacz prozę (docstringi, komentarze, komunikaty błędów; kod 1:1) w:
`src/driftscope/driftsim/{null_uniform,planted_signals,calibration}.py`,
`src/driftscope/adaptive/honest_watchlist.py` (zostały docstringi — komunikaty już EN),
`src/driftscope/pipeline.py` (zostały docstringi — output już EN).
Po każdym: `ruff check` + `mypy --strict` + odpowiednie testy; uważaj na (a) komunikaty
błędów matchowane w testach, (b) E501 po wydłużeniu PL→EN. Commit per batch.

Kontekst: user zdecydował (2026-06-29) że CAŁY projekt ma być po angielsku poza
`README.pl.md`. Zakres A „shipped+active". ZROBIONE: core/ + ingestion/ + methodology/
(15 plików). ZOSTAŁO ~39 plików .py + reporting/ + tests/ (25) + scripts/ (10) + demo/ +
report.qmd + preregistration_v7.md + flip konwencji w CLAUDE.md + re-render HTML.

---

## Co zrobiono w tej sesji

- ✓ **Audyt README↔kod** (`CLAUDE_CODE_README_AUDIT_PROMPT.md`) — dowodowy (27 claimów, żywe runy), 5 ról, runda adwersarialna. Deliverables `docs/audit/README_AUDIT.md` + `README_REVISED.md/.pl.md` (commit `c6104d5`). Główny finding: `p=0.005` PRNG = permutation floor (n_perm=199, nie default 499), nieoznaczony.
- ✓ **MUST fixy README** (`5e6205b`): floor `≤` w tabeli PRNG + caveat halucynacji przy haśle (EN+PL).
- ✓ **B — defekt kodu** (`09b5044`): `FAMILY_B_SIZE 450→150` (numeracja v7).
- ✓ **SHOULD/NICE** (`f17242a`+`28b50aa`): mini-słowniczek, „What you'll see", złagodzone „must agree", DoD-6 wording, FPR CI, „Beyond the Lottery" wyżej, linki do testów, **nowy `test_mmd_blind_to_pair_corr`**, **output CLI/raportu PL→EN**. Testy 279 collected (277 pass/2 skip).
- ✓ **START migracji PL→EN** (zakres A): `core/` (`1606e64`), `h1_classical`+`k4_mmd` (`c67eeb4`), reszta `methodology/` (`4ed01bb`) — 15 plików, ruff+mypy+testy zielone po każdym batchu.
- ✓ **Push** — wszystko na origin/master, `## master...origin/master` (synced 0/0).

## Co zostało (backlog sesji)

- ⟳ **Migracja EN — Batch 3+:** driftsim/, adaptive/, pipeline.py (docstringi) → potem reporting/ (6 plików), tests/ (25), scripts/ (10), demo/app.py.
- ⟳ **report.qmd** + **preregistration_v7.md** → EN; **flip CLAUDE.md** („Język komentarzy w kodzie: angielski"); **re-render** report.html/executive_summary.html (Quarto — może wymagać quarto CLI).
- ⟳ Residuum: `docs/report.html`/`executive_summary.html` mogą nieść starą tabelę PRNG (n_perm=199) + polskie summary — domknie się przy re-renderze.
- ⟳ `docs/audit/README_REVISED.*` zastąpione przez żywe README (zostają jako ślad audytowy).

## Aktywne pliki

- ZROBIONE (committed, pushed): `src/driftscope/{core,ingestion,methodology}/*.py` (EN), README.md/README.pl.md (fixy+EN output example), `multiple_testing.py` (FAMILY_B_SIZE), `pipeline.py`/`cli.py`/`adaptive/honest_watchlist.py` (output EN, docstringi nadal PL), `tests/test_mmd_properties.py` (+test), `docs/audit/*`.
- DO ZROBIENIA: `src/driftscope/{driftsim,reporting,adaptive,pipeline.py}` docstringi, `tests/*`, `scripts/*`, `demo/app.py`, `report.qmd`, `preregistration_v7.md`, `CLAUDE.md`.
- ACTIVE prereg = **v7** (treść bez zmian; tłumaczenie EN zaplanowane).

## Otwarte pytania

- Brak blokujących. Repo zsynchronizowane, working tree czyste.
- Czy `tests/` docstringi tłumaczyć w pełni (zakres A je obejmuje) — TAK wg decyzji, ale to objętościowo największy kawałek.

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-06-29]** — audyt README↔kod + MUST/SHOULD/NICE fixy + START migracji PL→EN (core+ingestion+methodology done, 15 plików). HEAD=`4ed01bb`, pushed. Decyzja: cały projekt EN poza README.pl.md; odpowiedzi asystenta zostają PL.
- Agent-memory: bez nowego wpisu (realizacja zapisana w repo + MEMORY.md projektu).

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

