# preregistration_v3.md — DriftScope Methodology Pre-registration

**Status:** ACTIVE (zastepuje v2; wersja zamrozona po W2, przed kalibracja W3)
**Wersja:** v3
**Data zamrozenia:** 2026-05-30 (W2 zamkniete; rewizja czysta — PRZED kalibracja real-data i Decision Gate)
**Supersedes:** preregistration_v2.md (ktora superseduje v1)

> Ten plik jest czescią architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §0. Revision reason (v2 → v3)

`revision_reason:` Jedna zmiana, czysta (PRZED jakakolwiek kalibracja DriftSim):

1. **Pinowanie siatek effect-size dla signal #3 (trend β) i signal #4 (seasonality c).**
   §6 v2 pinowal siatki tylko dla 3 z 5 sygnalow (freq_shift δ, autocorr ρ, pair_corr
   lift), a dla trend podawal jedynie "β dla 4 effect sizes" i dla seasonality "rozne p"
   — bez konkretnych wartosci. Implementacja `planted_signals.py` (W2) wymagala
   konkretnych liczb; uzyto siatek prowizorycznych, ktore TA rewizja ratyfikuje:
   - **trend:** β ∈ {0.01, 0.02, 0.05, 0.10} — analogicznie do freq_shift, by koncowa
     magnituda przy t=T byla porownywalna z freq_shift (p_planted(T) = 1/50 + β).
   - **seasonality:** c ∈ {0.01, 0.02, 0.05, 0.10}, kontrast realizowany jako +c na
     liczbie planted w piatki i −c we wtorki (clip > 0); analogiczna skala do δ.

   Rewizja czysta: nastapila PRZED kalibracja W3 (sensitivity/specificity), wiec wybor
   siatek nie jest informowany wynikami na danych. δ/ρ/lift bez zmian wzgledem v2.

Rozszerzenia information-theoretic (LZ76/MDL) nadal SWIADOMIE poza preregistracja —
stretch, NIE filar bramkujacy. DoD-4 pozostaje 3/3 (H1/MMD/DriftSim).

---

## §1. Hipotezy

**H1:** Strumien losowan EuroJackpot wykazuje mierzalne odchylenia od stacjonarnosci
w co najmniej jednym wymiarze (marginals / CP / spectral / MMD / recurrence)
w co najmniej jednym rezimie regul.

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

- **Input space:** frequency vector p ∈ Δ⁴⁹ per sliding window N=200 (NIE raw draws)
- **Kernel:** Gaussian RBF z bandwidth = median heuristic
- **Anti-leakage:** bandwidth obliczana WYLACZNIE na training window
- **Threshold stabilnosci:** FPR ≤ 7.5% na shuffled null (granica dwustronna wokol α=0.05)
- **Weryfikacja:** W4 PoC vs shuffled null — PRZED W5 Decision Gate
- **Teoria asymptotyczna:** Gretton et al. 2012

---

## §4. Specification Curve Space (pre-registered)

Parametry i wartosci:
- window size N ∈ {100, 200, 400}
- bandwidth ∈ {0.5×, 1×, 2×} median heuristic
= **9 punktow** spec curve per sygnal

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

## §6. DriftSim — planted signals (pre-registered)

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim** (× 3 = 63 unikalne). Sygnal izolowany w puli GLOWNEJ (Δ⁴⁹); euronumery i kalendarz pozostaja nullowe. Liczba noszaca sygnal #1/#3/#4 jest ustalona (reprodukowalnosc); para dla #5 ustalona.

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}  *(PINNED od v2)*
2. **Autocorrelation lag-1** — boost wag liczb z poprzedniego losowania o ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}  *(PINNED od v2)*
3. **Linear trend** — p_k(t) = 1/50 + β·(t/T), **β ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3 — §0)*
4. **Weekly seasonality** — kontrast wtorek vs piatek na liczbie planted: +c w piatki, −c we wtorki (clip > 0), **c ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3 — §0)*. **GUARD: tylko R3** — EuroJackpot losowal wylacznie w piatki do marca 2022; wtorki dodano w R3. W R1/R2 kontrast Tue/Fri nie istnieje → scenariusz degeneruje do uniform null (zajmuje slot datasetu, pelni role dodatkowego negative control; count 63 zachowany).
5. **Pair correlation** — liczby i,j wspolwystepuja czesciej, lift ∈ {1.1, 1.2, 1.5, 2.0}  *(PINNED od v2)*

**Permutacja stratyfikowana (R3):** w rezimie z dwoma dniami losowan permutacja zachowuje etykiete dnia (Tue/Fri), zeby null nie konfundowal signal #4.

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: zob. v2 §0. Piec zmian czystych (przed real-data): korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450 hipotez), synchronizacja BOCPD α=0.1/hazard=0.005 z kodem (korekta transkrypcji).
- **v2 → v3** [2026-05-30]: zob. §0 revision_reason. Jedna zmiana czysta (przed kalibracja): pinowanie siatek effect-size dla signal #3 (trend β ∈ {0.01,0.02,0.05,0.10}) i signal #4 (seasonality c ∈ {0.01,0.02,0.05,0.10}), ktore v2 §6 zostawial niedoprecyzowane. Doprecyzowano tez mechanizm seasonality (±c Fri/Tue na liczbie planted). δ/ρ/lift bez zmian.
