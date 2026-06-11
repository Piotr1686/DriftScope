# Uniwersalny prompt setupowy — Claude Code Session System

> **Jak użyć w dowolnym projekcie:**
> 1. Otwórz Claude Code w katalogu projektu (np. `cd D:\Programming_Projects\Neural-Mosaic && claude`)
> 2. Wklej cały poniższy prompt (od `PROMPT START` do `PROMPT END`)
> 3. Claude Code sam wykryje nazwę projektu, stack, typ i wszystko skonfiguruje

---

```
===================================================================
PROMPT START — UNIWERSALNY SETUP SESSION SYSTEM
===================================================================

Zaimplementuj w bieżącym projekcie system zarządzania stanem sesji Claude Code. System ma zapewnić ciągłość kontekstu między sesjami przez 4 pliki (CLAUDE.md, MEMORY.md, last_session.md) oraz 4 komendy slash (/start, /save, /end, /status).

Wszystkie informacje o projekcie wykrywasz SAM — nie pytaj mnie o nazwę, stack ani strukturę. Jeśli czegoś nie potrafisz wykryć jednoznacznie, wstaw sensowny placeholder i oznacz go jako "[do uzupełnienia]".

═══════════════════════════════════════════════════════════════════
KROK 1 — AUTO-DETEKCJA PROJEKTU
═══════════════════════════════════════════════════════════════════

Zbierz następujące informacje samodzielnie:

1.1. NAZWA PROJEKTU
   → Ostatni segment aktualnej ścieżki roboczej (basename CWD).
     Przykład: "D:\Programming_Projects\Neural-Mosaic" → "Neural-Mosaic"

1.2. STACK TECHNOLOGICZNY (sprawdź w tej kolejności)
   - pyproject.toml / requirements.txt / environment.yml → Python
     · wyciągnij wersję Pythona i kluczowe biblioteki (top 5-8)
   - package.json → Node.js / JavaScript / TypeScript
     · wyciągnij framework (React / Next / Vue / Express) i kluczowe deps
   - Cargo.toml → Rust
   - go.mod → Go
   - pom.xml / build.gradle → Java / Kotlin
   - *.csproj / *.sln → C# / .NET
   - Jeśli żadnego z tych plików nie ma → sprawdź rozszerzenia najczęstszych
     plików w src/ lub root i wywnioskuj stack z nich

1.3. TYP PROJEKTU (heurystyki)
   - Zawiera tkinter, customtkinter, PyQt, PySide, electron → Desktop App
   - Zawiera flask, fastapi, django, express, next → Web Backend/App
   - Zawiera torch, transformers, sklearn, tensorflow → AI/ML
   - Zawiera click, typer, argparse jako główny entry point → CLI Tool
   - Zawiera setup.py z "library" lub samo pyproject.toml bez entry → Library
   - W innym wypadku → "General Project"

1.4. CEL PROJEKTU (z README jeśli istnieje)
   - Szukaj README.md / README.rst / README.txt
   - Jeśli istnieje → wyciągnij pierwszy akapit opisowy (zwykle pod tytułem)
   - Jeśli nie istnieje → "[do uzupełnienia — brak README]"

1.5. STRUKTURA KATALOGÓW
   - Zrób krótką listę top-level katalogów (bez node_modules, __pycache__, .git, venv itp.)

1.6. STATUS GIT
   - Czy istnieje katalog .git? (tak/nie)
   - Czy istnieje plik .gitignore? (tak/nie)

1.7. ISTNIEJĄCE PLIKI SYSTEMU SESJI (ostrożnie!)
   - Sprawdź czy już istnieją: CLAUDE.md, MEMORY.md, last_session.md, .claude/commands/
   - Jeśli którykolwiek istnieje → zrób backup z suffixem `.backup_<timestamp>`
   - NIGDY nie nadpisuj bez backupu

═══════════════════════════════════════════════════════════════════
KROK 2 — RAPORT DETEKCJI
═══════════════════════════════════════════════════════════════════

Wyświetl zwięzły raport w formacie:

   📦 PROJEKT WYKRYTY:
   ├─ Nazwa:        [nazwa]
   ├─ Stack:        [stack z wersjami]
   ├─ Typ:          [typ]
   ├─ Cel:          [z README lub placeholder]
   ├─ Git:          [tak/nie] + .gitignore: [tak/nie]
   └─ Istniejące pliki sesji: [lista lub "brak"]

   🔧 PLAN DZIAŁANIA:
   → Utworzę: [lista plików do utworzenia]
   → Backup:  [lista plików do backupu]
   → Pominę:  [lista plików które już istnieją i NIE wymagają zmiany]

Następnie bez czekania na potwierdzenie PRZEJDŹ do kolejnych kroków. (Użytkownik preferuje autonomię — i tak może cofnąć zmiany z backupów.)

═══════════════════════════════════════════════════════════════════
KROK 3 — PLIK CLAUDE.md
═══════════════════════════════════════════════════════════════════

Utwórz CLAUDE.md w root projektu. Wypełnij wszystkie placeholdery używając danych z KROKU 1. Zachowaj polski język (użytkownik to Piotr, developer z Polski).

ZAWARTOŚĆ:

---
# CLAUDE.md — <NAZWA_PROJEKTU>

## Kontekst projektu
- **Projekt:** <NAZWA> — <CEL_Z_README lub placeholder>
- **Typ:** <TYP_PROJEKTU>
- **Stack:** <STACK_Z_WERSJAMI>
- **Środowisko:** Windows 11, Miniconda (Python 3.10), VS Code
- **Cel bieżący:** [do uzupełnienia przy pierwszej sesji /start]

## Zasady pracy
- Zawsze sprawdzaj MEMORY.md przed podjęciem decyzji architektonicznej
- Nie duplikuj rozwiązań już opisanych w MEMORY.md
- Przy każdej nowej sesji: zacznij od /start
- Przy zakończeniu sesji: zawsze wywołaj /end
- W trakcie dłuższej pracy rób checkpointy przez /save
- Język komunikacji: polski (chyba że user napisze po angielsku)

## Konwencje projektu
<!-- Dopasuj do wykrytego stacku -->
- Nazewnictwo plików: <snake_case dla Python / kebab-case dla JS-FE / camelCase dla JS-BE>
- Język komentarzy w kodzie: polski
- Styl commitów: conventional commits (feat:, fix:, refactor:, docs:, chore:)
- <jeśli wykryto linter/formatter np. ruff/black/prettier — dopisz tutaj>

## Pliki stanu sesji
- **MEMORY.md**       — długoterminowa pamięć projektu (czytaj na /start)
- **last_session.md** — stan ostatniej sesji (czytaj na /start, pisz na /end)

## Komendy dostępne w tym projekcie
| Komenda   | Kiedy używać                      | Co robi                                    |
|-----------|-----------------------------------|--------------------------------------------|
| `/start`  | Na początku każdej sesji          | Czyta MEMORY.md + last_session.md          |
| `/save`   | Checkpoint w trakcie pracy        | Aktualizuje last_session.md (sesja trwa)   |
| `/end`    | Na końcu sesji                    | Nadpisuje last_session.md + update MEMORY  |
| `/status` | Szybki podgląd (bez modyfikacji)  | Wyświetla aktualny stan z last_session.md  |

## Sprzęt / Ograniczenia
- **GPU:** RTX 3050 Laptop 4GB VRAM — nie ładuj modeli >3.5GB w FP16
- **CPU:** i5-12500H
- **RAM:** 32GB DDR4
- **Preferencje AI:** kwantyzacja GGUF Q4_K_M dla LLM, CPU offload dla zbyt dużych warstw

<!-- Jeśli typ projektu ≠ AI/ML → sekcja Sprzęt i tak zostaje, ale nie będzie używana często -->

## Struktura katalogów (wykryta)
<WSTAW_DRZEWO_Z_KROKU_1.5>
---

═══════════════════════════════════════════════════════════════════
KROK 4 — PLIK MEMORY.md
═══════════════════════════════════════════════════════════════════

Utwórz MEMORY.md w root projektu z tą zawartością (BEZ zmian w placeholderach — ten plik ma być pusty na start):

---
# MEMORY.md — Długoterminowa pamięć projektu <NAZWA_PROJEKTU>

> Ten plik kumuluje wiedzę o projekcie. Nigdy nie usuwaj wpisów — tylko dopisuj.
> Każdy wpis oznaczaj datą w formacie [YYYY-MM-DD].

---

## Architektura

<!-- Claude dopisuje tutaj decyzje architektoniczne wraz z uzasadnieniem -->

_Brak wpisów — zostaną dodane przy pierwszych decyzjach architektonicznych._

---

## Rozwiązane problemy

<!-- Gotowe rozwiązania trudnych problemów — żeby nie szukać ich ponownie -->

_Brak wpisów._

---

## Aktywne TODO (długoterminowe)

<!-- Zadania rozlewające się przez wiele sesji. Krótkoterminowe są w last_session.md -->

_Brak wpisów._

---

## Odrzucone podejścia

<!-- Co nie działało i dlaczego — unikamy powtarzania błędów -->

_Brak wpisów._

---

## Słownik projektu

<!-- Specyficzne terminy używane w tym projekcie -->

_Brak wpisów._

---

## Zewnętrzne zależności i integracje

<!-- Klucze API, serwisy zewnętrzne, specyficzne biblioteki -->

_Brak wpisów._
---

Tylko <NAZWA_PROJEKTU> podmień na wykrytą nazwę. Reszta placeholderów (_Brak wpisów._) zostaje.

═══════════════════════════════════════════════════════════════════
KROK 5 — PLIK last_session.md
═══════════════════════════════════════════════════════════════════

Utwórz last_session.md w root projektu. Podmień <DATA> na aktualną datę YYYY-MM-DD.

ZAWARTOŚĆ:

---
# last_session.md

**Sesja:** <DATA> · Setup systemu zarządzania sesjami
**Status:** ✓ Pierwsza sesja — system zainstalowany

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Uruchom `/start` aby zweryfikować że system działa poprawnie. Następnie ustal "Cel bieżący" w CLAUDE.md (sekcja "Kontekst projektu") i przejdź do pierwszego rzeczywistego zadania developerskiego.**

Kontekst: system Session State Management został dopiero zainstalowany. Pierwsza prawdziwa sesja pracy nie miała jeszcze miejsca. CLAUDE.md ma puste pole "Cel bieżący" wymagające uzupełnienia.

---

## Co zrobiono w tej sesji

- ✓ Utworzono strukturę `.claude/commands/`
- ✓ Utworzono CLAUDE.md z kontekstem projektu (auto-detekcja stacku)
- ✓ Utworzono MEMORY.md (pusty szablon)
- ✓ Utworzono last_session.md (ten plik)
- ✓ Utworzono 4 pliki komend: start.md, save.md, end.md, status.md

## Co zostało (backlog sesji)

- ⟳ Wypełnić "Cel bieżący" w CLAUDE.md
- ⟳ Pierwsze zadanie developerskie do ustalenia

## Aktywne pliki

- CLAUDE.md
- MEMORY.md
- last_session.md

## Otwarte pytania

- Jaki jest aktualny cel/faza tego projektu?
- Które pliki są teraz najważniejsze w pracy?

## Do MEMORY.md (przeniesiono)

_Brak — sesja techniczna (setup systemu), nie ma jeszcze decyzji do długoterminowej pamięci._
---

═══════════════════════════════════════════════════════════════════
KROK 6 — PLIKI KOMEND (.claude/commands/)
═══════════════════════════════════════════════════════════════════

Utwórz katalog `.claude/commands/` jeśli nie istnieje, a następnie te 4 pliki:

──────────────────────────────────────────
PLIK: .claude/commands/start.md
──────────────────────────────────────────

# /start — Inicjalizacja sesji

Wykonaj następujące kroki w podanej kolejności:

1. Odczytaj plik MEMORY.md i przyswój jego zawartość jako kontekst projektu.

2. Odczytaj plik last_session.md. Jeśli plik nie istnieje,
   poinformuj że to pierwsza sesja projektu.

3. Wyświetl raport startowy w formacie:
   - Projekt: [nazwa z CLAUDE.md]
   - Ostatnia sesja: [data z last_session.md]
   - Następny krok: [sekcja "NASTĘPNY KROK" z last_session.md]
   - Aktywne pliki: [lista z last_session.md]
   - Otwarte pytania: [jeśli istnieją]

4. Zapytaj: "Czy zaczynamy od następnego kroku, czy jest inne zadanie?"

──────────────────────────────────────────
PLIK: .claude/commands/save.md
──────────────────────────────────────────

# /save — Checkpoint sesji

Wykonaj następujące kroki (bez kończenia sesji):

1. Zaktualizuj sekcje "Co zrobiono" i "Co zostało" w last_session.md
   odzwierciedlając aktualny postęp. Nie zastępuj całego pliku —
   aktualizuj tylko te sekcje.

2. Jeśli w tej chwili podjęto ważną decyzję architektoniczną
   lub rozwiązano trudny problem — dopisz to do MEMORY.md
   w odpowiedniej sekcji z datą [YYYY-MM-DD].

3. Zaktualizuj "Aktywne pliki" jeśli zmienił się zestaw plików roboczych.

4. Potwierdź: "✓ Checkpoint zapisany o [HH:MM]. Kontynuujemy."

UWAGA: To NIE jest /end — sesja trwa dalej. Nie przekazuj podsumowania końcowego.

──────────────────────────────────────────
PLIK: .claude/commands/end.md
──────────────────────────────────────────

# /end — Zamknięcie sesji

Wykonaj następujące kroki:

1. Podsumuj co zostało zrobione w tej sesji (lista bullet points z ✓).

2. Zidentyfikuj JEDEN konkretny następny krok — możliwie szczegółowy
   (konkretna funkcja, plik, konkretna akcja). Unikaj ogólników typu
   "kontynuować pracę" albo "dokończyć feature X".

3. Jeśli w tej sesji podjęto decyzje architektoniczne lub znaleziono
   rozwiązanie trudnego problemu — dopisz je do MEMORY.md
   w odpowiedniej sekcji z datą [YYYY-MM-DD].

4. Nadpisz last_session.md w całości nową zawartością zgodnie
   z poniższym formatem:

   # last_session.md

   **Sesja:** [YYYY-MM-DD] · [HH:MM-HH:MM]
   **Status:** ✓ Zakończona poprawnie

   ---

   ## ▸ NASTĘPNY KROK (zacznij tutaj)

   [JEDEN konkretny następny krok z KROKU 2]

   Kontekst: [2-3 zdania dlaczego to jest następny krok]

   ---

   ## Co zrobiono w tej sesji
   [lista z KROKU 1]

   ## Co zostało (backlog sesji)
   [niedokończone zadania]

   ## Aktywne pliki
   [pliki z którymi pracowaliśmy]

   ## Otwarte pytania
   [nierozstrzygnięte kwestie]

   ## Do MEMORY.md (przeniesiono)
   [co dopisano do MEMORY.md w KROKU 3]

5. Potwierdź: "✓ Sesja zapisana. Następny krok: [następny krok z KROKU 2]"

──────────────────────────────────────────
PLIK: .claude/commands/status.md
──────────────────────────────────────────

# /status — Podgląd stanu

Odczytaj last_session.md i wyświetl:

1. Następny krok (sekcja "NASTĘPNY KROK")
2. Co zostało do zrobienia (sekcja "Co zostało")
3. Aktywne pliki
4. Otwarte pytania (jeśli są)

UWAGA: Nie modyfikuj żadnego pliku. To komenda tylko do odczytu.

═══════════════════════════════════════════════════════════════════
KROK 7 — .gitignore (warunkowo)
═══════════════════════════════════════════════════════════════════

JEŚLI istnieje plik .gitignore → dopisz na końcu (jeśli sekcja nie istnieje):

# --- Claude Code Session System ---
# Odkomentuj jeśli nie chcesz commitować stanu sesji:
# last_session.md
CLAUDE.md.backup_*
MEMORY.md.backup_*
last_session.md.backup_*

JEŚLI .gitignore NIE istnieje → NIE twórz go specjalnie. To nie jest nasz projekt decydować o git.

═══════════════════════════════════════════════════════════════════
KROK 8 — RAPORT KOŃCOWY
═══════════════════════════════════════════════════════════════════

Wyświetl końcowy raport w formacie:

   ✅ SESSION SYSTEM ZAINSTALOWANY

   <NAZWA_PROJEKTU>/
   ├── CLAUDE.md                     [✓ utworzony — wykryto <stack>]
   ├── MEMORY.md                     [✓ utworzony — pusty szablon]
   ├── last_session.md               [✓ utworzony — setup session]
   └── .claude/
       └── commands/
           ├── start.md              [✓]
           ├── save.md               [✓]
           ├── end.md                [✓]
           └── status.md             [✓]

   📋 CO DALEJ:
   1. Zamknij tę sesję Claude Code
   2. Uruchom ponownie: `claude` w tym samym katalogu
   3. Wpisz: /start
   4. Powinieneś zobaczyć raport startowy

   ⚠️ DO UZUPEŁNIENIA RĘCZNIE:
   - Pole "Cel bieżący" w CLAUDE.md (sekcja Kontekst projektu)
   - [jeśli były backupy] Sprawdź backupy: <lista_backupów>

NIE uruchamiaj /start teraz. To ma zrobić użytkownik w nowej sesji.

═══════════════════════════════════════════════════════════════════
KONIEC PROMPTU
===================================================================
PROMPT END — UNIWERSALNY SETUP SESSION SYSTEM
===================================================================
```

---

## Co ten prompt wykrywa automatycznie

| Element | Skąd | Gdy brak |
|---|---|---|
| **Nazwa projektu** | basename aktualnej ścieżki (CWD) | Nie może brakować — zawsze dostępne |
| **Stack** | pyproject.toml, package.json, Cargo.toml, go.mod, *.csproj | Wywnioskowany z rozszerzeń plików w src/ |
| **Typ projektu** | Heurystyka po kluczowych bibliotekach | "General Project" |
| **Cel projektu** | Pierwszy akapit README.md | Placeholder "[do uzupełnienia]" |
| **Struktura** | Top-level katalogi (bez venv/node_modules) | — |
| **Git status** | Obecność `.git/` i `.gitignore` | — |
| **Istniejące pliki sesji** | Skan root + .claude/commands/ | Backup z timestampem |

---

## Zastosowanie dla Twoich trzech projektów

**TerraLens** — już masz oddzielny prompt z poprzedniej wiadomości (wypełniony ręcznie). Ten uniwersalny też zadziała, ale tamten jest już odpalony.

**Neural-Mosaic** (`D:\Programming_Projects\Neural-Mosaic`):
```powershell
cd D:\Programming_Projects\Neural-Mosaic
claude
# → wklej prompt → czekaj → /end → zamknij
```
Prompt powinien wykryć: CustomTkinter, PyTorch, CLIP, VGG19 → stack AI/ML · Desktop App. Cel wyciągnie z README jeśli istnieje.

**Chronos-earth** (`D:\Programming_Projects\Chronos-earth`):
```powershell
cd D:\Programming_Projects\Chronos-earth
claude
# → wklej prompt → czekaj → zamknij
```
Nie znam stacku tego projektu — prompt sam wykryje i dostosuje CLAUDE.md.

---

## Dodatkowe rady dla universalnego workflow

### 🔁 Zrób sobie alias w PowerShell

Żeby nie wklejać promptu za każdym razem, zapisz go jako plik i stwórz alias:

```powershell
# Zapisz prompt raz jako plik:
# D:\Programming_Projects\_global\setup-session.md

# W profilu PowerShell ($PROFILE) dopisz:
function Install-ClaudeSession {
    Get-Content "D:\Programming_Projects\_global\setup-session.md" | Set-Clipboard
    Write-Host "✓ Prompt w schowku. Uruchom 'claude' i wklej (Ctrl+V)." -ForegroundColor Green
}
Set-Alias ics Install-ClaudeSession
```

Potem w dowolnym projekcie: `ics` → `claude` → Ctrl+V → Enter. Trzy kroki.

### 🌍 Centralny template — jedno źródło prawdy

Zamiast trzymać prompt w trzech miejscach:

```
D:\Programming_Projects\_global\
├── setup-session-prompt.md       ← ten prompt
├── session-template\             ← gotowe pliki (bez auto-detekcji)
│   ├── CLAUDE.md.template
│   ├── MEMORY.md
│   ├── last_session.md
│   └── .claude\commands\*.md
└── README.md                     ← opis obu opcji
```

Prompt = szybki setup z auto-detekcją. Template = ręczny setup (copy-paste) gdy Claude Code nie jest jeszcze zainstalowany lub nie działa.

### 🆚 Różnice między projektami — kiedy doedytować

Prompt ustawi wszystkie projekty na domyślne konwencje. Po setupie warto w CLAUDE.md doedytować ręcznie:

- **Projekty AI/ML** (Neural-Mosaic) — dopisz sekcję `## Modele` z listą używanych modeli i ich rozmiarem VRAM
- **Projekty Web** — dopisz `## Endpoints` lub `## Routes` jeśli to backend
- **Projekty desktopowe** (TerraLens, Neural-Mosaic) — dopisz `## Komponenty UI`
- **Projekty naukowe** (Chronos-earth?) — dopisz `## Źródła danych` i `## Notation`

### 📌 Utrzymanie synchronizacji między projektami

Jeśli poprawisz prompt (np. dodasz nową komendę `/reset`) — istniejące projekty nie zaktualizują się same. Dwa podejścia:

1. **Laissez-faire** — nowe projekty dostają nowy prompt, stare zostają jak są. Działa, jeśli stare są stabilne.
2. **Propagacja zmian** — raz na kwartał przejdź przez wszystkie `.claude/commands/` i zsynchronizuj z aktualną wersją.

Osobiście polecam #1 — zmiany w komendach są rzadkie, a różnice między projektami i tak się pojawiają.

### ⚡ Kiedy użyć template zamiast promptu

Prompt wymaga aktywnej sesji Claude Code. Są sytuacje gdy wolisz szybki copy-paste:

- Zakładasz projekt offline
- Nie chcesz zużywać tokenów na setup (chociaż to ~2-5k tokenów, niewiele)
- Chcesz pełną kontrolę nad zawartością CLAUDE.md

Wtedy template z `_global/session-template/` wystarczy. Prompt to tryb "zrób mi wszystko".

### 🧭 Sanity check po setupie w nowym projekcie

Przed pierwszym prawdziwym `/start` sprawdź:

```powershell
# Powinny istnieć wszystkie 4+3 pliki:
Get-ChildItem -Force | Where-Object { $_.Name -in @("CLAUDE.md","MEMORY.md","last_session.md",".claude") }

# Komendy w miejscu:
Get-ChildItem .claude\commands\
```

Jeśli widzisz wszystkie 4 komendy i 3 pliki root — wszystko gra. Jeśli brakuje — Claude Code mógł pominąć krok; uruchom ponownie i poproś "dokończ setup sesji".

### 🗑️ Jak odinstalować system

Gdyby okazało się że w jakimś projekcie system nie jest potrzebny:

```powershell
Remove-Item CLAUDE.md, MEMORY.md, last_session.md -ErrorAction SilentlyContinue
Remove-Item .claude -Recurse -Force -ErrorAction SilentlyContinue
```

Backupy (`*.backup_*`) zostają nietknięte — możesz wrócić jeśli zmienisz zdanie.

---

## TL;DR

Ten sam prompt wklejasz w Claude Code uruchomionym w **dowolnym** katalogu projektu. Reszta dzieje się sama. Dla Neural-Mosaic i Chronos-earth — dosłownie `cd <projekt>` → `claude` → wklej → gotowe.
