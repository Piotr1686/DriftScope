# preregistration_v2.md — DriftScope Methodology Pre-registration

**Status:** ACTIVE (zastepuje v1; wersja zamrozona przed W1)
**Wersja:** v2
**Data zamrozenia:** przed W1 (projekt na W0 — rewizja czysta, przed analiza real-data)
**Supersedes:** preregistration_v1.md

> Ten plik jest czescią architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna po Decision Gate tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §0. Revision reason (v1 → v2)

`revision_reason:` Cztery zmiany metodologiczne wprowadzone na W0, PRZED jakakolwiek analiza real-data (rewizja czysta):

1. **Korekta change-pointu 2014-10-08 → 2014-10-10.** 8 pazdziernika 2014 to byla sroda; pierwsze losowanie z poszerzona pula euronumerow (1-10) odbylo sie w piatek 10 pazdziernika 2014 (potwierdzone 3 niezaleznymi zrodlami). 2014-10-08 byla data komunikatu regulacyjnego, NIE data wejscia zmiany w zycie.
2. **Reframe DoD-1 na positive/negative control.** Change-pointy 2014/2022 sa ground truth WYLACZNIE dla pod-procesu euronumerow (rozszerzenie support 8→10→12). Glowna pula 1-50 nie zmienila sie → sluzy jako wbudowany negative control w tym samym realnym zbiorze.
3. **Nowy test family: recurrence / gap analysis** (zob. §5b). Gap goodness-of-fit kalibrowany permutacyjnie (analityczny KS niewazny dla rozkladow dyskretnych).
4. **Family B FDR: BH → Benjamini-Yekutieli**, 300 → 450 hipotez (dodany gap test; BY ze wzgledu na zaleznosc zliczen 5/50 i gapow).

Rozszerzenia information-theoretic (LZ76/MDL) SWIADOMIE poza preregistracja — stretch v2, NIE filar bramkujacy. DoD-4 pozostaje 3/3 (H1/MMD/DriftSim).

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
- **Negative control:** strumien glownych liczb 1-50. Brak znanej zmiany regul w 2014/2022. Detektor NIE powinien rankowac CP w tych datach; spurious CP = hallucination signal.

Oba strumienie pochodza z TEGO SAMEGO realnego zbioru — kontrola wbudowana, nie syntetyczna.

---

## §2. Model generatywny — Bayesian online CP (Adams-MacKay 2007)

- **Prior:** p ~ Dirichlet(α=1) — uniform flat prior na simpleksie Δ⁴⁹
- **Likelihood:** draw_t ~ Categorical(p)
- **Posterior update:** α_k += 1 dla kazdego wylosowanego k
- **Hazard:** geometric z rate r=1/250 (expected run length = 250 losowan)
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

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim** (× 3 = 63 unikalne):

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}
2. **Autocorrelation lag-1** — P(x_t=k | x_{t-1}=k) = 1/50 + ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}
3. **Linear trend** — p_k(t) = p_k + β·(t/T), β dla 4 effect sizes
4. **Weekly seasonality** — rozne p dla wtorek vs piatek (cycle = 2 losowania). **GUARD: tylko R3** — EuroJackpot losowal wylacznie w piatki do marca 2022; wtorki dodano w R3. W R1/R2 kontrast Tue/Fri nie istnieje → scenariusz degeneruje do uniform null (zajmuje slot datasetu, pelni role dodatkowego negative control; count 63 zachowany).
5. **Pair correlation** — liczby i,j wspolwystepuja czesciej, lift ∈ {1.1, 1.2, 1.5, 2.0}

**Permutacja stratyfikowana (R3):** w rezimie z dwoma dniami losowan permutacja zachowuje etykiete dnia (Tue/Fri), zeby null nie konfundowal signal #4.

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: zob. §0 revision_reason. Cztery zmiany czyste (przed real-data): korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450 hipotez).
