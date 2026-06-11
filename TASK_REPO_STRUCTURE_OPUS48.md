# TASK: Refaktoryzacja struktury repozytorium DriftScope

> **Wykonawca:** Claude Opus 4.8 (osobna sesja / agent)
> **Autor taska:** code-review struktury, 2026-06-11 (Fable 5)
> **Typ zmian:** WYŁĄCZNIE strukturalne (przenoszenie plików, dokumentacja, konfiguracja).
> **Zakaz:** jakichkolwiek zmian semantyki kodu Python. Zero zmian w logice, sygnaturach, testach (poza ścieżkami).

---

## 1. Kontekst

DriftScope to research-grade framework audytu niestacjonarności (Python 3.10, src-layout,
PEP 621 + hatchling, ruff + mypy --strict, CI na GitHub Actions). Fundamenty struktury są
**poprawne i nowoczesne** — ten task NIE jest przebudową, tylko sprzątaniem narosłego dryfu.

**Twarde ograniczenia kontraktowe (przeczytaj PRZED rozpoczęciem):**
1. `PROJECT_BRIEF.md` = **architectural contract** — każda zmiana decyzji architektonicznej
   wymaga osobnego commita aktualizującego z polem *rationale*.
2. Każda zmiana w `src/driftscope/methodology/` wymaga update `preregistration_v{N}.md`
   z polem `revision_reason` — dlatego punkty dotykające `methodology/` są oznaczone
   **[DECYZJA USERA]** i NIE wykonuj ich bez wyraźnej zgody.
3. `CLAUDE.md`, `MEMORY.md`, `last_session.md`, `last_session.archive.md`, `.claude/commands/`
   to infrastruktura sesyjna agenta — **zostają w root bez zmian**.
4. Język commitów: conventional commits; komentarze/dokumentacja po polsku; nazwy plików snake_case.
5. Każde przeniesienie pliku = `git mv` (zachowanie historii). Windows 11 + PowerShell —
   uwaga na `&` w ścieżce `R&D/` (cytuj ścieżki).
6. Commituj małymi krokami: jeden punkt = jeden commit (`chore(repo): ...` / `docs(...): ...`).

---

## 2. Inwentaryzacja problemów (findings)

### P0 — dryf dokumentacji względem rzeczywistości (najważniejsze)

**F1. Sekcja „Struktura katalogów" w CLAUDE.md jest mocno nieaktualna.**
Brakuje w niej istniejących plików/modułów:
- `src/driftscope/pipeline.py`
- `src/driftscope/reporting/{information_theory,prng_benchmark,multimulti_audit}.py`
- `src/driftscope/ingestion/rng_streams.py`
- `scripts/{calibrate_bocpd_threshold,calibrate_mmd_pool,convert_mm_seed,prng_benchmark,test_api_key}.py`, `scripts/scraper_selectors.md`
- `data/seed/multimulti_history.csv`
- 16 z 24 faktycznych plików testowych (udokumentowano 8)
- katalogów `R&D/`, `docs/research/`, plików `WORKFLOW.md`, `HARDWARE_PUSH_CATALOG.md`, `docs/executive_summary.html`
Akcja: po wykonaniu przenosin (F3–F7) przepisz drzewo w CLAUDE.md tak, by w 100% odpowiadało
`git ls-files`. To projekt „docs-as-contract" — dryf drzewa podważa jego wiarygodność.

**F2. Martwa deklaracja git-lfs i niespójna polityka artefaktów.**
CLAUDE.md mówi „artifacts/ git-lfs tracked (*.parquet)" i „DoD-6: git-lfs", ale:
- w repo NIE ma `.gitattributes` (lfs nigdy nie zmaterializowany),
- `.gitignore` ignoruje `artifacts/*.csv|png|webm|gif`, trackowany jest tylko `artifacts_manifest.json`,
- żaden `*.parquet` nie jest commitowany.
Akcja **[DECYZJA USERA]** — przedstaw userowi dwie opcje i wykonaj wybraną:
  (a) dopisać `.gitattributes` z regułą lfs dla `*.parquet` (materializacja deklaracji), albo
  (b) zaktualizować CLAUDE.md + PROJECT_BRIEF (commit z rationale): polityka = manifest SHA-256
      w repo, binaria odtwarzalne przez `--resume` (stan faktyczny). Rekomendacja: **(b)** —
      lfs na darmowym GitHub ma limity, a manifest już realizuje DoD-6.

**F3. Brak markera PEP 561 `py.typed`.**
Projekt jest mypy --strict i dystrybuowany jako pakiet (hatchling wheel), ale nie deklaruje
typów konsumentom. Akcja: dodaj pusty `src/driftscope/py.typed` + upewnij się, że hatchling
go pakuje (przy `packages = ["src/driftscope"]` plik niedotknięty kodem wejdzie do wheel;
zweryfikuj `python -m build` lub `hatch build` i podejrzyj zawartość wheel).

### P1 — porządek w root i R&D

**F4. Śmieci w root repo.**
- `poc_permutation_engine.py` — ukończony PoC (2026-05-17, „DONE" w CLAUDE.md). Akcja:
  `git mv` → `notebooks/poc_permutation_engine.py` (CLAUDE.md definiuje notebooks/ jako
  „exploratory — NIE part of pipeline" — to dokładnie ta kategoria). Zaktualizuj odwołania
  (CLAUDE.md drzewo + ewentualne wzmianki w README/PROJECT_BRIEF — sprawdź grepem).
- `universal-session-setup-prompt.md` — szablon promptu, nie należy do root. Akcja:
  `git mv` → `docs/templates/universal_session_setup_prompt.md` (utwórz katalog; przy okazji
  normalizacja nazwy na snake_case).
- `HARDWARE_PUSH_CATALOG.md` — meta-katalog technik; referencjonowany w CLAUDE.md (sekcja
  „Hardware Transcendence Stack"). Akcja (opcjonalna, P3): zostaw w root LUB przenieś do
  `docs/` i popraw referencję w CLAUDE.md. Rekomendacja: zostawić (niski koszt, jest linkowany).
- `WORKFLOW.md`, `PROJECT_BRIEF.md`, `README.md`, `LICENSE`, `.env.example` — **zostają w root** (standard).

**F5. Katalog `R&D/` — chaos nazewniczy i kolizja przeznaczenia z `docs/research/`.**
24 pliki archiwalnych cross-review z modeli AI; problemy:
- `&` w nazwie katalogu (uciążliwe w PowerShell/URL/CI),
- nazwy z kropkami i spacjami (`B. Szablon DECISION_PROMPT.md`), mieszanka konwencji
  (`3A_Cross-Review__GPT.md`, `7C_Brief2_Pre-Flight-Check_Gemini.md`),
- repo ma już `docs/research/` o tym samym przeznaczeniu (np. `docs/research/readme_rewrite/`).
Akcja: `git mv` całości → `docs/research/rd_archive/` z normalizacją nazw do snake_case
(np. `B. Szablon DECISION_PROMPT.md` → `b_szablon_decision_prompt.md`,
`3A_Cross-Review__GPT.md` → `3a_cross_review_gpt.md`). Wygeneruj w `docs/research/rd_archive/README.md`
tabelę mapowania stara→nowa nazwa (żeby historia konwersacji z userem nie straciła kontekstu).
Sprawdź grepem, czy nic nie linkuje do starych ścieżek (`R&D/` w *.md).

### P2 — scripts/ i pakiet

**F6. `scripts/test_api_key.py` — myląca nazwa.**
Prefiks `test_` sugeruje test pytest (pytest ma `testpaths=["tests"]`, więc NIE jest zbierany —
ale konwencja myli ludzi i narzędzia). Akcja: `git mv` → `scripts/check_api_key.py`.
Przy okazji ZWERYFIKUJ, że plik nie zawiera zahardkodowanego sekretu (jeśli zawiera — zgłoś
userowi, nie commituj poprawki samodzielnie).

**F7. `scripts/scraper_selectors.md` — dokumentacja w katalogu kodu.**
Akcja: `git mv` → `docs/scraper_selectors.md` LUB zostaw, jeśli jest czytana programowo
(sprawdź grepem `scraper_selectors` w src/ i scripts/ — jeśli jakikolwiek kod ją czyta, zostaw
i tylko odnotuj w drzewie CLAUDE.md).

**F8. Historia preregistration (v1–v6) w pakiecie src. [DECYZJA USERA]**
7 plików `.md` w `src/driftscope/methodology/` trafia do wheel i puchnie w pakiecie; tylko v7
jest ACTIVE. Profesjonalny układ: `docs/methodology/preregistration/{v1..v6}.md` (historia)
+ v7 zostaje w `methodology/` (kontrakt CLAUDE.md wymaga colokacji prereg z metodologią).
UWAGA: to dotyka `methodology/` → wymaga zgody usera + commit aktualizujący PROJECT_BRIEF
i CLAUDE.md z rationale. Alternatywa minimalna bez ruszania plików: wykluczyć `*.md` z wheel
w `[tool.hatch.build.targets.wheel]` (`exclude`). Rekomendacja: **alternatywa minimalna**
(zero ryzyka kontraktowego), pełne przeniesienie tylko jeśli user wybierze.

### P3 — opcjonalne wzmocnienia (research-grade polish)

**F9. `CITATION.cff`** — projekt pozycjonuje się jako research-grade/portfolio; plik cytowania
to tani sygnał profesjonalizmu (GitHub renderuje przycisk „Cite this repository").
**F10. `CHANGELOG.md`** (Keep a Changelog) — od wersji 0.1.0; opcjonalne przy solo-projekcie.
**F11. `report.qmd` w `src/driftscope/reporting/`** — niestandardowe (źródła raportów zwykle
poza pakietem), ale działa i ma wyjątki w .gitignore. **Zostaw bez zmian** — koszt przenosin
(ścieżki Quarto, cache, CI) przewyższa zysk. Odnotuj tylko w drzewie CLAUDE.md.

---

## 3. Struktura docelowa (po wykonaniu P0–P2)

```
DriftScope/
├── .claude/commands/                  # system sesyjny (bez zmian)
├── .github/workflows/ci.yml
├── .env.example  .gitignore  LICENSE  pyproject.toml
├── README.md  CLAUDE.md  MEMORY.md  PROJECT_BRIEF.md  WORKFLOW.md
├── HARDWARE_PUSH_CATALOG.md           # zostaje (linkowany z CLAUDE.md)
├── last_session.md  last_session.archive.md
├── data/seed/                         # eurojackpot_history.csv, multimulti_history.csv
├── artifacts/                         # manifest trackowany; binaria ignorowane (polityka F2)
├── demo/app.py
├── notebooks/                         # 00_power_preview.py, poc_permutation_engine.py (← root)
├── docs/
│   ├── index.html  report.html  executive_summary.html   # GitHub Pages
│   ├── scraper_selectors.md           # (← scripts/, jeśli F7 wykonalne)
│   ├── templates/
│   │   └── universal_session_setup_prompt.md             # (← root)
│   └── research/
│       ├── external/
│       ├── readme_rewrite/
│       └── rd_archive/                # (← R&D/, znormalizowane nazwy + README z mapowaniem)
├── scripts/                           # archive, calibrate_*, check_api_key (← test_api_key),
│   └── ...                            # convert_mm_seed, manual_import, multimulti_audit,
│                                      # prng_benchmark, smoke_test
├── src/driftscope/
│   ├── py.typed                       # NOWY (F3)
│   └── ... (bez zmian strukturalnych; prereg wg decyzji F8)
└── tests/                             # bez zmian
```

## 4. Kolejność wykonania (jeden punkt = jeden commit)

1. `chore(repo): dodaj py.typed (PEP 561)` — F3 (+ weryfikacja wheel).
2. `chore(repo): poc_permutation_engine.py -> notebooks/` — F4a (+ grep referencji).
3. `chore(repo): universal-session-setup-prompt -> docs/templates/ (snake_case)` — F4b.
4. `chore(repo): R&D/ -> docs/research/rd_archive/ + normalizacja nazw + mapowanie` — F5.
5. `chore(scripts): test_api_key -> check_api_key (audyt sekretow)` — F6.
6. `chore(repo): scraper_selectors.md -> docs/` — F7 (warunkowo, po grep).
7. **[STOP — DECYZJE USERA]** F2 (polityka lfs/artefakty) i F8 (prereg w wheel) — przedstaw
   opcje + rekomendacje, czekaj na wybór, wykonaj wybraną wariant + commit PROJECT_BRIEF
   z rationale jeśli dotyczy.
8. `docs(claude): synchronizacja drzewa katalogow z git ls-files` — F1 (NA KOŃCU, gdy
   struktura ustabilizowana; drzewo musi odpowiadać rzeczywistości 1:1).
9. Opcjonalnie (za zgodą usera): `docs(repo): CITATION.cff` (F9), `docs(repo): CHANGELOG.md` (F10).

## 5. Kryteria akceptacji (DoD taska)

- [ ] `pytest` — komplet zielony (żaden test nie zmieniony poza ewentualnymi ścieżkami).
- [ ] `ruff check .` i `mypy` — czysto (jak przed taskiem).
- [ ] CI green na pushu.
- [ ] `git log --follow` pokazuje ciągłość historii dla każdego przeniesionego pliku.
- [ ] Grep całego repo: zero martwych referencji do starych ścieżek
      (`R&D/`, `poc_permutation_engine`, `universal-session-setup-prompt`, `test_api_key`).
- [ ] Drzewo w CLAUDE.md == `git ls-files` (1:1, łącznie z nowymi lokalizacjami).
- [ ] Każda zmiana kontraktowa (F2/F8, jeśli wykonane) ma osobny commit w PROJECT_BRIEF.md
      z rationale.
- [ ] Wheel (`hatch build`) zawiera `py.typed`; jeśli wybrano F8-minimal — nie zawiera `preregistration_*.md` poza v7 (lub żadnego, wg decyzji).

## 6. Poza zakresem (NIE ruszać)

- Logika Python, sygnatury, testy merytoryczne, methodology/ (poza zatwierdzonym F8).
- Wyniki trwającego code-review diffu `origin/master..HEAD` (osobny task; znane findingi:
  stale docstring „all-clear" w `run_multimulti_audit`, liczniki testów w README/exec summary,
  magic `>= 2` poza `disagreement.py` — NIE poprawiaj ich w tym tasku, żeby nie mieszać commitów).
- `report.qmd` i pipeline Quarto (F11 — świadomie zostawione).
- Pliki sesyjne (`CLAUDE.md` poza drzewem, `MEMORY.md`, `last_session*.md`, `.claude/`).
