# WORKFLOW — Nowy Projekt

Ściąga krok po kroku. Otwierasz ten plik za każdym razem, gdy startujesz nowy projekt.

---

## SPIS TREŚCI

1. [Krok 1: Sklasyfikuj projekt (5 min)](#krok-1)
2. [Krok 2: Wypełnij SEED_IDEA.md (15 min)](#krok-2)
3. [Krok 3: Cross-review pomysłów (45 min)](#krok-3)
4. [Krok 4: DECISION_PROMPT (60 min)](#krok-4)
5. [Krok 5: PROJECT_BRIEF (30 min)](#krok-5)
6. [Krok 6: PoC na sprzęcie (30 min)](#krok-6)
7. [Krok 7: Cross-review briefu (60 min)](#krok-7)
8. [Krok 8: Setup w Claude Code (30 min)](#krok-8)
9. [Krok 9: Codzienna praca](#krok-9)

**Załączniki:**
- [A. Szablon SEED_IDEA.md](#a-szablon-seed_ideamd)
- [B. Szablon DECISION_PROMPT](#b-szablon-decision_prompt)
- [C. System sesji Claude Code](#c-system-sesji-claude-code)
- [D. Skrypty testowe](#d-skrypty-testowe)

---

## KROK 1 — Sklasyfikuj projekt {#krok-1}

Przed czymkolwiek innym odpowiedz: jak duży jest ten projekt? Workflow jest skalowalny — dla małych projektów większość kroków pomijasz.

| Wymiar | MICRO | SMALL | MEDIUM | LARGE |
|--------|-------|-------|--------|-------|
| Czas (solo) | <1 dzień | 2-5 dni | 1-2 tyg | 3+ tyg |
| Liczba plików | <5 | 5-15 | 15-40 | 40+ |
| Komponent AI/ML | brak | opcjonalny | tak | kluczowy |
| Cel | tool dla siebie | self-tool | portfolio kandydat | portfolio centralny |
| Dystrybucja | tylko ja | tylko ja | GitHub | GitHub + showcase |

**Zasada:** dominanta z 5 wymiarów. 4/5 wskazuje SMALL → projekt jest SMALL.

**Co robisz na podstawie tier-u:**

| Tier | Co wykonujesz |
|------|---------------|
| **MICRO** | Nic. Po prostu napisz kod. Workflow nie jest dla tego skali. |
| **SMALL** | Przeskocz do **Kroku 8** (Setup Claude Code). Pomiń SEED_IDEA, cross-review, brief. Napisz tylko 2-paragraph README. |
| **MEDIUM** | Wykonujesz: 2 → 4 → 5 → 6 → 7 (z 2 LLM-ami) → 8 → 9. **Pomijasz** Krok 3 (cross-review pomysłów). |
| **LARGE** | Wszystkie 9 kroków bez skrótów. |

**Reklasyfikacja jest legalna.** Jeśli MICRO rośnie w SMALL — dodaj Krok 8 retroactive. Jeśli MEDIUM puchnie do LARGE — wracaj do Kroku 2 zrobić retroactive SEED_IDEA. Jedyne czego nie robisz retroactive: Krok 3 (cross-review pomysłów dla projektu, który już wybrałeś, jest kabaretem).

---

## KROK 2 — SEED_IDEA.md {#krok-2}

Stwórz plik `SEED_IDEA.md` w folderze workflow projektu według **Szablonu A** (na końcu dokumentu). To jest tłumaczenie tego, co masz w głowie, na format, który LLM-y zrozumieją bez wymyślania własnych założeń.

**Najważniejsza decyzja w SEED_IDEA:** sekcja 6.2 (Priorytet — Portfolio-value vs Self-value). Bez tego LLM-y domyślnie wybierają portfolio i optymalizują UI/wow-factor kosztem narzędziowości.

**Drugi filtr:** sekcja 5 (Anti-goals). Bez tego dostaniesz "kolejny chatbot" / "kolejny dashboard".

**Klasyfikacja dojrzałości zalążka (L1-L4):**
- **L1 — TEMAT:** masz tylko domenę. *"Pomysły na klonowanie głosu jako lektora."*
- **L2 — KIERUNEK:** koncepcja produktowa + preferencje. *"Program do upscalingu zdjęć z AI."*
- **L3 — KONCEPCJA:** pełna wizja + linki/API. *"Algorytmy kwantowe + AI w analizie DNA z baz X, Y, Z."*
- **L4 — HIPOTEZA:** koncepcja + hipotezy architektoniczne. *"Desktop AI app (CustomTkinter) + CLIP + VGG19 do mozaik."*

Poziom określa wariant promptu w Kroku 3.

---

## KROK 3 — Cross-review pomysłów {#krok-3}

(Tylko LARGE. MEDIUM pomija.)

### 3A. Wyślij prompt do każdego LLM-a

Załącz `SEED_IDEA.md` + `HARDWARE_PUSH_CATALOG.md`. Wybierz wariant promptu zależny od poziomu dojrzałości zalążka.

**Wspólny fragment (do każdego wariantu):**

```
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
```

**Wariant L1 — TEMAT:** dodaj: *"Zaproponuj 4 oryginalne pomysły, każdy reprezentujący INNY kierunek. Minimum jeden poza ekosystemem Python+AI. Minimum jeden łączący domenę z inną."*

**Wariant L2 — KIERUNEK:** dodaj: *"Zaproponuj 4 warianty wzmacniające mój kierunek. Nie zmieniaj tematu — zmień kąt podejścia. Minimum jeden wariant bardziej ambitny, minimum jeden bardziej minimalistyczny ale z mocniejszym USP."*

**Wariant L3 — KONCEPCJA:** dodaj: *"Zaproponuj 3 alternatywne ujęcia mojej koncepcji + 1 śmiałe przemyślenie od nowa. Oceń źródła/API z SEED_IDEA — pasują czy potrzebne lepsze?"*

**Wariant L4 — HIPOTEZA:** dodaj: *"Podważ moją hipotezę. Format: [Krytyka merytoryczna] → [2 alternatywy] → [1 hybryda] → [Odpowiedzi na otwarte pytania]."*

### 3B. Selekcja w Claude.ai (nowa sesja)

Załącz `SEED_IDEA.md`, `HARDWARE_PUSH_CATALOG.md` i wszystkie odpowiedzi LLM-ów. Dwa kroki, nie jeden masowy prompt:

**Prompt A (selekcja):**

```
Załączam pomysły od [N] LLM-ów (poziom L[1/2/3/4]). Sam też
zaproponuj swoje propozycje wg tego samego promptu.

Krok A:
1. KATALOG: tabela wszystkich pomysłów (nazwa, źródło, pitch, stack,
   trudność 1-5, zgodność z SEED_IDEA 1-5, Hardware Transcendence
   Tier 1-5, VRAM zgodny z 4GB TAK/GRANICA/NIE).
2. GRUPOWANIE: pogrupuj tematycznie, eliminuj duplikaty koncepcyjne
   i pomysły z Tier 1 (ignorujące hardware).
3. SELEKCJA: z każdej grupy wybierz najsilniejszego reprezentanta.
   Cel: 6-8 finalistów. Uzasadnij każdy wybór.

Czekaj na akceptację listy przed Krokiem B.
```

**Prompt B (po akceptacji):**

```
Lista [N] finalistów zaakceptowana. Teraz:
1. SWOT dla każdego finalisty (przez pryzmat SEED_IDEA, max 4
   zdania na element).
2. TOP 3 + 2 hybrydy. Dla każdego z 5 kandydatów:
   - Uzasadnienie wyboru
   - Scoring: oryginalność, wow-factor, wykonalność, portfolio,
     zgodność z SEED_IDEA (1-10 każdy)
   - Kluczowe ryzyko + plan mitygacji
3. Twoja rekomendacja nr 1 (decyzja należy do mnie).

Format: plik markdown do pobrania (SWOT_ANALYSIS.md).
```

**Output:** `SWOT_ANALYSIS.md` + wybrany pomysł.

---

## KROK 4 — DECISION_PROMPT {#krok-4}

Nowa sesja Claude.ai. Załącz `SEED_IDEA.md`, `SWOT_ANALYSIS.md` (jeśli LARGE), `HARDWARE_PUSH_CATALOG.md` oraz **Szablon B** (na końcu).

**Prompt:**

```
Załączam SEED_IDEA.md, SWOT_ANALYSIS.md (lub: pomysł wybrany
poniżej), HARDWARE_PUSH_CATALOG.md i szablon DECISION_PROMPT.

Wybrany pomysł: [WKLEJ Z SWOT lub OPISZ]

Zadanie:
1. Stwórz DECISION_PROMPT dla mojego projektu używając szablonu
   jako wzorca struktury.
2. Dostosuj sekcje do specyfiki — jeśli brak komponentu AI,
   pomiń sekcję 6.5 (Hardware Transcendence Strategy).
3. W każdej sekcji "Typ aplikacji" i "Stack" dodaj "Wariant D:
   Twój autorski pomysł" — zachęcaj do wykraczania poza moje
   oczekiwania.
4. Wszystkie anti-goals i preferencje z SEED_IDEA muszą być
   widoczne w DECISION_PROMPT.

Zasady dialogu:
- Dawaj WYBORY (2-4 opcje z pros/cons), nie jedną odpowiedź
- Bądź szczery o ryzykach
- Nie ograniczaj do Pythona
- Pytaj o zdanie po każdej sekcji
```

Przejdź przez każdą sekcję w dialogu. Po podjęciu wszystkich decyzji:

```
Wygeneruj kompletny DECISION_PROMPT_[nazwa-projektu].md
z wypełnionymi sekcjami na podstawie moich decyzji.
```

**Output:** `DECISION_PROMPT_[nazwa-projektu].md`

---

## KROK 5 — PROJECT_BRIEF {#krok-5}

**Nowa** sesja Claude.ai (czysty kontekst). Załącz `SEED_IDEA.md`, `DECISION_PROMPT_[nazwa].md`, `HARDWARE_PUSH_CATALOG.md`.

**Prompt:**

```
Rola: ekspert architektury, AI/ML, szerokiego spektrum stacków.
Specjalizujesz się w projektowaniu rozwiązań, które kreatywnie
wykorzystują dostępne zasoby sprzętowe.

Zadanie: stwórz PROJECT_BRIEF.md gotowy do przekazania Claude
Code CLI. Brief musi zawierać:

- Wizja i elevator pitch
- 10-Second Hook (konkretna scena pierwszego użycia)
- Stack technologiczny z uzasadnieniem każdego wyboru
- Architektura (struktura katalogów, moduły, przepływ danych)
- Pipeline przetwarzania (krok po kroku, z bibliotekami)
- Hardware Execution Policy:
  • VRAM/RAM/Disk budget (precyzyjnie, MB per etap)
  • Hardware Transcendence Stack (tabela: oś | technika | lib | impact)
  • Build-time tasks (jeśli są: zadanie | gdzie | output | fallback)
  • Runtime fallbacki kaskadowe (A → B → C)
  • Composability check (czy techniki nie kolidują)
- Roadmap: MVP → Portfolio-ready → Open-source-ready
- Ryzyka techniczne + plany mitygacji
- Szacunki czasowe per faza

Zasady:
- Konkretnie: nazwy bibliotek, wersje, rozmiary modeli
- Nie unikaj kontrowersyjnych wyborów (jeśli Rust > Python, mów)
- Proponuj ambitne, nie minimum
- Zweryfikuj spójność z anti-goals z SEED_IDEA

Format: gotowy markdown bez sekcji "do uzupełnienia".
```

**Output:** `PROJECT_BRIEF-1.md`

---

## KROK 6 — Core Risk PoC {#krok-6}

Cel: udowodnić na sprzęcie, że kluczowy element działa, zanim poświęcisz czas na cross-review briefu.

### 6A. Identyfikacja Core Risk

Przeczytaj brief i odpowiedz: *"Co jest jedną rzeczą, która jeśli nie zadziała, unieważnia cały plan?"*

Zwykle to: model AI ładowany do GPU, nieznane API/format danych, nowa biblioteka, kluczowy krok pipeline'u.

### 6B. Bramka: single-variant czy dual-variant?

| Estymowany VRAM baseline | Co robisz |
|--------------------------|-----------|
| <60% × 4096MB = <2458MB | **Single-variant** (klasyczny PoC, jedna pętla 3-iter na wybranej technice) |
| ≥2458MB | **Dual-variant** (baseline + optimized — kod poniżej) |

Bramka chroni przed enterprise-bloat dla małych modeli.

### 6C. Skrypt PoC (max 100 linii)

```python
# Wzorzec PoC dual-variant z unified measurement
import torch, time, subprocess

def gpu_mem_used():
    """Pomiar VRAM przez nvidia-smi — działa dla każdego runtime'u
    (PyTorch, ONNX Runtime, TensorRT)."""
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.used,memory.free,memory.total",
         "--format=csv,noheader,nounits"]).decode().strip()
    used, free, total = map(int, out.split(","))
    return {"used": used, "free": free, "total": total}

# WARIANT A: BASELINE (FP16, batch=1, naiwna implementacja)
print("=== BASELINE ===")
baseline_result, baseline_vram, baseline_time = "PENDING", 0, None
try:
    torch.cuda.empty_cache()
    model_a = load_model_naive()
    # Warmup
    with torch.no_grad():
        _ = model_a(make_input())
    torch.cuda.synchronize()

    times, vrams = [], []
    for i in range(3):
        torch.cuda.synchronize(); t1 = time.time()
        with torch.no_grad():
            _ = model_a(make_input())
        torch.cuda.synchronize()
        times.append(time.time() - t1)
        vrams.append(gpu_mem_used()["used"])

    baseline_vram = max(vrams)
    baseline_time = sum(times) / 3
    baseline_result = "SUCCESS"
    print(f"VRAM={baseline_vram}MB, time={baseline_time:.2f}s")
    del model_a; torch.cuda.empty_cache()
except torch.cuda.OutOfMemoryError:
    baseline_result = "OOM"
    print("❌ OOM")
    torch.cuda.empty_cache()

# WARIANT B: OPTIMIZED (technika z briefu)
print("\n=== OPTIMIZED ===")
opt_result, opt_vram, opt_time = "PENDING", 0, None
try:
    model_b = load_model_optimized()  # CPU offload + Q4 + torch.compile
    with torch.no_grad():
        _ = model_b(make_input())  # warmup
    torch.cuda.synchronize()

    times, vrams = [], []
    for i in range(3):
        torch.cuda.synchronize(); t1 = time.time()
        with torch.no_grad():
            _ = model_b(make_input())
        torch.cuda.synchronize()
        times.append(time.time() - t1)
        vrams.append(gpu_mem_used()["used"])

    opt_vram = max(vrams)
    opt_time = sum(times) / 3
    opt_result = "SUCCESS"
    print(f"VRAM={opt_vram}MB, time={opt_time:.2f}s")
except torch.cuda.OutOfMemoryError:
    opt_result = "OOM"
    print("❌ OOM")

# RAPORT
print(f"\n=== POROWNANIE ===")
if baseline_result == "SUCCESS" and opt_result == "SUCCESS":
    delta = baseline_vram - opt_vram
    ratio = baseline_time / opt_time
    margin = 4096 - opt_vram
    print(f"VRAM saved: {delta}MB | Speed: {ratio:.2f}x | Margin: {margin}MB")
    print("✅ Warto" if opt_vram < 3500 else "⚠️ Zbyt blisko granicy")
elif baseline_result == "OOM":
    print("✅ Optymalizacja KONIECZNA — baseline crashuje")
elif opt_result == "OOM":
    print("❌ Optymalizacja gorsza niż baseline — pivot")
```

### 6D. Decyzja

| Wynik | Akcja |
|-------|-------|
| ✅ Działa, VRAM stabilny | Idź do Kroku 7 |
| ⚠️ Działa, na granicy | Wróć do briefu, dodaj fallback (CPU offload, mniejszy model, tiling) |
| ❌ OOM | Wróć do briefu, zmień model/strategię. Nie cross-review niedziałającego planu. |

Dopisz do `PROJECT_BRIEF-1.md` na końcu sekcję `## PoC Results` z liczbami z obu wariantów. Daje LLM-om w Kroku 7 twarde dane zamiast spekulacji.

---

## KROK 7 — Cross-review briefu {#krok-7}

### 7A. Runda 1 — wyślij brief do LLM-ów

Liczba LLM-ów: MEDIUM tier = 2, LARGE = 3-5.

**Prompt do każdego:**

```
Krytyczny audyt PROJECT_BRIEF. Solo developer, RTX 3050 (4GB VRAM),
32GB RAM, Windows 11. Cel: portfolio + narzędzie.

Załączam też HARDWARE_PUSH_CATALOG.md jako referencję.

Stwórz raport:

1. BŁĘDY FAKTYCZNE (każdy zarzut z cytatem fragmentu briefu)
2. SŁABE PUNKTY ARCHITEKTURY (nieskalowalne, over/under-engineered)
3. LEPSZE ALTERNATYWY (dla każdego zarzutu konkretne rozwiązanie)
4. BRAKUJĄCE ELEMENTY
5. UX / 10-Second Hook (czy realistyczny, czy zrobi wrażenie)
6. RYZYKA (czy szacunki czasowe realistyczne)
7. AUDYT KATALOGU
   a) Czy zastosowano kompozycję spójną z katalogiem?
   b) Czy są techniki HEAVILY relevantne, ale niezastosowane?
   c) Czy są techniki zastosowane, ale niepasujące?
   d) Czy PoC Results uzasadniają dodaną złożoność?
   e) Failure modes z katalogu — które realnie zagrażają?
8. SOURCE VERIFICATION
   Dla twierdzeń o kompatybilności: link do docs/issue
   lub oznacz jako "⚠️ UNVERIFIED — needs PoC test"

Zasady:
- Nie chwal — szukaj problemów
- Każdy zarzut z konkretną alternatywą
- Każdy zarzut musi cytować fragment briefu (eliminuje halucynacje)
- Nie proponuj rozwiązań chmurowych dla RUNTIME (build-time OK)
- Nie proponuj rozwiązań wymagających zespołu
```

### 7B. Agregacja w Claude.ai

**Prompt:**

```
Załączam raporty od [N] LLM-ów audytujących PROJECT_BRIEF-1.md.

1. Dla każdego zarzutu wydaj werdykt:
   ✅ PRZYJMUJĘ + co to zmienia
   ❌ ODRZUCAM + kontr-argument techniczny
   🔄 MODYFIKUJĘ + własna modyfikacja
2. Stwórz PROJECT_BRIEF-2.md z przyjętymi zmianami.
3. Tabela transparentności: zmiana → źródło → uzasadnienie.

Zasady:
- Kierujesz się dobrem projektu, nie ego
- Jeśli LLM nie cytował fragmentu briefu — odrzuć ("zarzut bez cytowania")
- Nie odrzucaj na "obecne wystarczy" — wyjaśnij dlaczego LEPSZE
- Nie dodawaj rzeczy "fajnie by było"
```

**Output:** `PROJECT_BRIEF-2.md`

### 7C. Runda 2 + Pre-Flight Check (LARGE only)

Wyślij `PROJECT_BRIEF-2.md` do 2-3 najwartościowszych LLM-ów z Rundy 1:

```
Druga (ostatnia) runda. Skup się na:
1. Czy zmiany z R1 są spójne i nie tworzą konfliktów?
2. Czy coś źle zaimplementowane (np. zmieniono model,
   ale nie zaktualizowano VRAM budgetu)?
3. Czy szacunki czasowe nadal realistyczne po zmianach?

NIE powtarzaj zarzutów z R1. NIE proponuj fundamentalnych zmian.
Format: zwięzły raport (max 100 linii).
```

Równolegle, **Pre-Flight Check** do jednego LLM-a:

```
Wyobraź sobie, że jesteś agentem kodującym, który dostał ten brief
z instrukcją "zbuduj projekt".

Oceń:
1. Czy zacząłbyś generować strukturę BEZ zadawania pytań?
2. Gdzie musiałbyś zgadywać intencje?
3. Czy brakuje konfiguracji (wersje bibliotek, parametry, formaty)?
4. Czy instrukcje są spójne?
5. Build-time tasks readiness (proporcjonalnie):
   - ≤2 artefakty: link do notebooka + ścieżka + 1-line smoke test
   - ≥3 artefakty: + tabela artefaktów + procedura kolejności

Format: lista braków z priorytetem (krytyczne/ważne/kosmetyczne).
Max 50 linii.
```

Finalizacja w Claude.ai:

```
Załączam raporty R2 + Pre-Flight Check.

Stwórz PROJECT_BRIEF-3.md (FINALNY):
1. Rozpatrz uwagi R2 (✅/❌/🔄)
2. Uzupełnij braki z Pre-Flight Check
3. Brief ma być CZYSTY — bez historii zmian, bez "zmieniono X na Y"
4. Zachowaj sekcje PoC Results i 10-Second Hook
5. Format: gotowy dokument do wrzucenia obok CLAUDE.md
```

**Output:** `PROJECT_BRIEF-3.md` (finalna wersja)

---

## KROK 8 — Setup w Claude Code CLI {#krok-8}

### 8A. Struktura + brief

```powershell
mkdir D:\Programming_Projects\NazwaProjektu
cd D:\Programming_Projects\NazwaProjektu
cp PROJECT_BRIEF-3.md .\PROJECT_BRIEF.md  # (lub README dla SMALL)
```

### 8B. System sesji + skrypty testowe

Skopiuj z globalnego szablonu (jeśli masz):

```powershell
cp -r D:\_global\session-template\.claude .\
cp D:\_global\session-template\MEMORY.md .\
cp D:\_global\session-template\last_session.md .\
cp -r D:\_global\session-template\tests .\
cp D:\_global\HARDWARE_PUSH_CATALOG.md .\
```

Jeśli **nie masz globalnego szablonu** — załącznik C i D pokazują, co umieścić w `D:\_global\session-template\`. Robisz to **raz**, potem zawsze kopiujesz.

**Opcjonalnie — świadomy routing Opus/Sonnet w Claude Code:**

```powershell
cp -r D:\_global\model_routing\.claude\commands\* .\.claude\commands\
cp -r D:\_global\model_routing\.claude\agents\* .\.claude\agents\
cp D:\_global\model_routing\MODEL_ROUTING.md .\
```

Dodaj do `CLAUDE.md` fragment z `D:\_global\model_routing\CLAUDE_md_snippet.md`.
Szczegóły: `D:\_global\model_routing\README.md`.

### 8C. Git

```powershell
git init
git add .
git commit -m "chore: initial commit — project scaffold, session system, brief"
```

### 8D. Pre-flight environment test

```powershell
python tests/test_environment.py
```

Sprawdza CUDA, sterownik NVIDIA, konflikty backendów GPU, MSVC Redist (Windows). Jeśli widzisz `⚠️` lub `ERROR` — napraw zanim ruszysz dalej.

### 8E. Claude Code init

```powershell
claude
```

```
/start
```

Następnie:

```
Przeczytaj PROJECT_BRIEF.md (zaudytowany brief po cross-review,
z wynikami PoC).

Na podstawie briefu:
1. /init — rozbuduj CLAUDE.md o pełny kontekst projektu (hardware,
   konwencje, stack, zasady). Zachowaj sekcję "Pliki stanu sesji".
   Dodaj sekcję "Hardware Transcendence Stack" z briefu.
2. Stwórz strukturę katalogów zgodną z architekturą z briefu.
3. Pliki konfiguracyjne (pyproject.toml/package.json/Cargo.toml).
   Pin wersje krytycznych bibliotek.
4. scripts/smoke_test — importuje zależności, sprawdza GPU,
   wypisuje wersje.
5. Dostosuj tests/test_vram_invariants.py do projektu (fixtures
   load_pipeline, sample_input zgodnie z architekturą).
6. NIE generuj jeszcze kodu logiki. Pokaż strukturę + smoke_test
   i czekaj na potwierdzenie.
7. /save po zakończeniu.

Hardware (do CLAUDE.md):
- GPU: RTX 3050 — 4GB VRAM
- RAM: 32GB DDR4
- CPU: i5-12500H (12C/16T)
- Łączny budżet VRAM ≤3.5GB dla jednocześnie załadowanych modeli
- batch_size=1 jako default tam gdzie dotyczy
```

Po zatwierdzeniu — pierwszy commit kodu:

```powershell
git add . && git commit -m "feat: initial project structure"
```

---

## KROK 9 — Codzienna praca {#krok-9}

### Pełny dzień

```
PORANEK
$ claude
> /start          # zawsze pierwsza komenda
                  # raportuje: ostatnia sesja, następny krok, otwarte pytania

W TRAKCIE — po skończeniu podzadania
> /save           # checkpoint, kontynuujesz pracę

PO PRZERWIE
> /status         # tylko odczyt, przypomnienie

WIECZÓR
> /end            # zawsze przed zamknięciem
                  # zapisuje decyzje do MEMORY.md + precyzyjny next-step
```

### Komendy

| Komenda | Kiedy | Modyfikuje? |
|---------|-------|-------------|
| `/start` | pierwsza komenda sesji | NIE |
| `/save` | po podzadaniu, co 45-60 min | TAK (częściowy) |
| `/end` | przed zamknięciem | TAK (pełny) |
| `/status` | kiedykolwiek, bez ryzyka | NIE |
| `/direct` | mechaniczne transformacje (rename, format, sort imports) | TAK (przez narzędzia) |

### Reguły higieny

1. **Zawsze `/start` na początku, `/end` na końcu.** Bez tego tracisz precyzję następnego kroku.
2. **`/save` co 45-60 min.** Kilka godzin pracy bez `/save` to ryzyko utraty kontekstu (limit 5h Claude Pro).
3. **`last_session.md` jest zastępowany, `MEMORY.md` rośnie.** Nie edytuj `last_session.md` ręcznie.

### Wzorzec batchowania (oszczędność tokenów)

Zamiast 3 tur:
```
> dodaj type hints do auth.py
> dodaj docstrings
> uruchom testy
```

Jedna tura:
```
> Dla auth.py: (1) type hints, (2) docstrings, (3) pytest tests/test_auth.py.
> Raport po wszystkich trzech.
```

### Wzorzec adversarial review (dla decyzji architektonicznych)

```
Działaj w dwóch rolach dla [decyzji X]:

ROLA 1 (Architekt): zaproponuj rozwiązanie z uzasadnieniem.
ROLA 2 (Krytyk): znajdź 3 najpoważniejsze słabości.
ROLA 1 (Architekt): odpowiedz na zarzuty i wzmocnij.

Zacznij od Roli 1.
```

### VRAM Smoke Test

Po każdej zmianie kodu dotykającej model loading lub inference:

```powershell
pytest tests/test_vram_invariants.py -v
```

Test failuje → znajdź ostatnią zmianę w `git diff`, refactoruj **zanim** pójdziesz dalej.

### Awaryjna procedura — sesja urwana bez `/end`

```powershell
git status && git diff
git add . && git commit -m "wip: [co było robione], sesja urwana"
```

W nowej sesji:

```
Sesja poprzednia urwała się bez /end. Odczytaj last_session.md,
wykonaj `git status` + `git diff` i zapytaj mnie:
"Co był ostatni wykonany krok?" Dopiero potem zaktualizuj
last_session.md i wywołaj /save.
```

### Kiedy wrócić do claude.ai?

- Decyzje architektoniczne zmieniające direction projektu
- Nowy duży feature poza briefem
- Debug trudnego problemu (Claude Code nie ogarnia kontekstu)

Wklej: treść CLAUDE.md + MEMORY.md + last_session.md + opis problemu.

---

## A. Szablon SEED_IDEA.md

```markdown
# SEED IDEA — [nazwa robocza]

Tier projektu: [MEDIUM / LARGE]

## 1. Pomysł bazowy
[Napisz tak, jak naturalnie przekazałbyś LLM-owi.]

## 2. Poziom dojrzałości zalążka

Zaznacz dokładnie JEDEN. Jeśli wahasz się między dwoma — wybierz wyższy
i potraktuj brakujące elementy jako "do uzupełnienia w cross-review".
Pusty checkbox = LLM-y zgadują wariant promptu w Kroku 3 i dostajesz
niespójne odpowiedzi.

[ ] L1 — TEMAT (domena + ogólna funkcja)
[ ] L2 — KIERUNEK (koncepcja produktowa + preferencje technologiczne)
[ ] L3 — KONCEPCJA (pełna wizja + konkretne źródła/API/linki)
[ ] L4 — HIPOTEZA (koncepcja + min. 1 hipoteza architektoniczna do podważenia)

## 3. Co już wiem / mam

⚠️ **NIE wpisuj tu sekretów w plaintext.** Ten plik trafi do 6+ zewnętrznych
LLM-ów w cross-review. Zamiast klucza wpisz nazwę zmiennej w `.env`
(np. `LOTTO_API_KEY w .env`) lub link do panelu, gdzie klucz uzyskujesz.

- **Źródła/inspiracje:** linki, repozytoria, papers — **selekcjonowane**.
  Maks. 5-7 pozycji podzielonych na: (a) źródła danych, (b) techniki
  (papers/biblioteki), (c) anti-references (świadomie odrzucone, z
  1-zdaniowym uzasadnieniem). Lista 13+ surowych linków = LLM zignoruje
  większość.
- **API/datasety/klucze:** które mam / które muszę zdobyć (NAZWY zmiennych
  env, NIE wartości).
- **Wcześniejsze rozmowy z LLM-ami:** streszczenie + **Twoja ocena** każdej
  propozycji ("chcę spróbować" / "podchodzę krytycznie" / "tło"). Bez oceny
  LLM-y zgadują, czy traktujesz cudze pomysły jako kanon czy checkpoint.
- **Własne eksperymenty/PoC:** jeśli były.

## 4. Preferencje technologiczne

| Oś | Chcę spróbować | Wolę uniknąć |
|---|---|---|
| Język/runtime | [...] | [...] |
| Framework główny (ML / web / etc.) | [...] | [...] |
| UI / frontend | [...] | [...] |
| Paradygmat / podejście | [...] | [...] |

## 5. Anti-goals

### 5A. Projekt NIE ma być (kształt produktu)
- [np. "nie kolejny wrapper na API"]
- [np. "nie kolejny chatbot/dashboard"]
- [np. "nie SaaS z logowaniem"]

### 5B. LLM w cross-review NIE ma (zachowanie LLM-a)
- [np. "nie tłumaczyć podstaw, jeśli pytam o szczegóły"]
- [np. "nie pivotować mojego celu na bardziej standardowy temat"]
- [np. "nie ograniczać propozycji do Pythona"]

> Jeśli sekcja 5B jest pusta — usuń ją. Jeśli używasz, każdy punkt MUSI być
> uzasadniony w §1 lub §6 (inaczej cross-review uzna to za irracjonalne
> ograniczenie i je obejdzie).

## 6. Cel nadrzędny

### 6.1 Problem i odbiorcy
- Problem, który rozwiązuję: [jedno zdanie]
- Dla kogo to jest: [portfolio / narzędzie dla siebie / open-source]

### 6.2 Priorytet — WYMAGANE
[ ] PRIMARY: Portfolio-value (wow dla rekrutera, UI dopracowany)
[ ] PRIMARY: Self-value (realne narzędzie, którego użyję)
Drugi cel akceptuję o ile nie kosztuje >20% dodatkowego czasu.

### 6.3 Motywacja i zakres
- Co fascynuje: [decyduje o motywacji na 4+ tygodnie pracy]
- Scope czasowy: [tygodnie na MVP]
- Dystrybucja: [.exe / pip / repo / strona demo / plugin]

### 6.4 Definition of Done — metryki sukcesu (WYMAGANE dla MEDIUM/LARGE)

MVP zostanie uznane za **udane**, jeśli:
- [konkretne, mierzalne kryterium #1]
- [konkretne, mierzalne kryterium #2]
- [konkretne, mierzalne kryterium #3]

**Anti-success criterion:** [co musi się NIE wydarzyć, żeby projekt nie był
zfailowany, mimo że "wygląda jakby działał" — szczególnie ważne dla projektów
ML, gdzie overfitting udaje sukces].

> Bez tej sekcji cross-review nie umie ocenić, czy proponowana architektura
> "wystarczy". LLM-y domyślają się ambicji z §6.3 i każdy domyśli inaczej.

## 7. Otwarte pytania do cross-review

Ułóż 6-10 pytań pogrupowanych w 4 kategorie. Generyczne pytania = generyczne
odpowiedzi.

### 7A. O architekturę
- [pytania o wybór algorytmu/modelu/stack'u]

### 7B. O wykonalność na 4GB VRAM (lub realny bottleneck — patrz §10.1)
- [pytania o hardware budget, latency, throughput]

### 7C. O scope / dane
- [pytania o rozmiar datasetu, augmentację, czas potrzebny na MVP]

### 7D. O ryzyka portfolio / strategiczne
- [pytania nie-techniczne: jak to wypadnie u rekrutera, czy framing jest
  dobry, naming]

## 8. Zakres danych (jeśli projekt jest data-driven)

Pomiń całą sekcję, jeśli projekt nie korzysta z datasetu (np. proceduralny
generator, narzędzie systemowe, code linter).

- **Volume:** [konkretna liczba próbek — np. "500 obrazów / 1000 wierszy CSV
  / 10k tokenów"]
- **Format:** [JSON / CSV / parquet / images / audio / mixed]
- **Source:** [public dataset / własne / API / scraping]
- **Cleanliness:** [wysoka / wymaga preprocessing / surowa]
- **Update frequency:** [statyczne / co X / streaming]
- **Augmentation strategy:** [jaką augmentację planujesz i czy jest UCZCIWA
  — nie generuje sztucznego sygnału tam, gdzie go nie ma]
- **Licencja:** [czy mogę publikować dataset w repo / tylko link / nie mogę]

## 9. Hardware i środowisko

> Bazowy setup: patrz `HARDWARE_PUSH_CATALOG.md` (zawiera GPU/RAM/CPU/OS/
> narzędzia/preferencje kwantyzacji).
>
> Tu wpisuj **TYLKO deltę** względem bazowego setupu, jeśli ten projekt
> wymaga czegoś specyficznego.

- **Delta dla tego projektu:** [np. "dodatkowo: Docker Desktop dla X" /
  "drugi monitor jako requirement UX testu" / "brak — standardowy setup"]

## 10. Ambicje przekraczające sprzęt

### 10.1 Co jest realnym bottleneckiem tego projektu?

VRAM jest najczęstszym bottleneckiem dla LLM/diffusion projektów, ale nie
zawsze głównym. Wskaż **dokładnie jeden** główny:

[ ] VRAM (>2GB FP16 modeli ładowanych jednocześnie)
[ ] CPU compute (np. quantum simulators, heavy preprocessing, bez GPU
    acceleration)
[ ] System RAM (>16GB w pamięci, np. duże embeddings, in-memory datasets)
[ ] Disk I/O (large datasets, sequential offloading)
[ ] Inference latency (real-time interactivity required, np. <100ms)
[ ] Training time (np. >24h overnight unacceptable)
[ ] Dataset size (<10k samples — bottleneck statystyczny, nie sprzętowy)
[ ] API rate limits / koszt (zewnętrzne services)

Dla wybranego bottlenecku opisz:
- Konkretny komponent/krok pipeline'u, który go powoduje
- Aktualne szacunkowe wartości (np. "TFT na 1000 punktów = 5 min training
  na CPU")
- Czy katalog Hardware Push w ogóle adresuje ten bottleneck (jeśli nie —
  odnotuj)

### 10.2 Akceptowalny narzut czasowy
[ ] Real-time (<1s) — agresywna kompilacja + kwantyzacja
[ ] Near-real-time (1-10s) — model CPU offload OK
[ ] Batch (10s-10min) — sequential offload OK
[ ] Overnight — wszystko legalne (AirLLM-style, disk offload)

### 10.3 Build-time cloud allowed?
[ ] TAK — Colab/Kaggle do jednorazowych zadań (distillation, fine-tune)
[ ] NIE — wszystko lokalnie (powód: ...)

### 10.4 Quality-vs-VRAM trade-off
[ ] 0% — FP32 pełna precyzja (offloading must-have)
[ ] ~0-1% — FP16/BF16 mixed precision (standard)
[ ] 1-5% — Q8/Q5_K_M, INT8 dynamic
[ ] 5-15% — Q4_K_M, AWQ-4bit, distillation z pre-distilled
[ ] >15% — pivot do mniejszego modelu

### 10.5 Doświadczenia z technikami (opcjonalne)
**Pozytywne** (co działało):
[lub puste]

**Negatywne** (co odrzuciłem + powód):
[lub puste]

**Nie znam:** zostaw puste — NIE wpisuj nazw "ze słyszenia".

## 11. Reality Check (jeśli problem jest teoretycznie trudny)

Wypełnij TYLKO jeśli Twój projekt dotyka jednego z:
- problemów no-free-lunch (predykcja czystej losowości, perfekcyjne
  kompresje stratne)
- problemów NP-hard z wymaganą skalą (TSP na 10k punktów w real-time)
- limitów fizycznych (sub-pixel super-resolution z fundamentalnym noise
  floor)
- problemów otwartych w dziedzinie (AGI, P=NP, świadome AI)

Pomiń, jeśli projekt jest "po prostu inżynieria" (większość przypadków).

**Jeśli wypełniasz:**
- **Teoretyczny limit:** [co matematyka/fizyka mówi o górnym pułapie tego,
  co projekt może osiągnąć]
- **Co model **może** legitnie nauczyć się:** [konkretnie, w ramach limitu]
- **Co model **nie może** osiągnąć:** [otwarte zadeklarowanie, bez owijania
  w bawełnę]
- **Jak Definition of Done (§6.4) się do tego ma:** [czy DoD jest pod, na,
  czy nad limitem]

> Wypełnienie tego upfront wyprzedza ~50% zarzutów cross-review dla projektów
> "ambitnych w niemożliwy sposób" i pozwala LLM-om skupić się na inżynierii
> zamiast tłumaczeniu Ci niemożliwości.
```

---

## B. Szablon DECISION_PROMPT

```markdown
# DECISION PROMPT — [NAZWA PROJEKTU]

## SYSTEM CONTEXT

Jesteś moim AI Project Advisor.

### Zasady:
1. WYBORY (2-4 opcje z pros/cons), nie jedna odpowiedź
2. Szczerość o ryzykach
3. Portfolio-first
4. Pytaj po każdej sekcji
5. NIE ograniczaj się do Pythona
6. Proponuj kreatywne obejścia ograniczeń, nie poddawaj się im
7. Respektuj anti-goals z SEED_IDEA
8. Na końcu wygeneruj PROJECT_BRIEF.md

## HARDWARE
- GPU: RTX 3050 Laptop — 4GB VRAM
- RAM: 32GB DDR4
- CPU: i5-12500H (12C/16T)

## ŚRODOWISKO
- OS: Windows 11
- Narzędzia: Miniconda Python 3.10, Node.js, VS Code, Claude Code CLI

## POMYSŁ BAZOWY
[WYBRANY POMYSŁ + KLUCZOWY KONTEKST Z SEED_IDEA: anti-goals,
otwarte pytania, preferencje, cel nadrzędny]

## DECYZJE

### SEKCJA 1: Wizja i nazwa
3-4 nazwy + kierunki produktowe. Dla każdego: pitch, wow-factor, trudność (1-5).

### SEKCJA 2: Typ aplikacji
- Web App (SPA, PWA, SSR)
- Desktop (natywna, Electron, Tauri)
- CLI Tool / Pipeline
- Mobile (React Native, Flutter, PWA)
- Extension (browser, VS Code, plugin)
- Hybrid (CLI + dashboard, API + frontend)
- MCP Server / Plugin
- Wariant D: Twoja autorska propozycja

### SEKCJA 3: Stack technologiczny
Nie zakładaj Pythona z góry. Rozważ wydajność, czas developmentu solo,
ekosystem bibliotek, potencjał portfolio.

### SEKCJA 4: Frontend / UI
Od CLI z Rich/Textual, przez Gradio/Streamlit, po React/Vue/Svelte
z Three.js/D3/Mapbox.

### SEKCJA 5: 10-Second Hook
1. Co użytkownik widzi/robi przez pierwsze 10 sekund? (konkretna scena)
2. Główny element wizualnego "wow"?
3. Custom design system / assety potrzebne?
4. Konkretna biblioteka wizualna?

### SEKCJA 6: Pipeline danych / AI
Dla każdego kroku: czy potrzebny? jaki model/algorytm? VRAM? alternatywy?

### SEKCJA 6.5: Hardware Transcendence Strategy
Z HARDWARE_PUSH_CATALOG.md.

Krok 1: Klasyfikacja tier (MVP/Balanced/Push/Extreme) wg rozmiaru
największego modelu w FP16.

Krok 2: Identyfikacja relevantnych osi (1/2/3/4+ proporcjonalnie do tier).
Dla nie-relevantnych: "N/A — poza scope" w 3 słowach.

Krok 3: Deep analysis dla relevantnych osi:
- Konkretna technika/biblioteka
- Oczekiwany impact (VRAM/speed/quality)
- Composability check

Krok 4: Sanity check "minimum sufficient" — czy mogę z mniejszą
liczbą technik osiągnąć ten sam VRAM budget? Jeśli tak — uprość.

Krok 5: Pytanie kontrolne — czy któraś technika jest CIĘŻKO relevantna,
ale standardowo pomijana?

Następnie 2-3 kompozycje:
- MVP (najmniej, najszybciej): X + Y
- PORTFOLIO (kompromis): X + Y + Z
- AMBITNA (pełen push): W + X + Y + Z

Dla każdej: VRAM, czas do MVP, quality cost, failure modes,
build-time tasks.

### SEKCJA 7: Architektura danych
- Storage (filesystem, SQLite, PostgreSQL, vector DB?)
- Cache strategia
- Wersjonowanie danych (DVC?)

### SEKCJA 8: Strategia realizacji
- MVP (demo-ready) — co i kiedy?
- Portfolio-ready — co dodajemy?
- Open-source-ready — co potrzebne?

### SEKCJA 9: Ryzyka i wyróżniki
- Co może pójść nie tak?
- Jak wyróżnić się?
```

---

## C. System sesji Claude Code

Treść do umieszczenia raz w `D:\_global\session-template\`.

### `CLAUDE.md` (szablon — wzbogacany przez `/init` w Kroku 8E)

```markdown
# CLAUDE.md — [NAZWA PROJEKTU]

## Kontekst
- Projekt: [1 zdanie]
- Stack: [Python 3.10 / Node / Rust / etc.]
- Środowisko: Windows 11, Miniconda, VS Code
- Cel bieżący: [co chcę osiągnąć w tej fazie]

## Zasady pracy
- Zawsze sprawdzaj MEMORY.md przed decyzją architektoniczną
- /start na początku każdej sesji
- /end przed zamknięciem
- /save po skończeniu podzadania
- Po zmianie kodu dotykającej model loading/inference:
  pytest tests/test_vram_invariants.py
- Failure → znajdź zmianę w git diff, refactoruj zanim pójdziesz dalej

## Konwencje
- Nazewnictwo: [snake_case / camelCase]
- Język komentarzy: [polski / angielski]
- Styl commitów: conventional commits

## Pliki stanu sesji
- MEMORY.md       — długoterminowa pamięć (czytaj na /start, dopisuj na /end)
- last_session.md — stan ostatniej sesji (czytaj na /start, replace na /end)

## Sprzęt / Ograniczenia
- GPU: NVIDIA RTX 3050 Laptop — 4GB VRAM (jeden model jednocześnie, max 3.5GB)
- RAM: 32GB DDR4
- CPU: Intel i5-12500H (12C/16T)
- batch_size=1 jako default
- Łączny budżet VRAM ≤3.5GB dla jednocześnie załadowanych modeli/tensorów
- Driver NVIDIA: [wersja na początku — sprawdź `nvidia-smi`]

## Hardware Transcendence Stack (z PROJECT_BRIEF.md)

### Zaaplikowane techniki (per oś z katalogu):
- Quantization: [...]
- Offloading: [...]
- Compilation: [...]
- Architecture Surgery: [...]
- Pipeline Tricks: [...]
- Hybrid Compute: [...]
- Runtime Engines: [...]

### Composability invariants:
- Łączny VRAM ≤3.5GB jednocześnie
- torch.cuda.empty_cache() po inferencji
- RUNTIME ISOLATION RULE: jeden GPU backend per pipeline (CUDA *lub* DirectML)

### Build-time artefakty:
- [np. model_distilled.onnx (450MB) — Colab notebook]

### Fallback chain:
- Próba 1: [pełna optymalizacja] → 2: [degraded] → 3: [CPU-only]
```

### `MEMORY.md` (startowa pusta struktura)

```markdown
# MEMORY.md — Długoterminowa pamięć projektu

## Architektura
<!-- Decyzje architektoniczne, format: [YYYY-MM-DD] decyzja + uzasadnienie -->

## Hardware Transcendence Decisions
<!-- Decyzje optymalizacyjne. Format:
- [YYYY-MM-DD] Decyzja: [krótko]
  Powód: [dane z PoC, nie spekulacja]
  Wpływ: [co to zmienia]
-->

## Rozwiązane problemy
<!-- Gotowe rozwiązania, żeby nie szukać ponownie -->

## Aktywne TODO
<!-- Przeniesione z last_session.md gdy stają się długoterminowe -->

## Odrzucone podejścia
<!-- Co NIE działało i dlaczego -->

## Słownik projektu
<!-- Specyficzne terminy -->
```

### `last_session.md` (startowy)

```markdown
# last_session.md

## Data ostatniej sesji
[YYYY-MM-DD HH:MM]

## NASTĘPNY KROK
Pierwsza sesja projektu — przeczytaj PROJECT_BRIEF.md
i zainicjalizuj strukturę zgodnie z briefem.

## Co zostało zrobione w ostatniej sesji
(brak — pierwsza sesja)

## Co zostało do zrobienia
- [ ] Inicjalizacja (/init)
- [ ] Struktura katalogów
- [ ] Smoke test środowiska
- [ ] Pierwszy moduł

## Aktywne pliki
(brak)

## Otwarte pytania
(brak)
```

### `.claude/commands/start.md`

```markdown
# /start — Rozpoczęcie sesji

1. Odczytaj CLAUDE.md, MEMORY.md, last_session.md (nie modyfikuj).
2. Wyświetl raport:
   ✓ Projekt: [z CLAUDE.md]
   ✓ Ostatnia sesja: [z last_session.md]
   ▸ Następny krok: [sekcja NASTĘPNY KROK]
     Kontekst: [najważniejsza decyzja z MEMORY.md ostatniego tygodnia]
     Otwarte pytania: [jeśli niepuste]
   Czy zaczynamy od następnego kroku?
3. Czekaj na odpowiedź. NIE rozpoczynaj pracy automatycznie.
```

### `.claude/commands/save.md`

```markdown
# /save — Checkpoint w trakcie sesji

1. Aktualizuj last_session.md:
   - Dopisz do "Co zostało zrobione" co właśnie skończyłeś
   - Aktualizuj "Aktywne pliki"
2. Jeśli podjęto WAŻNĄ decyzję architektoniczną — dopisz do MEMORY.md
   (sekcja "Architektura" lub "Rozwiązane problemy").
3. Jeśli zmieniono technikę optymalizacji — dopisz do MEMORY.md
   (sekcja "Hardware Transcendence Decisions"):
   - [YYYY-MM-DD] Decyzja: [krótko]
     Powód: [dane z PoC]
     Wpływ: [co zmienia]
4. Potwierdź: "Checkpoint zapisany o [HH:MM]. Kontynuujemy."
```

### `.claude/commands/end.md`

```markdown
# /end — Zakończenie sesji

1. Odczytaj last_session.md i kontekst sesji.
2. Dopisz do MEMORY.md kluczowe decyzje:
   - Architektoniczne, optymalizacyjne, rozwiązania, odrzucone, terminy
3. Zastąp last_session.md w całości:
   - Data: [aktualna]
   - NASTĘPNY KROK: PRECYZYJNY (np. "Zaimplementować funkcję X
     w src/Y.py — input: ..., output: ...")
   - Co zrobiono, co do zrobienia, aktywne pliki, otwarte pytania
4. Potwierdź: "Sesja zapisana. Następny krok: [...]"
```

### `.claude/commands/status.md`

```markdown
# /status — Podgląd stanu

Odczytaj last_session.md i wyświetl:
- Następny krok
- Co do zrobienia
- Aktywne pliki
- Otwarte pytania

Nie modyfikuj plików.
```

### `.claude/commands/direct.md`

```markdown
# /direct — Mechaniczne transformacje

NIE generuj kodu — użyj narzędzi systemowych
(Bash/sed/ripgrep/black/ruff/prettier/isort).

Kiedy używać:
- Rename pliku/zmiennej w projekcie
- Formatowanie (black/ruff/prettier)
- Sortowanie importów (isort/ruff --select I)
- Usunięcie console.log/print debugowych
- Proste zamiany tekstowe

Procedura:
1. Zidentyfikuj narzędzie systemowe.
2. Pokaż komendę PRZED wykonaniem — czekaj na akceptację.
3. Wykonaj przez Bash, pokaż wynik.

Anti-usage:
- Refactor zmieniający semantykę → standardowe generowanie
- Nowe funkcje/moduły → zawsze generowanie
```

---

## D. Skrypty testowe

Treść do umieszczenia raz w `D:\_global\session-template\tests\`.

### `tests/test_environment.py`

```python
"""Pre-flight environment sanity check.
Uruchamiany jako pierwszy w smoke_test, przed any model loading.

Użycie: python tests/test_environment.py
"""
import sys, subprocess, importlib


def check_torch():
    try:
        import torch
        info = {"torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available()}
        if torch.cuda.is_available():
            info["cuda_version"] = torch.version.cuda
            info["gpu_name"] = torch.cuda.get_device_name(0)
            free, total = torch.cuda.mem_get_info()
            info["vram_total_mb"] = round(total / 1e6)
            info["vram_free_mb"] = round(free / 1e6)
            info["compute_capability"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
        return info
    except ImportError:
        return {"torch": "NOT_INSTALLED"}
    except Exception as e:
        return {"torch_error": str(e)}


def check_driver():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL).decode().strip()
        return {"driver_version": out}
    except FileNotFoundError:
        return {"driver_version": "nvidia-smi not found (nie-NVIDIA?)"}
    except Exception as e:
        return {"driver_error": str(e)}


def check_gpu_backends():
    backends = []
    for module_name, friendly in [("onnxruntime", "ONNX Runtime"),
                                    ("openvino", "OpenVINO"),
                                    ("tensorrt", "TensorRT")]:
        try:
            importlib.import_module(module_name)
            backends.append(friendly)
        except ImportError:
            pass
    return backends


def check_msvc_redist():
    if sys.platform != "win32":
        return {"platform": sys.platform, "msvc_check": "skipped"}
    try:
        import ctypes
        ctypes.WinDLL("vcruntime140.dll")
        return {"vcruntime140": "OK"}
    except OSError:
        return {"vcruntime140": "MISSING — zainstaluj MSVC Redist 2015-2022"}


def main():
    print("=" * 60)
    print("ENVIRONMENT SANITY REPORT")
    print("=" * 60)

    torch_info = check_torch()
    driver_info = check_driver()
    backends = check_gpu_backends()
    msvc_info = check_msvc_redist()

    print(f"\n[Python] {sys.version.split()[0]} on {sys.platform}")
    print("\n[PyTorch / CUDA]")
    for k, v in torch_info.items(): print(f"  {k}: {v}")
    print("\n[NVIDIA Driver]")
    for k, v in driver_info.items(): print(f"  {k}: {v}")
    print("\n[GPU Backends]")
    if not backends:
        print("  Brak (PyTorch CUDA jako jedyny)")
    else:
        for b in backends: print(f"  - {b}")
        if len(backends) > 1:
            print("\n  ⚠️ MULTI-BACKEND WARNING:")
            print("     RUNTIME ISOLATION RULE — jeden backend GPU per pipeline.")
    print("\n[MSVC]")
    for k, v in msvc_info.items(): print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    if isinstance(torch_info.get("cuda_available"), bool) and torch_info["cuda_available"]:
        vram = torch_info.get("vram_total_mb", 0)
        if vram < 4000: print("⚠️  VRAM <4GB — projekt MUSI używać tier MVP/Balanced")
        elif vram < 8000: print("✓  VRAM 4-8GB — Push tier dostępny z optymalizacjami")
        else: print("✓  VRAM >8GB — wszystkie tiery dostępne")
    else:
        print("ℹ️  CUDA niedostępne — projekt CPU-only lub reinstalacja torch")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### `tests/test_vram_invariants.py`

```python
"""VRAM invariant tests — uruchamiane po każdej zmianie kodu
dotykającej model loading lub inference.

Użycie: pytest tests/test_vram_invariants.py -v

Dostosuj fixtures load_pipeline i sample_input do projektu.
"""
import gc, pytest, torch

VRAM_BUDGET_MB = 3500
LEAK_THRESHOLD_MB = 50
WARMUP_ITERS = 1
TEST_ITERS = 3


@pytest.fixture
def load_pipeline():
    """Zwraca callable ładujący pełen pipeline projektu.
    Implementuj per projekt:
        from src.engine import MyPipeline
        return lambda: MyPipeline.load_optimized()
    """
    pytest.skip("Implement load_pipeline fixture")


@pytest.fixture
def sample_input():
    """Reprezentatywny input do pipeline'u (realistyczny rozmiar)."""
    pytest.skip("Implement sample_input fixture")


@pytest.fixture(autouse=True)
def cleanup_cuda():
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
    gc.collect()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
def test_pipeline_under_vram_budget(load_pipeline, sample_input):
    pipe = load_pipeline()
    for _ in range(WARMUP_ITERS):
        with torch.no_grad(): _ = pipe(sample_input)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()

    with torch.no_grad(): _ = pipe(sample_input)
    torch.cuda.synchronize()

    peak_mb = torch.cuda.max_memory_allocated() / 1e6
    reserved_mb = torch.cuda.max_memory_reserved() / 1e6
    print(f"\nPeak: {peak_mb:.0f}MB | Reserved: {reserved_mb:.0f}MB | "
          f"Frag: {reserved_mb - peak_mb:.0f}MB")

    assert peak_mb < VRAM_BUDGET_MB, (
        f"VRAM regression: peak {peak_mb:.0f}MB > budget {VRAM_BUDGET_MB}MB. "
        f"Sprawdź ostatnią zmianę kodu.")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
def test_no_vram_leak_over_iterations(load_pipeline, sample_input):
    pipe = load_pipeline()
    with torch.no_grad(): _ = pipe(sample_input)
    torch.cuda.synchronize()

    vrams = []
    for i in range(TEST_ITERS):
        with torch.no_grad(): _ = pipe(sample_input)
        torch.cuda.synchronize()
        vrams.append(torch.cuda.memory_allocated() / 1e6)

    delta = vrams[-1] - vrams[0]
    print(f"\nVRAM per iter: {[f'{v:.0f}MB' for v in vrams]} | Delta: {delta:+.0f}MB")

    assert delta < LEAK_THRESHOLD_MB, (
        f"VRAM leak: +{delta:.0f}MB across {TEST_ITERS} iterations. "
        f"Możliwe: brak `with torch.no_grad()`, akumulacja gradientów, "
        f"cache w forward, retained tensors w globalnych zmiennych.")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
def test_no_double_loaded_models(load_pipeline):
    pipe = load_pipeline()
    torch.cuda.synchronize()

    after_load_mb = torch.cuda.memory_allocated() / 1e6
    print(f"\nVRAM po załadowaniu: {after_load_mb:.0f}MB")

    threshold = VRAM_BUDGET_MB * 0.7
    assert after_load_mb < threshold, (
        f"Po załadowaniu pipeline VRAM = {after_load_mb:.0f}MB > {threshold:.0f}MB. "
        f"Czy ładujesz 2+ modele równolegle? Composability invariant z CLAUDE.md "
        f"wymaga sekwencyjnego ładowania.")
```
