# SEED IDEA — DriftScope

Tier projektu: **MEDIUM** (kandydat na LARGE jeśli cross-review wskaże eksperymentalny track wart pełnego scope'u)

---

## 1. Pomysł bazowy

**DriftScope** to dwuwarstwowe narzędzie do detekcji niestacjonarności w rzekomo stacjonarnych procesach stochastycznych. **Case study:** strumień losowań EuroJackpot — proces zaprojektowany jako uniform, gdzie pytanie badawcze brzmi: *czy w danych widać jakiekolwiek odchylenia od stacjonarności*, i jeśli tak, to *jakiego typu*.

**Warstwa 1 — Pattern Auditor (główny komponent).**
Statystyczny + ML pipeline szukający w strumieniu częstości losowanych liczb pięciu typów odchyleń od stacjonarnego multinomial procesu:

- **Drift monotoniczny** — częstość liczby X rośnie/maleje w czasie.
- **Periodyczność** — częstość liczby X oscyluje z jakimś okresem (sinusoida).
- **Clustered bursts** — liczba X wypada w "fazach" gęstych przeplatanych ciszą.
- **Korelacje krzyżowe** — częstości par/trójek liczb zmieniają się wspólnie (sugeruje fizyczną interakcję, np. między kulami w bębnie).
- **Memory effect** — częstość liczby X w losowaniu *t* zależy od jej obecności w losowaniach *t-k*.

Każdy znaleziony wzorzec przechodzi przez **shuffle test** (permutacja porządku losowań, czy ta sama struktura pojawia się w danych przemieszanych — jeśli tak, struktura jest artefaktem detektora) oraz **multiple testing correction** (Bonferroni / FDR), bo przestrzeń hipotez jest duża.

**Warstwa 2 — Adaptive Predictor (nadbudowa).**
Konsumuje output Pattern Auditora. Generuje *watch list* liczb z podwyższoną estymowaną częstością — **tylko dla wzorców, które przeszły testy istotności**. Jeśli żaden wzorzec nie przeszedł, output predyktora to honest uniform. To kluczowe metodologicznie: predyktor *nie wymyśla* sygnału, którego auditor nie potwierdził.

**Naturalne ground truth:** EuroJackpot zmieniał reguły dwa razy (08.10.2014 — pula euronumerów z 8 na 10; 25.03.2022 — z 10 na 12). To są znane change-pointy, na których można walidować, że detektor *w ogóle działa*, zanim oceni się jego wskazania w obrębie reżimu.

**Skalowalność konceptu:** EuroJackpot to pierwsza aplikacja. Framework może obsługiwać inne procesy "z założenia uniform" (NIST RNG test data, kryptograficzne PRNG sequence, dane finansowe rzekomo random walk). To stoi w §6.3 jako stretch goal.

## 2. Poziom dojrzałości zalążka

[X] **L4 — HIPOTEZA**

Cztery hipotezy do podważenia (oczekuję krytyki, alternatyw, hybryd):

- **H1 — Pattern Auditor (klasyczny baseline):** klasyczne testy stacjonarności (Augmented Dickey-Fuller, KPSS), change-point detection (CUSUM, Page-Hinkley, Bayesian online change-point detection), Fourier/Welch spectrogram na strumieniu częstości, autocorrelation analysis — wszystkie z permutation-based istotnością i FDR correction — wystarczą do wykrycia wszystkich pięciu typów wzorców, *jeśli* w ogóle istnieją w EuroJackpot.

- **H2 — TFT (Temporal Fusion Transformer):** TFT trenowany jako one-step-ahead probability forecaster na strumieniu częstości znajdzie wzorce, których nie znajdą klasyczne testy z H1 — *lub* okaże się tylko świadectwem klasycznego overfittingu na 1000 punktach.

- **H3 — GNN (na grafie współwystępowania ewoluującym w czasie):** GNN wykryje wzorce *korelacji krzyżowych* (typ wzorca #4) lepiej niż klasyczne testy korelacji par/trójek — *lub* nie wykryje niczego ponad shuffle baseline.

- **H4 — Hybrydowy klasyczno-kwantowy (VQC + klasyczny extractor):** VQC jako głowica nad klasycznym ekstraktorem cech dostarczy reprezentację, której klasyczne sieci nie generują — *lub* okaże się czysto kosmetyczny (efekt narracyjny, nie statystyczny).

Każda hipoteza ma symetryczny "lub". Te cztery hipotezy NIE wyczerpują przestrzeni rozwiązań — patrz §7A.2.

## 3. Co już wiem / mam

### 3.1 Źródła danych
- **Lotto OpenAPI** (`developers.lotto.pl`) — oficjalne źródło, klucz w `.env` (NIE w repo).
- **Znane change-pointy do walidacji:** 08.10.2014 (zmiana puli euronumerów 8→10), 25.03.2022 (10→12). Detektor *musi* wykrywać te daty, inaczej nie jest w stanie wykryć niczego subtelniejszego.

### 3.2 Inspiracje techniczne (luźne, do oceny w cross-review)
- Klasyczne testy: **statsmodels** (ADF, KPSS), **ruptures** (change-point detection), **scipy.signal** (Welch, Lomb-Scargle dla nieregularnych szeregów).
- Bayesian online change-point: **bayesian_changepoint_detection** lib / własna implementacja Adams-MacKay 2007.
- TFT: **pytorch-forecasting** jako referencja.
- GNN: **PyG**, **DGL**.
- Frameworki kwantowe: **PennyLane**, **Qiskit** (CPU-friendly symulatory).
- *Anti-references* — hobby-repos predykcji EuroJackpot bez metryk uczciwego baseline'u (świadomie odrzucone jako wzorzec): `EurojackpotPredictor2024`, `eurojackpot-foreteller`, `Lotto_Wizard`.

> Powyższe to *kandydaci*, nie *commitment*. Cross-review mile widziany w roli "to są złe wybory, lepiej X".

### 3.3 Wcześniejsze rozmowy z LLM-ami
Gemini w pierwszej rundzie cross-review zaproponował m.in. trzy koncepcje (Null-Hypothesis, Spurious Engine, Stochastic Topology) zorientowane wokół architektur ML. Wyciągnięty wniosek: właściwym targetem nie jest "predykcja konkretnego losowania" tylko **detekcja niestacjonarności** — i to przeniosło projekt w stronę Pattern Auditor + Adaptive Predictor. Cross-review w obecnej rundzie proszę o ocenę tej zmiany framingu.

### 3.4 Własne PoC
Brak. Pierwszy PoC (Krok 6 workflow) zostanie ustalony po cross-review, prawdopodobnie wokół klasycznego baseline'u z H1 jako fundamentu.

## 4. Preferencje technologiczne

| Oś | Chcę spróbować | Wolę uniknąć |
|---|---|---|
| Język/runtime | Python 3.10 (znam ekosystem) | — |
| Framework ML | Otwarte — kandydaci w §3.2, ale cross-review może proponować inne | Czysty TensorFlow (ekosystem nie jest dla mnie) |
| UI / frontend | Otwarte — od CLI po Streamlit/CustomTkinter/web (Three.js, React, WebGL — wszystko OK jeśli wnosi wartość) | Pełnostackowy React jeśli nie wnosi wartości |
| Paradygmat | Hybrydowe modele klasyczno-kwantowe (główna fascynacja), ale otwarty na alternatywy — łącznie z paradygmatami, które *nie* są ML (czysta statystyka, symulacja, analiza topologiczna) | Naive frequency / regresja liniowa jako *jedyny* model |

## 5. Anti-goals

### 5A. Projekt NIE ma być (kształt produktu)
- Naive frequency analysis ("najczęstsza liczba w ostatnich 100 losowaniach") jako jedyny model.
- Predyktor, który *wymyśla* sygnał ignorując shuffle test / multiple testing — to byłby data dredging, nie nauka.
- Wrapper na cudzy model bez własnej kontrybucji.
- Aplikacja, która udaje, że "gwarantuje wygraną" lub eksploatuje gambling addiction (etyka + portfolio risk dla rekrutera).

### 5B. LLM w cross-review NIE ma (zachowanie LLM-a)
- Tłumaczyć, że losowanie jest niezależne — to jest *premise* projektu, nie błąd metodologiczny. Reality Check w §11 to adresuje.
- Tłumaczyć, że uniform random procesy są nieprzewidywalne — nie szukam predykcji konkretnego losowania, tylko detekcji *odchyleń od uniform*, co jest ortogonalne.
- Pivotować mojego celu na "kalkulator szans w pokerze" lub inne tematy "bezpieczniejsze".
- Ograniczać propozycji frameworków/UI do Pythona.

## 6. Cel nadrzędny

### 6.1 Problem i odbiorcy
- **Problem:** brak portfolio-pieces pokazujących nietrywialne ML *plus* matematyczną dojrzałość w warstwie metodologicznej (multiple testing, permutation tests, statistical power, change-point detection). Większość portfolio ML to "leaderboard chase"; chcę pokazać coś, co naturalnie pokazuje dojrzałość inżynierską.
- **Dla kogo:** Portfolio (rekruter ML/AI, w szczególności quant/research-leaning) + open-source (community zainteresowane testowaniem stacjonarności w streaming data).

### 6.2 Priorytet
[X] **PRIMARY: Portfolio-value**
[ ] PRIMARY: Self-value

> Self-value (Adaptive Predictor wykorzystany do faktycznego watch-list dla losowań) akceptowalne jeśli kosztuje <20% dodatkowego czasu i jest *honest* (nie wymyśla sygnału). Cross-review: **jeśli widzisz kreatywny self-value angle, który nie wymaga >20% dodatkowego scope'u, zaproponuj go nawet jeśli nie pasuje do głównych hipotez §2.**

### 6.3 Motywacja i zakres
- **Co fascynuje:** empiryczne pytanie — czy *cokolwiek* w EuroJackpot odbiega od uniform na poziomie wykrywalnym z 1000-1500 punktów. Nie znam odpowiedzi z góry. Jeśli odpowiedź brzmi "nie" — to też wynik wart raportu (negative result jest portfolio-value, jeśli powstał z dobrym testem).
- **Scope:** 6-8 tyg. do MVP, +2 tyg. polish (dashboard, README).
- **Dystrybucja:** GitHub repo + demo (HF Spaces, Render, lub inne — do dyskusji). Nie .exe.
- **Stretch goal (po MVP):** uogólnienie frameworka na inne procesy "z założenia uniform" (NIST RNG test data, kryptograficzne PRNG sequence). To czyni DriftScope biblioteką inżynierską, gdzie EuroJackpot jest pierwszą aplikacją.

> **Otwarte do cross-review:** czy 6-8 tyg. solo to realny scope dla wszystkich 4 hipotez, czy lepiej zawęzić do 1-2 i zrobić głębiej?

### 6.4 Definition of Done

MVP zostaje uznane za **udane**, jeśli spełnia *wszystkie* z poniższych:

- **DoD-1: Walidacja na ground truth.** Pattern Auditor wykrywa znane change-pointy 08.10.2014 i 25.03.2022 w oknie ±30 losowań od rzeczywistej daty zmiany reguł. Bez tego detektor jest niefunkcjonalny.
- **DoD-2: Kontrolowany false-positive rate.** Na shuffled wersji danych (permutowany porządek losowań w obrębie jednego reżimu reguł) Pattern Auditor zwraca *mniej* znaczących wzorców niż zadeklarowany α (np. α=0.05 po FDR correction → <5% shuffled runów daje "wzorzec znaleziony").
- **DoD-3: Multiple testing correction zaaplikowana wszędzie.** Każda zadeklarowana detekcja przeszła Bonferroni lub Benjamini-Hochberg FDR. Pojedynczy p-value bez korekcji nie kwalifikuje wzorca jako "znaleziony".
- **DoD-4: Cross-architecture consistency.** Jeśli wzorzec został zadeklarowany jako "znaleziony" przez jedną architekturę (np. TFT), sprawdzane jest, czy inne architektury (klasyczny baseline H1, GNN, VQC) go widzą. Wzorzec spójny między architekturami jest *istotnie* bardziej wiarygodny niż wzorzec widoczny tylko w jednej.
- **DoD-5: Honest predictor output.** Adaptive Predictor zwraca uniform distribution, jeśli żaden wzorzec nie przeszedł DoD-1...DoD-4. Nie ma "always-on" sugerowania liczb.
- **DoD-6: README dyzarmujący.** Pierwsze 3 zdania README jednoznacznie komunikują, że projekt to audit framework, nie predyktor wygranych. Patrz §7D.10.

**Anti-success criterion:** model, który *wydaje się* działać (znajduje wzorce na danych), ale nie przechodzi shuffle testu, jest klasycznym data dredging i jest odrzucany. Negative result ("nie znaleziono niczego istotnego po korekcji") jest *sukcesem* jeśli protokół był solidny.

> **Pytanie do cross-review:** czy ten zestaw DoD jest wystarczający i czy jest *uczciwy*? Czego brakuje, co dodać, co przeformułować?

## 7. Otwarte pytania do cross-review

### 7A. O architekturę

1. Z czterech hipotez (§2) — która ma realne szanse na empiryczną wartość przy ~1000-1500 punktach danych, a która jest "młotem szukającym gwoździa"? Czy klasyczny baseline z H1 jest tak silny, że H2/H3/H4 są over-engineering?

2. **[NAJWAŻNIEJSZE PYTANIE TEJ SEKCJI]** Zaproponuj minimum **jeden** paradygmat, który radykalnie przedefiniowuje target lub metodę poza H1-H4. Przykłady kierunków (nie wyczerpujące): topologiczna analiza danych (TDA), Wasserstein distance między rozkładami w czasie, ergodic theory dla procesów stochastycznych, eksperymenty wymuszające pokazanie limitów z fizycznym pomiarem (jeśli to w ogóle ma sens dla tego use case'u). To pytanie jest *ważniejsze* niż dyskusja H1/H2/H3/H4.

3. Czy istnieje sensowna hybryda 2 z 4 hipotez, czy lepiej trzymać je jako oddzielne tracki do porównania (per DoD-4)?

### 7B. O wykonalność (bottleneck w §10.1)

4. Symulator kwantowy (PennyLane CPU) dla 4-12 qubits — co realnie dostanę na i5-12500H? Jaki jest pułap qubitów, powyżej którego latency staje się nieakceptowalna dla H4?

5. Wszystkie kandydaci modeli są <1GB FP16 — czy w ogóle mam wchodzić w Hardware Transcendence Stack z katalogu, czy MVP tier wystarcza?

### 7C. O scope / dane

6. ~1000-1500 historycznych losowań (zależnie od tego, ile pre/post-2022 włączamy) — co to oznacza dla statistical power detektora? Dla jakich rozmiarów efektu mam realną szansę wykrycia? Jakie typy wzorców są poza zasięgiem przy tej próbce?

7. **Cadence aktualizacji modelu (ważne):** losowania odbywają się we wtorki i piątki wieczorem. Naturalna częstotliwość update'u to 2 razy w tygodniu. Pytanie: dla których komponentów ta częstotliwość ma sens, a dla których to over-engineering?
   - Online auditor (Bayesian change-point, CUSUM, sliding window statistics) — każdy nowy datapoint natychmiast. To jest właściwy paradygmat dla tej klasy algorytmów.
   - Heavy retrain (TFT, GNN, VQC) — co tydzień lub dwa tygodnie batch. Full retrain dwa razy w tygodniu to over-engineering.
   - Czy to rozdzielenie jest poprawne? Co byś zaproponował inaczej?

8. Co jest *uczciwą* augmentacją na danych dyskretnych typu losowania? Permutacje wewnątrz jednego losowania (kolejność nie znaczy) dają 5!=120× — co jeszcze?

### 7D. O ryzyka portfolio / strategiczne

9. Czy framing "stationarity auditor on a known-uniform process" jest atutem (intellectual maturity, niszowa kompetencja) czy ryzykiem (rekruter widzi "EuroJackpot" w README i zamyka CV)?

10. Jak ramować README, żeby pierwsze 3 zdania *od razu* dyzarmowały założenie "to scam o lotto"? Propozycja roboczah: *"DriftScope is a stationarity audit framework for streaming discrete-valued processes. The flagship case study is EuroJackpot — a process designed to be uniform-random, where the empirical question is whether any detectable deviation from uniformity exists. The project is methodological in nature; it neither claims nor seeks to predict lottery outcomes in any actionable sense."* — co byś zmienił?

### 7E. Meta-pytanie

11. **Jakie pytanie chciałbym, żebyś mi zadał — ale nie zadałem? Odpowiedz na nie.** (Sekcja istnieje, żeby wyciągnąć obserwacje, których sam nie nakierowałem.)

## 8. Zakres danych

- **Volume:** ~1000-1500 historycznych losowań EuroJackpot (od 2012-03 do dziś), w trzech reżimach reguł rozdzielonych change-pointami 2014/2022.
- **Format:** JSON z Lotto OpenAPI (data, 5 liczb 1-50 + 2 euronumery z puli zmieniającej się w czasie: 1-8, 1-10, 1-12).
- **Source:** Lotto OpenAPI (klucz w `.env`).
- **Cleanliness:** wysoka (źródło oficjalne).
- **Update frequency:** 2 nowe punkty tygodniowo (wtorek + piątek wieczorem). Patrz §7C.7 dla strategii konsumpcji tych update'ów per komponent.
- **Augmentation strategy:** otwarte — patrz §7C.8. Wstępne: permutacje wewnątrz losowania (5!=120× dla głównych, 2!=2× dla euronumerów).
- **Reżimy reguł:** trzy oddzielne procesy do osobnej walidacji (08.10.2014, 25.03.2022 jako granice).
- **Licencja:** do sprawdzenia w ToS Lotto API.

## 9. Hardware i środowisko

> Bazowy setup: patrz `HARDWARE_PUSH_CATALOG.md`.
> Delta dla tego projektu: **brak** — standardowy setup.

## 10. Ambicje przekraczające sprzęt

### 10.1 Realny bottleneck tego projektu

Wstępna hipoteza (do walidacji w cross-review): **NIE VRAM**.

Kandydaci na realny bottleneck:
- [X] **Dataset size** — ~1000-1500 losowań rozłożone na 3 reżimy = bottleneck statystyczny, nie sprzętowy. Statistical power dla detekcji subtelnych odchyleń jest tu główną limitacją.
- [X] **CPU compute** — symulator kwantowy w PennyLane (H4) skaluje się z 2^n_qubits. Shuffle test wymaga wielu permutacji (np. 10⁴) dla solidnych p-values → istotny koszt dla każdej architektury.
- [ ] VRAM — wszystkie kandydaci modeli <1GB FP16.

Jeśli H4 (QML) zostanie odrzucona w cross-review, bottleneck redukuje się do dataset size + permutation testing overhead.

### 10.2 Akceptowalny narzut czasowy

Rozróżnienie per komponent:

- **Online auditor** (Bayesian change-point, CUSUM, sliding window): [X] **Real-time (<1s)** per nowy datapoint. Update co losowanie.
- **Klasyczny baseline H1** (ADF, KPSS, Welch spectrogram, autocorrelation): [X] **Near-real-time (1-10s)** per pełny run. Update co losowanie OK.
- **TFT/GNN/VQC retrain**: [X] **Batch (10s-10min)** lub [X] **Overnight** dla hyperparameter search + permutation tests. Update co tydzień / dwa tygodnie.
- **Shuffle test runs** (10⁴ permutacji × każda architektura): [X] **Overnight** — to dominujący koszt obliczeniowy projektu.

### 10.3 Build-time cloud allowed?
[X] **TAK** — Colab/Kaggle do shuffle test runs (10⁴ permutacji × 4 architektury), eksperymentów z większymi VQC (>8 qubits), hyperparameter search.

### 10.4 Quality-vs-VRAM trade-off
[X] **~0-1%** — FP16/BF16 mixed precision (modele są małe, kwantyzacja niżej niemotywowana).

### 10.5 Doświadczenia z technikami
**Pozytywne:** brak (pierwsze podejście do QML/TFT/GNN/change-point detection).
**Negatywne:** brak.
**Nie znam:** PennyLane, pytorch-forecasting, PyG/DGL, ruptures, Bayesian online change-point — wszystko tier "uczę się w ramach projektu". Doświadczenia z poprzednich projektów (CLIP, VGG19, MediaPipe, Whisper, RAG, OCR) nie transferują wprost. Pozytywnie: solidna baza w statystyce klasycznej (testy hipotez, ANOVA) zostaje.

---

## 11. Reality Check

**Pytanie A: czy można predykować konkretne losowanie EuroJackpot?**

Dla niezależnych zdarzeń o rozkładzie jednostajnym, dolna granica średniego log-loss na infinite test set =

`log(C(50,5) · C(12,2)) = log(95,344,200) ≈ 18.37 nats`

Każdy model, którego średni log-loss na test set spadnie *systematycznie* poniżej tej wartości na losowo wybranym kawałku danych, robi jedną z trzech rzeczy:
1. Wykrywa rzeczywistą strukturę w danych (matematycznie zaskakujące, weryfikowalne).
2. Overfittuje na test set lub leaknął train → test.
3. Eksploatuje artefakt zbierania danych (np. bias w generatorze losowań — *to jest dokładnie* hipoteza badawcza DriftScope).

**Pytanie B: czy można wykryć niestacjonarność w strumieniu losowań?**

To *inne* pytanie i ma *inny* limit. Statistical power detekcji niestacjonarności zależy od:
- rozmiaru próbki *n* (tu: ~1000-1500),
- rozmiaru efektu (jak silne odchylenie szukamy),
- typu wzorca (drift monotoniczny łatwiejszy niż słaba periodyczność),
- multiple testing burden (większa przestrzeń hipotez → wyższy próg istotności po korekcji).

Konkretnie: dla detekcji drift'u w częstości pojedynczej liczby z poziomu p=0.1 (uniform) do p=0.11, przy n=1000 i α=0.05 po Bonferroniego dla 50 liczb, moc testu wynosi ~30%. Dla wzrostu do p=0.12, moc rośnie do ~70%. Czyli **bardzo słabe sygnały są poza zasięgiem na obecnej próbce**, ale umiarkowane są wykrywalne.

**Honest baseline dla DriftScope to shuffle test, nie uniform random.** Jeśli detektor widzi "strukturę" w prawdziwych danych z tą samą siłą co w przemieszanych — struktura jest artefaktem detektora, nie danych. Każde "found" musi przejść ten test.

**Co projekt może legitnie zrobić:**
- Wykryć znane change-pointy 2014/2022 (DoD-1 — ground truth dostępny).
- Skontrolować false-positive rate dzięki shuffle test + multiple testing correction.
- *Jeśli* wzorzec istnieje powyżej progu mocy testu — wykryć go z udokumentowaną pewnością statystyczną.
- Jeśli nic nie zostanie znalezione po solidnej procedurze — *to też wynik* i jest portfolio-value (negative result + dobrze udokumentowany protokół).

**Czego projekt nie może zrobić:**
- Przewidzieć konkretnego losowania powyżej baseline'u uniform (Pytanie A).
- Wykryć dowolnie słabego sygnału (limit statystyczny przy n=1000-1500).
- Zagwarantować, że *brak* znalezionych wzorców oznacza, że ich nie ma — tylko, że są poniżej progu wykrywalności w obecnej próbce.

> **Dlaczego ta sekcja istnieje:** żeby cross-review nie zużywał odpowiedzi na tłumaczenie premis. Wiem, że losowanie konkretne jest losowe. Wiem, że detekcja niestacjonarności to inne pytanie. Wiem, jakie są limity dla obu. Teraz pomóż mi zaprojektować dobry eksperyment w tych ramach — albo, *lepiej*, znajdź lepszy target analizy (§7A.2).
