# last_session.md

**Sesja:** 2026-06-07 · ~21:00-21:55
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 0e04caf @ master (origin zsynchronizowany)

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Zweryfikować RENDER nowego README na GitHubie oraz live Pages dla `0e04caf`.** Konkretnie:
(1) potwierdzić, że **oba diagramy Mermaid** (przepływ filarów + architektura) renderują się
na froncie repo `https://github.com/Piotr1686/DriftScope` — Mermaid o błędnej składni **psuje
się po cichu** (pokazuje surowy kod zamiast diagramu); (2) potwierdzić, że deploy
`pages-build-deployment` na `0e04caf` = success i live report pokazuje nową tabelę „IT (LZ) p"
per-regime. Weryfikacja: `gh run list --workflow=pages-build-deployment` + `gh run view <id>
--json headSha,conclusion` (sandbox blokuje HTTPS, curl exit 35) LUB poprosić usera o rzut oka
na URL repo.

Kontekst: framework (Ścieżka A) jest domknięty; README przepisany w tej sesji wg briefu
5-modeli. Render Mermaid to JEDYNE czego nie dało się zweryfikować lokalnie (renderuje go
GitHub, nie quarto). Brak ścieżki krytycznej — to ostatni punkt walidacyjny po rewrite.

---

## Co zrobiono w tej sesji

- ✓ **NASTĘPNY KROK z poprz. sesji DOMKNIĘTY — kolumna „IT (LZ) p" per-regime w `report.qmd`**
  (commit `bfa6731`): suplement IT czyta negative control jako clear również SEKWENCYJNIE per
  reżim. Realne (n_perm=199): **R1=0.535 · R2=0.855 · R3=0.620, wszystkie reject=False**.
  Wizualnie odrębny od tabeli 3 filarów (wzmacnia „supplement, NIE 4. filar"; DoD-4=3/3).
  Reuse `information_detector()`+`split_by_regime()`. Re-render `docs/{report,index}.html`.
  Weryfikacja: pytest 260/2, render exit 0, grep HTML (tabela + kotwice nietknięte).
- ✓ **PEŁNY rewrite `README.md`** (commit `822cb36`) wg `docs/research/readme_rewrite/
  README_REWRITE_BRIEF.md`: lejek laik→statystyk (16 sekcji), 2 diagramy Mermaid, sformułowania
  uczciwościowe (hallucination=błąd I rodzaju, None=abstynencja, quasi-ground-truth), porównanie
  do NIST/Dieharder jako KOMPLEMENTARNOŚĆ, roadmap bez fałszywych „done", About-author.
- ✓ **SPROSTOWANIA METRYK (zmierzone, dyscyplina briefu §0 — stary README miał błędy):**
  (1) „~4 GB RAM" → pojedynczy audyt **~210 MB / ~4.5 s** (4 GB to budżet sweepu DriftSim);
  (2) LZ76 full-stream EuroJackpot **p≈0.75 → 0.700**; (3) tabela PRNG ze świeżego renderu.
  Nuans BOCPD utrwalony: top-1 CP = 2015-01-23 (0.466, aftershock), ground-truthy 2014-11-28/
  2022-03-29 w top-5 → README mówi „covering both", NIE „top peaks" (nie zawyża).
- ✓ **Archiwum `0e04caf`:** `DriftScope_readme/` (root) → `docs/research/readme_rewrite/`
  (brief + 5 recenzji modeli), mirror konwencji `docs/research/external/`. Root posprzątany.
- ✓ **Walidacja:** 3 commity wypchnięte (`bfa6731`/`822cb36`/`0e04caf`), pytest 260/2 zielone,
  working tree czysty, HEAD=origin=`0e04caf`.

## Co zostało (backlog sesji — wszystko OPCJONALNE / stretch)

- ⟳ Weryfikacja renderu Mermaid + live Pages dla `0e04caf` (NASTĘPNY KROK).
- ⟳ Pages na `actions/deploy-pages` (usuwa Node20-warning) — stretch CI.
- ⟳ Głębsza analiza pary (10,25) w R2 — non-finding.

## Aktywne pliki

- `src/driftscope/reporting/report.qmd` — kolumna IT per-regime (`bfa6731`)
- `docs/{report,index}.html` — re-render z kolumną IT (`bfa6731`)
- `README.md` — pełny rewrite (`822cb36`)
- `docs/research/readme_rewrite/*.md` — zarchiwizowany brief + 5 recenzji (`0e04caf`)
- ACTIVE prereg = **v7** (bez zmian — sesja reporting/portfolio, poza prereg §0)

## Otwarte pytania

- **Render Mermaid na GitHubie** — czy oba diagramy w README renderują się (nie surowy kod).
- **Czy projekt „skończony"?** — jako framework audytowy (Ścieżka A) praktycznie TAK; README
  i portfolio domknięte. Pozostałe pozycje to czyste stretche bez ścieżki krytycznej.

## Do MEMORY.md (przeniesiono)

- Root `MEMORY.md` (Architektura): **[2026-06-07 sesja 2] IT per-regime + PRZEPISANY README +
  sprostowania metryk** (RAM ~210 MB nie 4 GB; LZ76 0.700 nie 0.75; nuans BOCPD top-1 aftershock;
  3 commity; archiwum briefu do docs/research).
- Pamięć agenta: zaktualizowany `it_supplement_lz76.md` (p≈0.75 → 0.700 + per-rezim).
