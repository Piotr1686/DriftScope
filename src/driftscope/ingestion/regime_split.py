"""Regime split 2014/2022 → regime_{1,2,3}.parquet (pre-rejestrowany prereg_v6 §1).

Granice reżimów = DATY ZMIANY REGUL EuroJackpot (pre-rejestrowane, NIE data-informed):

  R1: 2012-03-23 .. 2014-10-03   (5/50 + 2/8)   — draw_date <  2014-10-10
  R2: 2014-10-10 .. 2022-03-18   (5/50 + 2/10)  — 2014-10-10 ≤ draw_date < 2022-03-25
  R3: 2022-03-25 .. obecnie      (5/50 + 2/12)  — draw_date ≥  2022-03-25

UWAGA granica 2014: pierwsze losowanie wg nowych regul (pula euron 8→10) to **2014-10-10**
(piątek), NIE 2014-10-08 (środa — PROJECT_BRIEF historycznie błędnie). Granica jest
PRZEDZIALEM POLOTWARTYM [start, koniec): losowanie DOKLADNIE w dacie granicznej należy do
reżimu NOWEGO (2014-10-10 → R2, 2022-03-25 → R3). Patrz MEMORY.md regime_boundary_2014.

Moduł jest czystą warstwą danych: granice są już w prereg_v6 §1, więc split NIE wprowadza
nowej decyzji metodologicznej (nie podlega dyscyplinie prereg §0).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from driftscope.core.types import DrawRecord, RegimeSpec

# Granice = daty zmiany regul (prereg_v6 §1). Przedział półotwarty [start, koniec).
BOUNDARY_2014 = date(2014, 10, 10)  # 8→10 euronumerów (piątek, NIE 2014-10-08)
BOUNDARY_2022 = date(2022, 3, 25)   # 10→12 euronumerów

# Kolejność = chronologiczna; klucze zgodne z prereg_v6 §1 (R1/R2/R3).
REGIME_SPECS: tuple[RegimeSpec, ...] = (
    RegimeSpec(name="R1", start_date=date(2012, 3, 23), end_date=date(2014, 10, 3)),
    RegimeSpec(name="R2", start_date=BOUNDARY_2014, end_date=date(2022, 3, 18)),
    RegimeSpec(name="R3", start_date=BOUNDARY_2022, end_date=None),
)
REGIME_LABELS: tuple[str, ...] = tuple(spec.name for spec in REGIME_SPECS)

# Mapowanie etykieta reżimu → nazwa pliku artefaktu (regime_1/2/3.parquet wg CLAUDE.md).
_PARQUET_NAMES: dict[str, str] = {"R1": "regime_1", "R2": "regime_2", "R3": "regime_3"}


def regime_of(draw_date: date) -> str:
    """Etykieta reżimu ("R1"/"R2"/"R3") dla daty losowania (granice półotwarte)."""
    if draw_date < BOUNDARY_2014:
        return "R1"
    if draw_date < BOUNDARY_2022:
        return "R2"
    return "R3"


def split_by_regime(draws: list[DrawRecord]) -> dict[str, list[DrawRecord]]:
    """Dzieli strumień losowań na 3 reżimy regul (prereg_v6 §1).

    Partycja KOMPLETNA i ROZLACZNA: każde losowanie trafia do dokładnie jednego reżimu,
    suma = wejście. Kolejność wewnątrz reżimu zachowana (stabilna). Klucze ZAWSZE obecne
    (R1/R2/R3) — reżim bez losowań → pusta lista (np. przy niepełnym strumieniu).

    Returns: dict {"R1": [...], "R2": [...], "R3": [...]}.
    """
    out: dict[str, list[DrawRecord]] = {label: [] for label in REGIME_LABELS}
    for d in draws:
        out[regime_of(d.draw_date)].append(d)
    return out


def _draws_to_frame(draws: list[DrawRecord]) -> pl.DataFrame:
    """list[DrawRecord] → Polars DataFrame (kolumny jak seed CSV; draw_date jako Date)."""
    return pl.DataFrame(
        {
            "draw_date": [d.draw_date for d in draws],
            "main_1": [d.main_1 for d in draws],
            "main_2": [d.main_2 for d in draws],
            "main_3": [d.main_3 for d in draws],
            "main_4": [d.main_4 for d in draws],
            "main_5": [d.main_5 for d in draws],
            "euron_1": [d.euron_1 for d in draws],
            "euron_2": [d.euron_2 for d in draws],
        },
        schema={
            "draw_date": pl.Date,
            "main_1": pl.Int32, "main_2": pl.Int32, "main_3": pl.Int32,
            "main_4": pl.Int32, "main_5": pl.Int32,
            "euron_1": pl.Int32, "euron_2": pl.Int32,
        },
    )


def write_regime_parquet(
    regimes: dict[str, list[DrawRecord]],
    artifacts_dir: Path | None = None,
) -> dict[str, Path]:
    """Zapisuje każdy reżim do artifacts/regime_{1,2,3}.parquet (Zstd).

    Deterministyczne: kolejność wierszy = kolejność losowań w reżimie (split jest stabilny);
    Zstd zgodne z polityką storage (CLAUDE.md). Reżim bez losowań → plik z pustą ramką
    (zachowany schemat). `artifacts_dir` None → `settings.artifacts_dir`.

    Returns: dict {etykieta reżimu → ścieżka zapisanego pliku}.
    """
    if artifacts_dir is None:
        from driftscope.core.config import settings
        artifacts_dir = settings.artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for label in REGIME_LABELS:
        path = artifacts_dir / f"{_PARQUET_NAMES[label]}.parquet"
        _draws_to_frame(regimes.get(label, [])).write_parquet(path, compression="zstd")
        written[label] = path
    return written
