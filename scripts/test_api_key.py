"""Quick test weryfikujacy klucz API developers.lotto.pl.

Uruchomienie: python scripts/test_api_key.py
Wymaga: .env z LOTTO_API_KEY
"""
import json
import sys
import os

# Laduj .env recznie (bez pydantic-settings, zeby test byl standalone)
from pathlib import Path

def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"')
    return env


BASE_URL = "https://developers.lotto.pl"
ENV = load_env(Path(__file__).parent.parent / ".env")
API_KEY = ENV.get("LOTTO_API_KEY", os.getenv("LOTTO_API_KEY", ""))


def check(label: str, url: str, params: dict | None = None) -> dict | None:
    import httpx
    import warnings
    headers = {"secret": API_KEY}
    try:
        # verify=False: obejscie bledu SSL certyfikatow Miniconda na Win11
        # W produkcji: uzyc pip install pip-system-certs lub certyfikat CA
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = httpx.get(url, headers=headers, params=params, timeout=15, verify=False)
        print(f"\n{'='*60}")
        print(f"[{label}]")
        print(f"  URL:    {r.url}")
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Wypisz pierwsze 2 elementy jesli lista, albo top-level klucze
            if isinstance(data, list):
                print(f"  Typ:    lista, {len(data)} elementow")
                for item in data[:2]:
                    print(f"  Item:   {json.dumps(item, ensure_ascii=False, indent=4)[:500]}")
            elif isinstance(data, dict):
                print(f"  Klucze: {list(data.keys())}")
                print(f"  JSON:   {json.dumps(data, ensure_ascii=False, indent=4)[:800]}")
            return data
        else:
            print(f"  Body:   {r.text[:300]}")
            return None
    except Exception as exc:
        print(f"\n[{label}] BLAD: {exc}")
        return None


def main() -> int:
    print("=" * 60)
    print("DriftScope — TEST KLUCZA API (developers.lotto.pl)")
    print("=" * 60)

    if not API_KEY or API_KEY == "TUTAJ_WKLEJ_SWOJ_KLUCZ":
        print("\nBRAK KLUCZA: ustaw LOTTO_API_KEY w .env")
        return 1
    print(f"\nKlucz zaladowany: {API_KEY[:6]}...{API_KEY[-4:]}")

    # Test 1: ostatnie wyniki wszystkich gier
    data = check(
        "last-results (wszystkie gry)",
        f"{BASE_URL}/api/open/v1/lotteries/draw-results/last-results",
    )

    # Test 2: ostatnie wyniki per gra (probujemy rozne nazwy EuroJackpot)
    for game_id in ["eurojackpot", "EuroJackpot", "EUROJACKPOT", "ej"]:
        result = check(
            f"last-results-per-game [{game_id}]",
            f"{BASE_URL}/api/open/v1/lotteries/draw-results/last-results-per-game",
            params={"gameType": game_id},
        )
        if result:
            print(f"\n  --> POPRAWNA NAZWA GRY: gameType={game_id!r}")
            break

    # Test 3: paginacja index-based (1-based), 5 najstarszych losowan
    check(
        "by-date-per-game [index=1, size=5, asc]",
        f"{BASE_URL}/api/open/v1/lotteries/draw-results/by-date-per-game",
        params={"gameType": "EuroJackpot", "sort": "drawDate", "order": "asc",
                "index": 1, "size": 5},
    )

    # Test 4: zakres dat (kolo change-pointa 2022-03-25)
    check(
        "by-date-per-game [2022-03-01..2022-04-01, index=1, size=10]",
        f"{BASE_URL}/api/open/v1/lotteries/draw-results/by-date-per-game",
        params={"gameType": "EuroJackpot", "sort": "drawDate", "order": "asc",
                "drawDateFrom": "2022-03-01", "drawDateTo": "2022-04-01",
                "index": 1, "size": 10},
    )

    # Test 5: pierwsze losowanie (2012-03-23)
    check(
        "by-date-per-game [2012-03-01..2012-05-01, index=1, size=5]",
        f"{BASE_URL}/api/open/v1/lotteries/draw-results/by-date-per-game",
        params={"gameType": "EuroJackpot", "sort": "drawDate", "order": "asc",
                "drawDateFrom": "2012-03-01", "drawDateTo": "2012-05-01",
                "index": 1, "size": 5},
    )

    print("\n" + "=" * 60)
    print("Gotowe. Przejrzyj JSON powyzej — szukaj pol:")
    print("  drawDate / date, mainNumbers / numbers, euroNumbers / additionalNumbers")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
