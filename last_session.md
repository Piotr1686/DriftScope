# last_session.md

**Sesja:** 2026-06-07 · ~11:00-12:10
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 9c2dc2f @ master (origin: 99b4dea — patrz niżej)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Rozszerzyć per-regime sekcję w `src/driftscope/reporting/report.qmd` o kolumnę „IT (LZ) p"
na realnym EuroJackpot (R1/R2/R3)** — pokazać, że suplement IT czyta negative control jako
clear również pod kątem SEKWENCYJNYM (czwarty, niezależny obiektyw obok 3 filarów). Konkretnie:
w chunku raportu per-regime wywołać `information_detector()(draws_regime)` dla każdego reżimu i
dodać kolumnę z `p_value`; oczekiwane wartości wysokie (~clear), jak negative control 1-50.

Kontekst: IT pozostaje SUPLEMENTEM, NIE wchodzi do `classify()` / Disagreement Protocol
(DoD-4=3/3 nienaruszone). To domyka narrację „honest null" o sekwencyjny wymiar bez zmiany
kontraktu. Czysty stretch reporting — brak ścieżki krytycznej (framework Ścieżka A domknięty).

---

## Co zrobiono w tej sesji

- ✓ **Naprawa rozjazdów z /start:** dotrackowany `artifacts/{.gitkeep,artifacts_manifest.json}`
  (DoD-6 deliverable; poprz. sesja błędnie uznała „ignored"), odpięty `settings.local.json` od
  gita (`git rm --cached` + `.gitignore`) — koniec perpetualnego churnu allowlisty. Commity
  `7d73cb2`, `28ad0ca`, `1162bc4`. Push origin.
- ✓ **Faza A — detektor IT** (`reporting/information_theory.py`): złożoność Lempel-Ziv 1976
  (`@njit cache=True`) + bz2 cross-check; null **order-shuffle** (permutacja bloków losowań →
  zachowuje marginal+joint, łamie strukturę między-losowaniową). Komplementarny: ślepy na
  freq_shift/pair_corr, czuły na autocorr/period. `information_detector` = czysta funkcja (DoD-6,
  digest-seed jak cooccurrence). 10 testów (FPR≤α, power autocorr, ślepota freq_shift, determinizm).
- ✓ **Faza A.2 — integracja baterii PRNG:** kolumna IT (`it_reject`/`it_p`) w `prng_benchmark.py`
  (src+scripts), `report.qmd`. IT zapala się WYŁĄCZNIE na `+period(50)` (p≈0.01), milczy na
  good/crypto/bias i realnym EuroJackpot (p≈0.75).
- ✓ **Faza B — demo Streamlit** (`demo/app.py`, był stub): 3 zakładki (detection matrix /
  entropy-lens LZ76 / Turing test), grupa optional-dep `demo`. Buildery czyste, `st.*` pod
  `render()`/`__main__`. Smoke test + `AppTest` headless (0 wyjątków). Streamlit 1.58 zainstalowany.
- ✓ **Walidacja:** ruff + mypy strict (`src`+`demo`, 34 plików) clean; **260 passed / 2 skipped**.
- ✓ **Commity + push:** `e60b888` (IT), `99b4dea` (demo) → origin. README + root MEMORY.md
  zaktualizowane; `9c2dc2f` (docs readme) — patrz niżej co do push.

## Co zostało (backlog sesji)

- ⟳ **Kolumna IT per-regime w report.qmd** — NASTĘPNY KROK.
- ⟳ Pages na `actions/deploy-pages` (usuwa Node20-warning) — stretch CI.
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.
- ⚠ **`9c2dc2f` (docs readme) i commit stanu sesji NIEWYPCHNIĘTE** — origin na `99b4dea`.
  Push pozostawiony do decyzji (zob. Otwarte pytania).

## Aktywne pliki

- `src/driftscope/reporting/information_theory.py` (nowy) + `tests/test_information_theory.py`
- `src/driftscope/reporting/prng_benchmark.py`, `scripts/prng_benchmark.py`, `report.qmd` (kolumna IT)
- `demo/app.py` (nowy) + `tests/test_demo_smoke.py`; `pyproject.toml` (mypy override + grupa demo)
- `README.md`, `MEMORY.md` (root, wpis Architektura [2026-06-07])
- ACTIVE prereg = **v7** (bez zmian — IT jest suplementem poza prereg)

## Otwarte pytania

- **Wypchnąć `9c2dc2f` (docs readme) + commit stanu sesji?** origin stoi na `99b4dea`
  (feature'y już tam są). Brak ścieżki krytycznej; do decyzji na starcie następnej sesji.
- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) praktycznie TAK; IT i demo
  to zrealizowane wow-stretche. Pozostałe pozycje to czyste stretche.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-07] ✓ IT supplement (LZ76) + demo Streamlit** —
  decyzja suplement-nie-filar, reporting/ poza prereg, order-shuffle null, walidacja, integracja.
- Pamięć agenta: `it_supplement_lz76.md` (+ wpis w indeksie MEMORY.md agenta).
