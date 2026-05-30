# last_session.md

**Sesja:** 2026-05-29 · ~20:45–22:45
**Status:** ✓ Zakończona poprawnie

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Zaimplementować `src/driftscope/driftsim/null_uniform.py`** — funkcję:

```python
def generate_uniform_draws(
    n_draws: int,
    regime: Literal["R1", "R2", "R3"],
    rng: np.random.Generator,
) -> list[DrawRecord]
```

Uczciwy null generator: 5 z 50 (main, bez zwracania, ascending) + 2 z puli euron zależnej od reżimu (**R1: 1-8, R2: 1-10, R3: 1-12** — zob. preregistration_v2 §1). Daty syntetyczne (tygodniowe od arbitralnego startu; R3 może mieć 2/tydzień). RNG przez `core.seeds.make_worker_seeds(BASE_SEED, n)`. Test (`test_driftsim_calibration.py`): rozkład marginalny ≈ uniform (chi² NIE odrzuca przy braku sygnału), euron range zgodny z reżimem, determinizm per seed.

Kontekst: To **fundament W2** przed `planted_signals.py` (planted = null + wstrzyknięty sygnał). W0 dał skalibrowane oczekiwania (sensitivity δ=0.01 w R1 powinna wyjść ≈α), W1 dał zweryfikowane detektory H1 do kalibrowania. Pamiętaj o guardzie signal #4 (weekly seasonality = tylko R3) przy następnym pliku.

---

## Co zrobiono w tej sesji

- ✓ **Krytyczna analiza planowanych zmian kontraktu** — odradzona MDL jako Pillar 4 (brak niezależności od MMD/chi²); DoD-4 zostaje 3/3
- ✓ **Contract revision** (`d31ba66`) — data 2014-10-10; DoD-1 positive/negative control (+DoD-1c); recurrence.py do scope (gap perm-calibrated, NA, EVT); Family B BH→Benjamini-Yekutieli (300→450); signal #4 guard (tylko R3); BOCPD pełna macierz P(R_t); power→co-primary; R13
- ✓ **3 latentne błędy złapane** — euron range „1-10 pre-2014" (R1=1-8); signal #4 niemożliwy w R1/R2; analityczny KS nieważny dyskretnie
- ✓ **`preregistration_v2.md`** (`04e97a7`) — ACTIVE, v1 SUPERSEDED, revision_reason; wskaźniki przepięte w brief+CLAUDE
- ✓ **`lifelines` ODRZUCONY** (`7da269e`) — NA ~20 LOC własny, bez pandas
- ✓ **W0 power preview DONE** (`7da269e`+`2cefcd9`) — `notebooks/00_power_preview.py`; real n=958 (133/389/436, NIE 1500); positive control POTWIERDZONY na seed CSV; δ=0.01 per-reżim niewykrywalny
- ✓ **Przegląd W0** (`89b77eb`) — fix wadliwego flagu `mapping`; caveaty (power = UPPER BOUND: FDR, global heurystyka, tylko signal #1)
- ✓ **Przegląd W1** (`3912916`) — rdzeń BOCPD message-passing zweryfikowany jako POPRAWNY; złapana desync prereg↔kod (prereg był stale α=1, nie kod) → prereg zsynchronizowane do α=0.1/hazard=0.005; DoD-1b data 2014-10-10 + ±60 dla 2014; 27/27 zielonych
- ✓ **Pamięć agenta** — `communication_append_recommendation`, `contract_revision_w0`, `w0_power_and_real_n`, `project-root-memory-file` (lekcja: czytać projektowy MEMORY.md na /start)

## Co zostało (backlog sesji)

- ⟳ **PRIORYTET: W2 DriftSim** — `null_uniform.py` (NASTĘPNY KROK) → `planted_signals.py` (5×4, guard #4=R3) → kalibracja
- ⟳ **W4** — `k4_mmd.py` (stub 7 LOC) + N=200 PoC vs shuffled null
- ⟳ **W6** — `recurrence.py` (nowy), `multiple_testing.py`/`permutation.py`/`block_bootstrap.py`/`specification.py` (stuby); kalibracja progu BOCPD `reject_h0` (obecnie magiczne 0.3) w DoD-2
- ⟳ **W8** — BOCPD musi zwracać pełną macierz P(R_t) (dziś tylko cp_probs); animacja
- ⟳ **Ingestion** — `lotto_scraper.fetch_draw_by_date()` stub; SSL permanent fix (`pip-system-certs`)
- ⟳ **Baseline commit src/** — większość scaffoldu wciąż untracked (tylko h1_classical.py + test_h1_invariants.py weszły do gita)

## Aktywne pliki

- `PROJECT_BRIEF.md` — contract (real n=958, recurrence, DoD-1 controls, ±60/2014, lifelines reject)
- `CLAUDE.md` — zsynchronizowany
- `src/driftscope/methodology/preregistration_v2.md` — ACTIVE (α=0.1, hazard=0.005)
- `src/driftscope/methodology/h1_classical.py` — zrecenzowany (BOCPD core poprawny)
- `tests/test_h1_invariants.py` — 10/10; DoD-1b 2014-10-10
- `notebooks/00_power_preview.py` — W0 deliverable
- `src/driftscope/driftsim/null_uniform.py` — DO NAPISANIA (następny krok)

## Otwarte pytania

- Próg `reject_h0 = max_prob > 0.3` w BOCPD — magiczny, do kalibracji w DoD-2 (W6); na razie placeholder
- Czy dodać δ pośredni (np. 0.015) do gridu DriftSim, skoro δ=0.01 jest sub-threshold per-reżim? Wymagałoby preregistration_v3 — domyślnie NIE (δ=0.01 celowo jako sub-threshold anchor)
- `information_theory.py` (LZ76/MDL) — kiedy/czy jako stretch v2 (poza MVP)
- Kiedy zrobić baseline commit reszty scaffoldu src/ (obecnie untracked)

## Do MEMORY.md (przeniesiono)

- **Projektowy `MEMORY.md`** — dodano wpis `[2026-05-29] Contract revision + W0/W1 review — Ścieżka A utrwalona` (prereg v2, sync BOCPD α=0.1, W0 real n=958, W1 BOCPD core poprawny, 7 commitów)
- **Pamięć agenta** — `contract_revision_w0_2026_05_29` (zaktualizowany o sync BOCPD), `w0_power_and_real_n`, `project-root-memory-file` (lekcja procesowa), `communication_append_recommendation`
