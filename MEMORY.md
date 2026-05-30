# MEMORY.md — Długoterminowa pamięć projektu DriftScope

> Ten plik kumuluje wiedzę o projekcie. Nigdy nie usuwaj wpisów — tylko dopisuj.
> Każdy wpis oznaczaj datą w formacie [YYYY-MM-DD].

---

## Architektura

**[2026-05-26] PIVOT STRATEGICZNY — kierunek: predykcja na bazie anomalii**
User zakwestionował założenie ~50% take rate jako potencjalnie mylące (nie zweryfikowane empirycznie — pochodzi z ogólnych szacunków dla loterii europejskich, nie z oficjalnych danych EuroJackpot). Decyzja: na początku kolejnej sesji obmyślić plan rozszerzenia architektury DriftScope od audytu stacjonarności → w kierunku predykcji liczb opartej na wykrytych anomaliach statystycznych (niejednorodność, autocorrelacja, periodyczność). Zachować obecny audit framework jako warstwę bazową. Kluczowe pytania: (1) rzeczywisty take rate z oficjalnych raportów, (2) minimalne effect size eksploatowalne predykcyjnie, (3) komponenty do dodania: posterior Dirichlet per liczba, rolling window, Kelly criterion, alert system.

**[2026-05-26] W1 DONE — core/ + h1_classical.py + testy 27/27**
Zaimplementowano: `core/{config,types,seeds,guards}.py`, `methodology/h1_classical.py`, `ingestion/lotto_scraper.load_seed_csv()`, `tests/test_h1_invariants.py` (10 testów). Wszystkie 27 testów zielone (9 skipped stubs). DoD-1a (KPSS rejects na pełnym szeregu euron) i DoD-1b (BOCPD top-5 pokrywa 2014 ±60 dni + 2022 ±30 dni) spełnione.

**[2026-05-26] pyproject.toml — hatchling jako build backend**
Wybór: hatchling (nie setuptools). Uzasadnienie: lżejszy, natywna obsługa `src/` layout bez dodatkowej konfiguracji, PEP 621 native. `driftscope = "driftscope.cli:app"` jako CLI entrypoint.

**[2026-05-26] numba==0.65.1 — PINNED (nie range)**
`numba==0.65.1` z `==` zamiast `>=0.65,<0.66`. Uzasadnienie: zweryfikowane na Win11 + numpy 2.2.5 (PoC 2026-05-17); ryzyko regresji przy patch update na Windows jest realne. Jedyna biblioteka pinned dokładnie.

**[2026-05-26] test_environment.py — zastąpiony (był PyTorch/CUDA-focused)**
Oryginalny plik sprawdzał torch, nvidia-smi, onnxruntime — nieistotne dla CPU-only pipeline. Zastąpiony testami: Python 3.10.x, numpy 2.x, numba 0.65.x, JIT basic + cache=True, frequency vector primitive, key imports, joblib loky, MSVC Win32. Zachowany plik `scripts/smoke_test.py` jako quick diagnostic (nie pytest).

**[2026-05-26] test_vram_invariants.py — RAM invariants (nie VRAM)**
Nazwa zachowana z template; "VRAM" repurposed na RAM budget niezmienniki (§6.1). Fixtures: `sample_input` (200 DrawRecord-compatible draws), `sample_frequency_vector` (Δ⁴⁹), `load_pipeline` (placeholder dict W1/W4).

**[2026-05-29] Contract revision + W0/W1 review — Ścieżka A utrwalona**
Pivot predykcyjny [2026-05-26] ANULOWANY → Ścieżka A (audyt + 3 czary-mary: recurrence.py W6, BOCPD animation W8; information_theory/MDL → stretch). `preregistration_v2.md` (ACTIVE, v1 SUPERSEDED): korekta daty 2014-10-08→**2014-10-10**, DoD-1 positive/negative control (euronumery vs główne 1-50 jako wbudowany negative control), nowy `recurrence.py` (gap **perm-calibrated** + Nelson-Aalen + EVT Gumbel; NIE lifelines — pandas zakazany, NA ~20 LOC własny), Family B BH→**Benjamini-Yekutieli** (300→450 hyp). **DoD-4 zostaje 3/3** (MDL nie jest niezależny od MMD).
**BOCPD α/hazard zsynchronizowane prereg↔kod** (§2: α=0.1, hazard=0.005): v1 błędnie nosił α=1; faktyczna decyzja [2026-05-26] to α=0.1 (osłabienie sygnału przy α=1 potwierdzone empirycznie: max 0.14 vs 0.47). Korekta transkrypcji, NIE zmiana metody.
**W0 power preview DONE** (`notebooks/00_power_preview.py`): real n=**958** (R1=133/R2=389/R3=436, NIE 1500 — brief poprawiony); positive control POTWIERDZONY (euron [1-8]/[1-10]/[1-12] = granice reżimów); **δ=0.01 per-reżim NIEwykrywalny** global GoF (R1 power=0.10); power = co-primary deliverable; czytać jako UPPER BOUND (FDR nieskorygowane, global GoF heurystyka, tylko signal #1).
**W1 review:** rdzeń BOCPD message-passing **POPRAWNY** (R9 do obniżenia); DoD-1b ±60 dla 2014 (data-CP≈2014-11-28) vs ±30 dla 2022. 27/27 zielonych. 7 commitów d31ba66→3912916.

---

## Rozwiązane problemy

**[2026-05-26] pip SSL cert failure na Win11 + Miniconda**
Objaw: `SSLCertVerificationError` przy `pip install`. Rozwiązanie: `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org`. Przyczyną jest brak certyfikatów systemowych w środowisku Miniconda na Win11.

**[2026-05-26] hatchling wymaga README.md**
`pip install -e ".[dev]"` z hatchling jako build backend failuje z `OSError: Readme file does not exist: README.md` jeśli `readme = "README.md"` w pyproject.toml a plik nie istnieje. Rozwiązanie: stworzyć README.md przed instalacją.

**[2026-05-26] Oś 0 — zielona (11/11 passed)**
`pytest tests/test_environment.py` przeszedł wszystkie 11 testów na docelowym środowisku: Python 3.10.13, NumPy 2.2.5, Numba 0.65.1, @njit basic + cache=True + frequency_vector primitive, wszystkie kluczowe importy, Polars 1.41.0, joblib loky 2-job parallel, MSVC vcruntime140.dll present.

**[2026-05-26] BOCPD — bug w message passing (Adams-MacKay 2007)**
Klasyczny błąd: changepoint term używał `logsumexp(log_R + log_pred)` (ważone po run-length), a powinien używać `log_pred_prior` (predictive pod PRIOR, niezależnie od rozkładu run-length). Skutek błędu: max_cp_prob = H = 0.005 zawsze. Fix: `log_q_cp = log_H + log_pred[0]` (counts[0] = zeros zawsze = prior).

**[2026-05-26] BOCPD alpha — default 0.1, nie 1.0**
alpha=1.0 (Laplace smoothing) za silny prior dla danych EuroJackpot: osłabia sygnał przy zmianie puli. alpha=0.1 (słabszy prior, szybsza adaptacja) daje cp_prob > 0.4 przy pierwszym niewidzianym symbolu. Z alpha=0.1 BOCPD wykrywa zmianę 1-8→1-10 na 2014-11-28 (cp_prob=0.408).

**[2026-05-26] Rzeczywiste daty change-pointów w danych EuroJackpot**
PROJECT_BRIEF wymienia "2014-10-08" i "2022-03-25" jako ground truth — są to daty ZMIANY ZASAD. Daty pierwszych OBSERWOWALNYCH zmian w danych (seed CSV):
- 2014 (1-8→1-10): pierwsza "9" pojawiła się 2014-11-28 (51 dni po zmianie zasad!) — bo losowania 10.10-21.11.2014 trafiały tylko {1-8} przypadkowo
- 2022 (1-10→1-12): pierwsza "11" pojawiła się 2022-03-29 (4 dni po zmianie zasad — niemal natychmiast)
Implikacja dla DoD-1b: tolerancja ±30 dni dla 2014 → nieosiągalna dla BOCPD na danych (używamy ±60 dni w teście).

**[2026-05-26] W0.1 DONE — API zidentyfikowane, seed CSV pobrany**
Zidentyfikowano i zdokumentowano: developers.lotto.pl API (oficjalne PTS), endpoint params, JSON structure, zakres danych (~2017-present). Seed CSV (wynikilotto.net.pl) pobrany i skonwertowany — 958 losowan 2012-2026 w `data/seed/eurojackpot_history.csv`. Deliverable: `scripts/scraper_selectors.md`. HTML scraping porzucony (ECONNREFUSED). Research blocker usunięty.

---

## Aktywne TODO (długoterminowe)

**[2026-05-26] W2 — DriftSim planted signals (następny milestone)**
W1 DONE. W2: `driftsim/null_uniform.py` (uczciwy null generator) + `driftsim/planted_signals.py` (5 sygnałów × 4 effect sizes = 20 scenariuszy, preregistration §6). Cel: calibracja sensitivity/specificity testów H1.

---

## Odrzucone podejścia

**[2026-05-26] HTML scraping eurojackpot.org — PORZUCONE**
`ECONNREFUSED` przy próbie połączenia z eurojackpot.org/archive — blokada IP/bot. Zastąpione przez oficjalne API developers.lotto.pl (Tier 2) + CSV z wynikilotto.net.pl (Tier 1).

**[2026-05-26] API developers.lotto.pl — błędne parametry**
`drawDateFrom`/`drawDateTo` (zakres dat) → 404. `index=0` → 422 (index musi być >0, 1-based). Bez `sort`/`order` → 422. Właściwe parametry: `drawDate=YYYY-MM-DD` (pojedyncza data), `index=1`, `size=1`, `sort=drawDate`, `order=asc`. gameType: musi być `EuroJackpot` (capital E i J — case-sensitive).

---

## Słownik projektu

**DrawRecord** — jedna rekord losowania: `draw_date` (ISO 8601), `main_1..main_5` (liczby 1-50), `euron_1..euron_2` (liczby 1-12 od 2022-03-25, wcześniej 1-10).

**isNewEuroJackpotDraw** — flaga w API developers.lotto.pl; `true` od 2022-03-25 (change-point: pula euroNumbers rozszerzona z 1-10 na 1-12, dwa rysowania tygodniowo zamiast jednego).

**Tier 1/2/3 ingestion** — trójpoziomowa strategia pozyskiwania danych: (1) seed CSV `data/seed/eurojackpot_history.csv`, (2) API live `developers.lotto.pl`, (3) `scripts/manual_import.py` fallback.

---

## Zewnętrzne zależności i integracje

**[2026-05-26] developers.lotto.pl — oficjalne API Polskiego Totalizatora Sportowego**
Auth: nagłówek `"secret": <LOTTO_API_KEY>` (klucz w `.env`, nigdy nie commitować).
Endpoint główny: `GET /api/open/v1/lotteries/draw-results/by-date-per-game?gameType=EuroJackpot&drawDate=YYYY-MM-DD&index=1&size=1&sort=drawDate&order=asc`
Zakres danych: ~2017-09-15 do dziś (2012-2017 niedostępne — 404).
Swagger spec: `https://developers.lotto.pl/swagger/open-api-v1/swagger.json`
SSL: `verify=False` w httpx (Miniconda Win11 brak certyfikatów systemowych).

**[2026-05-26] wynikilotto.net.pl — historyczny CSV EuroJackpot**
URL: `https://www.wynikilotto.net.pl/download/eurojackpot.csv`
Format: `draw_no,DD.MM.YYYY,m1,m2,m3,m4,m5,e1,e2` (brak nagłówka).
Zakres: 2012-03-23 .. dziś (958 losowan stan 2026-05-26). Plik committed jako `data/seed/eurojackpot_history.csv`. Aktualizacja manualna (cotygodniowa).
