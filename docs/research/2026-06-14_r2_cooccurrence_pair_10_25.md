# Mini-study — para (10,25) w R2: anatomia „honest negative"

**Data:** 2026-06-14
**Typ:** analiza wewnętrzna (reporting-only; prereg v7 nietknięty)
**Cel:** Skonkretyzować jedyną flagę negative-controlu (R2, współwystąpienia) i pokazać,
dlaczego Disagreement Protocol klasyfikuje ją jako **1/3 „requires power context"**, a NIE
jako finding — na poziomie konkretnych liczb, nie ogólnika „one pair on the main pool".
**Status:** NIE jest findingiem. To demonstracja działania bramki rygoru na czystym nullu.

---

## Executive summary

W negative-controlu EuroJackpot (główna pula 1–50, niezmieniana przy reformach 2014/2022),
oceniana per-reżim przez trzy filary, werdykt brzmi **R1 0/3 · R2 1/3 · R3 0/3**. Jedyna
niezerowa flaga to test współwystąpień w **R2** (389 losowań), który lokalizuje parę
**(10, 25)**. Ta para to **podręcznikowa „clean cell"**: czysto **łączna** anomalia przy
całkowicie niewinnych marginesach. To dokładnie ta sama własność, która czyni współwystąpienia
„czystą komórką" Disagreement Protocol (widzą strukturę par niewidoczną dla marginesów) —
i która sprawia, że **spurious** fluke łączny też jest niewidoczny dla per-number FDR
(Family B). Stąd routing do 1/3, nie awans. Pojawienie się dokładnie jednej flagi w trzech
reżimach jest pod czystym nullem **najbardziej prawdopodobnym niezerowym wynikiem** (P ≈ 14%).

---

## 1. Wynik testu — trzy reżimy

Test: `cooccurrence_maxpair` (statystyka max-pair `z_ij = (O−E)/√E`, null = curveball
swap-randomization zachowujący oba marginesy; preregistration_v7 §5c). Detektor
deterministyczny — seed z digestu danych ⊕ base_seed (DoD-6).

| Reżim | n | p (max-pair) | max-z | top_pair | reject @ α=0.05 |
|---|---|---|---|---|---|
| R1 | 133 | 0.586 | 3.80 | (5, 12) | ✗ |
| **R2** | **389** | **0.024** | **4.60** | **(10, 25)** | **✓** |
| R3 | 436 | 0.667 | 3.33 | (28, 31) | ✗ |

(Wartości p przy `n_perm=999`. Kanoniczny raport renderuje przy `n_perm=199` — para i z są
niezmiennicze, p ≈ 0.010–0.024 to oczekiwana wariancja Monte Carlo permutacyjnego p-value.)

Para (10, 25) jest stabilna względem `n_perm`, bo `top_pair = argmax z` jest zdominowana
przez surowe **O**, nie przez szum estymaty E.

---

## 2. Anatomia pary (10, 25) — joint excess, marginesy niewinne

W R2 (n = 389) pod nullem curveball oczekiwane współwystąpienie pary wynosi E ≈ 2.2:

| Wielkość | Wartość | Komentarz |
|---|---|---|
| O(10,25) — obserwowane współwystąpienia | **9** | razem w 9 z 389 losowań |
| E(10,25) — oczekiwane pod nullem | **2.19** | curveball, marginesy zachowane |
| z = (O−E)/√E | **4.60** | ~4× ponad oczekiwane |
| Margines #10 (liczebność) | **28** | oczek. 38.9 → z_marg = **−1.84** |
| Margines #25 (liczebność) | **38** | oczek. 38.9 → z_marg = **−0.15** |

**Kluczowa obserwacja:** liczba 10 jest wręcz **najrzadszą** liczbą w R2 (min rozkładu
liczebności = 28 przy mean = 38.9, sd = 4.8), a liczba 25 jest **idealnie średnia**. Mimo to
parują się 4× za często. To nie jest artefakt marginesu — to **czysto łączna** struktura.

Pozostałe pary w ogonie są wyraźnie słabsze i izolowane (brak klastra):

| Rank | Para | O | E | z |
|---|---|---|---|---|
| 1 | (10, 25) | 9 | 2.19 | **4.60** |
| 2 | (16, 18) | 10 | 3.42 | 3.56 |
| 3 | (10, 32) | 7 | 2.03 | 3.49 |
| 4 | (27, 35) | 10 | 3.49 | 3.48 |
| 5 | (2, 45) | 8 | 2.54 | 3.42 |

---

## 3. Dlaczego to NIE awansuje — i dlaczego to spójne, nie sprzeczne

Awans do watchlist (DoD-5) wymaga **obu** bramek: per-number FDR (Family B, q ≤ α) **oraz**
konwergencji ≥1 filara. Para (10,25) nie przechodzi bramki FDR — i to **z konstrukcji**:

- Family B testuje **pojedyncze liczby** (`count_k ~ Binomial(n, 5/50)`). Widzi #10
  (niedoreprezentowaną, nieistotnie) i #25 (idealnie średnią). **Nie ma czego korygować** —
  per-number Family B daje 0/150 odrzuceń (min q = 1.0).
- Ta sama własność, która czyni współwystąpienia *jedynym* detektorem łapiącym czysty sygnał
  `pair_corr` (margin-preserving — „clean cell", §6.5 raportu), oznacza, że spurious fluke
  łączny **też** jest niewidoczny dla marginesów. Detektor par i bramka FDR patrzą na
  ortogonalne aspekty — więc flaga par nie ma jak być cross-walidowana marginalnie.

Stąd klasyfikacja **1/3 „requires power context"** to **decyzja routingowa**, nie odrzucenie.
Gdyby to był *prawdziwy* sygnał jednofamilijny, który dodatkowo czyściłby FDR — mógłby się
wybić (bramka konwergencji wymaga ≥1 filara, nie ≥2). Ten nie czyści FDR → nie awansuje.

---

## 4. Kontekst expected-rate — dlaczego dokładnie jedna flaga to null, nie sygnał

Trzy reżimy = trzy niezależne testy negative-controlu. Pod czystym nullem przy α = 0.05:

> P(≥1 z 3 reżimów flaguje) = 1 − (1 − 0.05)³ = 1 − 0.95³ = **0.1426 ≈ 14%**

Dostać dokładnie jedną flagę (R2) jest więc **najbardziej prawdopodobnym niezerowym wynikiem**
pod hipotezą zerową — w pełni spójne z „pula 1–50 jest uniform". Zero flag nie byłoby
„czystsze"; byłoby podejrzanie ciche względem własnej kalibracji (FPR ≈ α z konstrukcji
max-pair, zob. cooccurrence.py docstring, R3/W6).

---

## 5. Wniosek

Para (10, 25) jest **demonstracją działania Disagreement Protocol na czystym nullu**, nie
defektem losowania EuroJackpot. Trzy elementy składają się na honest-negative:

1. **Joint excess realny** (z = 4.60), ale **marginesy niewinne** (10 rzadka, 25 średnia) —
   czysto łączna struktura, „clean cell".
2. **Bramka FDR strukturalnie nie może go potwierdzić** (per-number ślepy na sygnał par) →
   1/3, nie awans. To routing, nie tłumienie.
3. **Expected-rate** (~14% na ≥1 flagę w 3 reżimach) czyni dokładnie jedną flagę najbardziej
   prawdopodobnym wynikiem pod nullem.

Framework **nie proponuje niczego** (watchlist = None). Surowy sygnał raportowany jako surowy,
brak konwergentnej evidencji jako brak evidencji.

---

*Reprodukcja:* `load_seed_csv()` → `split_by_regime()` → `cooccurrence_detector(n_perm=999)`
na reżimie R2; marginesy z `_incidence_matrix(...).sum(axis=0)`. Wszystko deterministyczne
(seed z digestu danych). Pełny pipeline: `run_audit(draws, n_perm=199)` → `report.regime_audits["R2"]`.
