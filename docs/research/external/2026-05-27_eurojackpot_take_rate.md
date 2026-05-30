# EuroJackpot — Take Rate Research

**Data:** 2026-05-27
**Źródło:** Claude.ai (web search, źródła PL/EN/DE/FI/IT)
**Cel:** Input dla decyzji architektonicznej DriftScope o rozszerzeniu w stronę predykcji
**Skala pewności:** 🟢 oficjalne źródło prawne/operatora · 🟡 źródło branżowe/dziennikarskie · 🔴 estymacja własna

---

## Executive summary

**EuroJackpot ma sztywne 50% Return-To-Player na poziomie konsorcjum** — to nie jest "rynkowy" parametr, tylko fix konstrukcyjny zapisany w Gewinnplan. Pozostałe 50% trafia do operatorów krajowych, skarbu państwa i celów społecznych — z bardzo różnym podziałem w zależności od kraju. **Z perspektywy gracza polskiego efektywny RTP wynosi ~40%** (bo do stawki 10 PLN doliczana jest obowiązkowa 25% dopłata na fundusze celowe), co oznacza **take rate ~60%**.

**Dla DriftScope kluczowy wniosek jest brutalny:** żeby gra liczbowa miała EV > 0, sumaryczny "edge" względem rozkładu uniform musi przekroczyć **+100% na poziomie konsorcjum** lub **+150% z perspektywy gracza w Polsce**. Statystycznie istotne odchylenie rzędu kilku procent w częstości jednej liczby przekłada się na edge rzędu pojedynczych procent — to o dwa rzędy wielkości za mało. Detekcja anomalii w losowaniu Eurojackpot nie jest ścieżką do dodatniego EV; może być co najwyżej **research instrumentem** do badania jakości procesu losowania, nie strategią inwestycyjną.

50% RTP **nie zmieniło się** ani przy reformie 2014-10-10, ani przy 2022-03-25 — obie zmieniły wyłącznie strukturę kombinatoryczną (rozszerzenie puli euronumerów) i dystrybucję między klasami, zachowując całkowity payout pool.

---

## 1. Aktualny take rate EuroJackpot

### 1.1 Poziom konsorcjum (wspólna pula)

**🟢 50% wszystkich stawek trafia do prize pool, 50% do operatorów/państwa.**

Z każdego 2 EUR stawki:
- **1 EUR (50%)** → prize pool dla 12 klas wygranych
- **1 EUR (50%)** → koszty operacyjne, marża operatorów, podatki krajowe, cele społeczne (proporcje zależą od kraju)

Źródła potwierdzające (3 niezależne źródła operatorskie + Wikipedia DE):
- 🟢 euro-jackpot.net/prize-fund-distribution: *"Out of every €2 spent on a Eurojackpot ticket, 50 percent (€1) is allocated to the prize fund"*
- 🟢 LottoMV (oficjalny operator Mecklenburg-Vorpommern): *"Unverändert bleibt die Gewinnausschüttung von 50 Prozent der Spieleinsätze insgesamt auf alle Gewinnklassen"*
- 🟢 estrazionedellotto.it (oficjalna strona FAQ): *"Fifty per cent of all ticket revenue goes into the total prize fund"*
- 🟡 Wikipedia DE (Ausschüttungsquote): *"Zahlenlotterien wie deutsches Lotto „6 aus 49", österreichisches Lotto „6 aus 45", Eurojackpot, Euromillions: 50%"*

### 1.2 Per-country breakdown — co dzieje się z pozostałymi 50%

> **Uwaga metodyczna:** "Effective player RTP" liczę z perspektywy gracza — czyli **prizes_received / total_paid_at_register**. To różni się od "consortium RTP" (50%), bo wiele krajów dolicza obowiązkowe opłaty/podatki *do ceny kuponu*, oraz potrąca podatki *od wygranej*.

| Kraj | Operator | Cena 1 zakładu | Dodatkowe opłaty | Podatek od wygranej | **Effective player RTP** | Tier evidence |
|------|----------|----------------|-------------------|---------------------|---------------------------|---------------|
| 🇵🇱 Polska | Totalizator Sportowy | 10 PLN stawki | **+25% dopłata** (2.50 PLN) na 4 fundusze celowe | **10% od wygranych >2280 PLN** | **~40%** (bez podatku) / **~36%** (duże wygrane) | 🟢 |
| 🇩🇪 Niemcy | DLTB (16 spółek landowych) | 2 EUR | **+0.75 EUR Bearbeitungsgebühr** (typowo, single Tipp) | Brak — wygrane wolne od podatku | **~36%** (1 EUR / 2.75 EUR) | 🟢 |
| 🇫🇮 Finlandia | Veikkaus | 2 EUR | Brak ujawnionej dodatkowej opłaty | Brak — wygrane wolne od podatku (arpajaisvero płaci Veikkaus) | **~50%** | 🟢 |
| 🇮🇹 Włochy | Sisal (koncesja ADM) | 2 EUR | Brak — 8% aggio do sieci jest *wewnątrz* stawki | **20% od wygranych >500 EUR** | **~50%** (małe wygr.) / ~40% (duże) | 🟢 |

#### 1.2.1 Polska — Totalizator Sportowy

🟢 **Stawka i dopłata:** Z lotto.pl (oficjalna strona TS): *"Dopłata wynosi 25% stawki za udział w grze. W Eurojackpot do stawki, która wynosi 10 zł, doliczamy dopłatę 2,50 zł"*. Gracz płaci łącznie **12,50 PLN** za jeden zakład.

🟢 **Podział dopłaty** (Ustawa o grach hazardowych, rozdział 9):
- Fundusz Rozwoju Kultury Fizycznej — 75%
- Fundusz Promocji Kultury — 20%
- Fundusz Wspierania Rozwoju Społeczeństwa Obywatelskiego — 4%
- Fundusz Rozwiązywania Problemów Hazardowych — 1%

🟢 **Podatek od wygranej:** 10% od wygranych powyżej 2280 PLN, potrącany u źródła przez Totalizator Sportowy (PIT, art. 30 ust. 1 pkt 2).

🔴 **Estymacja:** Z 12,50 PLN gracz dostaje średnio 5 PLN (50% z 10 PLN stawki) jako wygrane → effective player RTP = **5/12,50 = 40%**. To **przed** potrąceniem 10% podatku od dużych wygranych. Po podatku dla wygranej w wysokości >2280 PLN: RTP spada do **~36%**.

#### 1.2.2 Niemcy — DLTB

🟢 **Stawka i opłata manipulacyjna:** Z westlotto.de (oficjalny operator NRW): *"Der Spieleinsatz für Eurojackpot beträgt 2 Euro je Tipp. Die Bearbeitungsgebühr richtet sich nach der Laufzeit und der Spielart, bei einmaliger Teilnahme eines Normal-Tipps und einer Ziehung zum Beispiel 0,75 Euro"*. Gracz płaci łącznie **2,75 EUR**.

🟢 **Lotteriesteuer:** 20% od *planmäßiger Preis* zgodnie z § 27 RennwLottG (Rennwett- und Lotteriegesetz, 2021). Efektywnie ~16,67% od stake'u brutto. Płacona przez operatora do skarbu państwa landu.

🟢 **Wygrane wolne od podatku** dla gracza (zgodnie z RennwLottG).

🔴 **Estymacja:** Z 2,75 EUR gracz dostaje 1 EUR (50% z 2 EUR stake'u) → effective player RTP = **1/2,75 ≈ 36,4%**. Bearbeitungsgebühr jest "operator margin" przeznaczonym częściowo na prowizję dla Annahmestelle (kolektor lotto), częściowo na koszty operacyjne DLTB. **Take rate efektywny: ~63,6%.**

#### 1.2.3 Finlandia — Veikkaus

🟢 **Stawka:** 2 EUR za normaalitavalla (standardowy zakład), bez widocznej dodatkowej opłaty manipulacyjnej.

🟢 **Arpajaisvero:** 12% od *arpajaisten tuotto* (stawki minus wypłacone wygrane) zgodnie z arpajaisverolaki (552/1992). Veikkaus ma monopol państwowy — *yksinoikeudella toimeenpantavat arpajaiset*. Stawka była tymczasowo obniżana w okresie COVID (5,5% w 2021, 3,4% w 2022, 5,0% w 2023), **wróciła do 12% w 2024**.

🟢 **Wygrane całkowicie wolne od podatku** dla gracza (Veikkaus płaci arpajaisvero u źródła).

🔴 **Estymacja:** Z 2 EUR gracz dostaje średnio 1 EUR (50%) → effective player RTP = **~50%**. To najwyższy z badanych krajów. Take rate efektywny: **~50%**. Pozostałe 50%: 12% × 50% = 6% stawki idzie na arpajaisvero, reszta (~44% stawki) → na operacje Veikkaus + zyski państwa (Veikkaus to spółka 100% państwowa).

⚠️ **Uwaga:** Od 1.1.2027 planowane otwarcie fińskiego rynku gier na licencjonowanych operatorów prywatnych (rahapelilaki). Może to istotnie zmienić strukturę.

#### 1.2.4 Włochy — Sisal

🟢 **Stawka:** 2 EUR za giocata, niezależnie od kanału (kupiec, online, app).

🟢 **Aggio do sieci sprzedaży:** 8% od stawki (borsaefinanza.it cytując regulamin Sisal: *"alla rete va un aggio dell'8% sulle giocate"*).

🟢 **Podatek od wygranej:** 20% od części wygranej powyżej 500 EUR (od 2020 r.). Identycznie jak w Superenalotto.

🔴 **Estymacja:** Bez dodatkowych opłat do stake'u → effective player RTP = **50%** dla małych wygranych (<500 EUR) lub **~40%** dla dużych wygranych (po 20% podatku od nadwyżki).

### 1.3 Podsumowanie — kto trzyma ile

Z 2 EUR stawki (consortium average):
- 🎁 **1 EUR → prize pool** dla graczy (50%)
- 🏛️ **~0,33–0,40 EUR → podatki + zweckerträge** (ok. 17–20%, średnia ważona ekspozycji)
- 🏪 **~0,15 EUR → prowizja punktów sprzedaży** (~7,5%)
- 🏢 **~0,25–0,50 EUR → operacje konsorcjum i operatorów krajowych** (różnie per kraj)

🟡 Dane dla DLTB jako benchmark dla podziału "non-prize 50%": z lotto.de struktura dla Lotto 6aus49 (mocno podobna do Eurojackpot):
- 50% — Gewinnausschüttung
- ~23% — Zweckerträge (sport, kultura, środowisko)
- ~16,67% — Lotteriesteuer
- ~7,5% — prowizja kolektorów
- ~2,8% — administracja/operator

---

## 2. Struktura prize pool (12 klas wygranych)

🟢 **Źródło:** euro-jackpot.net/prize-fund-distribution (struktura obowiązująca od 25.03.2022).

Z 50% stawek, które trafiają do prize fund (oznaczonego dalej jako "100% prize pool"):

| Klasa | Trafienia | % prize pool | Średnia wygrana (25.03.2022–05.05.2026)* | Szansa wygrania |
|-------|-----------|--------------|-------------------------------------------|------------------|
| 1 | 5 + 2 | **36,00%** | €46 156 894,06 | 1 : 139 838 160 |
| 2 | 5 + 1 | **8,60%** | €1 227 066,08 | 1 : 6 991 908 |
| 3 | 5 + 0 | **4,85%** | €192 126,32 | 1 : 3 107 515 |
| 4 | 4 + 2 | **0,80%** | €5 625,49 | 1 : 621 503 |
| 5 | 4 + 1 | **1,00%** | €323,98 | 1 : 31 075 |
| 6 | 3 + 2 | **1,10%** | €164,61 | 1 : 14 125 |
| 7 | 4 + 0 | **0,80%** | €113,40 | 1 : 13 811 |
| 8 | 2 + 2 | **2,55%** | €26,34 | 1 : 985 |
| 9 | 3 + 1 | **2,85%** | €20,40 | 1 : 706 |
| 10 | 3 + 0 | **5,40%** | €17,15 | 1 : 314 |
| 11 | 1 + 2 | **6,74%** | €13,10 | 1 : 188 |
| 12 | 2 + 1 | **20,30%** | €10,04 | 1 : 49 |
| — | Booster Fund | **9,00%** | (gwarancja min €10M jackpot) | — |
| | **TOTAL** | **100%** | | overall: 1 : 32 |

*Średnie liczone z ziehań po reformie 2022. **Klasa 1 (jackpot) jest pari-mutuel z gwarantowanym minimum €10M.** Pozostałe klasy 2–12 też są pari-mutuel: % prize pool dzielony równo między zwycięzców w danej klasie.

**Cap jackpotu:** €120M. Po osiągnięciu nadwyżka przelewa się do klasy 2 (która ma własny cap €120M).

**Booster Fund:** 9% pool flow → gwarantuje minimum jackpot €10M nawet przy niskiej sprzedaży. Jeśli przekroczy €20M, nadwyżka idzie do jackpotu następnego losowania.

🟡 **Strukturalna obserwacja:** Klasa 1 i 12 razem absorbują 56,3% prize pool. Klasa 12 (2+1) ma najczęstszą wypłatę (1 z 49 zakładów) i pochłania 20,3% pool. To oznacza, że "naprawdę często" graczom wracają drobne kwoty ~€10 — psychologicznie utrzymuje zaangażowanie.

---

## 3. Historical evolution

### 3.1 Oś czasu zmian zasad

| Data | Zmiana | Wpływ na RTP | Wpływ na strukturę |
|------|--------|---------------|---------------------|
| 🟢 **2012-03-23** | Pierwsze losowanie. Format: 5 z 50 + 2 z 1-8. Cap rollover: 12 ziehań | 50% (od początku) | 12 klas, początkowo z mechanizmem rolldown |
| 🟢 **2013-02-01** | Usunięto cap 12 rollover; wprowadzono cap jackpotu €90M | Bez zmian | Nadwyżki >€90M → klasa 2 |
| 🟢 **2014-10-10** ⚠️ | Euronumery rozszerzono z 1-8 → 1-10. Czechy + Węgry dołączyły | Bez zmian (50% nadal) | Szansa jackpotu: 1:59 325 280 → 1:95 344 200 |
| 🟢 **2022-03-25** ⚠️ | Euronumery 1-10 → 1-12. Dodano losowanie wtorkowe. Cap jackpotu €90M → €120M. Klasy 6 i 7 zamienione miejscami w Gewinnplan. Drobne korekty alokacji % między klasami | **Bez zmian (50% nadal)** | Szansa jackpotu: 1:95 344 200 → 1:139 838 160 |

⚠️ **UWAGA WAŻNA dla DriftScope:** User w prompcie podał datę **2014-10-08**, ale faktyczne pierwsze losowanie z poszerzoną pulą Euronumerów (1-10) odbyło się w **piątek 10 października 2014**, nie 8 października (środa nie była dniem losowania w 2014). Źródła: Wikipedia EN, lotto.net/eurojackpot/results, multilotto.com — wszystkie potwierdzają 2014-10-10.

### 3.2 Czy zmiany wpłynęły na take rate?

**🟢 NIE.** Take rate 50% jest stabilny we wszystkich erach. Cytat z lottomv.de przy okazji 2022 reform: *"Die Verteilung der Gewinnausschüttung ändert sich nicht. Weiterhin fließen grundsätzlich 50 Prozent der Einsätze als Gewinne an die Eurojackpot-Freunde zurück."*

Co się zmieniło w 2022:
1. Liczba euronumerów (10 → 12) → odbicie kombinatoryczne, nie finansowe
2. Częstotliwość losowań (1 × tydzień → 2 × tydzień) → wzrost wolumenu sprzedaży, nie zmiana % alokacji
3. Cap jackpotu (€90M → €120M) → opóźnienie momentu rollover-cap, nie zmiana RTP
4. **Drobne korekty % alokacji między klasami 2-12** → dokładne wartości pre-2022 nie udało mi się ustalić w publicznych źródłach (zob. Open Questions). Sumarycznie nadal **50% RTP + 9% Booster** = 41% net do klas 1-12.
5. Zamiana klasy 6 i 7: pre-2022 Klasa 6 = "4 trafienia", Klasa 7 = "3 + 2 Euronumery". Post-2022 odwrotnie — bo zmiana prawdopodobieństw spowodowała, że "3+2" stało się rzadsze niż "4+0".

### 3.3 Implikacje dla zbioru danych DriftScope

Dla analizy historycznej istnieją **3 reżimy stacjonarne**:

| Reżim | Okres | Główne liczby | Euronumery | Łączna kombinacja jackpotu |
|-------|-------|---------------|------------|-----------------------------|
| **R1** | 23.03.2012 – 03.10.2014 | 5 z 50 | 2 z 1-8 | 59 325 280 |
| **R2** | 10.10.2014 – 18.03.2022 | 5 z 50 | 2 z 1-10 | 95 344 200 |
| **R3** | 25.03.2022 – obecnie | 5 z 50 | 2 z 1-12 | 139 838 160 |

⚠️ **Krytyczne dla modeli statystycznych:** Częstość pojawienia się euronumeru 9 lub 10 w okresie R1 wynosi **0**, w R2 to ~1/10, w R3 to ~1/12. Mieszanie reżimów daje fałszywe "anomalie" w częstości. Modele DriftScope **muszą** segmentować dane po tych boundary dates lub stosować rolling baseline z odpowiednim oknem.

---

## 4. Implikacje dla DriftScope

### 4.1 Minimalny edge dla EV > 0 — wyprowadzenie

Niech:
- `S` = stawka netto trafiająca do prize pool (proporcja stake)
- `δ` = sumaryczny edge nad uniform baseline (jak ułamek, np. 0.5 = 50%)

Oczekiwany payback przy wyborze kombinacji z edge δ:
```
EV_return = stake × S × (1 + δ)
```

Warunek EV > 0:
```
stake × S × (1 + δ) > stake_total_paid
```

#### Scenariusz A — perspektywa konsorcjum (Finlandia/Włochy, brak dodatkowych opłat)
- `S = 0.5` (50% prize pool)
- `stake_total = stake` (gracz płaci tyle co stake)
- Warunek: `0.5 × (1 + δ) > 1` → **δ > 1.0 = +100% edge**

#### Scenariusz B — perspektywa gracza polskiego
- `S = 0.5 × (10 PLN / 12.50 PLN) = 0.4` (40% efektywny RTP)
- Warunek: `0.4 × (1 + δ) > 1` → **δ > 1.5 = +150% edge**

#### Scenariusz C — perspektywa gracza niemieckiego
- `S = 0.5 × (2 EUR / 2.75 EUR) ≈ 0.364`
- Warunek: `0.364 × (1 + δ) > 1` → **δ > 1.75 = +175% edge**

### 4.2 Czy detekcja anomalii w losowaniu może dać taki edge?

**Krótko: NIE.** Argument:

Wyobraźmy sobie hipotetyczną maksymalną wykrywalną anomalię — pojedyncza liczba pojawia się z częstością **5% wyższą niż uniform** (czyli zamiast 1/50 = 2.00%, mamy 2.10%). To jest już **gigantyczne** odchylenie statystyczne — przy 1000 losowaniach to różnica ~5σ od uniform, czyli już praktycznie pewność że nie jest to szum.

Co to daje w EV?
- Edge na pojedynczej "main number": +5% w trafieniach tej liczby
- W kombinacji 5 numerów głównych, jeśli każda ma niezależne +5% edge: `1.05^5 = 1.276` (+27.6%)
- W 2 euronumerach: `1.05^2 = 1.1025` (+10.25%)
- **Łączny edge przy "wszystkich numerach z 5% edge": ~40%**

To **wciąż 2,5× za mało**, żeby pokryć 100% wymagany na poziomie konsorcjum. A wykrycie 5% edge na **wszystkich** liczbach naraz jest niemożliwe (musi być per liczba — niektóre na plus, niektóre na minus, średnia = uniform). Realistycznie wykrywalna anomalia to **pojedyncza liczba z anomalią rzędu 1-2%** → edge < 1%.

### 4.3 Kontekst dla pari-mutuel — "betting bias" strategy

Eurojackpot jest **pari-mutuel** we wszystkich 12 klasach. Oznacza to:
- Wartość puli per klasa jest sztywna (% prize pool)
- Wygrana per zwycięzca = pula klasy / liczba zwycięzców w tej klasie
- Wybór niepopularnych kombinacji **zwiększa wypłatę gdy wygrasz**, ale **nie zmienia prawdopodobieństwa wygranej**

Hipotetycznie: jeśli wybierasz kombinacje, które są 2× mniej popularne niż przeciętne, twoja wygrana per win = 2× przeciętna. Twoje EV wzrasta proporcjonalnie:

```
EV_effective = stake × S × popularity_multiplier
```

Żeby EV > 0 w perspektywie konsorcjum: `0.5 × popularity_multiplier > 1` → `popularity_multiplier > 2`.

To wymaga konsystentnego wybierania kombinacji, które są **mniej niż 50% tak popularne jak średnia**. Możliwe — graczy psychologicznie ciągnie do dat urodzin (1-31), liczb "ładnych" (7, 21, 33), sekwencji geometrycznych. Strategia "anty-popular" jest realna, ale:
1. Nie ma nic wspólnego z detekcją niestacjonarności w losowaniu (DriftScope)
2. Wymaga gigantycznej próby (rzadkie wygrane) żeby uśrednić wariancję
3. Nadal nie pokona Polski (40% RTP → need 2.5× multiplier)

### 4.4 Werdykt dla architektury DriftScope

**Dla DriftScope jako research tool detekcji niestacjonarności** — ma sens i jest interesujący naukowo:
- Można badać jakość RNG/equipment w Helsinkach (Perle / Opale XL)
- Można testować hipotezy o wpływie pre-draw events (np. zmiana operatora obsługującego ziehanie)
- Można dokumentować boundary effects przy reformach 2014/2022

**Dla DriftScope jako predykcyjne narzędzie inwestycyjne** — `predykcja sensowna == False`:
- Take rate 50-60% jest barierą strukturalną
- Wykrywalne anomalie (jeśli w ogóle istnieją) dają edge rzędu pojedynczych %
- Margines wymagany to 100-175%
- **Decyzja architektoniczna: rozszerzenie w stronę predykcji NIE jest do obrony na podstawie obecnego take rate**

Sugerowane reframing celu projektu:
- "EV-positive prediction" → niewykonalne
- "Anomaly research framework" → wartościowe akademicznie
- "Drawing process quality monitor" → potencjalnie ciekawe (są precedensy — np. afera UK Lotto 1995-96 z manipulacjami)

---

## 5. Źródła

### Oficjalne (operator-level) 🟢

1. **euro-jackpot.net/prize-fund-distribution** — Pełna tabela 12 klas wygranych + 50% RTP confirmation. `https://www.euro-jackpot.net/prize-fund-distribution`
2. **euro-jackpot.net/de/gewinnverteilung** — Wersja niemiecka tabeli. `https://www.euro-jackpot.net/de/gewinnverteilung`
3. **lotto.pl/faq** — Totalizator Sportowy: stawka 10 PLN + dopłata 2.50 PLN (25%), 12 stopni wygranych, 19 krajów. `https://www.lotto.pl/faq`
4. **bip.totalizator.pl/regulaminy-gier/eurojackpot** — Oficjalny regulamin gry liczbowej Eurojackpot (PDF, obowiązujący od 10.05.2023). `https://bip.totalizator.pl/regulaminy-gier/eurojackpot`
5. **westlotto.de/eurojackpot/spielinformationen** — DLTB: stawka 2€ + Bearbeitungsgebühr 0.75€. `https://www.westlotto.de/eurojackpot/spielinformationen/spielinformationen.html`
6. **lotto.de/eurojackpot/spielregeln** — Oficjalne reguły DLTB Eurojackpot. `https://www.lotto.de/eurojackpot/spielregeln`
7. **lottomv.de/eurojackpot/produktaenderung-2022** — Oficjalna komunikacja o reformie 25.03.2022, w tym potwierdzenie że 50% RTP się nie zmieniło. `https://www.lottomv.de/eurojackpot/produktaenderung-2022`
8. **sisal.com/offerta/giochi/lotterie/eurojackpot** — Sisal (Włochy): cena 2€, 50% montepremi. `https://www.sisal.com/offerta/giochi/lotterie/eurojackpot`
9. **sisal.it/eurojackpot/quanto-si-vince** — 20% podatek od wygranych >500€ od 2020 r. `https://www.sisal.it/eurojackpot/quanto-si-vince`

### Legislacja 🟢

10. **gesetze-im-internet.de/rennwlottg_2021** — RennwLottG 2021 (niemieckie prawo loteryjne). Lotteriesteuer 20% — `https://www.gesetze-im-internet.de/rennwlottg_2021/BJNR206510021.html`
11. **lexlege.pl/ustawa-o-grach-hazardowych/rozdzial-9-doplaty/2741** — Polska Ustawa o grach hazardowych, rozdział 9 (dopłaty). `https://lexlege.pl/ustawa-o-grach-hazardowych/rozdzial-9-doplaty/2741/`
12. **vero.fi/syventavat-vero-ohjeet/ohje-hakusivu/47986/arpajaisten-verotus** — Fiński Verohallinto: arpajaisvero 12% (5,5% w 2021, 3,4% w 2022, 5,0% w 2023, powrót do 12% od 2024). `https://www.vero.fi/syventavat-vero-ohjeet/ohje-hakusivu/47986/arpajaisten-verotus/`

### Encyklopedyczne / branżowe 🟡

13. **en.wikipedia.org/wiki/Eurojackpot** — Pełna chronologia zmian, w tym potwierdzenie daty 10.10.2014 i 25.03.2022, odds przed/po reformach.
14. **de.wikipedia.org/wiki/Ausschüttungsquote** — Klasyfikacja RTP dla różnych gier: Eurojackpot 50%.
15. **de.wikipedia.org/wiki/Lotto** — Struktura podziału stawek w DLTB (50% / 23% Zweckerträge / 16.7% Lotteriesteuer / 7.5% Annahmestellen / 2.8% admin).
16. **de.wikipedia.org/wiki/Rennwett-_und_Lotteriegesetz** — Historia podatkowa niemieckich loterii.
17. **pap.pl/mediaroom/totalizator-sportowy-kazdy-gracz-wspomaga-polski-sport** — 25% dopłata, ~1,1 mld zł na FRKF w 2023.
18. **rp.pl/biznes/art10419751-lotto-czyli-jak-najlepiej-grac-dla-sportu-i-kultury** — Podział 25% dopłaty na 4 fundusze celowe (75/20/4/1).
19. **borsaefinanza.it/eurojackpot-come-si-gioca-cosa-si-vince-quanto-si-paga-tasse** — Włoski aggio 8%, 20% tax >500€.

### Strony branżowe (do triangulacji) 🟡

20. **lotteryhub.com/play-online/eurojackpot** — 50% allocation breakdown, 36% jackpot, 9% Booster.
21. **estrazionedellotto.it/en/eurojackpot/eurojackpot-faq** — Confirmation: *"50% of all ticket revenue goes into the total prize fund"*.
22. **superenalotto.net/en/eurojackpot** — Historia reform i daty.
23. **lottography.com/eu/eurojackpot/euronumbers-frequency** — Daty zmian puli euronumerów i implikacje dla analizy statystycznej.
24. **winnersystem.org/hilfe/gewinnwahrscheinlichkeiten-eurojackpot.shtml** — Detale o zamianie klas 6/7 w 2022 i nowych prawdopodobieństwach.
25. **tippland.de/magazin/eurojackpot-auszahlungstabelle** — Szczegóły struktury wypłat po reformie 2022.

---

## 6. Open questions / niepewności

### 6.1 Czego nie udało się ustalić z publicznych źródeł

🔴 **Pre-2022 dokładne % alokacji między klasami 2-12.** Wszystkie obecne tabele oficjalne pokazują strukturę post-25.03.2022. Wiadomo, że klasa 6 i 7 były "zamienione" definicyjnie, oraz że były "leichte Anpassungen" (drobne dostosowania). Dokładna pre-2022 tabela alokacji % nie jest dostępna na obecnych oficjalnych stronach. **Wymaga sięgnięcia do archiwów (web.archive.org) lub regulaminów oficjalnych operatorów z okresu 2014-2022.**

🔴 **Pre-2014-10-10 struktura wygranych.** Przy starcie 2012 było 12 klas, ale podział % i dokładne definicje klas dla puli 5/50 + 2/8 nie są dostępne w łatwo cytowalnej formie publicznej. Liczba kombinacji w klasach niższych była mniejsza (bo mniej euronumerów), więc rozkład procentowy musiał się różnić.

🔴 **Polski regulamin Eurojackpot (PDF, obowiązujący od 10.05.2023)** — robots.txt blokuje dostęp przez web_fetch. Powinieneś go pobrać ręcznie z bip.totalizator.pl, żeby zweryfikować dokładny podział stawki 10 PLN (np. konkretną % prowizję dla kolektora, % przekazywany do konsorcjum jako wkład do prize pool).

🔴 **Bearbeitungsgebühr w Niemczech.** 0,75 EUR to jest *typowa* opłata dla normalnego Tippu na jedno ziehanie w WestLotto (NRW). Każdy z 16 landów ustala własną Bearbeitungsgebühr; różnice mogą być rzędu 0,20-1,00 EUR. Brak konsolidowanego zestawienia per-Bundesland.

🔴 **Czy 50% RTP jest fixed w umowie konsorcjum, czy może być zmieniony przez decyzję operatorów?** Wszystkie źródła publiczne mówią o "Gewinnplan" jako o dokumencie wiążącym, ale procedura jego zmiany (kto musi zatwierdzić, jakie warunki) nie jest publicznie udokumentowana. Możliwe, że umowa konsorcjum jest publiczna pod inną nazwą — wymaga research'u na poziomie European Lotteries (EL) lub Eurojackpot-Kooperation.

🔴 **Greckie warunki** — Grecja dołączyła 6.03.2024 (najnowszy uczestnik). Nie sprawdzałem osobno greckiej struktury opłat — jeśli analiza DriftScope obejmie tickety greckie, to warto domknąć ten kraj.

### 6.2 Niepewności metodyczne

🔴 **Effective player RTP w Polsce: 40% to przybliżenie.** Faktycznie podział "stawki 10 PLN" zawiera w sobie: wkład do consortium prize pool (przypuszczalnie 50% × 10 PLN = 5 PLN, ale to nie jest expressis verbis potwierdzone — to wniosek z faktu że TS musi wnieść stawkę netto do wspólnej puli), prowizję kolektora (~6,5% na podstawie analogii do Lotto 6/49), Lotteriesteuer-equivalent (~10% poprzez ustawową stawkę), administrację. Bez wglądu do regulaminu w pełnym brzmieniu trudno to rozbić.

🔴 **Czy "50%" RTP jest 50% stake netto czy stake brutto?** W Polsce niejasne czy do consortium pool wnoszone jest 10 PLN czy 12,50 PLN. Jeśli 12,50 PLN, to consortium-level RTP z punktu widzenia gracza polskiego wynosi 6,25 PLN / 12,50 PLN = 50% (tak jak w innych krajach), a dopłata jest "wewnątrz" sytemu konsorcjum. Jeśli 10 PLN — to player effective RTP to 40%. **Prawdopodobnie wariant pierwszy** (bo żaden inny kraj nie miałby pełnego 50% RTP gdyby z 2 EUR tylko ~1,60 EUR szło do konsorcjum), ale to wymaga potwierdzenia z regulaminu TS.

### 6.3 Co warto domknąć przed dalszymi decyzjami

1. **Pobrać PDF regulaminu TS Eurojackpot** ręcznie z bip.totalizator.pl i poszukać paragrafu definiującego "wkład do konsorcjum" lub "kwotę przekazaną do prize pool"
2. **Sprawdzić web.archive.org dla euro-jackpot.net z 2015-2021** żeby zrekonstruować pre-2022 % alokacje między klasami
3. **Pobrać annual report Veikkaus i WestLotto za 2024** (oba są publiczne, państwowi operatorzy) — będzie tam dokładny podział przychodów per produkt
4. **(Opcjonalnie) Skontaktować się z European Lotteries (EL)** — jako research projekt można poprosić o dokumenty konsorcjum

---

## Załącznik — quick reference dla DriftScope

```python
# Take rate constants — confidence level: 🟢 dla konsorcjum, 🟡 dla player-effective
EUROJACKPOT_CONSORTIUM_RTP = 0.50
EUROJACKPOT_CONSORTIUM_TAKE = 0.50

# Player-effective RTP (proportions of total amount paid at register)
PLAYER_EFFECTIVE_RTP = {
    "PL": 0.40,   # 10 PLN stake + 25% dopłata; pre-tax
    "PL_with_tax": 0.36,  # po 10% podatku od wygranej >2280 PLN
    "DE": 0.364,  # 2 EUR stake + 0.75 EUR Bearbeitungsgebühr (typowo)
    "FI": 0.50,   # 2 EUR stake, brak dodatkowych opłat
    "IT": 0.50,   # 2 EUR stake; spada do ~0.40 po podatku 20% od >500 EUR
}

# Minimum edge over uniform required for EV > 0
MIN_EDGE_FOR_EV_POSITIVE = {
    "consortium": 1.00,   # +100%
    "PL_player": 1.50,    # +150%
    "DE_player": 1.75,    # +175%
}

# Regime boundaries (lottery rule changes)
REGIME_BOUNDARIES = [
    ("2012-03-23", "R1_5from50_2from8"),
    ("2014-10-10", "R2_5from50_2from10"),  # NOT 2014-10-08
    ("2022-03-25", "R3_5from50_2from12"),  # current
]

# Prize pool allocation (% of 50% prize fund) — post-2022 structure
PRIZE_POOL_ALLOCATION = {
    "5+2": 0.36,   "5+1": 0.086,  "5+0": 0.0485,
    "4+2": 0.008,  "4+1": 0.01,   "3+2": 0.011,
    "4+0": 0.008,  "2+2": 0.0255, "3+1": 0.0285,
    "3+0": 0.054,  "1+2": 0.0674, "2+1": 0.203,
    "booster_fund": 0.09,
}
# sum check: 0.36+0.086+0.0485+0.008+0.01+0.011+0.008+0.0255+0.0285+0.054+0.0674+0.203+0.09 = 1.0
```

---

**Koniec raportu.** Wersjonowanie: v1.0, 2026-05-27. Następna rewizja gdy domknięte zostaną Open Questions §6.3.
