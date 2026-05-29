# preregistration_v1.md — DriftScope Methodology Pre-registration

**Status:** SUPERSEDED przez preregistration_v2.md [2026-05-29] — zob. v2 §0 revision_reason
**Wersja:** v1
**Data zamrozenia:** [uzupelnic przed W1]

> Ten plik jest czescią architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna po Decision Gate tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §1. Hipotezy

**H1:** Strumien losowan EuroJackpot wykazuje mierzalne odchylenia od stacjonarnosci
w co najmniej jednym wymiarze (marginals / CP / spectral / MMD)
w co najmniej jednym rezimie regul.

**H0:** Strumien jest generowany przez stacjonarny, uniform, i.i.d. proces
w kazdym rezimie (pre-2014, 2014-2022, post-2022).

---

## §2. Model generatywny — Bayesian online CP (Adams-MacKay 2007)

- **Prior:** p ~ Dirichlet(α=1) — uniform flat prior na simpleksie Δ⁴⁹
- **Likelihood:** draw_t ~ Categorical(p)
- **Posterior update:** α_k += 1 dla kazdego wylosowanego k
- **Hazard:** geometric z rate r=1/250 (expected run length = 250 losowan)
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
- Korekcja: BH FDR α=0.05 + Storey q-values (secondary sanity)

**Family B (per-number goodness-of-fit):**
- 50 liczb × 2 testy (chi-squared, exact binomial) × 3 rezimy = **300 hipotez**
- Korekcja: BH FDR α=0.05 only (Storey niestabilne przy 300 hipotez z dominujacym null)

---

## §6. DriftSim — planted signals (pre-registered)

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim**:

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}
2. **Autocorrelation lag-1** — P(x_t=k | x_{t-1}=k) = 1/50 + ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}
3. **Linear trend** — p_k(t) = p_k + β·(t/T), β dla 4 effect sizes
4. **Weekly seasonality** — rozne p dla wtorek vs piatek (cycle = 2 losowania)
5. **Pair correlation** — liczby i,j wspolwystepuja czesciej, lift ∈ {1.1, 1.2, 1.5, 2.0}

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: SUPERSEDED. Korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450). Szczegoly: preregistration_v2.md §0.
