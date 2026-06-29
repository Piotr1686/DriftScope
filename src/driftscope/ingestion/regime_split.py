"""Regime split 2014/2022 → regime_{1,2,3}.parquet (pre-registered prereg_v6 §1).

Regime boundaries = EuroJackpot RULE-CHANGE DATES (pre-registered, NOT data-informed):

  R1: 2012-03-23 .. 2014-10-03   (5/50 + 2/8)   — draw_date <  2014-10-10
  R2: 2014-10-10 .. 2022-03-18   (5/50 + 2/10)  — 2014-10-10 ≤ draw_date < 2022-03-25
  R3: 2022-03-25 .. present       (5/50 + 2/12)  — draw_date ≥  2022-03-25

NOTE on the 2014 boundary: the first draw under the new rules (euron pool 8→10) is **2014-10-10**
(Friday), NOT 2014-10-08 (Wednesday — PROJECT_BRIEF historically wrong). The boundary is a
HALF-OPEN INTERVAL [start, end): a draw EXACTLY on the boundary date belongs to the NEW regime
(2014-10-10 → R2, 2022-03-25 → R3). See MEMORY.md regime_boundary_2014.

This module is a pure data layer: the boundaries already live in prereg_v6 §1, so the split does
NOT introduce a new methodological decision (not subject to the prereg §0 discipline).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from driftscope.core.types import DrawRecord, RegimeSpec

# Boundaries = rule-change dates (prereg_v6 §1). Half-open interval [start, end).
BOUNDARY_2014 = date(2014, 10, 10)  # 8→10 euro numbers (Friday, NOT 2014-10-08)
BOUNDARY_2022 = date(2022, 3, 25)   # 10→12 euro numbers

# Order = chronological; keys consistent with prereg_v6 §1 (R1/R2/R3).
REGIME_SPECS: tuple[RegimeSpec, ...] = (
    RegimeSpec(name="R1", start_date=date(2012, 3, 23), end_date=date(2014, 10, 3)),
    RegimeSpec(name="R2", start_date=BOUNDARY_2014, end_date=date(2022, 3, 18)),
    RegimeSpec(name="R3", start_date=BOUNDARY_2022, end_date=None),
)
REGIME_LABELS: tuple[str, ...] = tuple(spec.name for spec in REGIME_SPECS)

# Mapping regime label → artifact file name (regime_1/2/3.parquet per CLAUDE.md).
_PARQUET_NAMES: dict[str, str] = {"R1": "regime_1", "R2": "regime_2", "R3": "regime_3"}


def regime_of(draw_date: date) -> str:
    """Regime label ("R1"/"R2"/"R3") for a draw date (half-open boundaries)."""
    if draw_date < BOUNDARY_2014:
        return "R1"
    if draw_date < BOUNDARY_2022:
        return "R2"
    return "R3"


def split_by_regime(draws: list[DrawRecord]) -> dict[str, list[DrawRecord]]:
    """Splits a draw stream into the 3 rule regimes (prereg_v6 §1).

    The partition is COMPLETE and DISJOINT: every draw lands in exactly one regime, and the
    union equals the input. Within-regime order is preserved (stable). Keys are ALWAYS present
    (R1/R2/R3) — a regime with no draws → an empty list (e.g. for a partial stream).

    Returns: dict {"R1": [...], "R2": [...], "R3": [...]}.
    """
    out: dict[str, list[DrawRecord]] = {label: [] for label in REGIME_LABELS}
    for d in draws:
        out[regime_of(d.draw_date)].append(d)
    return out


def _draws_to_frame(draws: list[DrawRecord]) -> pl.DataFrame:
    """list[DrawRecord] → Polars DataFrame (columns like the seed CSV; draw_date as Date)."""
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
    """Writes each regime to artifacts/regime_{1,2,3}.parquet (Zstd).

    Deterministic: row order = draw order within the regime (the split is stable);
    Zstd consistent with the storage policy (CLAUDE.md). A regime with no draws → a file with
    an empty frame (schema preserved). `artifacts_dir` None → `settings.artifacts_dir`.

    Returns: dict {regime label → path of the written file}.
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
