# preregistration_v5.md — DriftScope Methodology Pre-registration

**Status:** ACTIVE (zastepuje v4; rewizja MIESZANA, informowana DriftSim — zob. §0)
**Wersja:** v5
**Data zamrozenia:** 2026-05-31 (po implementacji + kalibracji testu wspolwystapien W6,
PRZED W5 Decision Gate)
**Supersedes:** preregistration_v4.md (ktora superseduje v3, v2, v1)

> Ten plik jest czescia architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §0. Revision reason (v4 → v5)

`revision_reason:` Rewizja MIESZANA, w calosci **informowana kalibracja DriftSim (W6)** —
ale na danych SYNTETYCZNYCH (planted signals), NIE na realnym EuroJackpot, ktory pozostaje
nietkniety i nie byl jeszcze przepuszczony przez te detektory. Ujawniam to zgodnie z
dyscyplina §0 z v4. Obie korekty wynikly z implementacji i walidacji testu wspolwystapien
§5c. Zamrazam PRZED W5 Decision Gate.

### (A) §5c statystyka: suma T → max-pair [DriftSim-informed, clean wrt real data]

v4 §5c pinowal statystyke primary jako T = Σ_{i<j}(O_ij − E_ij)²/E_ij (suma po parach).
Korekta na **max-pair** z_ij = (O_ij − E_ij)/sqrt(E_ij). Powod:
1. **Rozmycie rzadkiej alternatywy.** pair_corr to sygnal RZADKI (jedna para z 1225).
   Suma T rozmywa pojedyncza odchylona pare w szumie 1224 par nullowych (null T ~ 1225±49;
   wklad jednej pary rzedu kilku jednostek → tonie → power ≈ FPR, TA SAMA slepota co
   chi²/MMD). Statystyka EKSTREMALNA (max-pair) jest wlasciwa dla rzadkiej alternatywy.
2. **Miskalibracja.** Forma chi² (/E, skala Poissona) jest dla wspolwystapien zle
   skalibrowana — empirycznie FPR ~0.17 na nullu (R3). max-pair kalibruje sie poprawnie
   (FPR ≈ α). Argument strukturalny + empiryczny na DriftSim.
Null (curveball, zachowanie obu marginesow) i lokalizacja pary (top_pair) bez zmian.

### (B) §6 signal #5 pair_corr — re-design mechanizmu [DriftSim-informed, clean wrt real data]

Dwie zmiany sprzezone, oba wynikly z kalibracji testu §5c:

1. **Parametr: mnoznik lift → forced-fraction p ∈ {0.01, 0.02, 0.05, 0.10}.**
   Stara siatka lift ∈ {1.1..2.0} (PINNED od v2) dawala forced-frac = (lift−1)·P_base ∈
   {0.0008..0.0082} — przy lift=2.0 (max) power = 0.05 = FPR floor dla KAZDEGO testu.
   pair_corr byl niewykrywalny nie z powodu slepoty detektorow, lecz znikomej magnitudy
   ("2× lift" na bazie wspolwystapien 0.8% = +0.8pp). Analog findingu W0 (δ=0.01
   niewykrywalny). "lift" jako parametr myli skala — forced-fraction jest jawna.

2. **Mechanizm: margin-preserving (czysty sygnal joint).** Stary mechanizm ("wymus pare
   + 3 uniform") PRZECIEKAL do marginesow: P(liczba planted) = 0.1 + 0.9·p. Przy
   wykrywalnych p chi² zlapalby pair_corr przez SKOK MARGINALNY → kontrast joint-vs-marginal
   skazony, a §6 deklaruje "sygnal izolowany w jednym wymiarze" (zlamane). Nowy mechanizm —
   mieszanka 3-komponentowa (force-para z p / force-brak-obu z 9p / uniform z 1−10p, dla
   p ≤ 0.1) — zachowuje WSZYSTKIE marginesy DOKLADNIE (algebraicznie: P(i)=P(j)=P(inne)=0.1),
   a podnosi P(i,j razem) z 0.00816 do 0.918p+0.00816 (~6.6× przy p=0.05). pair_corr staje
   sie CZYSTYM sygnalem joint: chi²/MMD dowodliwie slepe (marginesy uniform), test §5c lapie.

**Walidacja (DriftSim, n_trials=50/n_perm=99):** czysta komorka Disagreement Protocol —
test wspolwystapien JEDYNYM detektorem lapiacym pair_corr:
| p     | R1 (133) | R2 (389) | R3 (436) |
|-------|----------|----------|----------|
| 0.01  | 0.06     | 0.06     | 0.08     |
| 0.02  | 0.08     | 0.40     | 0.36     |
| 0.05  | 0.80     | 1.00     | 1.00     |
| 0.10  | 1.00     | 1.00     | 1.00     |
Przy p=0.10: chi²=0.06, MMD=0.03 (oba FPR floor — marginesy zachowane → dowodliwie slepe);
cooc FPR(null)=0.03. Decision Gate (>70%) spelniony dla p ≥ 0.05 we wszystkich rezimach.

Count datasetow §6 ZACHOWANY (63): 4 effect sizes bez zmian, tylko ich znaczenie i mechanizm.
δ/ρ/β/c (sygnaly #1–#4) nietkniete. Rozszerzenia IT (LZ76/MDL) nadal poza preregistracja.
DoD-4 pozostaje 3/3.

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

## §5. Multiple Testing Families

**Family A (global time-series):**
- 4 testy (ADF, KPSS, Bayesian CP, Welch) × 3 rezimy = **12 hipotez**
- Korekcja: Benjamini-Hochberg FDR α=0.05 + Storey q-values (secondary sanity)

**Family B (per-number):**
- 50 liczb × 3 testy (chi-squared, exact binomial, gap goodness-of-fit — §5b) × 3 rezimy = **450 hipotez**
- Korekcja: **Benjamini-Yekutieli** FDR α=0.05 jako primary — wazny przy dowolnej strukturze zaleznosci (zliczenia 5/50 ujemnie skorelowane, gapy wspolzalezne), gdzie zalozenie PRDS dla BH jest niepewne; BH jako secondary. Storey odrzucony (niestabilny przy dominujacym null).

---

## §5b. Recurrence / gap analysis (pre-registered)

Czas (liczba losowan) miedzy kolejnymi wystapieniami danej liczby. Pod nullem uniform-iid: gap ~ Geometric(q), q = 5/50 dla puli glownej.

- **Gap goodness-of-fit:** odchylenie empirycznego rozkladu gapow od Geometric(q) per liczba per rezim. ⚠️ **NIE analityczny KS** (Kolmogorov-Smirnov niewazny dla rozkladow dyskretnych — bledne p-value). Statystyka kalibrowana PERMUTACYJNIE (silnik z §permutation, Krok 6 PROJECT_BRIEF).
- **Nelson-Aalen cumulative hazard** per liczba: liniowosc = stala intensywnosc = zgodnosc z uniform.
- **EVT max-gap:** maksymalny gap ma asymptotycznie rozklad Gumbela (gapy geometryczne w domenie przyciagania Gumbela).
- Zasilanie Family B FDR (§5).

---

## §5c. Co-occurrence test (pre-registered v4; statystyka skorygowana v5 §0(A))

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
  **Odrzucona** suma T = Σ(O−E)²/E (v4): rozmywa rzadki sygnal + miskalibrowana (zob. §0(A)).
- **Korekcja:** zasila Family B FDR (§5) jako dodatkowa rodzina per-rezim (finalny licznik
  hipotez domkniety przy pelnej integracji raportowej; ratyfikacja w v{N}, jesli ulegnie zmianie).
- **Status walidacji:** zaimplementowany i skalibrowany na DriftSim (W6). Power: zob. §0(B)
  i §6.5.

---

## §6. DriftSim — planted signals (pre-registered)

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim** (× 3 = 63 unikalne). Sygnal izolowany w puli GLOWNEJ (Δ⁴⁹); euronumery i kalendarz pozostaja nullowe. Liczba noszaca sygnal #1/#3/#4 jest ustalona (reprodukowalnosc); para dla #5 ustalona.

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}  *(PINNED od v2)*
2. **Autocorrelation lag-1** — boost wag liczb z poprzedniego losowania o ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}  *(PINNED od v2)*
3. **Linear trend** — p_k(t) = 1/50 + β·(t/T), **β ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3)*
4. **Weekly seasonality** — kontrast wtorek vs piatek na liczbie planted: +c w piatki, −c we wtorki (clip > 0), **c ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3)*. **GUARD: tylko R3** — EuroJackpot losowal wylacznie w piatki do marca 2022; wtorki dodano w R3. W R1/R2 kontrast Tue/Fri nie istnieje → scenariusz degeneruje do uniform null (zajmuje slot datasetu, pelni role dodatkowego negative control; count 63 zachowany).
5. **Pair correlation (MARGIN-PRESERVING, re-design v5 — §0(B))** — forced-fraction
   **p ∈ {0.01, 0.02, 0.05, 0.10}** (NIE mnoznik lift). Mieszanka 3-komponentowa: z p wymus
   pare {i,j}+3, z 9p wymus brak obu, z (1−10p) uniform. Zachowuje WSZYSTKIE marginesy
   DOKLADNIE (P(dowolnej liczby)=0.1), podnosi P(i,j razem) z 0.00816 do 0.918p+0.00816.
   Czysty sygnal JOINT: **detektor docelowy = §5c co-occurrence (max-pair, curveball null)**;
   chi²/MMD dowodliwie slepe (marginesy uniform). Stary mechanizm (lift, v2–v4) przeciekal do
   marginesow i byl below detection floor — zob. §0(B).

**Permutacja stratyfikowana (R3):** w rezimie z dwoma dniami losowan permutacja zachowuje etykiete dnia (Tue/Fri), zeby null nie konfundowal signal #4.

---

## §6.5. Wyniki kalibracji DriftSim (W3/W4/W6) — pre-rejestrowane oczekiwania vs empiria

Tabela komplementarnosci detektorow (n realne per rezim; zwalidowane testami):
- **freq_shift / trend** — chi² i MMD wykrywaja (odchylenie marginalne).
- **autocorr / seasonality** — chi² i MMD wykrywaja przez nadmierna dyspersje / kontrast.
- **pair_corr (joint, margin-preserving)** — WYLACZNIE §5c co-occurrence; chi²/MMD na FPR
  floor (dowodliwie slepe). Power §5c: p≥0.05 → ≥0.80 wszedzie (Decision Gate spelniony);
  p=0.01 below floor; p=0.02 floor w R1, czesciowy R2/R3. Zob. §0(B).

To uzasadnia DoD-4 = 3/3 (H1/MMD/co-occurrence sa wzajemnie NIE-redundantne) i zasila
Disagreement Protocol (kazdy sygnal: ktore z 3 rodzin go widza).

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: zob. v2 §0. Piec zmian czystych (przed real-data): korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450 hipotez), synchronizacja BOCPD α=0.1/hazard=0.005 z kodem (korekta transkrypcji).
- **v2 → v3** [2026-05-30]: zob. v3 §0. Jedna zmiana czysta (przed kalibracja): pinowanie siatek effect-size dla signal #3 (trend β) i #4 (seasonality c). Doprecyzowano mechanizm seasonality (±c Fri/Tue). δ/ρ/lift bez zmian.
- **v3 → v4** [2026-05-31]: zob. v4 §0. Rewizja MIESZANA. (A) INFORMOWANA real-data [disclosed]: §3 window 200→25 i §4 spec {100,200,400}→{15,25,40} — korekta wymuszona niewykonalnoscia na n≈958/non-overlap. (B) CZYSTA: §5c co-occurrence test (curveball null) pre-rejestrowany. (C) DOPRECYZOWANIE: §3 non-overlap + framing vs uniform reference.
- **v4 → v5** [2026-05-31]: zob. §0. Rewizja MIESZANA, INFORMOWANA DriftSim (synthetic, clean wrt real EuroJackpot). (A) §5c statystyka: suma T → **max-pair** (suma rozmywa rzadki sygnal + miskalibrowana, FPR~0.17). (B) §6 signal #5 pair_corr re-design: parametr lift → **forced-frac {0.01,0.02,0.05,0.10}** + mechanizm **margin-preserving** (3-komponentowy) — stary lift byl below detection floor ORAZ przeciekal do marginesow (lamiac izolacje §6). Nowy = czysty sygnal joint → czysta komorka Disagreement Protocol (co-occurrence JEDYNYM detektorem; chi²/MMD dowodliwie slepe). Count 63 zachowany; sygnaly #1–#4 nietkniete. Dodano §6.5 (tabela komplementarnosci).
