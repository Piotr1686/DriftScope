# HARDWARE_PUSH_CATALOG.md

Katalog technik wyjścia poza ograniczenia hardware.

**Hardware target:** RTX 3050 Laptop (4GB VRAM) / 32GB RAM / i5-12500H / Windows 11

Ten plik jest **załączany jako kontekst** do promptów w workflow, gdzie LLM proponuje architekturę projektu z komponentem AI/ML.

---

## TL;DR — 8 osi w 1 zdaniu

- **Oś 0 (Environment):** Pin wersji, jeden GPU backend per pipeline, env sanity test pierwszy.
- **Oś 1 (Quantization):** FP16 default, GGUF Q5/Q4 dla LLM, INT8 ONNX dla CV. NIE Q4 dla diffusion (artifacting).
- **Oś 2 (Offloading):** diffusers `enable_*_cpu_offload` dla SD, accelerate `device_map='auto'` dla LLM 5-15GB, AirLLM tylko dla LLM >30B batch processing.
- **Oś 3 (Compilation):** `torch.compile(mode='reduce-overhead')` lub ONNX export. CUDA EP > DirectML EP na NVIDII.
- **Oś 4 (Surgery):** Pre-distilled checkpoint hunt FIRST. DIY distillation tylko jako expert tier (1-3 tygodnie).
- **Oś 5 (Pipeline):** Tile 512x512 + overlap dla CV, sliding window dla audio, vector cache dla high-recurrence input.
- **Oś 6 (Hybrid):** Build-time na Colab Free (10-20h praktycznie/tydzień), runtime lokalny. Pre-distilled > custom distillation.
- **Oś 7 (Runtime):** ONNX Runtime CUDA EP dla CV na NVIDII, llama.cpp dla LLM, whisper.cpp dla audio.

---

## JAK TO DZIAŁA

LLM-y, którym załączysz ten plik, MUSZĄ:
1. Zaklasyfikować projekt do tieru (MVP/Balanced/Push/Extreme) na podstawie rozmiaru największego modelu w FP16.
2. Rozważyć osie proporcjonalnie do tieru (1/2/3/4+ osie).
3. Sprawdzić Composability Matrix (czy techniki kompatybilne).
4. Sprawdzić Failure Modes (czy nie wpadają w znaną pułapkę).

**Zasada nadrzędna: "Minimum sufficient, no more."** Jeśli jedna technika załatwia sprawę i daje >15% headroom VRAM, NIE dodawaj kolejnych.

---

## STATUSY WERYFIKACJI

Każda technika ma status weryfikacji na sprzęcie target:

- `✓✓` — przetestowane z PoC w MEMORY.md jednego z poprzednich projektów
- `✓` — community-confirmed na podobnym sprzęcie
- `⚠️` — teoretyczne / linuksowe / nieprzetestowane na RTX 3050 + Win11
- `❌` — znane problemy (z konkretnym FAILURE MODE)

Pierwsza wersja katalogu domyślnie ma większość na `⚠️`. Po projektach stopniowo upgrade'ujesz na `✓` lub `✓✓` na podstawie wpisów w MEMORY.md.

---

## OŚ 0 — ENVIRONMENT & DRIVER SANITY (Foundation)

**Filozofia:** Najlepsze techniki optymalizacji są bezsilne, jeśli środowisko się sypie. Bez Osi 0 wszystkie pozostałe osie ryzykują niepowodzenie z powodu trywialnych konfliktów.

### Praktyki

| Praktyka | Co rozwiązuje | Jak | Status |
|----------|----------------|-----|--------|
| Pin wersji w `pyproject.toml` (uv/conda-lock) | Drift wersji torch/cuda | `uv pip compile pyproject.toml` | ✓ |
| RUNTIME ISOLATION RULE | Konflikty GPU memory pool między backendami | Jeden backend GPU per pipeline (CUDA *lub* DirectML, nie miks) | ✓ |
| Dedykowany conda env per projekt | DLL hell przy reinstalacji | `conda create -n nazwa python=3.10` | ✓ |
| Driver freeze | "Update sterowników popsuł projekt" | Zapisz wersję w MEMORY.md przy starcie projektu | ✓ |
| MSVC Redistributables sanity | "DLL not found" | Zainstaluj wszystkie wersje 2015-2022 | ✓ |
| Pre-flight environment test | Wykrycie konfliktów ZANIM napiszesz kod | Skrypt `tests/test_environment.py` | ✓ |

### Composability:
- **Oś 0 vs wszystkie inne:** prerequisite. Bez niej F12 zabija wszystko.
- **Oś 0 vs Oś 7:** RUNTIME ISOLATION RULE — jeden runtime per pipeline. Multi-runtime tylko w oddzielnych subprocessach.

---

## OŚ 1 — QUANTIZATION

**Filozofia:** zmniejsz precyzję wag/aktywacji w zamian za VRAM.
**VRAM impact:** 2-4x redukcja. **Quality cost:** 0-15%.

### Techniki

| Technika | VRAM saved | Quality loss | Kiedy stosować | Lib/repo | Status |
|----------|-----------|--------------|----------------|----------|--------|
| FP16 | 2x | <0.1% | Always start here | torch (`.half()`) | ✓ |
| BF16 | 2x* | <0.1% | Modern GPUs, większy dynamic range | torch (`.bfloat16()`) | ⚠️ |
| INT8 (post-training) | 4x | 1-3% | Inference, batch | ONNX Runtime (Win), bitsandbytes (Linux) ⚠️ | ⚠️ |
| Q5_K_M (GGUF) | 3-4x | 1-2% | LLM, audio | llama.cpp, whisper.cpp | ✓ |
| Q4_K_M (GGUF) | 4-5x | 3-7% | LLM must-fit | llama.cpp | ✓ |
| AWQ-4bit | 4-5x | 2-5% | LLM, niska latencja | autoawq, vLLM | ⚠️ |
| GPTQ-4bit | 4-5x | 2-6% | LLM batch | auto-gptq | ⚠️ |
| INT4 weight-only | 4x | 3-8% | Vision/CV | torchao, NNCF | ⚠️ |
| Dynamic quant (ONNX) | 2-3x | 1-3% | CV/CNN, ONNX deployment | onnxruntime | ⚠️ |

\* **BF16 na RTX 3050 (Ampere):** Sprzętowo wspierane, ale memory footprint **identyczny** jak FP16. BF16 to "speed precision", nie "memory precision" — zaleta to większy dynamic range (uniknięcie overflow w attention scores). Default FP16, BF16 tylko gdy widzisz NaN/Inf.

⚠️ **bitsandbytes na Windows:** instalacja problematyczna (wymaga ręcznej kompilacji DLL). Dla Win11 + RTX 3050 preferuj **ONNX Runtime z INT8 dynamic** lub **GGUF Q5_K_M/Q4_K_M**. Reserwuj bitsandbytes dla WSL2/Linux.

### Decision tree:
- **LLM lokalnie?** → GGUF Q5_K_M (priorytet) lub Q4_K_M (must-fit)
- **CV model na ONNX Runtime?** → INT8 dynamic quant
- **Audio?** → llama.cpp / whisper.cpp
- **Diffusion model?** → BF16 + xFormers (kwantyzacja często psuje jakość)

### Anti-patterns:
- **Aggressive Q4 post-training quantization dla diffusion (PyTorch native)** — ARTIFACTING. Use BF16/FP16 + offloading.
  - **Wyjątek:** Pre-quantized community checkpoints (np. SDXL GGUF, INT8 ONNX) działają akceptowalnie — testuj per model.
- **Q4 dla speech recognition** — degradacja WER 10%+. Use Q5_K_M.

### Composes well with:
- Compilation (Oś 3) — kompilowany kwantyzowany model = 2-3x speedup
- Runtime engines (Oś 7) — ONNX Runtime + INT8 = optimal CPU path

---

## OŚ 2 — OFFLOADING

**Filozofia:** trzymaj wagi w taniej pamięci (RAM/Disk), ładuj do VRAM tylko aktywne warstwy.
**VRAM impact:** 4-10x redukcja. **Latency cost:** 1.5-10x wolniej.

### Techniki

| Technika | VRAM saved | Latency cost | Kiedy stosować | Lib/repo | Status |
|----------|-----------|--------------|----------------|----------|--------|
| `device_map="auto"` (Accelerate) | 2-4x | 1.5-2x | Modele 5-15GB na 4GB VRAM | huggingface/accelerate | ⚠️ |
| Sequential CPU offload (Diffusers) | 5-8x | 3-5x | SDXL, large diffusion | diffusers | ⚠️ |
| Model CPU offload (Diffusers) | 2-3x | 1.5-2x | SD1.5, mid-size | diffusers | ⚠️ |
| Layer-wise offload (AirLLM) | 10x+ | 10-100x+ | Huge LLMs, batch only | lyogavin/airllm | ⚠️ |
| ZeRO-Infinity (DeepSpeed) | 10x+ | 5-20x | Training huge models | microsoft/DeepSpeed | ⚠️ |
| Attention slicing | 1.5-2x | 1.2-1.5x | Diffusion, attention-heavy | diffusers | ⚠️ |
| VAE tiling/slicing | 2-3x VRAM peak | 1.2x | Diffusion z dużymi obrazami | diffusers | ⚠️ |
| Gradient checkpointing | 2-3x (training) | 1.3x | Training/fine-tuning | torch.utils.checkpoint | ⚠️ |
| `safetensors` mmap loading | RAM saved | -50% load time | Każde ładowanie modelu | safetensors | ✓ |

ℹ️ **AirLLM realistic latency:**
- 13B-30B na PCIe 4.0 x4 (laptop NVMe) → **10-50x** spowolnienie
- 70B na PCIe 4.0 x4 → **100-500x** spowolnienie (140GB FP16 / ~7GB/s I/O)
- 405B → curiosity, nie regularnego użytku

AirLLM nadaje się do **batch processing** (overnight) lub **one-shot inference**, nie real-time. Dla LLM lokalnych: `llama.cpp` + GGUF Q4_K_M na 7B-13B.

### Decision tree:
- **LLM 7B+?** → Accelerate `device_map="auto"` (mid-tier) lub AirLLM (extreme)
- **Stable Diffusion XL?** → diffusers sequential_cpu_offload + attention_slicing + vae_tiling
- **Stable Diffusion 1.5/2.1?** → diffusers model_cpu_offload (wystarcza)
- **Custom CV model >2GB?** → safetensors mmap + manual to-device per stage

### Anti-patterns:
- AirLLM dla real-time CV (50ms response) — PCIe bottleneck.
- Sequential offload dla małego modelu <500MB — overhead > benefit.

### Composes well with:
- Quantization (Oś 1) — offload + Q4 = 4x z 4x = 16x effective
- Compilation (Oś 3) — `torch.compile` z offload działa, ale wymaga `mode="reduce-overhead"`

### Composes BADLY with:
- TensorRT NIE wspiera offloadingu. ONNX Runtime tak.

---

## OŚ 3 — COMPILATION / JIT

**Filozofia:** PyTorch eager mode jest interpretowany. Kompilacja graphs = 1.5-3x speedup za darmo.
**VRAM impact:** 0%. **Quality cost:** 0%.

### Techniki

| Technika | Speedup | Warmup cost | Kiedy stosować | Lib/repo | Status |
|----------|---------|-------------|----------------|----------|--------|
| `torch.compile()` (default) | 1.3-2x | 30-60s | PyTorch 2.x, każdy model | torch | ⚠️ Win |
| `torch.compile(mode="reduce-overhead")` | 1.5-2.5x | 60-120s | Repeating inference | torch | ⚠️ Win |
| `torch.compile(mode="max-autotune")` | 2-3x | 5-15min | Long-running inference | torch | ⚠️ Win |
| `torch.jit.trace()` | 1.2-1.5x | <10s | Stable shapes | torch (legacy) | ✓ |
| ONNX export + ORT | 1.5-3x | 0 (offline) | Cross-platform | onnx, onnxruntime | ✓ |
| TensorRT compile | 2-5x | 5-30min | NVIDIA-only, latency-critical | NVIDIA/TensorRT | ⚠️ |
| OpenVINO compile | 2-4x (CPU+iGPU) | 1-5min | Intel CPUs (i5-12500H) | openvinotoolkit | ⚠️ |
| Apache TVM autotune | 2-5x | hours | Custom hardware | apache/tvm | ❌ rzadko warto |

⚠️ **`torch.compile` na Windows:** ograniczone wsparcie backendów (inductor problematyczny). Test ostrożnie — jeśli warmup >5min lub crashuje, fallback do `torch.jit.trace()` lub ONNX.

### Decision tree:
- **PyTorch model, długo-działający?** → `torch.compile(mode="reduce-overhead")` — best ROI gdy działa
- **CV inference, niska latencja?** → ONNX export + ORT z CUDA EP (natywny dla RTX 3050)
- **Real-time + RTX 3050?** → TensorRT (jeśli akceptujesz lock-in F11)
- **CPU/iGPU?** → OpenVINO

### Anti-patterns:
- `torch.compile` z dynamicznymi shape'ami — recompilacja per call. Fix: `torch.compile(dynamic=True)` (PyTorch 2.1+) lub pad inputs do bucket sizes.
- TensorRT dla projektów portable — non-portable, lock-in (F11).

### Composes well with:
- Quantization (Oś 1) — compile(quantized) = 4-5x speedup combined
- Runtime engines (Oś 7) — natural pairing

---

## OŚ 4 — ARCHITECTURE SURGERY

**Filozofia:** Zmień sam model — usuń niepotrzebne, zastąp mniejszym, routuj sparingly.
**VRAM impact:** 2-10x redukcja. **Quality cost:** 1-15%.

**KRYTYCZNA HIERARCHIA dla solo dev:**
1. **Pierwszy krok ZAWSZE: poszukaj pre-distilled checkpointu** (HF Hub). Społeczność już to zrobiła — pobranie 450MB ONNX > tygodnie własnego treningu.
2. **Drugi krok: gotowe techniki (LoRA fine-tune)** jeśli musisz dostroić.
3. **Ostatni krok: DIY distillation/pruning** TYLKO gdy żaden gotowy artefakt nie spełnia wymagań. Expert tier — 1-3 tygodnie + dataset.

### Techniki

| Technika | VRAM saved | Quality loss | Effort | Lib/repo | Status |
|----------|-----------|--------------|--------|----------|--------|
| Pre-distilled checkpoint download | 3-10x | 1-5% | Trivial (godziny) | HF Hub, communities | ✓ |
| Magnitude pruning | 1.5-3x | 1-5% | Medium | torch.nn.utils.prune | ⚠️ |
| Structured pruning | 2-4x | 3-10% | Medium-high | torch-pruning | ⚠️ |
| Lottery Ticket finding | 5-10x | 2-7% | Very high | research-grade | ❌ rzadko warto |
| Layer dropping | 1.5-3x | 5-15% | Low | manual edit | ⚠️ |
| MoE routing (manual) | 2-5x active | 0% | Medium | custom router | ⚠️ |
| Knowledge distillation (DIY) | 3-10x | 2-8% | **Expert (1-3 tygodnie)** | torch, custom training | ❌ ostatnia opcja |

### Pre-distilled checkpoint hunt (FIRST STEP, zawsze)

Zanim rozważysz custom distillation, sprawdź czy istnieje gotowy mniejszy odpowiednik:

| Domain | Original | Pre-distilled alternative | Repo/Hub |
|--------|----------|---------------------------|----------|
| Diffusion (image gen) | SDXL (6.5GB) | SDXL Turbo / SDXL Lightning | huggingface.co/stabilityai |
| Diffusion (image gen) | SD 1.5 (4GB) | LCM-LoRA (kilka MB merge) | huggingface.co/latent-consistency |
| LLM general | Llama 3 70B | Llama 3 8B + GGUF Q4 (~5GB) | TheBloke/* na HF |
| LLM general | GPT-4 quality | Mistral 7B / Mixtral 8x7B GGUF | mistralai na HF |
| ASR (speech) | Whisper Large (3GB) | Distil-Whisper Large v3 (~750MB) | distil-whisper |
| BERT / NLP | BERT-base (440MB) | DistilBERT (270MB) | distilbert-base-* |
| Vision | ViT-Large | ViT-Small / DINOv2-Small | timm |
| Image SR | Real-ESRGAN x4 | Real-ESRGAN-Anime / community Q4 ONNX | ai-forever, communities |

**Heurystyka:** szukaj na HF Hub `<model_name> distilled OR small OR quantized OR onnx`. Jeśli znajdziesz — pobierz, dodaj do `artifacts/models/`, gotowe.

### Custom distillation (EXPERT TIER ONLY)

Realistic requirements:
- 1-3 **tygodni** pracy solo dev
- Dataset reprezentatywny (sam zbierz/syntetyzuj)
- Pętla treningowa: distillation loss (KL+MSE), feature matching, validation
- Hardware: T4 15GB (Colab) starczy do ~3B params
- Iteracja: pierwsze 2-3 próby zwykle dają student gorszy niż pre-distilled

**Werdykt:** Custom distillation tylko gdy żaden pre-distilled nie spełnia constraints (niche domain, niestandardowa modalność, requirement na konkretny rozmiar).

### Addendum: Fine-tuning (powiązane z Oś 4 ale nie surgery)

| Technika | Memory saved (training) | Quality loss | Effort | Lib/repo | Status |
|----------|-------------------------|--------------|--------|----------|--------|
| LoRA | 50x+ | <1% | Low | huggingface/peft | ✓ |
| QLoRA | 100x+ | 0-2% | Low-Medium | peft + bitsandbytes (Linux/WSL2) | ⚠️ Win |
| DoRA (newer) | ~LoRA | <1% | Low-Medium | peft (>=0.10) | ⚠️ |

**Definicyjnie:** Fine-tuning ≠ Architecture Surgery. Surgery zmienia strukturę, fine-tuning dostraja wagi.

### Decision tree:
- **Have time for Colab Free run?** → Distillation jest game-changer
- **Need exact same output?** → NIE pruning/distillation. Use offloading.
- **Multiple specialized tasks?** → Manual MoE routing
- **Fine-tuning na własnych danych?** → QLoRA na Colab, eksport do GGUF

### Anti-patterns:
- Distillation bez datasetu o podobnej dystrybucji — degradacja w polu, nie testach.
- Aggressive pruning >50% bez retraining — catastrophic.

### Composes well with:
- Quantization (Oś 1) — distilled + Q4 = ultra-light
- Hybrid compute (Oś 6) — distillation NA chmurze, deploy lokalnie

---

## OŚ 5 — PIPELINE TRICKS

**Filozofia:** Nie zmieniaj modelu — zmień jak go wywołujesz.
**VRAM impact:** 2-5x redukcja peak VRAM. **Quality cost:** 0-3%.

### Techniki

| Technika | VRAM peak ↓ | Latency cost | Kiedy stosować | Implementacja | Status |
|----------|-------------|--------------|----------------|---------------|--------|
| Tile-based processing | 2-10x peak | +overlap (10-30%) | CV na large images | manual chunking + blend | ✓ |
| Sliding window (audio) | 3-5x | +overlap (10%) | Whisper, audio | librosa + ChunkPipe | ✓ |
| Streaming/chunked LLM | 1x (RAM saved) | none | LLM long context | llama.cpp streaming | ✓ |
| Prefetching async | 0% VRAM | -20-40% wall time | I/O-bound | torch.utils.data + workers | ✓ |
| Caching (vector DB) | 0-100% (gdy hit) | µs vs s | High-recurrence input | FAISS, Chroma, Qdrant | ✓ |
| Progressive resolution | 5-20x peak | none (smarter) | CV high-res | manual: detect→focus | ⚠️ |
| Two-speed pipeline | n/a | UX win | User-facing apps | async queue | ⚠️ |
| Embedding-based RAG | huge | none | Q&A, search | sentence-transformers + FAISS | ✓ |

### Decision tree:
- **Image >1024×1024 i model >500MB?** → Tile-based (512×512 + 64px overlap)
- **Audio >30s i Whisper?** → Sliding window 30s + 5s overlap
- **Frequent repeated inputs?** → Vector cache
- **User wants instant feedback ALE pełna jakość?** → Two-speed pipeline (light → heavy async)

### Anti-patterns:
- Tile-based bez overlap — VIDOCZNE szwy/seams.
- Caching bez TTL/eviction — disk full.
- Progressive resolution bez detekcji — robi 2x pracy.

### Composes well with:
- Compilation (Oś 3) — kompilowany pipeline z tilingiem = pure win
- Hybrid compute (Oś 6) — heavy batch path → chmura

---

## OŚ 6 — HYBRID COMPUTE

**Filozofia:** Niektóre zadania robisz raz (training, distillation, dataset prep) — używaj darmowych chmur. Runtime pozostaje lokalny.

### Build-time platforms

| Platform | GPU | Czas/sesja | Limit/tydzień | Idealne do | Status |
|----------|-----|-----------|---------------|------------|--------|
| Google Colab Free | T4 zwykle (15GB) | 3-12h dynamic | ~10-20h praktycznie | Fine-tuning LoRA, prototypowanie | ✓ |
| Google Colab Pro ($10/mc) | A100 (40GB) sometimes | 24h | unlimited | Heavy distillation | ⚠️ |
| Kaggle Notebooks | P100/T4 (16GB) | 9h | 30h teoret. | Training, dataset | ✓ |
| HuggingFace Spaces (CPU) | CPU only (free) | unlimited | n/a | Demo deployment | ✓ |
| HuggingFace Spaces (GPU paid) | T4/A10G | unlimited | $$/h | Demo dla portfolio | ⚠️ |
| Modal Labs (free $30/mc) | T4/A100 on-demand | per-call | $30 free | One-shot processing | ⚠️ |
| Replicate | various | per-call | pay-as-you-go | API replacement | ⚠️ |

⚠️ **Realizm Colab Free:** Limity dynamiczne. W praktyce możesz dostać 3h/dzień zamiast 12h, lub T4 niedostępny. Dla build-time critical path → Colab Pro lub Kaggle. **Zawsze checkpointuj co 15-30 min** (F9).

### Browser-side compute

| Tech | Idealne do | Lib | Status |
|------|-----------|-----|--------|
| WebGPU + ONNX Runtime Web | CV inference w przeglądarce | onnxruntime-web | ⚠️ |
| transformers.js | LLM/embedding w przeglądarce | xenova/transformers.js | ⚠️ |
| WebLLM | LLM 7B in browser | mlc-ai/web-llm | ⚠️ |
| TensorFlow.js | CV/audio w przeglądarce | tensorflow/tfjs | ✓ |

### Patterns

- **Distill-then-Deploy:** trenuj na Colab → ONNX → lokalne ONNX Runtime
- **One-shot Dataset Build:** Kaggle/Colab → S3 (R2/B2 free) → download lokalnie
- **Browser Demo:** desktop + browser version (jedno repo, dwa runtime'y)

### Build-time fallback rule

Każdy build-time task musi mieć defined fallback:
- Resume-able od ostatniego checkpoint (zapisuj co 30 min do GDrive/HF Hub)
- Jeśli chmura padnie → CPU local fallback
- Jeśli CPU local nieosiągalny → degraded MVP path (gorszy model)

### Output Planning Rule (dla build-time chmury)

- Artefakt FP16 musi zmieścić się w lokalnym RAM (32GB) i dysku
- Reguła kciuka: artefakt po distillation ≤25% oryginału (np. SDXL 6.5GB → 1.6GB max)
- Jeśli artefakt FP16 >26GB → on-cloud quantization PRZED downloadem
- Jeśli wciąż >5GB → rozważ czy projekt właściwie scoped

### Anti-patterns:
- Runtime od chmury (production stale connected) — łamie filozofię "lokalny laptop"
- Free-tier dla long-running services — szybko hit limits

---

## OŚ 7 — RUNTIME ENGINES

**Filozofia:** PyTorch eager nie jest produkcyjnym runtime. Wybierz engine pasujący do typu deploymentu.
**VRAM impact:** 0-30% redukcja. **Speed impact:** 1.5-5x.

### Engines

| Engine | Speed | VRAM ↓ | Cross-platform | Use case | Lib/repo | Status |
|--------|-------|---------|---------------|----------|----------|--------|
| ONNX Runtime + CUDA EP | 2-3x | 1.2x | NVIDIA | Default dla CV na NVIDII | onnxruntime-gpu | ✓ |
| ONNX Runtime + DirectML EP | 1.5-2x | 1.2x | Cross-vendor (DX12) | Portability claim, traci 20-40% perf vs CUDA EP | onnxruntime-directml | ⚠️ |
| ONNX Runtime (CPU default) | 1.5x | 1.2x | YES (Win/Linux/Mac/iOS/Android) | CPU fallback | microsoft/onnxruntime | ✓ |
| OpenVINO | 2-4x (CPU+iGPU) | 1.5x | Intel CPUs | i5-12500H zoptymalizowany | openvinotoolkit | ⚠️ |
| TensorRT | 3-5x | 1.5x | NVIDIA only, **arch-specific** (F11) | Real-time inference | NVIDIA/TensorRT | ⚠️ |
| llama.cpp | n/a (LLM) | 4-5x (z GGUF) | Wszędzie | LLM lokalne | ggerganov/llama.cpp | ✓ |
| whisper.cpp | n/a (ASR) | 4-5x | Wszędzie | Audio transcription | ggerganov/whisper.cpp | ✓ |
| stable-diffusion.cpp | n/a (Diffusion) | 4-5x | Wszędzie | Diffusion bez Pythona | leejet/stable-diffusion.cpp | ⚠️ |
| MLC-LLM | n/a (LLM) | 3-4x | iOS/Android/Web/Desktop | Cross-platform LLM | mlc-ai/mlc-llm | ⚠️ |
| vLLM | n/a (LLM serving) | 0% | Linux | LLM batching server | vllm-project/vllm | ❌ Linux only |
| NCNN | 1.5-2x | 1.5x | Mobile-first | Edge/mobile CV | Tencent/ncnn | ⚠️ |
| MNN | 1.5-2x | 1.5x | Mobile-first | Edge/mobile CV | alibaba/MNN | ⚠️ |

### Decision tree (Windows 11 + RTX 3050 + Intel iGPU):
- **CV model PyTorch, max performance?** → ONNX Runtime + **CUDA EP** (~2x szybszy niż DirectML)
- **CV model z portability claim?** → ONNX Runtime + **DirectML EP** (cross-vendor, traci 20-40%)
- **CV model na CPU/iGPU?** → **OpenVINO**
- **LLM lokalnie?** → llama.cpp + GGUF Q4_K_M
- **Audio (Whisper)?** → whisper.cpp (10x szybsze niż transformers Whisper)
- **Diffusion?** → diffusers + ONNX export lub stable-diffusion.cpp (extreme push)
- **Real-time?** → TensorRT (lock-in F11)

### Anti-patterns:
- TensorRT dla portable apps — non-portable, build-on-target wymagany (F11).
- vLLM dla single-user desktop — over-engineering, llama.cpp wystarczy. Dodatkowo Linux only.
- llama.cpp dla CV models — NIE jest CV runtime.

### Composes well with:
- Quantization (Oś 1) — ONNX Runtime + INT8 = 2-3x speed combined
- Compilation (Oś 3) — ONNX export to forma kompilacji

---

## COMPOSABILITY MATRIX

| ↓Oś A vs Oś B → | Quant | Offload | Compile | Surgery | Pipeline | Hybrid | Runtime |
|------------------|-------|---------|---------|---------|----------|--------|---------|
| Quantization | — | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️* |
| Offloading | ⚠️ | — | ❌ default torch.compile** | ⚠️ | ⚠️ | ⚠️ | ❌ TensorRT |
| Compilation | ⚠️ | ❌ default | — | ⚠️ | ⚠️ | ⚠️ | ✓ ONNX = compile |
| Surgery | ⚠️ | ⚠️ | ⚠️ | — | ⚠️ | ⚠️ idealne | ⚠️ |
| Pipeline tricks | ⚠️ | ⚠️ | ⚠️ | ⚠️ | — | ⚠️ | ⚠️ |
| Hybrid compute | ⚠️ | ⚠️ | ⚠️ | ⚠️ idealne | ⚠️ | — | ⚠️ |
| Runtime engines | ⚠️* | ❌ TensorRT | ✓ | ⚠️ | ⚠️ | ⚠️ | — |

\* TensorRT akceptuje INT8 calibration. ONNX Runtime akceptuje INT8 dynamic. llama.cpp ZAKŁADA GGUF.

\** Offload + torch.compile w trybie domyślnym ma znane problemy z device_map="auto" — zmień na `mode="reduce-overhead"` lub używaj `accelerate.disk_offload`.

---

## FAILURE MODES

### F1 — PCIe bottleneck przy AirLLM
**Symptom:** Model ładuje się OK, inferencja 50-100x wolniejsza.
**Przyczyna:** PCIe 4.0 x4 (laptop NVMe) ~7GB/s. Model 7GB layer-by-layer = 7s minimum/call.
**Mitygacja:** Real-time → distillation (Oś 4) + quantization (Oś 1).

### F2 — Fragmentacja VRAM
**Symptom:** Mieści się na 1. iter, OOM na 4.
**Przyczyna:** PyTorch caching allocator nie defragmentuje.
**Mitygacja:** `torch.cuda.empty_cache()` po iteracji. Stałe shape'y (padding inputs).

### F3 — torch.compile recompilation hell
**Symptom:** Każda inferencja z innym shape'em: 30s warmup.
**Przyczyna:** Dynamic shapes triggerują recompilation.
**Mitygacja:** `torch.compile(dynamic=True)` (PyTorch 2.1+) lub pad inputs do bucket sizes.

### F4 — INT8/Q4 degradacja na edge cases
**Symptom:** Benchmarks 95%, własne dane 70%.
**Przyczyna:** Calibration dataset nie reprezentował dystrybucji input'ów.
**Mitygacja:** Calibruj na własnych danych. Nie ufaj "default INT8 calibration".

### F5 — DirectML vs CUDA mismatch (Windows)
**Symptom:** Torch w CUDA, ONNX w DirectML — łączne zużycie 2x większe.
**Przyczyna:** Dwa runtime'y nie współdzielą GPU memory pool.
**Mitygacja:** Wybierz JEDEN runtime per pipeline. RUNTIME ISOLATION RULE w Oś 0.

### F6 — Sequential CPU offload kills batch
**Symptom:** `enable_sequential_cpu_offload()` OK dla batch=1, batch=4 trwa 8x dłużej.
**Przyczyna:** Każdy batch element wymaga przeładowania weights.
**Mitygacja:** Dla batch processing użyj `enable_model_cpu_offload()` zamiast sequential.

### F7 — Distillation bez retraining VAE/scheduler
**Symptom:** Distilled UNet działa, ale outputy diffusion zniekształcone.
**Przyczyna:** Distillation tylko UNet, VAE/scheduler nie były tunowane.
**Mitygacja:** Distill całość lub używaj pre-distilled checkpoints (LCM, Turbo).

### F8 — Vector cache blow-up
**Symptom:** Cache działa świetnie, po 2 tygodniach disk full.
**Przyczyna:** Brak eviction policy.
**Mitygacja:** TTL + LRU eviction. Maksymalny rozmiar cache.

### F9 — Colab session timeout w środku distillation
**Symptom:** 8h trening, sesja zerwana w 7h, 0 checkpoint.
**Przyczyna:** Brak intermittent saves do GDrive/HF Hub.
**Mitygacja:** Save co 30min do GDrive. Notebook musi być resume-able.

### F10 — Build-time → runtime gap
**Symptom:** Distillation na Colab z PyTorch 2.3, deployment lokalnie z 2.1 — `RuntimeError: operator not implemented`.
**Przyczyna:** Drift versions.
**Mitygacja:** ZAWSZE eksportuj do ONNX/safetensors. NIGDY `.pt` files cross-environment.

### F11 — TensorRT cross-architecture incompatibility
**Symptom:** Silnik z RTX 3050 (Ampere) nie odpala się na RTX 4070 (Ada).
**Przyczyna:** TensorRT generuje silnik zoptymalizowany pod konkretną mikroarchitekturę GPU (compute capability).
**Mitygacja:** **Build-on-target rule**:
- Wysyłaj ONNX (portable) zamiast .engine
- Kompiluj silnik przy pierwszym uruchomieniu (5-30 min warmup)
- LUB pre-built engines dla popularnych GPU

**Alternatywa:** ONNX Runtime + CUDA EP — portable, mniejszy lock-in, wolniejszy ~30%.

### F12 — Driver/DLL Conflict (Windows)
**Symptom:** `OSError: [WinError 126] Module not found` lub `cuDNN not found` przy `import torch`.
**Przyczyna na Windows:**
- Multiple CUDA toolkits side-by-side → wrong PATH
- cuDNN nie skopiowane do CUDA folder
- Brakujące MSVC Redist
- Mismatch torch wheel CUDA version vs system CUDA

**Mitygacja:**
1. Single source of truth: `nvidia-smi` (driver), `nvcc --version` (toolkit)
2. Pin `torch==2.3.0+cu121` zamiast `torch>=2.0`
3. ONNX Runtime z CUDA — zwykle lepiej **NIE** instalować osobnego CUDA toolkit (ORT ma własny libcuda od 1.18+)
4. Test: `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`

---

## TIER SELECTION DECISION TREE

```
┌─ Czy projekt ma komponent AI/ML?
│   ├─ NIE → katalog nie aplikuje
│   └─ TAK → idź dalej
│
├─ Oszacuj największy model w FP16 → przypisz tier:
│
│   Model <1GB FP16 → MVP TIER (1 oś rozważona)
│      • Tylko Oś 1 (FP16) + Oś 7 (Runtime engine)
│      • Skip Offloading, Surgery, Hybrid (overkill)
│      • Single-variant PoC wystarczy
│
│   Model 1-4GB FP16 → BALANCED TIER (2 osie)
│      • Oś 1 (FP16/FP32 lub Q5_K_M jeśli LLM)
│      • Oś 7 (ONNX Runtime z odpowiednim EP)
│      • Single-variant PoC (baseline w 60% VRAM)
│
│   Model 4-10GB FP16 → PUSH TIER (3 osie)
│      • Oś 1 (Q4_K_M lub INT8) — must
│      • Oś 2 (Offloading dla diffusion / device_map dla LLM)
│      • Oś 7 (CUDA EP / llama.cpp)
│      • Dual-variant PoC (baseline + optimized)
│
│   Model >10GB FP16 → EXTREME TIER (4+ osie)
│      • Pełna eksploracja katalogu
│      • Pre-distilled checkpoint hunt PRIORITY 1
│      • Build-time cloud OK (Colab + checkpointing)
│      • Akceptuj: 5-50x latency overhead
│
└─ Sanity check: "Minimum sufficient, no more"
      ├─ Z mniejszą liczbą technik osiągnę >15% headroom?
      ├─ TAK → uprość, usuń ostatnio dodaną
      └─ NIE → continue
```

---

## QUICK REFERENCE — TYPOWE STACKI

### Stack: Lokalna aplikacja desktopowa CV
- Oś 1: FP16 dla CV, INT8 dla ONNX export
- Oś 3: ONNX export
- Oś 5: Tile-based dla dużych obrazów
- Oś 7: ONNX Runtime + CUDA EP
- Build-time: pre-distilled hunt; jeśli brak — distillation na Colab

### Stack: Lokalna aplikacja LLM-powered
- Oś 1: GGUF Q5_K_M (mid) lub Q4_K_M (must-fit)
- Oś 7: llama.cpp jako runtime
- Oś 4: LoRA fine-tune na własnych danych (Colab Free)
- Oś 5: Streaming output dla UX
- Oś 6: HF Hub jako artifact storage

### Stack: Diffusion-powered desktop app
- Oś 1: BF16 (NIE Q4 PyTorch native — artifacting)
- Oś 2: diffusers `enable_sequential_cpu_offload()` + `enable_attention_slicing()` + `enable_vae_tiling()`
- Oś 4: Pre-distilled checkpoint (LCM-LoRA, SDXL Turbo, SDXL Lightning)
- Oś 5: Two-speed pipeline
- Oś 7: ONNX export jeśli możliwe

### Stack: Audio app (Whisper)
- Oś 1: Q5_K_M GGUF (whisper.cpp)
- Oś 4: Distil-Whisper Large v3 jako pre-distilled (~750MB vs 3GB)
- Oś 5: Sliding window 30s
- Oś 7: whisper.cpp (10x szybsze niż transformers)
- Oś 6: Browser version (transformers.js) jako bonus

### Stack: Vision Pipeline (multi-model)
- Oś 1: ONNX z INT8 quantization per model
- Oś 4: Pre-distilled checkpoint per model
- Oś 5: Progressive resolution (256→512→1024 dla regions of interest)
- Oś 5: Vector cache dla precomputed regions
- Oś 7: ONNX Runtime + CUDA EP, jeden runtime dla wszystkich (uniknięcie F5)

---

## KIEDY KATALOG NIE APLIKUJE

- Projekt bez komponentu AI/ML (tooling deweloperski, gra bez ML, blog)
- Projekt CPU-bound bez ML (data crunching pandas, statystyka)
- Projekt I/O-bound bez ML (ETL, web scraper)
- Projekty MICRO/SMALL z workflow

W tych przypadkach katalog nie wnosi wartości — pomiń sekcje o nim w workflow.
