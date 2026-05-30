# scraper_selectors.md — W0.1 Scraper Probe

**Data:** 2026-05-26  
**Status:** DONE — API zidentyfikowane, seed CSV pobrany

---

## Decyzja: API zamiast HTML scrapera

Źródło danych: **developers.lotto.pl** (oficjalne API Polskiego Totalizatora Sportowego)  
Autoryzacja: nagłówek `"secret": <LOTTO_API_KEY>` (klucz z .env)  
SSL: `verify=False` tymczasowo (Miniconda Win11 nie ma certyfikatów systemowych — do poprawy)

HTML scraping eurojackpot.org porzucony — ECONNREFUSED (blokada IP/bot).

---

## Endpointy EuroJackpot

### Ostatnie losowanie
```
GET https://developers.lotto.pl/api/open/v1/lotteries/draw-results/last-results-per-game
Params: gameType=EuroJackpot
Auth:   secret: <key>
```

### Losowanie dla konkretnej daty (główny endpoint do ingestion)
```
GET https://developers.lotto.pl/api/open/v1/lotteries/draw-results/by-date-per-game
Params (wymagane):
  gameType  = EuroJackpot        (case-sensitive, wielkie E i J)
  drawDate  = YYYY-MM-DD         (ISO 8601, pojedyncza data)
  index     = 1                  (paginacja 1-based)
  size      = 1                  (jedno losowanie per dzień)
  sort      = drawDate
  order     = asc | desc
Params (opcjonalne):
  hour, minute
```

### Wszystkie gry w danym dniu
```
GET https://developers.lotto.pl/api/open/v1/lotteries/draw-results/by-date
Params (opcjonalne):
  drawDate  = YYYY-MM-DD
```

---

## Struktura odpowiedzi JSON (EuroJackpot)

```json
{
  "totalRows": 1,
  "items": [
    {
      "drawSystemId": 237,
      "drawDate": "2022-03-25T19:00:00Z",
      "gameType": "EuroJackpot",
      "multiplierValue": 0,
      "isNewEuroJackpotDraw": true,
      "results": [
        {
          "drawDate": "2022-03-25T19:00:00Z",
          "drawSystemId": 237,
          "gameType": "EuroJackpot",
          "resultsJson": [46, 11, 35, 31, 20],
          "specialResults": [6, 10]
        }
      ]
    }
  ]
}
```

**Mapowanie na DrawRecord:**
| API pole | DrawRecord pole | Uwagi |
|---|---|---|
| `items[0].drawDate` | `draw_date` | ISO 8601, konwersja do YYYY-MM-DD |
| `items[0].results[0].resultsJson` | `main_1..main_5` | lista 5 liczb 1-50, nie jest sortowana |
| `items[0].results[0].specialResults` | `euron_1..euron_2` | lista 2 liczb 1-12 |
| `isNewEuroJackpotDraw` | (metadata) | `true` od 2022-03-25 (pula 1-12 zamiast 1-10) |

---

## Zakres danych w API

| Zakres | Dostępność |
|---|---|
| 2012-03-23 .. 2017-09 | **BRAK w API** (404) |
| 2017-09-15 .. dziś | Dostępne (z drobnymi lukami w 2017) |
| 2022-03-25 | Potwierdzony change-point (`isNewEuroJackpotDraw: true`) |

---

## Strategia ingestion (trójpoziomowa)

### Tier 1 — seed CSV (historyczny, 2012-2026)
**Źródło:** `https://www.wynikilotto.net.pl/download/eurojackpot.csv`  
**Plik:** `data/seed/eurojackpot_history.csv`  
**Zawartość:** 958 losowan, 2012-03-23 do 2026-05-26  
**Pobrany:** 2026-05-26 (committed do repo, aktualizacja manualna)  
**Format źródłowy:** `draw_no,DD.MM.YYYY,m1,m2,m3,m4,m5,e1,e2` (brak nagłówka)  
**Format docelowy:** `draw_date,main_1..5,euron_1..2` (ISO 8601)

### Tier 2 — API live (lotto.pl, ~2017-dziś)
**Użycie:** cotygodniowe update (wtorek/piątek wieczorem)  
**Metoda:** pętla po datach losowan → `by-date-per-game?gameType=EuroJackpot&drawDate=...`  
**Rate limit:** 2s delay między requestami (SCRAPER_RATE_LIMIT_DELAY_SEC)

### Tier 3 — manual import
**Plik:** `scripts/manual_import.py`  
**Użycie:** fallback gdy API i CSV niedostępne

---

## Harmonogram losowan EuroJackpot
- 2012-03-23 .. 2022-03-22: **tylko piątki**
- 2022-03-25 .. dziś: **wtorek + piątek** (zmiana zasad, `isNewEuroJackpotDraw=true`)

---

## Znane problemy SSL
```
SSLCertVerificationError na Miniconda Win11
Rozwiązanie tymczasowe: verify=False w httpx
Docelowe: pip install pip-system-certs  (lub certifi z Windows store)
```

---

## Plik Swagger spec
`https://developers.lotto.pl/swagger/open-api-v1/swagger.json`  
(znaleziony przez inspekcję HTML: `/swagger/index.html` → configObject.urls)
