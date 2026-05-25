# SWOT_ANALYSIS — DriftScope cross-review finalists

**Kontekst:** Analiza ósemki finalistów wyłonionych w Kroku A z 20 propozycji (6 LLM-ów + 3 Claude). Każdy finalista oceniony przez pryzmat SEED_IDEA.md (anti-goals, DoD-1...DoD-6, §10.1 bottleneck) oraz przez pryzmat predykcyjności (zdolność do honest watch-list per DoD-5) z explicit przeciwwagą **Hallucination Risk** (skłonność do znajdowania spurious structure w shuffled data).

**Konwencja clusterów (z Kroku A):**
- **P** = Predictive cluster (model natywnie generuje p(x_{t+1} | history))
- **A** = Audit-only cluster (model wykrywa niestacjonarność jako globalny scalar/kształt)

**Konwencja Hallucination Risk:** 1/5 = bardzo niski (deterministyczny algorytm z asymptotyczną teorią), 5/5 = bardzo wysoki (over-parameterized model z dużą capacity vs n=1000–1500).

**Konwencja DoD-1 (skorygowana):** Reguły 2014/2022 EuroJackpot zmieniły *wyłącznie* pulę euronumerów (8→10→12), nie pulę głównych 50 liczb. Stąd:
- **DoD-1a (sanity check):** algorytm wykrywa pojawienie się nowych euronumerów (trywialne, wariancja skacze z zera).
- **DoD-1b (real test):** algorytm uruchomiony *tylko* na wektorze 50 głównych liczb — gdzie zmiana reguł formalnie nie wystąpiła, ale mogła towarzyszyć wymianie maszyny losującej / protokołu fizycznego. To jest właściwy ground truth.
- **DoD-1 blind protocol:** pipeline generuje ranking change-pointów *przed* porównaniem z 2014/2022; brak strojenia parametrów pod znane daty (mityguje target leakage).

---

## 1. SWOT analiza 8 finalistów

### 1.1 K2 — TDA Microscope [Cluster A]

**Strengths.** Persistent homology to deterministyczne narzędzie z asymptotyczną teorią stabilności (Cohen-Steiner et al.) — Hallucination Risk 1/5, brak overfittingu na n=1000. Stack `gudhi/ripser` jest mature, CPU-only, omija VRAM bottleneck całkowicie. Math-heavy framing ("Topological Data Analysis") natychmiast neutralizuje "lotto-scam" narrative w README.

**Weaknesses.** Surowy Vietoris-Rips na chmurze R^50 z n=1000 napotyka curse of dimensionality — odległości euklidesowe tracą dyskryminację, Betti > 0 rzadko produkuje nietrywialne cechy. Rozwiązanie: **time-delay embedding (Takens)** na 1D szeregach częstości, gdzie chmura w R^2/R^3 ma matematycznie poprawną strukturę (Perea & Harer 2015) — albo **Mapper algorithm** zamiast Vietoris-Rips. Pred. Power 1/5 — DoD-5 wymaga drugiego systemu lub akceptacji audit-only framing. Wybór filtracji, embeddingu i metric tworzy dużą przestrzeń decyzji — **interpretation overfitting risk** istnieje, choć **model overfitting risk** nie.

**Opportunities.** TDA z Takens embedding w szeregach dyskretnych to nisza rzadko spotykana w junior portfolio — silny differentiator dla quant/research/biostat. Naturalnie spełnia DoD-1b (change-pointy 2014/2022 jako "śmierć" cech topologicznych po embedding), DoD-2 (shuffle test na Bottleneck distance), DoD-4 (cross-architecture consistency vs H1). Persistence landscapes (zamiast surowych barcode'ów) dają stabilne statystyki dla małych próbek.

**Threats.** Przekład sygnatury topologicznej na konkretne numerical findings ("liczba 23 zaczęła być częstsza") wymaga analizy **representative cycles** generatorów homologii — to dodatkowy moduł poza barcode viz. Ryzyko, że WebGL barcode viz przesłoni matematyczną substancję dla recruitera niematematycznego (over-decorating). Frontend effort (Three.js custom shaders) to drugi tech stack — bez prior experience to realnie 3–5 tyg, nie 2 tyg. Jeśli Takens embedding nie ujawni struktury, projekt staje się "negative result demonstrator" — wymaga jawnej decyzji architektonicznej już w tygodniu 1.

---

### 1.2 Q2 — WassersteinFlow [Cluster A]

**Strengths.** Wasserstein-2 distance to **skalar metryczny zmieniający się płynnie w czasie** — daje ciągły pomiar siły driftu zamiast binarnego p-value. Naturalnie integruje się z `ruptures` change-point detection (kompozycja z H1). Geomstats + Riemannian geometry to mocne "research instrument" framing — neutralizuje "lotto-scam" narrative. Hallucination Risk 2/5 — deterministyczna metryka z controlled regularization (Sinkhorn ε).

**Weaknesses.** Pred. Power 2/5 — transport map daje *kierunek* przepływu masy, ale ekstrapolacja na t+1 jest indirect i bez statistical guarantee. **JAX nie ma oficjalnego wsparcia dla Windows** — instalacja JAX z GPU to praktycznie WSL2-only, dla solo dev'a bez doświadczenia debugowanie może pochłonąć 1–2 tygodnie (F12 z HW catalog: DLL hell). Sinkhorn entropy regularization wprowadza hiperparametr ε wymagający calibration. Geomstats + jax.jit + POT to trzy nieoczywiste biblioteki bez prior experience (§10.5).

**Opportunities.** OT używane w GAN-ach i diffusion models — pokazuje znajomość modern ML metric theory. Wasserstein między oknami → szereg czasowy skalarów, idealne wejście dla classical change-point detection (DoD-4 cross-method). Stretch goal: porównanie z f-divergences (KL, χ²) jako extension story w README. **Plan B na JAX:** PyTorch z custom Sinkhorn lub `ot.gromov` (Windows-friendly) — zachowuje paradygmat bez ekosystem risk.

**Threats.** Przy n=1000–1500 i 50 wymiarach Wasserstein może być noisy — wymaga careful regularization. Brak natywnej "honest" predykcji utrudnia DoD-5. Czas MVP 5–7 tyg na samego auditora; predyktor warunkowy nadbudowany = +2–3 tyg. Jeśli pozostanie JAX, ryzyko utopienia 25% scope'u na environment debugging.

---

### 1.3 Q3 — EntangleScope (MPS) [Cluster P → ograniczony do wzorca #4]

**Strengths.** MPS daje pełny joint p(x_1,...,x_7) jednego losowania — predykcja warunkowa przez marginalizację jest natywna (Pred. Power 4/5 *dla wzorca #4*). Bond dimension χ jako jawny regularizer chroni przed overfittingiem na n=1000. Łączy fascynację quantum z §4 SEED_IDEA *bez* PennyLane CPU bottleneck (omija §7B.4 — MPS skaluje O(N·χ²), nie 2^n). Hallucination Risk 3/5 — χ truncation działa też jako information bottleneck.

**Weaknesses.** **MPS w standardowej formie nie pokrywa wzorca #5 (memory effect)** — modeluje strukturę przestrzenną pojedynczego losowania, nie zależności czasowe między losowaniami. Pokrycie #5 wymagałoby u-MPS lub MPS-MPO dla operatorów ewolucji — to ekspert-tier, nie MVP. Faktyczna przestrzeń stanów: C(50,5) × C(12,2) ≈ 140M (nie 50^7 ≈ 781G) — to **constrained sampling many-body system** z particle number conservation (dokładnie 5 wyróżnionych "spinów" w głównej puli). Trudność 4/5 — quimb/TeNPy mają stromą krzywą uczenia bez prior experience (§10.5).

**Opportunities.** "Quantum-inspired many-body model with particle conservation constraint" w README to silny technical framing dla AI/quant research — *bez* ryzyka "egzotyki niewolnej od artefaktów" (zarzut wobec H4 VQC). Entanglement entropy jako sygnał driftu *wewnątrz losowania* to oryginalny narrative — wzorzec #4 (cross-correlations) natywnie pokryty. χ jako jawny knob expressivity/regularization daje principled hyperparameter story.

**Threats.** Bond dimension χ jednocześnie **regularizuje i ogranicza capacity** — pod weak-signal regime może suppress'ować zarówno noise, jak i genuine structure. Czas MVP 6–8 tyg na granicy scope'u §6.3 (zero buffer'a). FP16 mixed precision wnosi ~0.5% błąd numerical — znaczący przy testach istotności na granicy α. Wzorzec #5 wymaga osobnego modelu czasowego (RNN, state-space, lub time-augmented tensor train) poza Q3 scope'em — to pęknięcie w pokryciu DoD.

---

### 1.4 D2 — Causal Drift Inference Engine [Cluster P]

**Strengths.** Causal discovery to "czarne złoto" w rekrutacji quant/ML research — bardzo rzadko spotykane w junior portfolio. Animowany graf przyczynowy z bootstrap-resampled edges to silny WOW. gCastle wspiera LiNGAM, PC, GES — trzy ortogonalne algorytmy = wewnętrzny cross-method validation. Bootstrap na krawędziach grafu daje principled FDR control (DoD-3).

**Weaknesses.** **Acyclicity i faithfulness wewnątrz pojedynczego losowania są fizycznie absurdalne** — wszystkie 5 liczb losowane są quasi-jednocześnie z tego samego bębna, nie ma causal ordering między X₁ a X₂. PC/LiNGAM jako *spatial* causal discovery wymaga przeniesienia na **Granger causality lub PCMCI na szeregach częstości czasowych** (50 zmiennych × 1000 punktów czasowych) — to inny algorytm niż oryginalny pitch, inny scope. PC algorithm wymaga n=5000+ dla stabilnego grafu na 50 zmiennych — przy n=1000 graf może być w 60–70% noisy edges. Hallucination Risk 5/5 — **wysokie prawdopodobieństwo produkcji wizualnie przekonujących, ale statystycznie nieidentyfikowalnych struktur causal**.

**Opportunities.** Pivot na Granger/PCMCI temporal pozwala uratować D2 z legitnym matematycznym uzasadnieniem — *causality* ma fizyczny sens między losowaniami (wczorajsze losowanie wpływa na dzisiejsze poprzez ewentualną zmianę protokołu), nie wewnątrz losowania. Cross-correlation patterns (wzorzec #4) = naturalny target dla causal temporal graphs. Skalowalność stretch goal: causality jest paradigm-agnostic, działa na każdym discrete temporal process.

**Threats.** Recruiter quant/research może wyłapać błąd faithfulness w 5 minut, jeśli graf zaprezentowany jest jako *spatial* zamiast *temporal*. Bootstrap 10⁴ permutacji × 3 algorithms = 3×10⁴ graph fits = dominujący koszt CPU, overnight batch z marginesem. Latent confounders (np. ukryta zmiana stanu maszyny) są praktycznie zawsze obecne, łamiąc założenia PC. Po wszystkich korektach D2 staje się projektem fundamentalnie innym niż oryginalny pitch — to jest istotny scope drift.

---

### 1.5 K4 — Adversarial Stationarity Probe [Cluster P]

**Strengths.** Najszybszy MVP wśród finalistów (3–4 tyg), najniższa trudność (2/5 dla MLP variant, 3/5 dla small transformer). Adversarial two-sample testing jako framing odnawia klasyczny shuffle test (§7A.2). **Alternatywna implementacja jako analityczny test MMD (Maximum Mean Discrepancy)** w RKHS — nie wymaga trenowania wag, stabilny dla N=100–500, eliminuje overfitting risk (Gretton et al. 2012). Hallucination Risk: 3/5 dla neural variant, 2/5 dla MMD variant.

**Weaknesses.** **Architektoniczny wybór wymaga jednoznacznej deklaracji:** (a) MLP + saliency maps (gradient × input, integrated gradients) — niska trudność, ograniczona interpretowalność per-liczba; (b) small transformer 2L/4H ~10MB — attention maps legalne, trudność 3/5; (c) MMD — kernel-based, no training, brak per-liczbowej density, ale stabilny. Każdy wariant ma inny trade-off; oryginalna formulacja "MLP + attention" była niespójna. C2ST (Classifier Two-Sample Test) daje binarne "czy rozkład się zmienił?", nie p(X|history) — Pred. Power 3/5, nie 4/5.

**Opportunities.** **MMD jako preferowany silnik** ze względu na asymptotyczną teorię (Gretton et al.), brak training instabilności, kompatybilność z małymi N — idealny dla wykrytych reżimów post-segmentation. Interpretability heatmap "AI vs Randomness" daje WOW bez ciężkiej frontend pracy (D3.js wystarcza). Kompozycja z H1 trywialna — K4 (MMD) może być "neural-flavored two-sample test" obok klasycznych ADF/KPSS, spełniając DoD-4 elegancko. Buffer czasowy (2–4 tyg) wykorzystać na rigorystyczny protokół: conformal p-values (Vovk), permutation-based FDR (Storey), held-out shuffled validation.

**Threats.** "Tylko MLP" lub "tylko kernel test" może wyglądać niewystarczająco math-heavy dla quant/research recruiterów — wymaga careful framing jako "neural two-sample test" z odwołaniem do Lopez-Paz & Oquab (2017) lub Gretton et al. (2012). Adversarial training (jeśli neural variant) jest niestabilny — wymaga GAN-like tricks (gradient penalty, spectral normalization). Two-sample testing wymaga starannie zdefiniowanej null distribution (shuffle vs uniform vs parametric bootstrap). Jeśli używane wewnątrz segmentu o N=130 (post regime-split), nawet mały MLP overfituje — MMD jest jedyną bezpieczną opcją w tym kontekście.

---

### 1.6 G3 — Entropy Auditor (compression-based transformer) [Cluster P, MVP tier]

**Strengths.** Pred. Power 5/5 — autoregresyjny transformer to *literalnie* p(x_{t+1} | x_{<t}), watch-list = top-k logits. Compression ↔ prediction equivalence (Shannon, Hutter) daje principled framing: "LLM jako detektor anomalii entropijnej". 5–10M parametrów w FP16 to ~10–20MB modelu (z optimizer states ~100–300MB peak VRAM) — **MVP tier**. Wystarcza 1 oś z katalogu (Oś 1: FP16); `torch.compile` opcjonalny (na Windows status ⚠️ — fallback ONNX Runtime z Oś 7).

**Weaknesses.** **Hallucination Risk 5/5** — 5–10M parametrów na 1000 punktów to klasyczny over-parameterized regime. Compression gain na finite samples *nie jest* wystarczającym dowodem genuine process structure bez ekstensywnych shuffled and synthetic controls. Mały transformer może kompresować artefakty kolejności, exploitować leakage, modelować finite-sample irregularities — to nie jest paradoks teoretyczny, to realny mechanizm patogenu. Custom transformer architecture wymaga decyzji o positional encoding, head size, layer count — duża powierzchnia design choice'ów.

**Opportunities.** Możliwy "TFT-replacement" framing — odpowiada na H2 SEED_IDEA z silniejszym statystycznym uzasadnieniem (compression theory vs forecasting). Aggressive dropout + weight decay + early stopping na shuffled validation set daje principled regularization. Bardzo dobre dla DoD-5 (honest predictor): jeśli na shuffled danych log-likelihood = uniform baseline, model nie halucynuje. Synthetic benchmark (planted vs no-planted signals) jest **mandatory** dla kalibracji G3 — bez tego pipeline produkuje wow-factor bez walidacji.

**Threats.** "TFT jako failure demonstrator" framing dotyczy tu wprost — wysoka Pred. Power w problemie audit-first to *liability*, nie asset. Wymaga bardzo aggressive shuffle test (10⁴ + held-out shuffled validation) — koszt CPU znaczący. 6–7 tyg na MVP zostawia mało buffer'a na polish/README/dashboard. Bez DriftSim (synthetic benchmark) jako mandatory infrastructure, G3 może produkować "compression gain" które są w 100% finite-sample hallucination.

---

### 1.7 C1 — SpectraDrift (RMT) [Cluster A]

**Strengths.** Hallucination Risk 1/5 — RMT operuje na deterministycznych invariantach algebraicznych macierzy korelacji. RMT używany w covariance matrix denoising w Markowitz portfolio (quant finance) — natychmiastowe rozpoznanie metody przez recruitera quant. Bardzo mały compute footprint (`scipy.linalg.eigvalsh` na 50×50 = ~1ms), zero VRAM, naturalna kompozycja z klasycznym baseline H1. Świetna interpretowalność: eigenvectors poza bulk *bezpośrednio* wskazują grupy skorelowanych liczb.

**Weaknesses.** Pred. Power 2/5 — eigenvalue spectrum sygnalizuje non-randomness, ale nie generuje natywnie p(x_{t+1}). **Klasyczny Marchenko–Pastur jest asymptotyczny dla p, n → ∞ przy q = p/n ∈ (0, 1); przy q = 50/1000 = 0.05 jesteśmy poza klasycznym regimem** — bulk MP jest skrajnie wąski, Tracy–Widom edge corrections są nieadekwatne. Wymagana adaptacja: **spiked covariance model** (Johnstone 2001), specjalnie zaprojektowany dla q→0, lub bootstrap permutation na eigenvalues jako finite-sample correction. Brak prior experience z RMT (§10.5) — krzywa uczenia z fizyki statystycznej.

**Opportunities.** Naturalny duet z TDA — RMT na spektrum kowariancji vs TDA na kształcie chmury punktów = dwa ortogonalne aspekty tej samej geometrii, perfect DoD-4 setup. Animacja eigenvalues "wystrzeliwujących" z spiked-corrected bulk przy change-pointach to silny WOW przy prostym matplotlib/plotly. Skalowalność stretch goal: RMT to standardowy tool w analizie financial time series, NIST RNG, neural network spectra. Najsilniejsze "quant legitimacy" framing w README: "We use spiked covariance corrections (Johnstone 2001), not classical Marchenko–Pastur, because q ≈ 0.05 places us outside the classical regime."

**Threats.** Wymaga explicit deklaracji w README, że używana jest poprawka spiked, nie klasyczny MP — bez tego recruiter quant wyłapie błąd w 5 minut. Eigenvectors interpretowalne, ale recruiter niematematyczny zobaczy "eigenvalues" i przeczyta jako "PCA" — wymaga jasnego framingu. Brak self-value (DoD-5) bez drugiego modelu nadbudowanego. RMT nie wykryje wzorca #5 (memory effect temporal) — wymaga ograniczenia scope'u do wzorców #1–#4 lub kompozycji z modelem czasowym.

---

### 1.8 C2 — DriftDPMM (Bayesian Nonparametrics) [Cluster P]

**Strengths.** Posterior predictive p(x_{n+1} | x_{1:n}) jest natywnym celem inference w BNP, analytical closed-form w stick-breaking representation. Dirichlet Process concentration parameter α daje natural regularization przeciw overfittingowi — Hallucination Risk 3/5, najniższy w Cluster P wśród modeli z Pred. Power 4–5. K_posterior(t) jako sygnał driftu = posterior on model complexity itself, oryginalny twist. Sequential Monte Carlo (particle filter on K) daje natywny online auditor — spełnia §7C.7 cadence "online <1s".

**Weaknesses.** **DPMM stosowane na surowych losowaniach daje degenerate K ≈ n** — przestrzeń stanów ~140M, okno ~100 losowań, prawdopodobieństwo powtórki ~0; "Chinese Restaurant Process" wizualizacja pokazałaby 100 stolików po 1 kliencie. **Wymagany preprocessing: DPMM na wektorach częstości w oknie (50-wymiarowy histogram), nie na surowych draws** — wtedy clustering operuje na rozkładach prawdopodobieństwa, gdzie DPMM jest dobrze zachowany. NumPyro/JAX na Windows 11 jest historically wonky — **rekomendowany fallback PyMC z PyTorch backend** (Windows-friendly). MCMC convergence diagnostics (R-hat, ESS, divergent transitions) wymagają explicit checks — pułapka silent failure.

**Opportunities.** BNP w portfolio to "elite tier" — częstsze w pracach naukowych niż w komercyjnych, mocny differentiator dla research-leaning recruiters. Posterior uncertainty quantification (słupki probabilistyczne na K) to silne "honest framing" — zero false certainty. Stretch goal: HDP (Hierarchical Dirichlet Process) lub HMM-DP hybrydy dla pokrycia wzorca #5 (memory effect) przez ukryte stany dyskretne.

**Threats.** Stick-breaking truncation poziom (K_max) wymaga calibration. Ryzyko, że "Chinese Restaurant Process" framing wygląda zbyt akademicko dla recruiterów spoza research. Inference na window-frequency vectors wymaga starannego doboru base distribution G₀ — niewłaściwy wybór daje degenerate posterior nawet po preprocessing fix. 6–7 tyg na MVP zostawia ograniczony buffer; environment risk (NumPyro→PyMC migration) zjada potencjalnie tydzień.

---

## 2. TOP 3 + 2 hybrydy

Selekcja TOP 5 z 8 finalistów + 2 hybrydy. Kryteria: balans między portfolio-value (§6.2 PRIMARY), wykonalnością w 6–8 tyg (§6.3), zgodnością z DoD-1...DoD-6, **Hallucination Risk** (kontrola false positives jako centralny problem projektu), pokryciem self-value angle (§6.2 fallback <20%).

**Mandatory infrastructure dla każdego wyboru:** DriftSim (synthetic data generator z planted/no-planted signals) — bez tego kalibracja sensitivity/specificity auditorów jest niemożliwa, a żaden detector nie ma uczciwego null baseline'u. **DoD-1 blind protocol** (ranking change-pointów *przed* porównaniem z 2014/2022, bez strojenia pod znane daty) — mityguje target leakage.

---

### TOP 1: **K4 (MMD variant) + H1 — Kernel Two-Sample + Classical Baseline**

**Uzasadnienie wyboru.** Najczystszy metodologicznie kandydat: H1 (statsmodels, ruptures) spełnia DoD-1...DoD-3 natywnie z klasycznych testów (ADF, KPSS, CUSUM, Welch, autocorrelation); MMD (kernel two-sample test w RKHS) spełnia DoD-4 jako *trzecia, niezależna* metoda — nie wymaga treningu, stabilny dla N=100–500, asymptotyczna teoria Gretton et al. (2012). Hallucination Risk 2/5 — wszystkie komponenty mają explicit null distribution i kontrolowany false-positive rate; żaden komponent nie ma "magicznego" predyktora, który mógłby halucynować strukturę. Stack PyTorch + scipy + statsmodels + sklearn = pełen ekosystem znany Piotrowi (§10.5), brak nieznanych technologii (JAX, NumPyro, quimb, gudhi/ripser), 6–8 tyg jest realne. Buffer czasowy (2–4 tyg) inwestowany w rigor metodologiczny: conformal p-values (Vovk), permutation-based FDR (Storey), held-out shuffled validation, DriftSim calibration curves.

**Scoring (1–10):**

| Wymiar | Score |
|---|---|
| Oryginalność | 7 |
| Wow-factor | 7 |
| Wykonalność (3–4 tyg base + 2 tyg rigor + 1 tyg polish) | 10 |
| Portfolio-value | 9 |
| Zgodność z SEED_IDEA | 10 |
| **TOTAL** | **43/50** |

**Hallucination Risk: 2/5** (very low — kernel test deterministic, classical tests asymptotic).

**Kluczowe ryzyko + mitygacja.**
- *Ryzyko:* "Klasyczne testy + kernel two-sample" może wyglądać zbyt prosto math-heavy dla recruiterów quant/research.
- *Mitygacja:* Centralny framing jako "rigorous statistical audit framework with calibrated null distributions". Buffer czasowy wykorzystać na: (1) DriftSim z explicit sensitivity/specificity curves dla różnych signal strengths, (2) conformal p-values dla distribution-free type-I error control, (3) reporting protocol per ASA statistical significance guidelines. To zamienia "prosty stack" na "głębokie testowanie hipotez". Wzbogacenie o **persistence landscapes na Takens embedding** (lekka warstwa TDA bez full ripser pipeline) jako opcjonalny stretch goal — dodaje math depth bez frontend complexity.

---

### TOP 2: **C1 (spiked covariance) — Random Matrix Theory Auditor**

**Uzasadnienie wyboru.** Najsilniejsze "quant legitimacy" framing wśród audit-only finalistów: RMT używany w covariance denoising w Markowitz portfolio, neural network spectra (Pennington & Worah 2017), NIST RNG analysis. Hallucination Risk 1/5 — deterministyczne invariants algebraiczne z asymptotyczną teorią. Bardzo mały compute footprint (`scipy.linalg.eigvalsh` ~1ms per window), zero VRAM, naturalna kompozycja z H1. Eigenvectors poza bulk *bezpośrednio* wskazują grupy skorelowanych liczb — silna interpretowalność. Math depth bez frontend complexity — animacja eigenvalues vs spiked-corrected bulk w plotly wystarczy.

**Scoring (1–10):**

| Wymiar | Score |
|---|---|
| Oryginalność | 10 |
| Wow-factor | 7 |
| Wykonalność (5–6 tyg, MVP tier, CPU-only, scipy-native) | 8 |
| Portfolio-value | 10 |
| Zgodność z SEED_IDEA | 9 |
| **TOTAL** | **44/50** |

**Hallucination Risk: 1/5** (very low — deterministic algebra with closed-form null).

**Kluczowe ryzyko + mitygacja.**
- *Ryzyko 1:* Klasyczny Marchenko–Pastur jest nieadekwatny dla q=0.05 — bez korekt wynik jest niewiarygodny.
- *Ryzyko 2:* Pred. Power 2/5 — DoD-5 wymaga drugiego systemu lub akceptacji audit-only framing.
- *Mitygacja 1:* Explicit deklaracja w README: "spiked covariance corrections (Johnstone 2001), bootstrap permutation on eigenvalues as finite-sample baseline". Faza 0 PoC waliduje, że spiked-corrected bulk jest węższy niż empirical eigenvalue distribution na shuffled data.
- *Mitygacja 2:* Naturalna kompozycja z K4 (MMD) jako predyktor warunkowy w obrębie wykrytych spektralnych reżimów — zob. HYBRYDA-2. Lub akceptacja audit-only framing dla maksymalnej defensywności (zero "lotto-scam risk").

---

### TOP 3: **K2 (Takens embedding) — TDA Microscope**

**Uzasadnienie wyboru.** Najsilniejszy math-heavy framing wśród audit-only finalistów: persistent homology z Takens embedding daje legitne narzędzie dla szeregów dyskretnych (Perea & Harer 2015) — nie surowy Vietoris-Rips na R^50. Hallucination Risk 1/5 dla model overfitting, 3/5 dla interpretation overfitting (przestrzeń decyzji: filtracja × embedding × metric × window). WebGL 3D barcode viz to silny WOW-factor dla skill diversification w portfolio. Math-heavy framing ("Topological Data Analysis") natychmiast neutralizuje "lotto-scam" w README.

**Scoring (1–10):**

| Wymiar | Score |
|---|---|
| Oryginalność | 9 |
| Wow-factor | 9 |
| Wykonalność (4–5 tyg core + 2–3 tyg frontend WebGL) | 7 |
| Portfolio-value | 9 |
| Zgodność z SEED_IDEA | 8 |
| **TOTAL** | **42/50** |

**Hallucination Risk: 2/5** (low model risk, moderate interpretation risk).

**Kluczowe ryzyko + mitygacja.**
- *Ryzyko 1:* Bez Takens embedding (raw R^50 cloud) TDA produkuje czysty szum próbkowania — pierwsza technical decision musi być explicit.
- *Ryzyko 2:* WebGL custom shaders to 3–5 tyg dla osoby bez frontend background, nie 2 tyg.
- *Ryzyko 3:* Interpretation overfitting przez eksplorację wielu filtracji / embeddings.
- *Mitygacja 1:* Faza 0 PoC obowiązkowo waliduje Takens embedding na 1D szeregach częstości — jeśli persistence diagrams są nietrywialne na real data i degenerate na shuffled, paradygmat się broni.
- *Mitygacja 2:* Plan B na WebGL: matplotlib + plotly dla barcode viz (mniej WOW, ale 1 tydzień zamiast 3–5).
- *Mitygacja 3:* Pre-registration wyboru filtracji/embeddingu *przed* uruchomieniem na real data, lub jawny "specification curve analysis" (Simonsohn et al. 2020) raportujący wyniki dla wszystkich kombinacji.

---

### HYBRYDA-1: **K2 (Takens) + K4 (MMD) + H1 — Three-Pillar Audit Stack**

**Uzasadnienie wyboru.** Three-pillar architecture spełnia DoD-4 *cross-architecture consistency* explicit: H1 (klasyczny baseline) + K2 (topologiczny) + K4-MMD (kernel two-sample). Każdy filar operuje na innym matematycznym fundamencie (parametric tests / algebraic topology / RKHS embeddings), co daje **methodological diversity i architectural diversity** — choć nie pełną statistical independence (wszystkie trzy karmione tą samą próbką). K4 jako MMD eliminuje N=130-overfitting trap przy regime-conditional analysis. Math depth z TDA + quant legitimacy z H1 + modern ML signaling z MMD.

**Scoring (1–10):**

| Wymiar | Score |
|---|---|
| Oryginalność | 9 |
| Wow-factor | 9 |
| Wykonalność (6–8 tyg — H1 1 tyg + K2-Takens 3–4 tyg + MMD 1–2 tyg + integration 1 tyg) | 7 |
| Portfolio-value | 10 |
| Zgodność z SEED_IDEA | 10 |
| **TOTAL** | **45/50** |

**Hallucination Risk: 2/5** (low across all three pillars).

**Kluczowe ryzyko + mitygacja.**
- *Ryzyko 1:* Częściowa tautologia w pipeline (K2 segmentuje → K4-MMD testuje segmenty → "confirms" the segmentation).
- *Ryzyko 2:* Frontend WebGL effort wciąż 2–4 tyg, zjada buffer dla rigor.
- *Ryzyko 3:* Trzy stack-i (statsmodels + gudhi/ripser + sklearn-kernel) zwiększają complexity onboardingu.
- *Mitygacja 1:* K4-MMD trenowany *nie* na segmentach z K2, ale na całym strumieniu z change-points jako *covariate* (nie *target*). Held-out validation set spoza wykrytych reżimów. DriftSim z planted regimes do walidacji, że pipeline nie halucynuje. Explicit tabela w README: statistical independence (NO) / methodological diversity (YES) / architectural diversity (YES) / evidence triangulation (PARTIAL).
- *Mitygacja 2:* Plan B na WebGL: matplotlib + plotly dla barcode viz, czas zaoszczędzony inwestowany w specification curve analysis.
- *Mitygacja 3:* Decision gate w tygodniu 5: jeśli K2 (Takens) nie przeszedł DoD-1b w blind protocol, pivot do K4-MMD + H1 standalone (TOP 1) bez utraty pracy — H1 i MMD są niezależne od K2.

---

### HYBRYDA-2: **C1 (spiked) + K4 (MMD) + H1 — Spectral Gate + Kernel Predictor + Classical Baseline**

**Uzasadnienie wyboru.** Najsilniejsze "quant research instrument" framing wśród hybrydy: dwa principled mathematical frameworks (Random Matrix Theory + Reproducing Kernel Hilbert Spaces) plus klasyczny baseline H1. C1 jako spectral gate — eigenvalues poza spiked-corrected bulk sygnalizują non-randomness; K4-MMD jako predyktor warunkowy fitowany *tylko gdy* gate sygnalizuje signal. Hallucination Risk 1/5 we wszystkich filarach. Eigenvectors z C1 informują strukturę correlated groups, które MMD testuje jako joint two-sample hypothesis — naturalny information flow bez tautologii (eigenvalues są spektralnym descriptorem, MMD testuje empirical density — ortogonalne aspekty).

**Scoring (1–10):**

| Wymiar | Score |
|---|---|
| Oryginalność | 10 |
| Wow-factor | 7 |
| Wykonalność (6–7 tyg — H1 1 tyg + C1 3–4 tyg + MMD 1–2 tyg + integration 1 tyg) | 8 |
| Portfolio-value | 10 |
| Zgodność z SEED_IDEA | 9 |
| **TOTAL** | **44/50** |

**Hallucination Risk: 1/5** (very low — deterministic algebra + asymptotic kernel theory + classical tests).

**Kluczowe ryzyko + mitygacja.**
- *Ryzyko 1:* C1 wymaga spiked corrections implementation — bez prior experience to dodatkowy 1–2 tyg onboardingu na RMT.
- *Ryzyko 2:* Brak frontend wow-factor — animacja eigenvalues vs spiked bulk w plotly jest matematycznie elegancka, ale wizualnie mniej imponująca niż WebGL barcode.
- *Mitygacja 1:* Faza 0 PoC waliduje, że bootstrap permutation na eigenvalues daje sensible finite-sample correction nawet bez pełnej spiked theory — to fallback gdy spiked implementation zjada buffer.
- *Mitygacja 2:* Wzbogacenie viz o eigenvector heatmaps (które grupy liczb są skorelowane) + 3D scatter eigenvalues w czasie — daje "math beauty" zamiast "shader beauty". Pre-registration: wybór corrected bulk distribution (spiked vs bootstrap) *przed* uruchomieniem na real data.

---

## Tabela porównawcza TOP 3 + 2 hybrydy

| Kandydat | Cluster | Tier | Trudność | Czas MVP | Pred. Power | Halluc. Risk | Total Score |
|---|---|---|---|---|---|---|---|
| **TOP 1** K4 (MMD) + H1 | P+A | MVP | 2 | 3–4 tyg + 2–4 rigor | 3/5 | **2/5** | 43/50 |
| **TOP 2** C1 (spiked) | A | MVP | 4 | 5–6 tyg | 2/5 | **1/5** | 44/50 |
| **TOP 3** K2 (Takens) | A | MVP | 3 | 4–5 tyg + 2–3 frontend | 1/5 | 2/5 | 42/50 |
| **HYBRYDA-1** K2 + K4 + H1 | A+P+A | MVP | 3 | 6–8 tyg | 3/5 | 2/5 | **45/50** |
| **HYBRYDA-2** C1 + K4 + H1 | A+P+A | MVP | 4 | 6–7 tyg | 3/5 | **1/5** | 44/50 |

---

## 3. Rekomendacja nr 1

### **TOP 1: K4 (MMD variant) + H1 + DriftSim — Kernel Two-Sample + Classical Baseline + Synthetic Calibration**

**Dlaczego ta, a nie inne.**

Trzy konwergujące argumenty:

**1. Najczystsza metodologia spośród kandydatów.** H1 (klasyczne testy — ADF, KPSS, CUSUM, Welch, autocorrelation z `statsmodels`/`ruptures`) spełnia DoD-1...DoD-3 natywnie. MMD (kernel two-sample test w RKHS) jest analitycznym testem z asymptotyczną teorią (Gretton et al. 2012) — nie wymaga treningu wag, stabilny dla małych N, brak overfitting risk per se. DriftSim (synthetic benchmark z planted/no-planted signals) zapewnia calibrated null baseline dla DoD-5 (honest predictor — model nie halucynuje na shuffled/uniform synthetic data). Spełnienie DoD-4 (cross-architecture consistency) jest natywne: klasyczne testy + kernel test to dwa niezależne paradygmaty z różnymi null distributions.

**2. Niskie Hallucination Risk (2/5).** Wszystkie trzy komponenty mają explicit null distribution i kontrolowany false-positive rate. Żaden komponent nie ma "magicznego" predyktora wysokiej capacity, który mógłby produkować "compression gain" lub "causal edges" jako finite-sample artefakt. To kluczowa cecha — centralnym problemem projektu jest kontrola false positives, nie eksploracja "wow architecture".

**3. Realistyczny scope dla solo developera na Windows 11.** PyTorch + scipy + statsmodels + sklearn = pełen ekosystem znany Piotrowi (§10.5). Brak nieznanych technologii (JAX, NumPyro, quimb, gudhi/ripser z WebGL shaders). 6–8 tyg jest realne, nie optymistyczne. Buffer czasowy (2–4 tyg) inwestowany w rigor metodologiczny: conformal p-values (Vovk), permutation-based FDR (Storey, Benjamini-Hochberg), DriftSim calibration curves (ROC dla różnych signal strengths), specification curve analysis (Simonsohn et al. 2020).

**Co konkretnie wybudować w MVP (6–8 tyg):**

- **Tydzień 1:** H1 core — ADF, KPSS, CUSUM, Welch, autocorrelation na 50 głównych liczbach. Pierwsza walidacja DoD-1a (sanity check euronumerów) i DoD-1b (blind change-point detection na głównych liczbach). Setup statsmodels + ruptures pipeline.
- **Tygodnie 2–3:** DriftSim — synthetic data generator z planted patterns (monotonic drift, periodicity, clustered bursts, cross-correlations) i no-planted (uniform null). Calibration curves (sensitivity/specificity) dla każdego testu H1.
- **Tydzień 4:** MMD core — kernel two-sample test (Gaussian RBF, polynomial), sliding window z DriftSim baseline'em. Comparison z H1 testami na shuffled data.
- **Tydzień 5 — DECISION GATE:** Czy H1 + MMD wykrywają planted signals w DriftSim z sensible sensitivity? TAK → kontynuacja rigor + viz. NIE → diagnostyka przed dalszym scope.
- **Tygodnie 6–7:** Rigor — conformal p-values, FDR correction (Benjamini-Hochberg), held-out shuffled validation, specification curve analysis. Cross-method consistency reporting (DoD-4).
- **Tydzień 8:** README, dashboard (plotly + streamlit lub D3), dokumentacja protokołu, "negative result first-class" framing.

**Plan B (fallback):**
- Jeśli H1 + MMD nie wykrywają planted signals w tygodniu 5 → projekt staje się "**framework for measuring detector hallucination rates in supposedly memoryless processes**": centralnym deliverable jest *kalibracja detektorów na DriftSim*, nie samo wykrywanie. To inny portfolio framing, ale wartościowy — epistemic project o granicach detekcji wzorców.
- Jeśli buffer pozwoli (tygodnie 7–8) → opcjonalne wzbogacenie o **K2 z Takens embedding** jako czwarty filar (TDA na 1D szeregach częstości, R^2/R^3 — gdzie matematyka jest poprawna). Jeśli daje sensowne barcode'y na DriftSim z planted signals, dodaje math depth; jeśli nie, README dokumentuje "TDA is not adequate for this domain at this sample size" — negative result jako portfolio-value.

**Co to oznacza dla narracji portfolio:**

> *DriftScope is a statistical audit framework for non-stationarity detection in streaming discrete processes. It combines classical hypothesis testing (ADF, KPSS, CUSUM, permutation FDR) with a kernel two-sample test (MMD in RKHS), calibrated against synthetic benchmarks with planted and no-planted signals. EuroJackpot serves as a benchmark case study — a process designed to be uniform-random, used here to validate detection protocols under strict permutation-based controls and multiple-testing correction. The project does not predict lottery outcomes; it measures whether a given detector can distinguish signal from its own hallucinations.*

To framing:
- math-heavy bez "egzotyki" (klasyczne testy + RKHS + synthetic calibration),
- defensywne wobec "lotto-scam" (EuroJackpot jako "benchmark", nie "predictor target"),
- spójne z DoD-1a/DoD-1b (blind protocol)...DoD-6,
- spójne z preferencjami §4 (rigor metodologiczny jako fascynacja),
- skalowalne (stretch goal: NIST RNG, kryptograficzne PRNG, financial returns — wszystkie discrete/continuous processes z null hypothesis stationarity).

---

**Decyzja należy do Ciebie.** Powyższa rekomendacja jest moim najsilniejszym uzasadnionym wskazaniem, ale wszystkie 5 kandydatów (TOP 3 + 2 hybrydy) są legitnymi opcjami z różnymi profilami ryzyka:

- **Najprostszy MVP + najczystsza metodologia** → TOP 1 (K4-MMD + H1).
- **Najsilniejsze quant legitimacy + lowest Hallucination Risk** → TOP 2 (C1 spiked) lub HYBRYDA-2 (C1 + K4 + H1).
- **Najsilniejszy WOW + math depth + skill diversification (WebGL)** → TOP 3 (K2 Takens) lub HYBRYDA-1 (K2 + K4 + H1).
- **Maksymalna oryginalność matematyczna w portfolio** → HYBRYDA-2 (RMT + RKHS + classical).

Niezależnie od wyboru, **DriftSim (synthetic benchmark) i DoD-1 blind protocol są mandatory infrastructure** — bez nich kalibracja detektorów i kontrola false positives są iluzoryczne.

Czekam na Twój wybór przed Krokiem B.
