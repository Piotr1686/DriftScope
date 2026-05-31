# preregistration_v4.md — DriftScope Methodology Pre-registration

**Status:** SUPERSEDED przez v5 [2026-05-31] (history; zastepowala v3; rewizja MIESZANA — zob. §0)
**Wersja:** v4
**Data zamrozenia:** 2026-05-31 (po kalibracji W4 K4-MMD, PRZED W5 Decision Gate i W6)
**Supersedes:** preregistration_v3.md (ktora superseduje v2, v1)

> Ten plik jest czescia architectural contract (PROJECT_BRIEF.md).
> Kazda korekta metodologiczna tworzy preregistration_v{N+1}.md
> z polem `revision_reason: <text>`.

---

## §0. Revision reason (v3 → v4)

`revision_reason:` Ta rewizja jest **MIESZANA** i — w odroznieniu od v1→v2→v3 (wszystkie
czyste, przed jakakolwiek kalibracja) — zawiera czesc **informowana real-data (W4)**.
Rozdzielam te dwie natury jawnie, bo cicha zmiana parametrow preregistracji po obejrzeniu
danych to dokladnie ta praktyka, ktorej DriftScope ma byc audytem. Dyscyplina: v4
zamrazam PRZED W5 Decision Gate i PRZED implementacja W6 — zaden dalszy data-informed
tuning nie wchodzi do bramki.

### (A) Korekta wymuszona wykonalnoscia — INFORMOWANA real-data [DISCLOSED]

**§3 K4-MMD: window N = 200 → N = 25.** Powod nie jest wyborem czulosci, lecz
mechaniczna niewykonalnoscia: realny strumien ma n≈958 (R1=133 / R2=389 / R3=436).
Przy `window=200` i WYMAGANYM non-overlap (zob. (C)) caly strumien daje ~4 okna, a
najmniejszy rezim R1 — **zero**. Test dwuprobkowy MMD jest wtedy niedefiniowalny.
`window=25` daje R1→5, R2→15, R3→17 okien (cienko, ale zdefiniowane), FPR ≤ 7.5%
zwalidowane na realnym n (W4, 2026-05-31).

Dlaczego to NIE jest p-hacking, mimo ze nastapilo po kalibracji: wartosc 200 byla
fizycznie niemozliwa do uruchomienia na deklarowanym n — to korekta bledu specyfikacji,
nie dobor parametru pod wynik. Ale poniewaz nowa siatka §4 (ponizej) jest dobierana po
zobaczeniu, ktore okna w ogole licza sie na tych danych, oznaczam caly blok (A) jako
**post-data** i transparentnie ujawniam. Liczby effect-size (§6), hipotezy (§1),
kontrole (§1b), rodziny testow (§5) — BEZ zmian, nietkniete przez (A).

**§4 Spec curve: N ∈ {100, 200, 400} → N ∈ {15, 25, 40}.** Konsekwencja (A): siatka
{100,200,400} jest na n≈958 (i tym bardziej na R1=133) niewykonalna w non-overlap.
Nowa siatka zachowuje 3 punkty × 3 bandwidth = 9 (struktura §4 niezmieniona). FPR dla
punktow ≠ 25 NIE jest jeszcze zwalidowany — **musi byc zweryfikowany w W6** przy
implementacji spec curve (kryterium FPR ≤ 7.5% per punkt; punkt nieprzechodzacy zostaje
udokumentowany jako niestabilny, nie usuwany po cichu).

### (B) Pre-rejestracja testu wspolwystepowan (§5c) — CZYSTA [pre-data na realnych]

Kalibracja W3 (chi²) i W4 (MMD) wykazaly zgodnie, ze OBA detektory sa **slepe na
signal #5 (pair_corr)** — power ≈ FPR. To nie artefakt, lecz fakt strukturalny: detektory
**marginalne** (czestosci pojedynczych liczb) z zalozenia nie widza struktury **lacznej**
przy zachowanych marginesach. Stad nowy, dedykowany test wspolwystepowan §5c, ktorego
statystyke i null pinuje TERAZ — przed napisaniem kodu W6. Motywacja jest twierdzeniem
(marginalna slepota), nie wynikiem na realnych danych EuroJackpot → blok czysty.

### (C) Formalizacja decyzji projektowych z W4 — DOPRECYZOWANIE

Dwie decyzje zapadly w implementacji W4, ktore v3 §3 zostawial nie-pinowane; v4 je
ratyfikuje (nie zmieniaja metody, domykaja luki specyfikacji):
1. **Non-overlap (step ≥ window) WYMAGANY.** v3 §3 mowil "sliding window" bez pinowania
   kroku. Okna nakladajace sie lamia wymienialnosc permutacyjnego nulla (silnie
   skorelowane within-X, niezalezne X⊥Y) → MMD² systematycznie > null → FPR ~1.0
   (zmierzone W4). Pinuje `step = window`.
2. **Framing = vs uniform reference.** v3 §3 nie pinowal par (X, Y). Pinuje:
   X = okna obserwacji, Y = okna SWIEZEGO uniform 5/50 o tym samym n (symetryczna
   wymienialnosc pod H0).

Rozszerzenia information-theoretic (LZ76/MDL) nadal SWIADOMIE poza preregistracja —
stretch, NIE filar bramkujacy. DoD-4 pozostaje 3/3 (H1/MMD/DriftSim).

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
- **Window size:** **N = 25 (deployed, v4)** — patrz §0(A). Okna **NIENAKLADAJACE sie**:
  `step = window` (non-overlap WYMAGANY, §0(C); `step < window` ZABRONIONE — lamie
  wymienialnosc permutacyjna → FPR ~1.0).
- **Framing:** dwuprobkowy MMD² (X = okna obserwacji, Y = okna swiezego uniform 5/50
  o tym samym n) — §0(C).
- **Kernel:** Gaussian RBF z bandwidth = median heuristic
- **Anti-leakage:** bandwidth obliczana WYLACZNIE na probie X (training window)
- **Estymator:** unbiased MMD² (Gretton et al. 2012)
- **Null:** permutacja etykiet polaczonej puli okien nad pre-policzona macierza Grama
- **Threshold stabilnosci:** FPR ≤ 7.5% na shuffled/uniform null (granica dwustronna
  wokol α=0.05) — zwalidowany na realnym n dla N=25 (W4, 2026-05-31)
- **Ograniczenie danych:** R1 (n=133 → 5 okien) jest na granicy wykonalnosci MMD
  okiennego; power w R1 z zalozenia nizsza. Liczyc jako floor, nie failure.
- **Teoria asymptotyczna:** Gretton et al. 2012

---

## §4. Specification Curve Space (pre-registered)

Parametry i wartosci (siatka skorygowana w v4 §0(A) — wykonalna na n≈958/non-overlap):
- window size N ∈ **{15, 25, 40}**  *(było {100,200,400} w v3 — niewykonalne)*
- bandwidth ∈ {0.5×, 1×, 2×} median heuristic
= **9 punktow** spec curve per sygnal

**Walidacja FPR (W6):** FPR ≤ 7.5% zweryfikowany dotad TYLKO dla N=25. Punkty N∈{15,40}
× bandwidth musza przejsc te sama kalibracje przy implementacji spec curve w W6; punkt
nieprzechodzacy = udokumentowany jako niestabilny (NIE usuwany po cichu).

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

## §5c. Co-occurrence test (pre-registered, NOWY v4 — §0(B))

**Cel:** wykryc strukture LACZNA (signal #5 pair_corr), na ktora detektory marginalne
(chi² §5, MMD §3) sa z zalozenia slepe — para liczb (i,j) wspolwystepuje w jednym
losowaniu czesciej/rzadziej niz pod uniform, przy NIEzmienionych marginesach.

- **Null:** uniform-iid → kazda para (i,j) wspolwystepuje z p_pair = C(48,3)/C(50,5)
  = 20/2450 ≈ 0.00816; liczba wspolwystapien ~ Binomial(n, p_pair) marginalnie.
- **Statystyka:** suma kwadratow standaryzowanych reszt par
  T = Σ_{i<j} (O_ij − E_ij)² / E_ij  (analog chi² na macierzy par 50×50),
  oraz max-pair |z_ij| jako statystyka pomocnicza (lokalizacja najsilniejszej pary).
- **Kalibracja — KRYTYCZNA decyzja nulla:** **swap-randomization / curveball** na
  macierzy incydencji losowanie×liczba. Permutacja zachowuje JEDNOCZESNIE sumy wierszy
  (=5 liczb na losowanie) i sumy kolumn (=marginalna czestosc kazdej liczby), a lamie
  TYLKO strukture parowania. To izoluje sygnal laczny od marginalnego — analityczny
  Binomial(n, p_pair) jest niewazny przy nie-uniform marginesach, dlatego null
  permutacyjny (model wspolwystepowan Connor-Simberloff / Strona curveball).
- **Korekcja:** zasila Family B FDR (§5) jako dodatkowa rodzina per-rezim (rozszerza
  licznik hipotez Family B; finalny licznik domkniety przy implementacji W6 i
  zaratyfikowany w preregistration_v5, jesli ulegnie zmianie).
- **Status walidacji:** statystyka i null PINOWANE; implementacja + kalibracja
  sensitivity/specificity na DriftSim signal #5 = zadanie W6.

---

## §6. DriftSim — planted signals (pre-registered)

5 typow sygnalu × 4 effect sizes = 20 scenarios per rezim + 1 null = **21 datasetow per rezim** (× 3 = 63 unikalne). Sygnal izolowany w puli GLOWNEJ (Δ⁴⁹); euronumery i kalendarz pozostaja nullowe. Liczba noszaca sygnal #1/#3/#4 jest ustalona (reprodukowalnosc); para dla #5 ustalona.

1. **Frequency shift** — p_k = 1/50 + δ, δ ∈ {0.01, 0.02, 0.05, 0.10}  *(PINNED od v2)*
2. **Autocorrelation lag-1** — boost wag liczb z poprzedniego losowania o ρ, ρ ∈ {0.05, 0.10, 0.15, 0.20}  *(PINNED od v2)*
3. **Linear trend** — p_k(t) = 1/50 + β·(t/T), **β ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3 — §0)*
4. **Weekly seasonality** — kontrast wtorek vs piatek na liczbie planted: +c w piatki, −c we wtorki (clip > 0), **c ∈ {0.01, 0.02, 0.05, 0.10}**  *(PINNED w v3 — §0)*. **GUARD: tylko R3** — EuroJackpot losowal wylacznie w piatki do marca 2022; wtorki dodano w R3. W R1/R2 kontrast Tue/Fri nie istnieje → scenariusz degeneruje do uniform null (zajmuje slot datasetu, pelni role dodatkowego negative control; count 63 zachowany).
5. **Pair correlation** — liczby i,j wspolwystepuja czesciej, lift ∈ {1.1, 1.2, 1.5, 2.0}  *(PINNED od v2)*. **Detektor docelowy: §5c co-occurrence (v4)** — marginalne chi²/MMD slepe (W3/W4).

**Permutacja stratyfikowana (R3):** w rezimie z dwoma dniami losowan permutacja zachowuje etykiete dnia (Tue/Fri), zeby null nie konfundowal signal #4.

---

## §7. Revision Log

- **v1 → v2** [2026-05-29]: zob. v2 §0. Piec zmian czystych (przed real-data): korekta daty 2014-10-10, control design positive/negative, recurrence test family, Family B BH → Benjamini-Yekutieli (300 → 450 hipotez), synchronizacja BOCPD α=0.1/hazard=0.005 z kodem (korekta transkrypcji).
- **v2 → v3** [2026-05-30]: zob. v3 §0 revision_reason. Jedna zmiana czysta (przed kalibracja): pinowanie siatek effect-size dla signal #3 (trend β ∈ {0.01,0.02,0.05,0.10}) i signal #4 (seasonality c ∈ {0.01,0.02,0.05,0.10}). Doprecyzowano mechanizm seasonality (±c Fri/Tue). δ/ρ/lift bez zmian.
- **v3 → v4** [2026-05-31]: zob. §0. Rewizja MIESZANA. (A) INFORMOWANA real-data [disclosed]: §3 window 200→25 i §4 spec curve {100,200,400}→{15,25,40} — korekta wymuszona niewykonalnoscia na n≈958/non-overlap, NIE dobor pod wynik; FPR≠25 do walidacji w W6. (B) CZYSTA: §5c co-occurrence test (swap-randomization/curveball null) pre-rejestrowany — domyka strukturalna slepote chi²/MMD na pair_corr (W3/W4). (C) DOPRECYZOWANIE: §3 non-overlap (step=window) + framing vs uniform reference (decyzje implementacyjne W4). Hipotezy/kontrole/Family A/§6 effect-sizes bez zmian.
