# last_session.md

**Sesja:** 2026-07-20 · 20:30–21:30
**Status:** ✓ Zakończona poprawnie
**Punkt odniesienia (git):** 4f368b5 @ master — ostatni commit KODU
**Uwaga:** na wierzchu siedzi jeszcze commit `chore(session)` z tym plikiem (stąd HEAD ≠ 4f368b5;
to normalne, nie desync). Łącznie **5 commitów ahead origin/master — NIE pushed.**

---

## ▸ NASTĘPNY KROK (zacznij tutaj)

**Wznów skan beacon chain, potem policz audyt:**

```bash
python scripts/fetch_beacon_chain.py --resume --rate 20 --out data/seed
python scripts/randao_audit.py
```

Skan stoi na **19200/96000 slotów (600/3000 epok, 71 pominięć)**, w pełni checkpointowany —
`--resume` podejmie od `cursor` w `data/seed/randao_scan_meta.json`. Pozostałe ~77 tys. slotów
przy ~19 req/s to **~65–70 min w tle**. Potem `scripts/randao_audit.py` drukuje profil pozycji,
test pierwotny (pozycja 31), wtórny (ogon 28–31), omnibus Family B i **wiązanie mocy**.

Kontekst: cała infrastruktura B3 jest zbudowana, przetestowana (16 testów) i zacommitowana —
brakuje wyłącznie danych i raportu. Specyfikacja testu została zacommitowana (`606dee3`) **zanim
wyniki istniały**, więc historia gita dowodzi kolejności.

> ⚠ **NIE ZMIENIAJ DEFINICJI TESTU.** Ani pozycji pierwotnej (31), ani zbioru ogonowego (28–31),
> ani wykluczenia pozycji 0. Kolejność commitów to jedyny mocny argument prerejestracyjny tej
> sekcji i przepisanie testu po zobaczeniu liczb niweczy go bezpowrotnie.
> **Odnotowane jawnie:** przy weryfikacji integralności pliku widziano już częściowe zliczenia
> (poz. 0 = 23 pominięcia vs średnia 1.5 na poz. 1–31 → 15× nadmiar = przewidziany konfundent
> przejścia epoki; poz. 31 = 1, na średniej). Wstępny odczyt to „clear", zgodnie z literaturą.

Po wyniku: sekcja 8 `report.qmd` (World Lottery Audit jest 7, Reproducibility → 9), tabele
README EN/PL, re-render `docs/`, push + CI.

---

## Co zrobiono w tej sesji

- ✓ **Research źródeł beaconów** — drand, NIST 2.0, Ethereum RANDAO: endpointy, formaty, dostępność
  historyczna, limity. Wszystkie sprawdzone na żywo z tej maszyny.
- ✓ **ODRZUCONO zapisany plan B** jako metodologicznie błędny (patrz „Otwarte pytania" → rozstrzygnięte).
  Bateria uniformności na miksie RANDAO ma **moc zerową** wobec withholdingu.
- ✓ **B2 SHIPPED** (`fd79f61`) — `ingestion/beacon_streams.py`, `scripts/fetch_beacons.py`,
  12 testów, 2678 rund drand + 1339 pulsów NIST (~486 KB) zacommitowane. **Oba `clear` na 4 osiach.**
  Wiersze w tabelach README EN/PL + uzasadnienie + nota o wykluczeniu RANDAO.
- ✓ **B3 spec zacommitowana PRZED wynikami** (`606dee3`) — `reporting/randao_audit.py`,
  `ingestion/beacon_chain.py`, 2 CLI, 16 testów. Git dowodzi, że test wybrano bez wglądu w wynik.
- ✓ **Analiza mocy** — tabela epoki × wykrywalny atakujący; 3000 epok → 1 wstrzymanie / 259 epok.
- ✓ **Bug AIMD znaleziony i naprawiony w locie** (`8afe77a`) — czysty backoff zabetonował skan
  na 4 req/s; po poprawce ~19 req/s. 2 testy regresyjne.
- ✓ **Sync drzewa CLAUDE.md** (`4f368b5`) — ścieżki A i B, 25→28 plików testowych.
- ✓ Suite **284 → 312 collected**; ruff + mypy --strict czyste w zakresie CI.

## Co zostało (backlog sesji)

- ⟳ **B3: skan (20% zrobione) + audyt + raport** — patrz NASTĘPNY KROK.
- ⟳ **Push 4 commitów** — nic nie poszło na origin w tej sesji; CI nie było uruchamiane.
- ⟳ **Migracja i18n:** `scripts/` (Batch 6; nowe `fetch_beacons`/`fetch_beacon_chain`/`randao_audit`
  już EN), flip konwencji CLAUDE.md („Język komentarzy: polski"→EN), `preregistration_v7.md`,
  `demo/app.py`. `notebooks/` świadomie poza zakresem.
- ⟳ **Zastane 9 błędów ruff w `scripts/make_readme_assets.py`** — poza zakresem CI (`ruff check src tests`),
  nieblokujące, ale warto posprzątać przy Batch 6.
- ⟳ Stretch A: strumienie bonus (k=1), UK Lotto (licencja mirrorów), rodzynki rygoru.

## Aktywne pliki

- NOWE (zacommitowane): `src/driftscope/ingestion/{beacon_streams,beacon_chain}.py`,
  `src/driftscope/reporting/randao_audit.py`, `scripts/{fetch_beacons,fetch_beacon_chain,randao_audit}.py`,
  `tests/{test_beacon_streams,test_randao_audit}.py`, `data/seed/{drand,nist}_beacon.csv`.
- ZMIENIONE (zacommitowane): `reporting/prng_benchmark.py` (+klasa `beacon`), `scripts/prng_benchmark.py`,
  `tests/test_prng_benchmark.py`, `README.md`/`README.pl.md`, `CLAUDE.md`.
- **ZACOMMITOWANE:** `data/seed/randao_missed_slots.csv` + `randao_scan_meta.json` — skan częściowy
  (19200/96000, `complete = False`). Wcześniejsza decyzja o nieśledzeniu **odwrócona**: rekord jest
  samoopisujący się (`ScanMeta.cursor`/`.complete`, `load_scan` waliduje względem metadanych), a pliki
  nieśledzone nie przeżywają `git clean` ani zmiany maszyny. Ciągłość > purystyczne `data/seed/`.

## Otwarte pytania

- **ROZSTRZYGNIĘTE w tej sesji:** (1) plan B z poprzedniej sesji odrzucony jako metodologicznie
  nieadekwatny; (2) prereg v8 — user zdecydował **NIE**, wystarczy commit przed wynikami.
- Nierozstrzygnięte: czy po B3 wracamy do stretch A (UK Lotto / bonus streams), czy zamykamy
  wdrożenie bojowe i wracamy do i18n Batch 6.
- UK Lotto: mirror z pełną historią i jego licencja — nadal TBD (odziedziczone).

## Do MEMORY.md (przeniesiono)

- Projektowy `MEMORY.md` (Architektura): **[2026-07-20]** — pełny wpis: korekta planu B (dlaczego
  bateria uniformności ma moc zerową wobec withholdingu), właściwy obserwowalny (pozycja pominięcia
  w epoce), konfundent pozycji 0 i dlaczego czyni test ogonowy czystym, decyzja o braku prereg v8,
  moc jako obowiązkowy element wyniku null, B2 clear/clear, DoD-6 bez ziarna dla beaconów,
  zmierzona dostępność danych (stany przycięte / nagłówki 2M+), pułapka burst-vs-podtrzymany rate
  limit, bug AIMD i lekcja, reguła 404-vs-nie-wiemy w ingestion, stan skanu. HEAD=`4f368b5`.
