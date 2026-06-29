# README_AUDIT.md — Audyt README ↔ kod (dowodowy, wielodziedzinowy + adwersarialny)

**Data audytu:** 2026-06-29 · **HEAD:** `255f6d8` · **Metoda:** każde twierdzenie README
zweryfikowane wobec konkretnego pliku / funkcji / testu, z żywymi uruchomieniami dla liczb
wrażliwych. README = hipoteza, kod = prawda.

**Zakres weryfikacji żywej (wykonane w tej sesji):**
- `pytest -q` (pełny pakiet) → **276 passed, 2 skipped** (109 s).
- `pipeline.run_audit` na seed CSV → czas/RAM, daty CP, posteriory, reżimy, Family B, watchlist.
- `scripts/prng_benchmark.py` z **domyślnymi** parametrami (n_draws=1500, **n_perm=499**).
- Inspekcja źródeł: `pipeline.py`, `multiple_testing.py`, `disagreement.py`,
  `honest_watchlist.py`, `reporting/prng_benchmark.py`, `core/seeds.py`, `core/types.py`,
  `cli.py`, `preregistration_v7.md`, `tests/test_reproducibility.py` + grep testów.

---

## Część A — Tabela claim → evidence

Status: **POTWIERDZONE** / **CZĘŚCIOWE** / **NIEPOTWIERDZONE** / **SPRZECZNE**.

| # | Twierdzenie (README) | Plik / funkcja / test | Status | Dowód / komentarz |
|---|---|---|---|---|
| 1 | 958 real EuroJackpot draws | `data/seed/eurojackpot_history.csv`; live `len(draws)` | POTWIERDZONE | 959 linii − header = 958; run pokazał `N draws: 958` |
| 2 | Multi Multi 16 827 draws, 20-of-80 | `data/seed/multimulti_history.csv`; `DrawRecord.generic` | POTWIERDZONE | 16 828 linii − header = 16 827 |
| 3 | 278 testów (276 pass / 2 skip) | live `pytest` | POTWIERDZONE | `278 collected`; `276 passed, 2 skipped` |
| 4 | ~4.5 s, ~210 MB peak RAM | live timed `run_audit` | POTWIERDZONE (≈) | **4.63 s**, **221 MB** RSS na tej maszynie (i5-12500H). Mieści się w „~". |
| 5 | CP: 2014-11-28 (≈0.41), 2022-03-29 (≈0.40); top peak 2015-01-23 (≈0.47) | `pipeline.run_audit` → `pc.metadata["top_changepoint_*"]`; live summary | POTWIERDZONE | Live: `2015-01-23 (0.47), 2014-11-28 (0.41), 2022-03-29 (0.40)` — co do liczby |
| 6 | R1=133 / R2=389 / R3=436 | live summary; `regime_split` | POTWIERDZONE | Identycznie |
| 7 | R1 0/3 · R2 1/3 · R3 0/3; lone R2 flag = co-occurrence pair | live summary | POTWIERDZONE | `R2 1/3 [... cooccurrence=reject]` — dokładnie |
| 8 | FDR over 150 hypotheses (50×3 regimes, BY) rejects 0/150 | `pipeline.family_b_size`; live | POTWIERDZONE | `benjamini_yekutieli 150 reject 0` |
| 9 | Honest watchlist = None | live; `honest_watchlist.build_watchlist` | POTWIERDZONE | `WATCHLIST: None (honest null)` |
| 10 | n_perm domyślnie 999 (CLI) | `pipeline._DEFAULT_N_PERM`, `cli.run` | POTWIERDZONE | `=999`; `--n-perm` default 999 |
| 11 | Benjamini-Yekutieli (Family B), BH (Family A) | `multiple_testing.correct_family_{a,b}` | POTWIERDZONE | B→`fdr_by` primary + BH secondary; A→`fdr_bh` + Storey |
| 12 | Uzasadnienie BY: 5/50 counts ujemnie zależne, PRDS dla BH niepewne | `multiple_testing.py` docstring + prereg v7 §5 | POTWIERDZONE | Zgodne |
| 13 | Disagreement 3/3·2/3·1/3·0/3 nad 3 filarami | `disagreement.classify`, `PILLARS`, `_LABELS` | POTWIERDZONE | h1/mmd/cooccurrence; etykiety 1:1 |
| 14 | Primary gate = FDR (Family B), konwergencja ≥1 filar; else None | `honest_watchlist.build_watchlist` (`q≤α AND n_agree≥min_convergence=1`) | POTWIERDZONE | Dokładnie ta logika |
| 15 | Komplementarność „near-analytic, confirmed empirically on planted signals" | `tests/test_driftsim_calibration.py::test_chi2_blind_to_pair_correlation`, `tests/test_permutation_null.py::test_serial_blind_to_pair_corr`, `tests/test_cooccurrence.py::test_detects_planted_pair_corr_showcase`, `tests/test_disagreement.py::test_clean_cell_pair_corr_1_of_3` | POTWIERDZONE | Twarde testy na planted signal, nie tylko proza. *Niuans: brak dedykowanego testu ślepoty MMD (chi² = marginal proxy)* |
| 16 | RNG seedowany z zawartości danych (⊕ BASE_SEED), niezależnie od kolejności | `k4_mmd`, `cooccurrence`, `permutation`, `block_bootstrap`, `recurrence`, `information_theory`: `blake2b(matrix.tobytes())⊕base_seed`; `test_detector_call_order_independence` | POTWIERDZONE | Mechanizm realny. *Niuans: hardcoded base_seed 20260531/20260607, nie 42* |
| 17 | Pre-rejestracja zamraża „każdy wybór" + revision_reason clean/data-informed | `methodology/preregistration_v7.md` §0–§7 | POTWIERDZONE | Statystyki/nulle/progi/siatki zamrożone; rewizje z `[disclosed]` clean/data-informed |
| 18 | Roadmap (streaming MMD, Kafka, FastAPI, PyPI, arXiv) = planned, nic shipped | README §Roadmap, §Beyond-the-Lottery; brak w kodzie | POTWIERDZONE | Jawnie „none is shipped"; brak modułów w drzewie |
| 19 | PRNG: 2 good + 2 crypto → clear; 2 defekty → FLAG | live benchmark | POTWIERDZONE | Werdykty 1:1; sensitivity/specificity OK |
| 20 | bias caught narrowly (Family B + MMD, nie co-occ); period caught broadly (3 filary) | live: bias 1/50 + mmd; period 27/50 + mmd + cooc + IT | POTWIERDZONE | Wzorce defektów reprodukują się |
| 21 | IT (LZ76) = suplement, nie 4. filar; real EJ p≈0.70 | `reporting/information_theory.py`; live EJ it_p=0.698 | POTWIERDZONE | Non-voting; p≈0.70 |
| 22 | **PRNG „p = 0.005"** (oba defekty) | `reporting/prng_benchmark.py`; live | **SPRZECZNE** | p=0.005 = **permutation floor 1/(199+1)**. Live default (n_perm=499) → floor **0.002**. Wszystkie wartości w tabeli README to wielokrotności 1/200 ⇒ tabelę wygenerowano **n_perm=199**, nie udokumentowanym default 499. README nie oznacza `p≤`. |
| 23 | „MT19937 co-occ 0.055 (borderline α)" | live n_perm=499: cooc_p=**0.124** | CZĘŚCIOWE | Estymata MC z jednego runu; „borderline" to artefakt szumu, nie własność generatora |
| 24 | MMD FPR = 0.035 (pool 80, 200 trials); BOCPD próg 0.34 | `scripts/calibrate_mmd_pool.py`, `scripts/calibrate_bocpd_threshold.py` (pool=80, k=20) | CZĘŚCIOWE | Skrypty istnieją; 0.035/0.34 to ich OUTPUT (zwalidowane wcześniej, MEMORY). 200-trial sweep nie re-run w tej sesji (drogi). Brak CI w README. |
| 25 | „bit-identical reproduction" (DoD-6) | `tests/test_reproducibility.py`; `scripts/archive.py` | CZĘŚCIOWE | Testy dowodzą determinizmu **same-process** + call-order + manifest. Cross-OS/CPU/BLAS NIE testowany. Manifest haszuje **seed CSV (input)**; README mówi „SHA-256 manifest over the CSV outputs". README hedguje „in the same pinned environment" (poprawnie). |
| 26 | BOCPD próg per-pole (euron / main) | `preregistration_v7.md` §2: euron **0.33** / main **0.70** | POTWIERDZONE | Posteriory 0.40–0.47 > próg euron 0.33 ✓ |
| 27 | „2.7× JIT speedup" | README wskazuje `notebooks/poc_permutation_engine.py` | POTWIERDZONE (source-cited) | Uczciwie zakotwiczone w PoC; nie re-run (PoC = pojedynczy pomiar, README to mówi) |

---

## Część B — Audyt z pięciu ról

### B1. Statystyk (krytyczny recenzent)
**Mocne:** doprecyzowanie „hallucination = Type I error @ α≈0.05" rzetelne i poparte DoD-2;
honest null jako *decision abstention*; jawny „within the power of the test"; thin-regime R1
disclosure (n=133, ~1% shift below detection).
**Słabości:** (a) **p=0.005 to floor**, nie wartość — sugeruje fałszywą precyzję; (b)
**„crypto-grade clear"** ryzykuje sugerowanie *dowodu jakości* zamiast *braku mocy*; (c) **brak
CI** dla FPR=0.035 (n=200, ~±0.013 Wald → spójne z α) i dla 0.055; „borderline α" to szum; (d)
„2.7×" gołe w Highlights (źródło jednak wskazane).
**Poprawki:** `p ≤ 0.005 (floor)`; FPR=0.035 z MC/CI; 1 zdanie „clear = brak dowodu defektu w
granicach mocy, nie certyfikat losowości".

### B2. Laik (czytelnik bez żargonu)
**Termíny przed definicją:** BOCPD, MMD, co-occurrence, posterior, null, FDR, permutacja,
regime, „3/3", PRDS, change-point, Type I error.
**Mocne:** metafory „three expert witnesses", „answer key", „lottery with answer key";
ostrzeżenie „not a lottery predictor" wcześnie (§30-second) — napięcie rozbrojone w porę.
**Słabości:** brak **przykładowego outputu** („co zobaczę po `driftscope run`?"), a realny
output to **polski** `report.summary()` — zgrzyt w EN-README. Brak glos/mini-słowniczka.
**Poprawki:** glosy inline; blok „What you'll see" z przykładowym werdyktem tuż po Quick Start;
rozważyć EN-summary.

### B3. Marketingowiec
**Top haki (z pokryciem w Części A):** (1) „knows when *not* to shout" (honest null); (2)
„a lottery with an answer key" (pos/neg control); (3) „two defects, detected differently"
(bias wąsko / period szeroko); (4) „pre-registered = can't be p-hacked"; (5) „same battery,
second real game, zero code changes" (Multi Multi).
**Kolejność:** „Beyond the Lottery" **za nisko** — to sekcja łapiąca nie-loteryjną publiczność.
Dodać „for whom" w §30-second; rozważyć podniesienie sekcji. Wizualny „przed/po" = tabela PRNG
(clear vs FLAG).
**Uwaga:** hak #3 musi iść z floor-oznaczeniem (inaczej „0.005" wprowadza w błąd).

### B4. Rekruter (dev / data / ML)
**Sygnalizuje:** metodologię (prereg, family-aware FDR), kalibrację (FPR≈α, progi per-pole),
reprodukowalność (pure-function seeding, manifest), inżynierię (Polars/Numba/Pydantic/Typer,
CPU-only, CI-green, 278 testów, mypy --strict).
**Najmocniejsze:** **świadome trade-offy z uzasadnieniem** (joblib NIGDY nad permutacjami;
non-overlap windows; BY zamiast BH) + **decyzja o abstynencji** (None) — rzadka dojrzałość.
**Brakuje:** **linków do konkretnych testów** jako dowód; jeden „engineering decision log";
mocniejsze wykorzystanie pozycjonowania **pharma×AI/ML** w About-the-Author.

### B5. Programista (zastosowania)
Faktyczny API surface: `DrawRecord.generic(draw_date, numbers, pool_size)` →
`list[DrawRecord]` → `pipeline.run_audit(draws) -> AuditReport`. Werdykt:
`report.watchlist is None` (clear) / `report.family_b.n_reject` /
`report.regime_audits[R].verdict.fraction`. **Brak** publicznego `audit_stream(...)`.

| Zastosowanie | Adapter DrawRecord | Entrypoint | Werdykt fail/pass |
|---|---|---|---|
| CI guard RNG/seedów | `generic(date, ints, pool)` per tick | `run_audit` / `reporting.prng_benchmark.run_battery` | `core_votes≥2` → fail |
| Pre-deploy ML drift | kategorie→ints; train vs prod jako 2 okna | `mmd_uniform_detector` / `run_audit` | `mmd.reject_h0` / watchlist≠None → block |
| A/B bucketing / flagi | pary bucketów jako co-występienia | `cooccurrence_detector` | `cooc.reject_h0` |
| QA logów / fraud | zdarzenia→symbole, okno czasowe | `run_bocpd` + co-occurrence | CP>próg / pair flag |
| Walidacja syntetyków | rekordy→generic | `cooccurrence_detector` (margin-preserving null) | `cooc.reject_h0` |

**Do `audit_stream(...)`:** `run_audit` jest *funkcjonalnie* publiczny, ale (a) zakłada regime
split kalendarzowy; (b) brak konstruktora „z iterable/array"; (c) output = dataclass, nie JSON.
Domknięcie: wrapper `audit_stream(iterable, pool_size, k) -> dict` (~30 LOC) + serializacja.

---

## Część C — Dziennik adwersarialny (claim → atak → obrona → werdykt)

| Twierdzenie | Atak | Obrona | Werdykt |
|---|---|---|---|
| „p = 0.005" | floor 1/(n_perm+1), nie wartość; z niezadeklarowanego n_perm=199 | brak — faktycznie floor | **NIE PRZECHODZI → `p ≤ floor`** |
| „0.055 borderline α" | cherry-pick z szumnego runu; live=0.124 | brak | **NIE PRZECHODZI → usunąć/MC-estimate** |
| „honest null = kalibracja, nie ślepota" | null z braku mocy (małe n) | PRNG benchmark = sensitivity dowód; DriftSim power≥0.80 (p≥0.05); R1 thin disclosed | **PRZECHODZI** |
| „bit-identical reproduction" | cross-OS/BLAS/Numba threading złamie | testy = determinizm same-process; README hedguje „pinned env"; manifest haszuje input CSV | **CZĘŚCIOWO → doprecyzować** |
| „three detectors that must agree" | watchlist promuje 1/3 → nie muszą | celowe (pure-pair=1/3); gate=FDR+≥1; wyjaśnione „Why we do not hard-gate ≥2/3" | **PRZECHODZI** (ale „must agree" nadkomunikuje → złagodzić) |
| „does not hallucinate" | cytowalne jako „gwarancja braku błędów" | caveat istnieje, ale 6 sekcji dalej | **CZĘŚCIOWO → przyciągnąć do hasła** |
| „not a lottery predictor" | szuka zdania-obietnicy | brak; ostrzeżenie wczesne | **PRZECHODZI** |
| „150 hypotheses, 0/150" | a kod mówi 450 — selektywne? | prereg v7 §0(A) koryguje 450→150 (omnibus≠per-number); 450 = stara stała | **PRZECHODZI** (kod do poprawy) |
| „pre-registered, can't be p-hacked" | garden-of-forking-paths | v7 zamraża wszystko; rewizje clean/data-informed `[disclosed]` | **PRZECHODZI** |

**Reguła „przetrwa atak własnego adwersarza":** 5/9 czysto; 4 wymaga korekt (floor,
borderline, repro precision, „must agree" + caveat „hallucinate").

---

## Defekty kodu / dokumentacji (znalezione po drodze)

- **SHOULD-FIX (kod):** `methodology/multiple_testing.py` — `FAMILY_B_SIZE = 450` + docstring
  „50 liczb × 3 testy × 3 reżimy" to **stara numeracja (v5)**; prereg v7 §0(A) skorygował do
  **150** (per-number = wyłącznie exact-binomial; chi²/gap/cooc = omnibus, raportowane osobno).
  README (150) jest *poprawniejsze* niż stała w kodzie. → Zaktualizować stałą + docstring do v7.
- **NICE (test):** brak dedykowanego testu ślepoty **MMD** na pair_corr (jest chi² jako marginal
  proxy + serial/H1). Dodać `test_mmd_blind_to_pair_corr` dla pełnej symetrii claimu.
- **NICE (spójność):** detektory używają hardcoded `base_seed` (20260531/20260607), a README/DoD
  mówi „⊕ BASE_SEED" (=42). Determinizm zachowany, ale narrację warto ujednolicić.

---

## Posortowana lista zmian dla README

### MUST FIX
1. **Tabela PRNG — floor.** Oznaczyć `p ≤ 0.005` jako permutation floor `= 1/(n_perm+1)` i
   podać użyte `n_perm`. Rekomendacja: zregenerować tabelę z **udokumentowanego** default
   (n_perm=499 → floor 0.002) i oznaczyć floory; non-floor p opisać jako estymaty MC.
2. **Caveat „does not hallucinate" przy haśle.** Przyciągnąć „within the power of the test,
   α=0.05" do §30-second (dziś 6 sekcji dalej, §Why-You-Can-Trust).

### SHOULD FIX
3. Usunąć/złagodzić „0.055 borderline α"; oznaczyć non-floor p jako MC-estimates (run-specific).
4. **DoD-6 precyzja:** „bit-identical *in the same pinned environment*" przy haśle; sprostować
   „manifest over the CSV outputs" (manifest obejmuje committed seed CSV — potwierdzić zakres).
5. **Złagodzić „must agree"** (Highlights) — np. „…or a single champion detector that also
   clears FDR" — by nie kłóciło się z promocją 1/3.
6. **Przykładowy output `driftscope run` wcześnie** + rozważyć EN-summary (dziś PL).
7. FPR=0.035 z CI/MC-noise; 1 zdanie „crypto clear = brak dowodu defektu w granicach mocy".
8. Podnieść „Beyond the Lottery" / dodać „for whom" w intro.

### NICE TO HAVE
9. Linki do konkretnych testów (dla rekrutera: `test_chi2_blind_to_pair_correlation` itd.).
10. Mini-słowniczek / glosy przy pierwszym użyciu żargonu (BOCPD, MMD, FDR, null, regime).
11. (kod) `FAMILY_B_SIZE` 450→150; dedykowany test MMD-blind; ujednolicić narrację `base_seed`.

---

## Werdykt ogólny

Rdzeń metodologiczny i **wszystkie liczby headline'owe EuroJackpot** się bronią — zweryfikowane
na żywo co do liczby (czas, RAM, daty CP, posteriory, reżimy, 0/150, watchlist None). Pre-rejestracja,
family-aware FDR, Disagreement Protocol, honest gate, komplementarność (twarde testy) i
reusability (DrawRecord) są rzetelne. Realne problemy są **wąsko skupione w sekcji PRNG**
(permutation floor prezentowany jako wartość; non-floor p run-specific) plus drobne nieprecyzyjności
(DoD-6 wording, „must agree", caveat „hallucinate" za daleko od hasła). Po zastosowaniu MUST+SHOULD
README jest jednocześnie rzetelne statystycznie i czytelne — bez utraty haka „wie, kiedy nie krzyczeć".
