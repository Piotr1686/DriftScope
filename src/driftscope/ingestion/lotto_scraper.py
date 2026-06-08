"""Ingestion — wczytywanie danych EuroJackpot: seed CSV + API developers.lotto.pl.

Tier 1: load_seed_csv() — wczytuje data/seed/eurojackpot_history.csv → list[DrawRecord]
Tier 2: fetch_draw_by_date() — API lotto.pl (stub, implementacja W1+)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from driftscope.core.types import DrawRecord


def load_seed_csv(path: Path | None = None) -> list[DrawRecord]:
    """Wczytuje seed CSV → list[DrawRecord].

    Format CSV: draw_date,main_1,main_2,main_3,main_4,main_5,euron_1,euron_2
    Źródło: data/seed/eurojackpot_history.csv (958 losowan 2012-2026).
    """
    if path is None:
        from driftscope.core.config import settings
        path = settings.data_seed_path

    df = pl.read_csv(
        path,
        schema_overrides={
            "draw_date": pl.Utf8,
            "main_1": pl.Int32,
            "main_2": pl.Int32,
            "main_3": pl.Int32,
            "main_4": pl.Int32,
            "main_5": pl.Int32,
            "euron_1": pl.Int32,
            "euron_2": pl.Int32,
        },
    )

    draws: list[DrawRecord] = []
    for row in df.iter_rows(named=True):
        draws.append(
            DrawRecord(
                draw_date=date.fromisoformat(row["draw_date"]),
                main_1=int(row["main_1"]),
                main_2=int(row["main_2"]),
                main_3=int(row["main_3"]),
                main_4=int(row["main_4"]),
                main_5=int(row["main_5"]),
                euron_1=int(row["euron_1"]),
                euron_2=int(row["euron_2"]),
            )
        )

    return draws


def load_generic_seed_csv(path: Path, pool_size: int) -> list[DrawRecord]:
    """Wczytuje generyczny seed CSV (gra k-z-`pool_size`) → list[DrawRecord].

    Format CSV: pierwsza kolumna = `draw_date`, WSZYSTKIE pozostałe = liczby losowania
    (np. Multi Multi: `draw_date,n1,...,n20`). Loader jest agnostyczny co do liczby
    kolumn liczb — działa dla dowolnego k (MM=20, ale reusable na grę 3+).

    `pool_size` (rozmiar puli głównej, MM=80) jest niesiony przez każdy `DrawRecord`
    (zob. `DrawRecord.generic`), więc detektory wyprowadzają pulę/k z danych. Walidację
    zakresów 1..pool_size egzekwuje `DrawRecord._validate_shape`.
    """
    df = pl.read_csv(path)
    date_col = df.columns[0]
    num_cols = df.columns[1:]

    draws: list[DrawRecord] = []
    for row in df.iter_rows(named=True):
        numbers = [int(row[c]) for c in num_cols if row[c] is not None]
        draws.append(
            DrawRecord.generic(
                draw_date=date.fromisoformat(str(row[date_col])),
                numbers=numbers,
                pool_size=pool_size,
            )
        )

    return draws


# ---------------------------------------------------------------------------
# Tier 2 — API developers.lotto.pl (stub, W1+)
# ---------------------------------------------------------------------------

def fetch_draw_by_date(draw_date: date, api_key: str) -> DrawRecord | None:
    """Pobiera wynik jednego losowania z API developers.lotto.pl.

    Stub — implementacja w W1+. Dokumentacja: scripts/scraper_selectors.md.
    """
    raise NotImplementedError(
        "fetch_draw_by_date: stub — zaimplementuj z httpx + tenacity (W1+)"
    )
