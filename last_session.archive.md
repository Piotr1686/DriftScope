## ═══ Sesja zarchiwizowana [2026-06-09 22:40] ═══

# last_session.md

**Sesja:** 2026-06-09 · ~21:00-21:20
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 7ed0ca6 @ master (commit docs MM/exec-summary; pushed na origin)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Naprawić semantykę werdyktu runnera MM: `MultiMultiAuditRow.verdict` (w
`src/driftscope/reporting/multimulti_audit.py`) używa naiwnego OR po WSZYSTKICH
detektorach → zwraca "FLAG" przy samotnym MMD, choć MM jest merytorycznie clear.**
Zmienić na agregację Disagreement: policzyć rejecty wśród **3 filarów rdzeniowych**
(BOCPD-main / MMD / co-occurrence) → ułamek "k/3"; verdict = "clear" gdy konwergencja
<2/3, "FLAG" dopiero ≥2/3. IT = suplement (nie filar), Family B = osobna bramka FDR.
Dodać pole `core_fraction` (lub reuse `reporting/disagreement.classify_from_results`).
Zaktualizować CLI `scripts/multimulti_audit.py` (drukować ułamek + uczciwy verdict,
usunąć mylące "FLAG | Expected: clear"). Dodać test do `tests/test_generic_pool_invariants.py`.

Kontekst: ten dług przeszedł z poprzedniej sesji nietknięty (tę sesję poświęciliśmy
na rozstrzygnięcie 2 otwartych pytań scope, nie na ten krok). Obecny runner drukuje
"FLAG" a potem "Expected: clear" — niespójność załatana prozą w report.qmd, ale sam
werdykt CLI/dataklasy wciąż kłamie. Czysta poprawka semantyki (reporting, poza prereg §0),
reuse istniejącej logiki Disagreement Protocol. NIE pilne, ale najbardziej konkretny dług.

---

## Co zrobiono w tej sesji

- ✓ **Rozstrzygnięto 2 otwarte pytania scope** (decyzja usera przez AskUserQuestion):
  - **Gra 3 (Keno/Lotto) = ZAPARKOWANA** — reusability nasycona przy 2 grach; robić tylko
    gdy pojawi się dataset z known ground-truth change-pointem.
  - **exec summary = EJ-flagship 1-pager + JEDNO zdanie MM callout** (nie pełna sekcja).
- ✓ **Commit docs** (`7ed0ca6`, pushed `133300b..7ed0ca6`):
  - `docs/executive_summary.html`: callout reusability MM 20/80 wpleciony w bullet
    "Performance & clean architecture" (game-agnostic na realnym 2. datasecie; odseparowany
    od figury "958 real draws" EJ-only).
  - Fix stale test count: exec summary **246→268**, README **266→268** (źródło prawdy =
    żywy `pytest --collect-only` = 268).
- ✓ Pamięć: agent `scope_game3_and_exec_summary.md` + index; root MEMORY.md milestone [2026-06-09].
- ✓ Weryfikacja: greps zielone (268 zsynchronizowane, zero resztek 246/266, callout obecny).

## Co zostało (backlog sesji)

- ⟳ **Werdykt runnera MM = Disagreement, nie OR** (NASTĘPNY KROK — dług z 2 sesji).
- ⟳ Wizualny check exec summary Ctrl+P = 1×A4 (ryzyko ~zero — rozszerzony 1 bullet, bez nowego punktu).
- ⟳ CI na `7ed0ca6` (uruchomione tuż przed /end — sprawdzić zielone; zmiany czysto doc).
- ⟳ Cross-check kalibracji BOCPD n=5000 pool=80 (opcjonalny — próg length-invariant).

## Aktywne pliki

- `src/driftscope/reporting/multimulti_audit.py` (verdict semantyka — następny krok)
- `scripts/multimulti_audit.py` (CLI — następny krok)
- `tests/test_generic_pool_invariants.py` (dodać test werdyktu)
- (zacommitowane+pushed) `docs/executive_summary.html`, `README.md`
- ACTIVE prereg = **v7** (bez zmian — MM = reusability/reporting, poza §0)

## Otwarte pytania

- (brak — oba pytania scope z poprzedniej sesji rozstrzygnięte)

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-09] DECYZJE SCOPE** — gra 3 zaparkowana,
  MM callout w exec summary, fix test count 246/266→268, commit `7ed0ca6` pushed.
- Pamięć agenta: `scope_game3_and_exec_summary.md` (project) + wpis w MEMORY.md index.

## ═══ Sesja zarchiwizowana [2026-06-09 21:16] ═══

# last_session.md

**Sesja:** 2026-06-08 · ~21:50-22:25
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 133300b @ master (ostatni commit kodu MM; ten zapis stanu = kolejny commit on top)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Naprawić semantykę werdyktu runnera MM: `MultiMultiAuditRow.verdict` (w
`src/driftscope/reporting/multimulti_audit.py`) używa naiwnego OR po WSZYSTKICH
detektorach → zwraca "FLAG" przy samotnym MMD, choć MM jest merytorycznie clear.**
Zmienić na agregację Disagreement: policzyć rejecty wśród **3 filarów rdzeniowych**
(BOCPD-main / MMD / co-occurrence) → ułamek "k/3"; verdict = "clear" gdy konwergencja
<2/3, "FLAG" dopiero ≥2/3. IT = suplement (nie filar), Family B = osobna bramka FDR.
Dodać pole `core_fraction` (lub reuse `reporting/disagreement.classify_from_results`).
Zaktualizować CLI `scripts/multimulti_audit.py` (drukować ułamek + uczciwy verdict,
usunąć mylące "FLAG | Expected: clear"). Dodać test do `tests/test_generic_pool_invariants.py`.

Kontekst: obecny runner drukuje "FLAG" a potem "Expected: clear" — niespójność załatana
prozą w report.qmd (poprawnie tłumaczy 1/3=not-a-finding), ale sam werdykt CLI/dataklasy
wciąż kłamie. To czysta poprawka semantyki (reporting, poza prereg §0), reuse istniejącej
logiki Disagreement Protocol. NIE pilne (MM gra 2 jest funkcjonalnie kompletna), ale to
najbardziej konkretny dług jakościowy z tej sesji.

---

## Co zrobiono w tej sesji

- ✓ **Krok 6 — runner MM** (`0501b6b`): `load_generic_seed_csv(path, pool_size)` (agnostyczny
  loader CSV), `reporting/multimulti_audit.py` (`run_multimulti_audit` + `MultiMultiAuditRow`,
  okno 2000, reuse `prng_benchmark.run_battery`), CLI `scripts/multimulti_audit.py`.
- ✓ **Krok 8 — kalibracja + testy** (`b02709e`): FINDING ROZSTRZYGNIĘTY — runner dał FLAG
  przez graniczny MMD (p=0.03); hipoteza inflacji MMD pool=80 OBALONA (200 trials: window=25→
  FPR=0.035). MM FLAG = lone false-positive (1/3) wchłonięty przez Disagreement. Brak zmiany
  konfiguracji, prereg v7 nietknięty. `tests/test_generic_pool_invariants.py`. Gotcha: 2 inwersje
  dat w MM seed (2010) → runner sortuje defensywnie.
- ✓ **Krok 7 — raport** (`133300b`): `report.qmd` sekcja 6 "Second real-world case study —
  Multi Multi" (Reproducibility→7), narracja uczciwa. README sekcja reusability + liczby 260→266.
  Re-render quarto, `docs/{report,index}.html` zweryfikowane grep-em przed kopiowaniem.
- ✓ **Push** `0e04caf..133300b` na origin/master. **CI = success** (2m57s, ruff+mypy+pytest ubuntu).
- ✓ MEMORY.md (root: milestone [2026-06-08]; agent: `mm_mmd_fpr_pool80.md` rozstrzygnięcie + index).

## Co zostało (backlog sesji)

- ⟳ **Werdykt runnera MM = Disagreement, nie OR** (NASTĘPNY KROK).
- ⟳ Cross-check kalibracji BOCPD n=5000 pool=80 (opcjonalny, pominięty — próg length-invariant).
- ⟳ `docs/executive_summary.html` — osobny EJ 1-pager, NIE re-renderowany; liczba testów może
  być stale (260). Drobne — do rozważenia czy w ogóle MM tam wchodzi.
- ⟳ Ewentualna gra 3 (Keno/Lotto) — generyczny loader + parametryzacja gotowe; diminishing returns.

## Aktywne pliki

- `src/driftscope/reporting/multimulti_audit.py` (verdict semantyka — następny krok)
- `scripts/multimulti_audit.py` (CLI — następny krok)
- `tests/test_generic_pool_invariants.py` (dodać test werdyktu)
- (zacommitowane+pushed) `ingestion/lotto_scraper.py`, `scripts/calibrate_mmd_pool.py`,
  `reporting/report.qmd`, `README.md`, `docs/{report,index}.html`
- ACTIVE prereg = **v7** (bez zmian — MM = reusability/reporting, poza §0)

## Otwarte pytania

- Czy MM warto dodać do `executive_summary.html` (1-strona), czy zostaje EJ-only.
- Czy robić grę 3 (reusability już udowodniona 2 grami — wartość krańcowa maleje).

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-08] MULTI MULTI GRA 2 DOMKNIĘTA** — kroki 6+8+7,
  3 commity pushed, finding MMD pool=80 rozstrzygnięty (FPR=0.035, lone-FP nie defekt), gotcha
  inwersje dat, CI success.
- Pamięć agenta: `mm_mmd_fpr_pool80.md` przepisany na ROZSTRZYGNIĘTE (hipoteza inflacji obalona) + index.

## ═══ Sesja zarchiwizowana [2026-06-08 22:23] ═══

# last_session.md

**Sesja:** 2026-06-07 · ~22:45-23:20
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** a21cc92 @ master (commit kodu MM; ten zapis stanu = kolejny commit on top)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Krok 6 planu — runner MM negative-control-only: utworzyć `src/driftscope/reporting/multimulti_audit.py`**
(ścieżka jak `reporting/prng_benchmark.py`, POZA prereg §0). Wczytać `data/seed/multimulti_history.csv`
przez generyczny loader (DrawRecord.generic, pool_size=80), na **OGRANICZONYM oknie** (np. ostatnie
~1500-2000 losowań — NIE pełne 16827, bo BOCPD jest O(T²)), policzyć baterię: BOCPD(field="main") +
MMD + cooccurrence + Family B + IT (reuse `pipeline.default_pillar_detectors`/
`family_b_per_number_pvalues`, `information_detector`, `multiple_testing.correct_family_b`). Struktura
wyniku jak `BenchmarkRow` (flagged/verdict). Oczekiwany wynik: **all-clear**. CLI prezentacji w
`scripts/multimulti_audit.py`.

Kontekst: kroki 1-5 (parametryzacja + dane + kalibracja) są DONE i zacommitowane (a21cc92), EJ
regression = 0. Smoke MM na 800 losowaniach już przeszedł all-clear (BOCPD 0.221<0.34, Family B 0/80).
Brakuje generycznego loadera CSV (obecny `load_seed_csv` jest EJ-specyficzny — main_1..5/euron) →
dodać `load_generic_seed_csv(path, pool_size)` w `ingestion/lotto_scraper.py` lub w runnerze.

Plan całości: `C:\Users\plazo\.claude\plans\flickering-stirring-lovelace.md` (zatwierdzony).

---

## Co zrobiono w tej sesji

- ✓ **Krok 0 — regression gate**: baseline 260 passed / 2 skipped; mypy --strict clean; ruff src clean
  (8 błędów ruff to pre-existing dług w notebooks/poc/scripts — POZA src, nie nasze).
- ✓ **Krok 1 — dane MM**: `data/seed/multimulti_history.csv` (16827 losowań 1996-2026) + konwerter
  `scripts/convert_mm_seed.py` ze źródła `wynikilotto.net.pl/download/multi_multi.csv`.
- ✓ **Krok 2 — unified `DrawRecord`** (`core/types.py`): pola EJ opcjonalne + `numbers`/`pool_size`,
  `model_validator` XOR, `DrawRecord.generic()`. Back-compat EJ zweryfikowany.
- ✓ **Krok 3 — przekrojowa parametryzacja pool/k**: detektory wyprowadzają pool/k z rekordów
  (8 modułów: cooccurrence, recurrence, k4_mmd, permutation, block_bootstrap, information_theory,
  pipeline.family_b, calibration.chi2, h1_classical.run_bocpd). **EJ regression = 0** (260 passed).
- ✓ **Krok 4 — `generate_generic_uniform`** (`driftsim/null_uniform.py`) — honest null k-z-pool bez euron.
- ✓ **Krok 5 — kalibracja BOCPD(80,20)**: p95=0.3314 (n=2000, trials=200, FPR@p95=0.05) → próg 0.34
  w `_MAIN_REJECT_THRESHOLD_BY_POOL`. Skrypt rozszerzony o `calibrate_generic`.
- ✓ **Smoke MM end-to-end** (800 losowań): all-clear (BOCPD 0.221, Family B 0/80, min_q=0.959).
- ✓ **Commit kodu** `a21cc92` (feat, 14 plików). mypy + ruff src czyste po wszystkim.
- ✓ MEMORY.md (root + agent) zaktualizowane.

## Co zostało (backlog sesji)

- ⟳ **Krok 6 — runner MM** (NASTĘPNY KROK) + generyczny loader CSV.
- ⟳ **Krok 7 — sekcja „Second real-world case study: Multi Multi" w `report.qmd`** + re-render docs + README.
- ⟳ **Krok 8 — walidacja**: FPR/kalibracja sanity pool=80; pełny suite + nowy `tests/test_generic_pool_invariants.py`.
- ⟳ Cross-check kalibracji BOCPD n=5000 (opcjonalny, potwierdza niezmienniczość względem długości; ~kilkanaście min O(T²)).
- ⟳ Push commitów (origin za d8df02f; lokalnie a21cc92 + state on top) — do decyzji.

## Aktywne pliki

- (następna sesja) `reporting/multimulti_audit.py` (nowy), `scripts/multimulti_audit.py` (nowy CLI),
  `ingestion/lotto_scraper.py` (generyczny loader), `reporting/report.qmd`, `tests/test_generic_pool_invariants.py` (nowy)
- (zacommitowane a21cc92) `core/types.py`, `methodology/*`, `pipeline.py`, `driftsim/null_uniform.py`,
  `reporting/information_theory.py`, `data/seed/multimulti_history.csv`, `scripts/{convert_mm_seed,calibrate_bocpd_threshold}.py`
- ACTIVE prereg = **v7** (bez zmian — MM to reusability/reporting + parametryzacja, poza §0)

## Otwarte pytania

- **Okno analizy runnera MM** — ile ostatnich losowań (1500? 2000?) vs pełne 16827 (BOCPD O(T²) wyklucza pełne).
- **Lokalizacja generycznego loadera CSV** — `ingestion/lotto_scraper.py` (`load_generic_seed_csv`) vs lokalnie w runnerze.
- **Czy MM trafia do `report.qmd` jako pełna sekcja** (jak PRNG) czy lżejsza nota.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-07 sesja 4] IMPLEMENTACJA MM kroki 1-5 DONE** —
  technika „detektory wyprowadzają pool/k z rekordów", unified DrawRecord, próg BOCPD per-pool
  (80→0.34, nieintuicyjnie < 50→0.70 bo wyższe K/N), źródło danych, gotcha BOCPD O(T²).
- Pamięć agenta: `mm_parametrization_pool_k.md` (nowy wpis + index).

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
