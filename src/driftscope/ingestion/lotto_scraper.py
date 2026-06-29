"""Ingestion — loading EuroJackpot data: seed CSV + developers.lotto.pl API.

Tier 1: load_seed_csv() — loads data/seed/eurojackpot_history.csv → list[DrawRecord]
Tier 2: fetch_draw_by_date() — lotto.pl API (stub, implementation W1+)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from driftscope.core.types import DrawRecord


def load_seed_csv(path: Path | None = None) -> list[DrawRecord]:
    """Loads the seed CSV → list[DrawRecord].

    CSV format: draw_date,main_1,main_2,main_3,main_4,main_5,euron_1,euron_2
    Source: data/seed/eurojackpot_history.csv (958 draws, 2012-2026).
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
    """Loads a generic seed CSV (a k-of-`pool_size` game) → list[DrawRecord].

    CSV format: the first column = `draw_date`, ALL remaining columns = the draw numbers
    (e.g. Multi Multi: `draw_date,n1,...,n20`). The loader is agnostic to the number of
    number columns — it works for any k (MM=20, but reusable for a 3rd game+).

    `pool_size` (the main pool size, MM=80) is carried by each `DrawRecord`
    (see `DrawRecord.generic`), so detectors derive the pool/k from the data. Range
    validation 1..pool_size is enforced by `DrawRecord._validate_shape`.
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
# Tier 2 — developers.lotto.pl API (stub, W1+)
# ---------------------------------------------------------------------------

def fetch_draw_by_date(draw_date: date, api_key: str) -> DrawRecord | None:
    """Fetches a single draw result from the developers.lotto.pl API.

    Stub — implementation in W1+. Documentation: scripts/scraper_selectors.md.
    """
    raise NotImplementedError(
        "fetch_draw_by_date: stub — implement with httpx + tenacity (W1+)"
    )
