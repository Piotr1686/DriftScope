Załączam SEED_IDEA.md (zalążek pomysłu, kontekst, anti-goals)
oraz HARDWARE_PUSH_CATALOG.md (katalog technik optymalizacji
hardware). Oceniaj wszystko przez pryzmat tych danych.

Wymagania uniwersalne dla każdego pomysłu:
1. ORYGINALNOŚĆ — nie "kolejny chatbot/dashboard/wrapper".
2. KREATYWNOŚĆ TECHNICZNA — niebanalne łączenia, ciekawe algorytmy.
3. EFEKT WOW — w 10 sekund robi wrażenie.
4. WYKONALNOŚĆ + HARDWARE TRANSCENDENCE
   Solo developer, 4GB VRAM, MVP w 4-8 tygodni.
   Dla każdego pomysłu oszacuj największy model w FP16, potem
   zastosuj proporcjonalną głębokość analizy:
   - <1GB FP16 (MVP tier): 1 oś z katalogu wystarczy.
   - 1-4GB (Balanced): 2 osie.
   - 4-10GB (Push): 3 osie.
   - >10GB (Extreme): 4+ osie.
   Dodatkowo wskaż 1 oś, która jest CZĘSTO STOSOWANA dla tego
   typu projektu, ale NIE PASUJE tutaj (z uzasadnieniem).
5. ZGODNOŚĆ Z SEED_IDEA — uwzględnij anti-goals i preferencje.

Dla każdego pomysłu podaj:
- Nazwa, elevator pitch (2-3 zdania), wow-factor
- Stack (nie ograniczaj się do Pythona)
- Tier (MVP/Balanced/Push/Extreme)
- Hardware Transcendence Stack:
  • Oś główna z katalogu + konkretna technika/biblioteka
  • Oczekiwany VRAM po optymalizacji
  • Strata jakości i koszt latency
- Trudność (1-5), czas do MVP, potencjał portfolio
- Jak odpowiada na "otwarte pytania" z SEED_IDEA


ODPOWIEDŹ GeminiAI (po zmianach w sseed_idea.md):
Ocena tego zalążka wymaga intelektualnej uczciwości. Projektowanie pipeline'u ML na danych z założenia losowych (gdzie limit log-loss to ~18.37 nats) jest fascynującym eksperymentem, który rekruterzy mogą odebrać dwojako. Zła nazwa i brak jasnego celu krzyczą "naiwny hazardzista". Z kolei precyzyjna izolacja szumu od sygnału i rygorystyczne testowanie granic architektur krzyczą "dojrzały inżynier Data Science".

Poniżej znajdują się trzy warianty architektoniczne, które przekształcają ten ryzykowny cel w solidny atut do portfolio, wykorzystując wskazane środowisko sprzętowe.

Koncepcja 1: Null-Hypothesis (Odpowiedź na H1 - QML)
Rozwiązanie problemu nazewnictwa i ryzyka "predict to win". Zamiast szukać wygranej, szukamy matematycznego dowodu na brak wzorca.

Elevator Pitch: Platforma badawcza porównująca klasyczny model klasyfikacyjny z Quantum Neural Network (VQC) w zderzeniu z czystą entropią. Aplikacja udowadnia, że zaawansowane architektury nie potrafią pokonać teoretycznego limitu log-loss (18.37 nats), tworząc edukacyjny benchmark dla badaczy ML.

Wow-factor: Działający w czasie rzeczywistym wykres dystansujący predykcje QML i klasycznego LSTM od linii "Uniform Random Baseline", demonstrujący jak modele "miotają się", próbując znaleźć sygnał w szumie.

Stack: Python 3.10, PyTorch, PennyLane (QML), Streamlit (dashboard analityczny).

Tier: MVP (<1GB FP16). Modele są ekstremalnie małe.

Hardware Transcendence Stack:

Oś główna (Oś 7 - Runtime): ONNX Runtime (CPU) dla klasycznego modelu, PennyLane na CPU dla kwantowego. RTX 3050 odpoczywa, i5-12500H liczy symulację kwantową.

VRAM: < 200MB (narzut samego interpretera).

Jakość i Latency: Symulacja 12-16 kubitów na CPU zamknie się w 2-5 sekundach (akceptowalne near-real-time).

Nie pasuje (Oś 2 - Offloading): Używanie CPU offloadingu (jak w accelerate) dla modeli poniżej 500MB to czysty anti-pattern. Koszt transferu przez szynę PCIe zniszczy wydajność, nie oszczędzając odczuwalnie VRAM-u.

Trudność: 4/5 (matematyka kwantowa jest stroma). Czas: 6 tygodni.

Potencjał Portfolio: Ekstremalnie wysoki. Udowadnia zrozumienie limitów ML i niszowych bibliotek (QML).

Koncepcja 2: The Spurious Engine (Odpowiedź na H2 - TFT)
Eksperyment diagnostyczny z Temporal Fusion Transformer (TFT). Udowadnia, jak głębokie modele szeregów czasowych ulegają halucynacjom strukturalnym.

Elevator Pitch: System śledzenia korelacji pozornych z użyciem Temporal Fusion Transformer (TFT). Świadomie wstrzykujemy "szum" informacyjny (fazy księżyca, pogodę, indeksy S&P500) do danych loterii, aby zwizualizować i precyzyjnie zmierzyć, w którym momencie model zaczyna overfittować.

Wow-factor: "Overfit-O-Meter". Interaktywne narzędzie pokazujące wagę uwagi (attention weights) modelu skupiającą się na np. ciśnieniu atmosferycznym w Tokio podczas generowania losowania EuroJackpot.

Stack: PyTorch Forecasting (TFT), Weights & Biases (śledzenie log-loss i metryk), FastAPI + Vue.js (UI).

Tier: Balanced (1-4GB FP16). Duże okna czasowe i embeddingi zmiennych pobocznych zwiększają footprint modelu.

Hardware Transcendence Stack:

Oś główna (Oś 1 - Quantization & Oś 3 - Compilation): FP16 jako domyślny format wag oraz torch.compile(mode='reduce-overhead') dla przyspieszenia iteracji treningowych na RTX 3050.

VRAM: ~1.5GB po kwantyzacji do FP16.

Jakość i Latency: Spadek jakości bliski 0%, przyspieszenie inferencji o 1.5-2.5x dzięki JIT.

Nie pasuje (Oś 4 - Surgery): Szukanie pre-distilled checkpoints dla modeli typu TFT nie istnieje na Hugging Face. Robienie DIY knowledge distillation dla 1000 punktów danych mija się z celem empirycznym projektu.

Trudność: 3.5/5. Czas: 5 tygodni.

Potencjał Portfolio: Pokazuje dojrzałość w inżynierii cech (Feature Engineering) i wyciąganie wniosków ze złych wyników, co jest rzadkie na poziomie Junior/Mid.

Koncepcja 3: Stochastic Topology (Odpowiedź na H3 - GNN)
Architektura GNN jest "młotem szukającym gwoździa" w szeregach czasowych loterii. Zmieńmy więc loterię w układ topologiczny.

Elevator Pitch: Reprezentacja historii losowań jako grafu współwystępowania i krawędzi temporalnych, analizowanego przez Graph Neural Network (PyG). Model nie przewiduje kolejnych liczb, lecz szuka anomalii topologicznych — sprawdzając, czy struktura grafu ewoluuje inaczej niż idealnie losowy proces stochastyczny.

Wow-factor: Interaktywny, renderowany w przeglądarce za pomocą WebGL graf 3D. Węzły (liczby) przyciągają się grawitacyjnie na podstawie wag uwagi GNN, odzwierciedlając fałszywe lub prawdziwe skupiska z 1000 historycznych losowań.

Stack: PyTorch Geometric (PyG), DGL, NetworkX, Three.js / D3.js (Front-end).

Tier: MVP (<1GB). Złożoność leży w budowie macierzy sąsiedztwa, nie w głębokości sieci.

Hardware Transcendence Stack:

Oś główna (Oś 5 - Pipeline Tricks): Vector Cache (np. FAISS) do przechowywania pre-komputowanych embeddingów węzłów dla każdego historycznego stanu loterii, drastycznie zmniejszając narzut obliczeniowy przy re-treningu.

VRAM: ~400MB.

Jakość i Latency: Odzyskiwanie z cache trwa mikrosekundy zamiast sekund.

Nie pasuje (Oś 6 - Hybrid Compute): Zestaw 1000 rekordów to ułamek megabajta. Używanie chmury (Google Colab / Kaggle) do procesu budowy tak małego datasetu wprowadzi zbędne komplikacje sieciowe i złamie zasadę "Minimum sufficient".

Trudność: 4.5/5 (modelowanie grafowe zjawisk niezależnych to wyzwanie abstrakcyjne). Czas: 6-8 tygodni.

Potencjał Portfolio: Wysoce nieszablonowe użycie GNN, które błyszczy na GitHubie wizualnie i koncepcyjnie.

Rozwiązanie otwartych pytań (Sekcja 7)
Ad Q1/Q2/Q3 (Architektura): H3 (GNN) to definitywny przypadek "młota", jeśli chcesz po prostu zliczać liczby. Nabiera sensu dopiero, gdy zmienisz cel z predykcji na detekcję anomalii topologicznych (Koncepcja 3). Hybryda H1 i H2 jest możliwa (VQC jako warstwa cech dla TFT), ale dla solowego dewelopera w 6 tygodni spowoduje "piekło" z integracją gradientów między PennyLane a modułami PyTorcha. Wybierz jeden konkretny tor.

Ad Q4 (Bottleneck PennyLane): Limit dla symulatora CPU to zazwyczaj okolice 14-16 kubitów. Powyżej tego narzut skaluje się na i5 wprost koszmarnie. Trzymaj układ mały (np. obwód 8-kubitowy na konkretne embeddingi okna z ostatnich 10 losowań).

Ad Q5 (Czy wchodzić w Hardware Push): Ponieważ target sprzętowy to RTX 3050 a modele loteryjne są fizycznie mikroskopijne, tkwisz w MVP Tier. Skup się wyłącznie na czystości środowiska (Oś 0), formacie FP16 (Oś 1) i silniku uruchomieniowym (Oś 7). Reszta optymalizacji to over-engineering.

Ad Q6 (Augmentacja bez oszukiwania): Z losowaniami EuroJackpot nie zrobisz SMOTE czy dodawania gaussowskiego szumu do wartości dyskretnych. Uczciwą augmentacją jest tu tylko wstrzykiwanie zmiennych niezwiązanych (jak w Koncepcji 2) w celu kalibracji wskaźników przeuczenia.

Ad Q7 (Online vs Batch): Batch. Aktualizacja 1 punktu co kilka dni to stanowczo za rzadko, by walczyć z ciągłym online learningiem i problemem "catastrophic forgetting". Pełen retrain w nocy wystarczy.

Ad Q8/Q9/Q10 (Nazwa i Framing): Unikaj słów Predictor, Wizard, Jackpot. Nazwy w stylu Null-Hypothesis, Entropy Boundary czy Stochastic Graph Sandbox stawiają projekt w sferze badawczej. Pierwsze zdanie README musi brzmieć: "An empirical study demonstrating the limits of modern Deep Learning architectures against probabilistically independent, uniform distributions." To natychmiastowo ucina oskarżenia o szukanie magicznych sztuczek hazardowych.