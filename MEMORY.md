# MEMORY.md — Długoterminowa pamięć projektu DriftScope

> Ten plik kumuluje wiedzę o projekcie. Nigdy nie usuwaj wpisów — tylko dopisuj.
> Każdy wpis oznaczaj datą w formacie [YYYY-MM-DD].

---

## Architektura

**[2026-05-26] PIVOT STRATEGICZNY — kierunek: predykcja na bazie anomalii**
User zakwestionował założenie ~50% take rate jako potencjalnie mylące (nie zweryfikowane empirycznie — pochodzi z ogólnych szacunków dla loterii europejskich, nie z oficjalnych danych EuroJackpot). Decyzja: na początku kolejnej sesji obmyślić plan rozszerzenia architektury DriftScope od audytu stacjonarności → w kierunku predykcji liczb opartej na wykrytych anomaliach statystycznych (niejednorodność, autocorrelacja, periodyczność). Zachować obecny audit framework jako warstwę bazową. Kluczowe pytania: (1) rzeczywisty take rate z oficjalnych raportów, (2) minimalne effect size eksploatowalne predykcyjnie, (3) komponenty do dodania: posterior Dirichlet per liczba, rolling window, Kelly criterion, alert system.

**[2026-05-26] W1 DONE — core/ + h1_classical.py + testy 27/27**
Zaimplementowano: `core/{config,types,seeds,guards}.py`, `methodology/h1_classical.py`, `ingestion/lotto_scraper.load_seed_csv()`, `tests/test_h1_invariants.py` (10 testów). Wszystkie 27 testów zielone (9 skipped stubs). DoD-1a (KPSS rejects na pełnym szeregu euron) i DoD-1b (BOCPD top-5 pokrywa 2014 ±60 dni + 2022 ±30 dni) spełnione.

**[2026-05-26] pyproject.toml — hatchling jako build backend**
Wybór: hatchling (nie setuptools). Uzasadnienie: lżejszy, natywna obsługa `src/` layout bez dodatkowej konfiguracji, PEP 621 native. `driftscope = "driftscope.cli:app"` jako CLI entrypoint.

**[2026-05-26] numba==0.65.1 — PINNED (nie range)**
`numba==0.65.1` z `==` zamiast `>=0.65,<0.66`. Uzasadnienie: zweryfikowane na Win11 + numpy 2.2.5 (PoC 2026-05-17); ryzyko regresji przy patch update na Windows jest realne. Jedyna biblioteka pinned dokładnie.

**[2026-05-26] test_environment.py — zastąpiony (był PyTorch/CUDA-focused)**
Oryginalny plik sprawdzał torch, nvidia-smi, onnxruntime — nieistotne dla CPU-only pipeline. Zastąpiony testami: Python 3.10.x, numpy 2.x, numba 0.65.x, JIT basic + cache=True, frequency vector primitive, key imports, joblib loky, MSVC Win32. Zachowany plik `scripts/smoke_test.py` jako quick diagnostic (nie pytest).

**[2026-05-26] test_vram_invariants.py — RAM invariants (nie VRAM)**
Nazwa zachowana z template; "VRAM" repurposed na RAM budget niezmienniki (§6.1). Fixtures: `sample_input` (200 DrawRecord-compatible draws), `sample_frequency_vector` (Δ⁴⁹), `load_pipeline` (placeholder dict W1/W4).

**[2026-05-29] Contract revision + W0/W1 review — Ścieżka A utrwalona**
Pivot predykcyjny [2026-05-26] ANULOWANY → Ścieżka A (audyt + 3 czary-mary: recurrence.py W6, BOCPD animation W8; information_theory/MDL → stretch). `preregistration_v2.md` (ACTIVE, v1 SUPERSEDED): korekta daty 2014-10-08→**2014-10-10**, DoD-1 positive/negative control (euronumery vs główne 1-50 jako wbudowany negative control), nowy `recurrence.py` (gap **perm-calibrated** + Nelson-Aalen + EVT Gumbel; NIE lifelines — pandas zakazany, NA ~20 LOC własny), Family B BH→**Benjamini-Yekutieli** (300→450 hyp). **DoD-4 zostaje 3/3** (MDL nie jest niezależny od MMD).
**BOCPD α/hazard zsynchronizowane prereg↔kod** (§2: α=0.1, hazard=0.005): v1 błędnie nosił α=1; faktyczna decyzja [2026-05-26] to α=0.1 (osłabienie sygnału przy α=1 potwierdzone empirycznie: max 0.14 vs 0.47). Korekta transkrypcji, NIE zmiana metody.
**W0 power preview DONE** (`notebooks/00_power_preview.py`): real n=**958** (R1=133/R2=389/R3=436, NIE 1500 — brief poprawiony); positive control POTWIERDZONY (euron [1-8]/[1-10]/[1-12] = granice reżimów); **δ=0.01 per-reżim NIEwykrywalny** global GoF (R1 power=0.10); power = co-primary deliverable; czytać jako UPPER BOUND (FDR nieskorygowane, global GoF heurystyka, tylko signal #1).
**W1 review:** rdzeń BOCPD message-passing **POPRAWNY** (R9 do obniżenia); DoD-1b ±60 dla 2014 (data-CP≈2014-11-28) vs ±30 dla 2022. 27/27 zielonych. 7 commitów d31ba66→3912916.

**[2026-05-30] W2 DriftSim + preregistration v3 + W3 calibration core**
Baseline commit całego scaffoldu (`50862ad`). **W2:** `null_uniform.py` (`9aa6265`, uczciwy null 5/50 + 2/{8,10,12}, daty synthetic R3=Tue/Fri vs R1/R2=Fri) + `planted_signals.py` (`85a46e0`, 5 sygnałów × 4 effect = 63 datasety, guard #4 seasonality-tylko-R3, refactor `synthetic_dates`/`sample_euron` współdzielone).
**`preregistration_v3.md` ACTIVE** (`8f60de2`, supersedes v2): ratyfikacja siatek effect-size które v2 §6 zostawiał nie-pinowane — **trend β ∈ {0.01,0.02,0.05,0.10}** i **seasonality c ∈ {0.01,0.02,0.05,0.10}** (mechanizm: +c piątek/−c wtorek na liczbie planted). Rewizja czysta (przed kalibracją). Pointery przepięte w CLAUDE.md+PROJECT_BRIEF.md. (Numeracja: po v2 jest **v3**, nie v4 — wcześniejsza notatka o „v4" była błędna.)
**W3 `calibration.py`** (`0218822`→`a670fb4`→`2dd2379`): detector-agnostyczny harness Monte Carlo (power/FPR) + `chi2_main_uniformity` (Family B chi², §5); domyślne n = realne 133/389/436. **Finding (empiryczny, zwalidowany):** chi² wykrywa freq_shift/trend (marginal) ORAZ autocorr/seasonality (przez nadmierną dyspersję zliczeń); **ŚLEPY tylko na pair_corr** (joint→power≈FPR). Wstępna hipoteza była odwrotna — korekta po failu testu.
**Lekcja operacyjna:** zniekształcony output narzędzi (stale/fresh interleaving, fałszywe „updated successfully"/„commit OK") → 2 przejściowo-czerwone commity W3. Weryfikować stan przez `grep`/`git log`, nie sam renderer. Końcowo zielone: 83 passed / 7 skip, HEAD `2dd2379`.

**[2026-05-31] W4 K4-MMD — implementacja + kalibracja + naprawy po code-review (NIEzacommitowane)**
`methodology/k4_mmd.py` (był stub): two-sample MMD² (Gaussian RBF, median heuristic anti-leakage na X, unbiased Gretton 2012) na frequency vectors Δ⁴⁹ per okno; null permutacyjny w `@njit(cache=True)` nad pre-policzoną macierzą Grama; `mmd_uniform_detector` wpięty w harness `calibration.py`. **Framing (decyzja usera, §3 nie pinuje X/Y):** vs uniform reference — X=okna obserwacji, Y=okna świeżego uniform 5/50 (ten sam n). RBF liczony ręcznie (NIE sklearn `pairwise_kernels` z CLAUDE.md) — celowo, dla integracji z njit; udokumentowane.
**Finding W4 (empiryczny):** MMD łapie freq_shift(~1.0)/trend(R2/R3~1.0)/autocorr(R2/R3 0.68/0.82)/seasonality(R3~0.88); **ŚLEPY na pair_corr** (≈FPR) — TAK SAMO jak chi². → osobny **test współwystąpień W6 jest KONIECZNY** (rozstrzyga otwarte pytanie z W3). null FPR ≤ 7.5% wszystkie reżimy. Tabela 95 passed / 5 skip.
**Code-review (lokalny `/code-review high`) → 4 naprawy:** (1) crash guard ≥2 okna (ZeroDivisionError w njit przy 1 oknie); (2) **pure-function reseed** — rng seedowany z hash zawartości `draws` ⊕ base_seed → detektor czystą funkcją, DoD-6 niezależny od kolejności (był stanowy rng w domknięciu); (3) footgun non-overlap — usunięty `DEFAULT_STEP=1`, `step` wymagany; (4) test FPR na wdrożonej konfiguracji window=25. Matematyka MMD²/anti-leakage/p-value potwierdzone poprawne.
**Ustalenie metodologiczne (dla prereg_v4 przed W5):** `window=200` z §3 niewykonalny na realnych danych — strumień ~958 daje przy non-overlap tylko ~4 okna (statystycznie za cienko). Wdrożona konfiguracja MMD = `window=25` (15–17 okien, czysty FPR). Spec curve §4 N∈{100,200,400} też do rewizji.

**[2026-05-31] preregistration v4 — rewizja MIESZANA (zacommitowana `cdab71b`)**
v3 SUPERSEDED. (A) INFORMOWANA real-data [JAWNIE oznaczona]: §3 window **200→25**, §4 spec curve **{100,200,400}→{15,25,40}** (200 niewykonalny na n≈958/non-overlap — korekta błędu spec, NIE dobór pod wynik; FPR≠25 do walidacji w W6). (B) CZYSTA: §5c co-occurrence test pre-rejestrowany (curveball null). (C) DOPRECYZOWANIE: §3 non-overlap (step=window) + framing vs uniform reference. Pierwsza rewizja z częścią informowaną danymi — dyscyplina §0: jawne rozdzielenie clean vs data-informed.

**[2026-05-31] W6 test współwystąpień + preregistration v5 (zacommitowane `8fb9932` prereg, `9550b51` kod)**
`methodology/cooccurrence.py` (nowy): domyka pair_corr, na który chi²(W3)/MMD(W4) ślepe. Null = **curveball swap-randomization** (njit, zachowuje OBA marginesy: wiersze=5, kolumny=częstości; łamie parowanie; łańcuch burn-in+thinning). Statystyka = **max-pair** z=(O−E)/√E + lokalizacja pary; pure-function reseed (DoD-6).
**Korekta §5c PRZED implementacją:** pre-zarejestrowana w v4 suma `Σ(O−E)²/E` matematycznie ROZMYWA rzadki sygnał (1 para z 1225) → power≈FPR (ta sama ślepota co chi²/MMD) + miscalib (FPR~0.17). Przełączone na max-pair (poprawna kalibracja FPR≈α). Lekcja: statystyki walidować PRZED zamrożeniem (powtórka W3).
**Re-design pair_corr §6:** stary mechanizm (lift) był PODWÓJNIE wadliwy — (1) below detection floor (forced-frac=(lift−1)·0.00816 ∈ {0.0008..0.0082}, analog W0 δ=0.01), (2) PRZECIEKAŁ do marginesów (P(planted)=0.1+0.9p) łamiąc deklarację §6 o izolacji. Nowy: **margin-preserving** mieszanka 3-komponentowa (force-para p / force-brak-obu 9p / uniform 1−10p), parametr forced-frac {0.01,0.02,0.05,0.10}. Zachowuje WSZYSTKIE marginesy DOKŁADNIE (P(dowolnej)=0.1), podnosi P(i,j razem) ~12× przy p=0.10.
**Showcase (zwalidowany, czysta komórka Disagreement Protocol):** co-occurrence JEDYNYM detektorem pair_corr — power p≥0.05 → ≥0.80 wszystkie reżimy (R1@0.05=0.80; Decision Gate >70% spełniony); chi²=0.06/MMD=0.03 przy p=0.10 = FPR floor (dowodliwie ślepe, marginesy uniform); cooc FPR(null)=0.03. Uzasadnia DoD-4=3/3 (3 rodziny NIE-redundantne). preregistration **v5 ACTIVE** (po v4), +§6.5 tabela komplementarności. Suite 104 passed / 5 skip.

**[2026-05-31] W6 — recurrence + multiple_testing + permutation; DoD-2 i DoD-3 DOMKNIĘTE**
Dokończono rdzeń metodologiczny W6 — cztery komplementarne rodziny detektorów (wszystkie czyste funkcje DoD-6, FPR≈α, wspólny harness `calibration.Detector`):
- **`recurrence.py`** (`598a25d`, §5b) — rodzina TEMPORALNA. gap GoF: KS gapów vs Geometric(q=0.1), **draw-order shuffle** perm-calibrated (NIE analityczny KS — niewazny dyskretnie), omnibus max_k + lokalizacja liczby. + Nelson-Aalen (~20 LOC własny, bez lifelines) + EVT max-gap Gumbel. Kluczowe: shuffle zachowuje liczność → WARUNKUJE na marginesie → ślepy na freq_shift(0.03)/trend(0.10)/pair_corr(0.00), łapie autocorr (R3 ρ=.20→0.78, słabiej przy małym ρ).
- **`permutation.py`** (`36044c2`, **DoD-2**) — kanoniczny silnik: `permutation_pvalue` prymityw (1+#≥)/(B+1) + **lag-1 serial overlap** (statystyka ZALEZNA OD KOLEJNOSCI; PoC chi² na zliczeniach był niezmienniczy na permutację wierszy = degeneracja). njit hot loop (wzorzec PoC). FPR(null)=0.050 ✓ DoD-2. **Najsilniejszy autocorr detektor** (ρ=.05/.10/.20→1.00; recurrence dawał 0.05 przy ρ=.05 — komplementarne, nie redundantne, różne mechanizmy/granularność).
- **`multiple_testing.py`** (`6021c0a`, §5/**DoD-3**) — Family A (BH primary + Storey własny ~15 LOC, secondary) / Family B (Benjamini-Yekutieli primary + BH secondary; Storey odrzucony). `FDRResult` (q-values+maska); BH/BY przez statsmodels. Tu spłyną per-number p-values z chi²/gap.
**Macierz komplementarności:** freq_shift/trend→marginalna; autocorr→serial(1.0)+recurrence+chi²; seasonality→chi²/MMD+część recurrence; **pair_corr→WYŁĄCZNIE co-occurrence**. Każdy sygnał ma ≥1 championa. DoD-2/3/6 ✓.

**[2026-05-31] W6 — specification.py + block_bootstrap.py; WSZYSTKIE stuby methodology/ zaimplementowane**
- **`specification.py`** (`9c658fb`, §4) — spec curve 9 pkt (window∈{15,25,40} × bw∈{0.5,1,2}× median heuristic); kryterium stabilności znika w >2/9. Dodano `bandwidth_mult` do `mmd_uniform_detector` (backward-compat, σ=mult·median_heuristic(x), anti-leakage zachowane). **Zamyka walidację FPR N∈{15,40}** z v5 §4: NULL R3 → 0/9 significant (0/135 odrzuceń); freq_shift .10 → 9/9 stable.
- **`block_bootstrap.py`** (`c9e1a5d`) — moving block bootstrap (alternatywny null, block∈{5,10,20}), statystyka serial overlap (reuse permutation). Konserwatywny (FPR≤α=0.00); power autocorr maleje z block_size (b=20→0.85) = gradient zasięgu zależności. njit hot loop.
- **Stan:** 6 modułów metodologicznych kompletnych (cooccurrence, recurrence, permutation, multiple_testing, specification, block_bootstrap) + k4_mmd/h1_classical z W1/W4. Suite **152 passed / 4 skip**, nowe pliki ruff-czyste. Dług: repo ma 34 pre-existing ruff violations (N803/N806 notacja matematyczna w h1_classical/k4_mmd/test_mmd + I001/F401/E501 w cli/scraper/conftest) — NIE z tej sesji, osobny cleanup. Pozostało w W6: TYLKO kalibracja progu BOCPD reject_h0=0.3 (dotyka W1).

**[2026-05-31] W6 DOMKNIĘTY — kalibracja progu BOCPD + warm-up exclusion (NIEzacommitowane)**
Ostatnia pozycja W6. Magiczny `reject_h0 = max_cp_prob > 0.3` (jeden próg dla obu pól) był **fałszywie skalibrowany**: ukryty bug — pole `main` (N=50, K=5) dawało **FPR=0.77** pod nullem (0.3 ≪ p95=0.73), czyli negative control 1-50 *zawsze* zapalał. euron (N=12, K=2) FPR=0.07. Rozkład nullowy `max(cp_prob)` silnie zależy od (N, K) → próg MUSI być per-pole.
- **`_BOCPD_REJECT_THRESHOLD` (per-pole, 95. perc. nullu, FPR≈0.05):** euron **0.33** (p95=0.329), main **0.70** (p95=0.699). Reprodukcja: `scripts/calibrate_bocpd_threshold.py` (BASE_SEED=42, 200 trials, R3).
- **Warm-up exclusion (decyzja usera, zalecana — wymaga preregistration_v6):** `max(cp_prob)` liczone POMIJAJĄC pierwsze `warmup = N//K` losowań (euron=6, main=10). Powód: `max(cp_prob)` pod nullem to **transient burn-in** (argmax≈4-7, IDENTYCZNY dla n=436 i n=958 → próg length-invariant, ważny dla pełnej serii) — zanim pula symboli zostanie „zobaczona", każde losowanie wnosi nowe symbole → sztuczny spike, NIE change-point. Na realnym `main` JEDYNY ponadprogowy peak był w idx=7 (2012-05-11, burn-in); po warm-up max spada 0.770→0.208 → **clean negative control**. euron positive control nietknięty (peaki 2014-11-28/2022-03-29 są mid-series).
- **Walidacja:** euron reject=True (DoD-1b), main reject=False (nowy test `test_dod_1b_bocpd_negative_control_main`) + `test_bocpd_fpr_under_null` (euron/main FPR≈0.05, DoD-2 dla rodziny BOCPD). Suite **155 passed / 4 skip**.
- **Dług kontraktowy (NASTĘPNY KROK):** zmiana reguły reject + warm-up to zmiana w `methodology/` → wymaga `preregistration_v6.md` z revision_reason ZANIM commit. Real-data-informed (inspekcja neg-control/burn-in) — ujawnić wg dyscypliny §0. Próg czysto null-kalibrowany; warm-up strukturalnie uzasadniony. Plus I001 w test_h1_invariants.py + update CLAUDE.md (ACTIVE v5→v6).

---

## Rozwiązane problemy

**[2026-05-31] MMD sliding-window + permutacja etykiet → okna MUSZĄ być nienakładające się**
Objaw: detektor MMD z oknami nakładającymi się (step<window) dawał **FPR~1.0** (always-reject) na nullu. Przyczyna: permutacja etykiet połączonej puli okien zakłada WYMIENIALNOŚĆ; okna nakładające się są silnie skorelowane within-sample, a X⊥Y między strumieniami → wymienialność złamana → obserwowane MMD² systematycznie > null permutacyjny. Rozwiązanie: wymusić `step ≥ window` (twardy guard w `mmd_uniform_detector`). „sliding window" z §3 NIE pinuje kroku; FPR ≤ 7.5% z §3 wymaga non-overlap pod tym nullem. `window=25/step=25` → FPR ≤ 4–6% wszystkie reżimy.

**[2026-05-26] pip SSL cert failure na Win11 + Miniconda**
Objaw: `SSLCertVerificationError` przy `pip install`. Rozwiązanie: `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org`. Przyczyną jest brak certyfikatów systemowych w środowisku Miniconda na Win11.

**[2026-05-26] hatchling wymaga README.md**
`pip install -e ".[dev]"` z hatchling jako build backend failuje z `OSError: Readme file does not exist: README.md` jeśli `readme = "README.md"` w pyproject.toml a plik nie istnieje. Rozwiązanie: stworzyć README.md przed instalacją.

**[2026-05-26] Oś 0 — zielona (11/11 passed)**
`pytest tests/test_environment.py` przeszedł wszystkie 11 testów na docelowym środowisku: Python 3.10.13, NumPy 2.2.5, Numba 0.65.1, @njit basic + cache=True + frequency_vector primitive, wszystkie kluczowe importy, Polars 1.41.0, joblib loky 2-job parallel, MSVC vcruntime140.dll present.

**[2026-05-26] BOCPD — bug w message passing (Adams-MacKay 2007)**
Klasyczny błąd: changepoint term używał `logsumexp(log_R + log_pred)` (ważone po run-length), a powinien używać `log_pred_prior` (predictive pod PRIOR, niezależnie od rozkładu run-length). Skutek błędu: max_cp_prob = H = 0.005 zawsze. Fix: `log_q_cp = log_H + log_pred[0]` (counts[0] = zeros zawsze = prior).

**[2026-05-26] BOCPD alpha — default 0.1, nie 1.0**
alpha=1.0 (Laplace smoothing) za silny prior dla danych EuroJackpot: osłabia sygnał przy zmianie puli. alpha=0.1 (słabszy prior, szybsza adaptacja) daje cp_prob > 0.4 przy pierwszym niewidzianym symbolu. Z alpha=0.1 BOCPD wykrywa zmianę 1-8→1-10 na 2014-11-28 (cp_prob=0.408).

**[2026-05-26] Rzeczywiste daty change-pointów w danych EuroJackpot**
PROJECT_BRIEF wymienia "2014-10-08" i "2022-03-25" jako ground truth — są to daty ZMIANY ZASAD. Daty pierwszych OBSERWOWALNYCH zmian w danych (seed CSV):
- 2014 (1-8→1-10): pierwsza "9" pojawiła się 2014-11-28 (51 dni po zmianie zasad!) — bo losowania 10.10-21.11.2014 trafiały tylko {1-8} przypadkowo
- 2022 (1-10→1-12): pierwsza "11" pojawiła się 2022-03-29 (4 dni po zmianie zasad — niemal natychmiast)
Implikacja dla DoD-1b: tolerancja ±30 dni dla 2014 → nieosiągalna dla BOCPD na danych (używamy ±60 dni w teście).

**[2026-05-26] W0.1 DONE — API zidentyfikowane, seed CSV pobrany**
Zidentyfikowano i zdokumentowano: developers.lotto.pl API (oficjalne PTS), endpoint params, JSON structure, zakres danych (~2017-present). Seed CSV (wynikilotto.net.pl) pobrany i skonwertowany — 958 losowan 2012-2026 w `data/seed/eurojackpot_history.csv`. Deliverable: `scripts/scraper_selectors.md`. HTML scraping porzucony (ECONNREFUSED). Research blocker usunięty.

---

## Aktywne TODO (długoterminowe)

**[2026-05-26] W2 — DriftSim planted signals (następny milestone)**
W1 DONE. W2: `driftsim/null_uniform.py` (uczciwy null generator) + `driftsim/planted_signals.py` (5 sygnałów × 4 effect sizes = 20 scenariuszy, preregistration §6). Cel: calibracja sensitivity/specificity testów H1.

---

## Odrzucone podejścia

**[2026-05-26] HTML scraping eurojackpot.org — PORZUCONE**
`ECONNREFUSED` przy próbie połączenia z eurojackpot.org/archive — blokada IP/bot. Zastąpione przez oficjalne API developers.lotto.pl (Tier 2) + CSV z wynikilotto.net.pl (Tier 1).

**[2026-05-26] API developers.lotto.pl — błędne parametry**
`drawDateFrom`/`drawDateTo` (zakres dat) → 404. `index=0` → 422 (index musi być >0, 1-based). Bez `sort`/`order` → 422. Właściwe parametry: `drawDate=YYYY-MM-DD` (pojedyncza data), `index=1`, `size=1`, `sort=drawDate`, `order=asc`. gameType: musi być `EuroJackpot` (capital E i J — case-sensitive).

---

## Słownik projektu

**DrawRecord** — jedna rekord losowania: `draw_date` (ISO 8601), `main_1..main_5` (liczby 1-50), `euron_1..euron_2` (liczby 1-12 od 2022-03-25, wcześniej 1-10).

**isNewEuroJackpotDraw** — flaga w API developers.lotto.pl; `true` od 2022-03-25 (change-point: pula euroNumbers rozszerzona z 1-10 na 1-12, dwa rysowania tygodniowo zamiast jednego).

**Tier 1/2/3 ingestion** — trójpoziomowa strategia pozyskiwania danych: (1) seed CSV `data/seed/eurojackpot_history.csv`, (2) API live `developers.lotto.pl`, (3) `scripts/manual_import.py` fallback.

---

## Zewnętrzne zależności i integracje

**[2026-05-26] developers.lotto.pl — oficjalne API Polskiego Totalizatora Sportowego**
Auth: nagłówek `"secret": <LOTTO_API_KEY>` (klucz w `.env`, nigdy nie commitować).
Endpoint główny: `GET /api/open/v1/lotteries/draw-results/by-date-per-game?gameType=EuroJackpot&drawDate=YYYY-MM-DD&index=1&size=1&sort=drawDate&order=asc`
Zakres danych: ~2017-09-15 do dziś (2012-2017 niedostępne — 404).
Swagger spec: `https://developers.lotto.pl/swagger/open-api-v1/swagger.json`
SSL: `verify=False` w httpx (Miniconda Win11 brak certyfikatów systemowych).

**[2026-05-26] wynikilotto.net.pl — historyczny CSV EuroJackpot**
URL: `https://www.wynikilotto.net.pl/download/eurojackpot.csv`
Format: `draw_no,DD.MM.YYYY,m1,m2,m3,m4,m5,e1,e2` (brak nagłówka).
Zakres: 2012-03-23 .. dziś (958 losowan stan 2026-05-26). Plik committed jako `data/seed/eurojackpot_history.csv`. Aktualizacja manualna (cotygodniowa).
