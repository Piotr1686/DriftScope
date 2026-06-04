# preregistration_v7.md — DriftScope Methodology Pre-registration

**Status:** ACTIVE (zastepuje v6; rewizja CZYSTA — korekta licznika Family B + scope per-rezim, zob. §0)
**Wersja:** v7
**Data zamrozenia:** 2026-06-04 (przed regime-aware `run_audit`; Faza 2)
**Supersedes:** preregistration_v6.md (ktora superseduje v5, v4, v3, v2, v1)

> Ten plik jest czescia architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §0. Revision reason (v6 → v7)

`revision_reason:` Rewizja **CZYSTA** (NIE informowana wynikami real-data — korekta
specyfikacji wykryta przy integracji end-to-end / Faza 2, przez inspekcje CO detektory
faktycznie zwracaja, nie ich wynikow). Dwie zmiany sprzezone:

### (A) §5 licznik Family B: 450 → 150 [CZYSTA — korekta bledu kategorii]

Pre-rejestrowane (od v2) **„Family B = 450 = 50 liczb × 3 testy {chi², exact-binomial,
gap GoF} × 3 rezimy"** zawiera **blad kategorii**: zaklada, ze wszystkie trzy testy
zwracaja p-value PER LICZBA. To nieprawda — tylko **exact-binomial** jest naturalnie
per-liczba (50 p-values/rezim, count_k ~ Binomial(n, 5/50)). Pozostale to detektory
**OMNIBUS**, zwracajace **1 p-value + lokalizacje** na strumien/rezim:

- `chi2_main_uniformity` (§5) — jeden chi² nad 50 zliczeniami,
- `gap_recurrence_test` (§5b) — omnibus max_k (+ lokalizacja liczby),
- `cooccurrence` (§5c) — omnibus max-pair (+ lokalizacja pary).

Mnoznik „× 3 testy" laczyl per-number z omnibus w jednej rodzinie per-number — niespojnie.

**Korekta:** rodzina per-number (FDR Benjamini-Yekutieli) sklada sie **wylacznie**
z exact-binomial: **50 liczb × 3 rezimy = 150 hipotez**. Detektory omnibus (chi²/gap/cooc)
tworza **rodziny komplementarne raportowane OSOBNO** (po 1 p-value/rezim), zasilaja
Disagreement Protocol (§6.5) i NIE napompowuja per-number licznika. Pelne wciagniecie
gap/cooc do rodziny per-number/per-para wymagaloby refaktoru tych statystyk na granularnosc
per-liczba/per-para — odrzucone (ryzyko miskalibracji; lekcja W3/W6: walidowac statystyki
PRZED zamrozeniem). Family A (§5, 4 testy omnibus × 3 rezimy = 12) jest spojna i bez zmian.

### (B) §1c scope audytu: negative control + Family B liczone PER REZIM [CZYSTA — wybor metodologiczny zgodny z H0 §1]

H0 (§1) jest pre-rejestrowana per rezim („proces stacjonarny, uniform, i.i.d. **w kazdym
rezimie**"). Ratyfikuje sie, ze:

- **Negative control** (3 filary: H1/temporal, MMD/distributional, co-occurrence/joint na
  puli GLOWNEJ 1-50) liczony jest **per rezim** (R1/R2/R3) — test stacjonarnosci WEWNATRZ
  rezimu, zgodnie z H0 §1. Pula glowna jest strukturalnie niezmienna przez wszystkie rezimy,
  wiec kazdy rezim to niezalezny negative control.
- **Family B** (per-number exact-binomial) liczona **per rezim** → 50 × 3 = **150** (spojne z (A)).
- **Positive control** (BOCPD na euronumerach) pozostaje **FULL-STREAM**. Sygnal ground-truth
  EuroJackpot to zmiana puli euron MIEDZY rezimami (8→10→12); ciecie euron per-rezim
  ZNISZCZYLOBY ten sygnal. BOCPD-euron jest detektorem przejscia, nie stacjonarnosci wewnatrz.

Zmiana dotyczy granulacji RAPORTOWANIA (per-rezim vs full-stream) + licznika hipotez.
Modele generatywne, statystyki, nulle, progi (§2–§6.5) BEZ zmian. DoD-4 pozostaje 3/3.

---

## §1. Hipotezy

**H1:** Strumien losowan EuroJackpot wykazuje mierzalne odchylenia od stacjonarnosci
w co najmniej jednym wymiarze (marginals / CP / spectral / MMD / recurrence /
co-occurrence) w co najmniej jednym rezimie regul.

**H0:** Strumien jest generowany przez stacjonarny, uniform, i.i.d. proces
w kazdym rezimie:
- **R1:** 2012-03-23 → 2014-10-03 (5/50 + 2/8)
- **R2:** 2014-10-10 → 2022-03-18 (5/50 + 2/10)
- **R3:** 2022-03-25 → obecnie (5/50 + 2/12)

---

## §1b. Control design (pre-registered)

- **Positive control:** strumien euronumerow. Znana zmiana support w 2014-10-10 (8→10) i 2022-03-25 (10→12). Detektor MUSI zapalic — sanity check, ze dziala w ogole.
- **Negative control:** strumien glownych liczb 1-50. Brak znanej zmiany regul w 2014/2022. Detektor NIE powinien rankowac CP w tych datach; spurious CP = halucynacja.

Oba strumienie pochodza z TEGO SAMEGO realnego zbioru — kontrola wbudowana, nie syntetyczna.

**Tolerancja detekcji (DoD-1b):** BOCPD wykrywa zmiane w DANYCH, nie w regulach.
Pierwszy nowy symbol: 2014 → 2014-11-28 (~49 dni po regule 2014-10-10, losowania
trafialy {1-8} przypadkowo); 2022 → 2022-03-29 (~4 dni). Stad **±60 dni dla 2014**,
**±30 dni dla 2022** (MEMORY.md 2026-05-26).

---

## §1c. Scope audytu — granularnosc per-rezim (v7 §0(B))

- **Positive control (BOCPD euron):** FULL-STREAM. Wykrywa zmiany puli MIEDZY rezimami
  (ground truth 2014/2022). NIE ciety per-rezim (zniszczyloby sygnal przejscia).
- **Negative control (3 filary H1/MMD/co-occurrence na puli glownej 1-50):** PER REZIM
  (R1/R2/R3). Test stacjonarnosci WEWNATRZ rezimu (H0 §1). Pula glowna niezmienna → kazdy
  rezim = niezalezny negative control. Oczekiwane: 0/3 w kazdym rezimie.
- **Family B (per-number exact-binomial):** PER REZIM → 150 hipotez (§5).
- **Detektory omnibus (chi²/gap/cooc):** po 1 p-value/rezim, rodziny komplementarne
  raportowane osobno (§5, §6.5).

R1 (n=133) jest najcienszy — MMD okienne na granicy wykonalnosci (§3 „Ograniczenie danych");
wynik per-rezim raportowany z ta uwaga.

---

## §2. Model generatywny — Bayesian online CP (Adams-MacKay 2007)

- **Prior:** p ~ Dirichlet(α=0.1) — slaby (sparse) prior na simpleksie Δ⁴⁹.
  **Decyzja empiryczna** (MEMORY.md 2026-05-26): α=1 (flat) osłabia sygnał przy
  zmianie puli; α=0.1 daje cp_prob>0.4 przy pierwszym niewidzianym symbolu.
- **Likelihood:** draw_t ~ Categorical(p)
- **Posterior update:** α_k += 1 dla kazdego wylosowanego k
- **Hazard:** geometric z rate r=1/200 = 0.005 (expected run length = 200 losowan)
- **Output:** pelna macierz run-length posterior P(R_t) (forward-pass) — wymagana dla animacji W8 i surprise S_t = -log P(x_t | R_{t-1})
- **Implementacja:** wlasna (~150 LOC), cross-check vs ruptures PELT
- **Cross-check kryterium:** disagreement z PELT ≤ 10%

**Regula reject (v6 §0, bez zmian):**
- **Warm-up:** detekcja (max cp_prob + kandydaci na CP) liczona z pominieciem pierwszych
  `warmup = N // K` losowan (euron 6, main 10) — usuwa transient burn-in, w ktorym cp_prob
  rosnie sztucznie zanim pula symboli zostanie „zobaczona" (NIE change-point).
- **Prog per-pole:** `reject_h0 ⇔ max(cp_prob[warmup:]) > prog`, gdzie prog = 95. percentyl
  rozkladu nullowego uniform-iid (FPR≈0.05): **euron 0.33 / main 0.70**. Prog zalezy od
  (N, K) — magiczny wspolny prog 0.3 dawal FPR=0.77 dla `main`. Wazny dla α=0.1, hazard=0.005;
  length-invariant. Kalibracja: `scripts/calibrate_bocpd_threshold.py`.

---

## §3. K4-MMD — stabilnosc i parametry

- **Input space:** frequency vector p ∈ Δ⁴⁹ per sliding window (NIE raw draws)
- **Window size:** **N = 25 (deployed, v4)** — patrz v4 §0(A). Okna **NIENAKLADAJACE sie**:
  `step = window` (non-overlap WYMAGANY; `step < window` ZABRONIONE — lamie wymienialnosc
  permutacyjna → FPR ~1.0).
- **Framing:** dwuprobkowy MMD² (X = okna obserwacji, Y = okna swiezego uniform 5/50
  o tym samym n).
- **Kernel:** Gaussian RBF z bandwidth = median heuristic
- **Anti-leakage:** bandwidth obliczana WYLACZNIE na probie X (training window)
- **Estymator:** unbiased MMD² (Gretton et al. 2012)
- **Null:** permutacja etykiet polaczonej puli okien nad pre-policzona macierza Grama
- **Threshold stabilnosci:** FPR ≤ 7.5% na shuffled/uniform null — zwalidowany dla N=25
- **Ograniczenie danych:** R1 (n=133 → 5 okien) na granicy wykonalnosci MMD okiennego.
- **Teoria asymptotyczna:** Gretton et al. 2012

---

## §4. Specification Curve Space (pre-registered)

- window size N ∈ **{15, 25, 40}** (skorygowane w v4 §0(A) — wykonalne na n≈958/non-overlap)
- bandwidth ∈ {0.5×, 1×, 2×} median heuristic
= **9 punktow** spec curve per sygnal

**Walidacja FPR (W6):** FPR ≤ 7.5% zweryfikowany dotad dla N=25. Punkty N∈{15,40} × bandwidth
musza przejsc te sama kalibracje; punkt nieprzechodzacy = udokumentowany jako niestabilny.

**Kryterium stabilnosci:** sygnal niestabilny jesli znika w >2/9 punktach (p > 0.05) → nie raportowany.

---

## §5. Multiple Testing Families (licznik skorygowany v7 §0(A))

**Family A (global time-series, omnibus):**
- 4 testy (ADF, KPSS, Bayesian CP, Welch) × 3 rezimy = **12 hipotez**
- Kazdy test zwraca 1 p-value/rezim (omnibus) → licznik spojny, bez zmian.
- Korekcja: Benjamini-Hochberg FDR α=0.05 + Storey q-values (secondary sanity)

**Family B (per-number, FDR primary Benjamini-Yekutieli):**
- **Rodzina per-number = WYLACZNIE exact-binomial:** 50 liczb × 3 rezimy = **150 hipotez**
  (skorygowane z 450 — zob. §0(A) blad kategorii). Pod uniform count_k ~ Binomial(n, 5/50),
  dwustronny exact test per liczba per rezim.
- Korekcja: **Benjamini-Yekutieli** FDR α=0.05 jako primary — wazny przy dowolnej strukturze
  zaleznosci (zliczenia 5/50 ujemnie skorelowane), gdzie zalozenie PRDS dla BH jest niepewne;
  BH jako secondary. Storey odrzucony (niestabilny przy dominujacym null).

**Rodziny komplementarne OMNIBUS (raportowane OSOBNO, NIE w per-number Family B):**
- chi² (§5 per-rezim), gap GoF (§5b per-rezim), co-occurrence (§5c per-rezim) — kazdy
  1 p-value + lokalizacja/rezim. Nie sa per-liczba → nie wchodza do rodziny per-number (§0(A)).
  Zasilaja Disagreement Protocol (§6.5) jako niezalezne filary. Korekcja FDR w obrebie wlasnej
  rodziny jesli liczba czlonkow > 1 (np. 3 rezimy); inaczej raportowane jako pojedyncze testy.

**Klaryfikacja: konwergencja (DoD-4) ≠ kontrola FDR.** Disagreement Protocol (§6.5, DoD-4)
liczy **SUROWE** per-rezim `reject_h0` filarow przy α (mierzy ZGODNOSC trzech niezaleznych
rodzin, nie family-wise error). Korekcja FDR w obrebie rodziny omnibus przez rezimy (powyzej)
to OSOBNA warstwa raportowania i NIE bramkuje liczenia konwergencji. Konsekwencja: pojedynczy
filar zapalajacy w JEDNYM rezimie → klasyfikacja **1/3** ("single-pillar, requires power
context"), NIE finding. Promocja do findingu wymaga gate'u watchlisty (DoD-3 FDR via Family B
per-number ORAZ DoD-4 konwergencja ≥min) — single-pillar 1/3 na czystej puli glownej nie
przechodzi. [Doprecyzowanie strukturalne wykryte przy integracji Fazy 2 — zob. §0; ujawniam,
ze zaobserwowano je przy single-pillar cooc w jednym rezimie real-data, ale regula jest
strukturalna, niezalezna od konkretnego wyniku.]

---

## §5b. Recurrence / gap analysis (pre-registered)

Czas (liczba losowan) miedzy kolejnymi wystapieniami danej liczby. Pod nullem uniform-iid: gap ~ Geometric(q), q = 5/50 dla puli glownej.

- **Gap goodness-of-fit:** odchylenie empirycznego rozkladu gapow od Geometric(q) per liczba per rezim. ⚠️ **NIE analityczny KS** (Kolmogorov-Smirnov niewazny dla rozkladow dyskretnych — bledne p-value). Statystyka kalibrowana PERMUTACYJNIE (silnik z §permutation, Krok 6 PROJECT_BRIEF).
- **Nelson-Aalen cumulative hazard** per liczba: liniowosc = stala intensywnosc = zgodnosc z uniform.
- **EVT max-gap:** maksymalny gap ma asymptotycznie rozklad Gumbela (gapy geometryczne w domenie przyciagania Gumbela).
- **Status w liczniku (v7 §0(A)):** detektor OMNIBUS (1 p-value max_k + lokalizacja/rezim).
  Rodzina komplementarna raportowana OSOBNO (§5), NIE czlonek per-number Family B.

---

## §5c. Co-occurrence test (pre-registered v4; statystyka skorygowana v5 §0(A); licznik ratyfikowany v7 §0(A))

**Cel:** wykryc strukture LACZNA (signal #5 pair_corr), na ktora detektory marginalne
(chi² §5, MMD §3) sa z zalozenia slepe — para liczb (i,j) wspolwystepuje w jednym
losowaniu czesciej niz pod uniform, przy NIEzmienionych marginesach.

- **Null — swap-randomization (curveball, Strona et al. 2014):** permutacja macierzy
  incydencji losowanie×liczba zachowuje JEDNOCZESNIE sumy wierszy (=5 liczb/losowanie) i
  sumy kolumn (marginalna czestosc kazdej liczby), a lamie TYLKO parowanie. Izoluje sygnal
  laczny od marginalnego — analityczny Binomial(n, p_pair) niewazny przy nie-uniform
  marginesach. Lancuch sekwencyjny (burn-in + thinning, Gotelli 2000; Besag-Clifford serial).
- **Statystyka (v5 §0(A)):** **max-pair** z_ij = (O_ij − E_ij)/sqrt(E_ij); reject ⇔
  max_ij z_ij w prawym ogonie nulla. E_ij = srednia wspolwystapien pod nullem (z permutacji).
  p = (1 + #{maxstat_perm ≥ maxstat_obs})/(n_perm+1). Lokalizacja: top_pair = argmax z_ij.
  **Odrzucona** suma T = Σ(O−E)²/E (v4): rozmywa rzadki sygnal + miskalibrowana (zob. v6 §0(A)).
- **Status w liczniku (v7 §0(A), RATYFIKACJA otwartego punktu v5/v6):** detektor OMNIBUS
  (1 p-value max-pair + lokalizacja pary/rezim). NIE jest per-para czlonkiem per-number
  Family B (rozwiniecie na per-para wymagaloby refaktoru → ryzyko miskalibracji, odrzucone).
  Rodzina komplementarna raportowana OSOBNO (§5), zasila Disagreement Protocol (§6.5).
- **Status walidacji:** zaimplementowany i skalibrowany na DriftSim (W6). Power: zob. §6.5.

---

## §6. DriftSim — planted signals (pre-registered)

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim** (× 3 = 63 unikalne). Sygnal izolowany w puli GLOWNEJ (Δ⁴⁹); euronumery i kalendarz pozostaja nullowe. Liczba noszaca sygnal #1/#3/#4 jest ustalona (reprodukowalnosc); para dla #5 ustalona.

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}  *(PINNED od v2)*
2. **Autocorrelation lag-1** — boost wag liczb z poprzedniego losowania o ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}  *(PINNED od v2)*
3. **Linear trend** — p_k(t) = 1/50 + β·(t/T), **β ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3)*
4. **Weekly seasonality** — kontrast wtorek vs piatek na liczbie planted: +c w piatki, −c we wtorki (clip > 0), **c ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3)*. **GUARD: tylko R3** — EuroJackpot losowal wylacznie w piatki do marca 2022; wtorki dodano w R3. W R1/R2 kontrast Tue/Fri nie istnieje → scenariusz degeneruje do uniform null (zajmuje slot datasetu, pelni role dodatkowego negative control; count 63 zachowany).
5. **Pair correlation (MARGIN-PRESERVING, re-design v5 — v6 §0(B) ref)** — forced-fraction
   **p ∈ {0.01, 0.02, 0.05, 0.10}** (NIE mnoznik lift). Mieszanka 3-komponentowa: z p wymus
   pare {i,j}+3, z 9p wymus brak obu, z (1−10p) uniform. Zachowuje WSZYSTKIE marginesy
   DOKLADNIE (P(dowolnej liczby)=0.1), podnosi P(i,j razem) z 0.00816 do 0.918p+0.00816.
   Czysty sygnal JOINT: **detektor docelowy = §5c co-occurrence (max-pair, curveball null)**;
   chi²/MMD dowodliwie slepe (marginesy uniform). Stary mechanizm (lift, v2–v4) przeciekal do
   marginesow i byl below detection floor.

**Permutacja stratyfikowana (R3):** w rezimie z dwoma dniami losowan permutacja zachowuje etykiete dnia (Tue/Fri), zeby null nie konfundowal signal #4.

---

## §6.5. Wyniki kalibracji DriftSim (W3/W4/W6) — pre-rejestrowane oczekiwania vs empiria

Tabela komplementarnosci detektorow (n realne per rezim; zwalidowane testami):
- **freq_shift / trend** — chi² i MMD wykrywaja (odchylenie marginalne).
- **autocorr / seasonality** — chi² i MMD wykrywaja przez nadmierna dyspersje / kontrast.
- **pair_corr (joint, margin-preserving)** — WYLACZNIE §5c co-occurrence; chi²/MMD na FPR
  floor (dowodliwie slepe). Power §5c: p≥0.05 → ≥0.80 wszedzie (Decision Gate spelniony);
  p=0.01 below floor; p=0.02 floor w R1, czesciowy R2/R3.

To uzasadnia DoD-4 = 3/3 (H1/MMD/co-occurrence sa wzajemnie NIE-redundantne) i zasila
Disagreement Protocol (kazdy sygnal: ktore z 3 rodzin go widza).

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: zob. v2 §0. Piec zmian czystych (przed real-data): korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450 hipotez), synchronizacja BOCPD α=0.1/hazard=0.005 z kodem (korekta transkrypcji).
- **v2 → v3** [2026-05-30]: zob. v3 §0. Jedna zmiana czysta (przed kalibracja): pinowanie siatek effect-size dla signal #3 (trend β) i #4 (seasonality c). Doprecyzowano mechanizm seasonality (±c Fri/Tue). δ/ρ/lift bez zmian.
- **v3 → v4** [2026-05-31]: zob. v4 §0. Rewizja MIESZANA. (A) INFORMOWANA real-data [disclosed]: §3 window 200→25 i §4 spec {100,200,400}→{15,25,40} — korekta wymuszona niewykonalnoscia na n≈958/non-overlap. (B) CZYSTA: §5c co-occurrence test (curveball null) pre-rejestrowany. (C) DOPRECYZOWANIE: §3 non-overlap + framing vs uniform reference.
- **v4 → v5** [2026-05-31]: zob. v5 §0. Rewizja MIESZANA, INFORMOWANA DriftSim (synthetic, clean wrt real EuroJackpot). (A) §5c statystyka: suma T → **max-pair**. (B) §6 signal #5 pair_corr re-design: lift → **forced-frac** + mechanizm **margin-preserving**. Dodano §6.5.
- **v5 → v6** [2026-06-02]: zob. v6 §0. Rewizja MIESZANA reguly reject BOCPD (§2). (A) CLEAN: prog `max_cp_prob>0.3` → per-pole 95. perc. nullu (**euron 0.33 / main 0.70**, FPR≈0.05; stary 0.3 dawal FPR=0.77 dla `main`). (B) STRUKTURALNE [disclosed]: warm-up exclusion `max(cp_prob[warmup:])`, warmup=N//K. Model generatywny i §3–§6.5 bez zmian. DoD-4=3/3.
- **v6 → v7** [2026-06-04]: zob. §0. Rewizja **CZYSTA** (korekta specyfikacji przy integracji Faza 2; NIE informowana wynikami). (A) §5 licznik Family B **450 → 150**: blad kategorii — „50 × 3 testy × 3 rezimy" zakladal chi²/gap/cooc jako per-liczba, gdy sa OMNIBUS (1 p-value/rezim). Rodzina per-number = wylacznie exact-binomial (50 × 3 rezimy); chi²/gap/cooc = rodziny komplementarne raportowane osobno (NIE napompowuja per-number FDR). Domyka otwarty punkt licznika z §5c v5/v6. Dodano klaryfikacje §5: konwergencja DoD-4 liczy SUROWE per-rezim rejecty (≠ family-wise FDR; single-pillar 1/3 = nie finding). (B) §1c scope per-rezim: negative control (3 filary) + Family B liczone per rezim (R1/R2/R3) zgodnie z H0 §1 (stacjonarnosc WEWNATRZ rezimu); positive control BOCPD-euron pozostaje FULL-STREAM (wykrywa przejscia MIEDZY rezimami — ground truth). Statystyki/nulle/progi bez zmian. DoD-4 pozostaje 3/3.
