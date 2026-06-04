"""Regime split (prereg_v6 §1) — granice 2014-10-10 / 2022-03-25, partycja, persystencja.

Split jest czystą warstwą danych: testujemy poprawność granic (przedział półotwarty),
kompletność/rozłączność partycji oraz determinizm zapisu Parquet. Na realnym seed CSV
sprawdzamy znane liczności reżimów (133/389/436, MEMORY.md W0).
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from driftscope.core.types import DrawRecord
from driftscope.ingestion.regime_split import (
    BOUNDARY_2014,
    BOUNDARY_2022,
    regime_of,
    split_by_regime,
    write_regime_parquet,
)

_SEED_CSV = Path(__file__).parent.parent / "data" / "seed" / "eurojackpot_history.csv"


def _draw(d: date) -> DrawRecord:
    """Minimalny poprawny DrawRecord o zadanej dacie (liczby nieistotne dla splitu)."""
    return DrawRecord(
        draw_date=d,
        main_1=1, main_2=2, main_3=3, main_4=4, main_5=5,
        euron_1=1, euron_2=2,
    )


# ---------------------------------------------------------------------------
# regime_of — granice (przedział półotwarty [start, koniec))
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("d", "expected"),
    [
        (date(2012, 3, 23), "R1"),                          # pierwszy losowanie
        (BOUNDARY_2014 - timedelta(days=1), "R1"),          # 2014-10-09 → wciąż R1
        (BOUNDARY_2014, "R2"),                              # 2014-10-10 → NOWY reżim
        (BOUNDARY_2022 - timedelta(days=1), "R2"),          # 2022-03-24 → wciąż R2
        (BOUNDARY_2022, "R3"),                              # 2022-03-25 → NOWY reżim
        (date(2026, 1, 1), "R3"),
    ],
)
def test_regime_of_boundaries(d: date, expected: str) -> None:
    assert regime_of(d) == expected


# ---------------------------------------------------------------------------
# split_by_regime — partycja kompletna i rozłączna
# ---------------------------------------------------------------------------

def test_split_keys_always_present_even_when_empty() -> None:
    """Klucze R1/R2/R3 zawsze obecne; reżim bez losowań → pusta lista."""
    only_r3 = [_draw(date(2023, 1, 6)), _draw(date(2023, 1, 13))]
    parts = split_by_regime(only_r3)
    assert set(parts) == {"R1", "R2", "R3"}
    assert parts["R1"] == [] and parts["R2"] == []
    assert len(parts["R3"]) == 2


def test_split_is_complete_and_disjoint() -> None:
    """Suma reżimów = wejście; brak duplikatów między reżimami."""
    draws = [
        _draw(date(2013, 5, 3)),   # R1
        _draw(date(2014, 10, 9)),  # R1 (dzień przed granicą)
        _draw(date(2014, 10, 10)), # R2 (granica)
        _draw(date(2020, 6, 5)),   # R2
        _draw(date(2022, 3, 25)),  # R3 (granica)
        _draw(date(2025, 9, 9)),   # R3
    ]
    parts = split_by_regime(draws)
    total = sum(len(v) for v in parts.values())
    assert total == len(draws)
    assert [d.draw_date for d in parts["R1"]] == [date(2013, 5, 3), date(2014, 10, 9)]
    assert [d.draw_date for d in parts["R2"]] == [date(2014, 10, 10), date(2020, 6, 5)]
    assert [d.draw_date for d in parts["R3"]] == [date(2022, 3, 25), date(2025, 9, 9)]


def test_split_preserves_within_regime_order() -> None:
    """Kolejność wewnątrz reżimu = kolejność wejścia (stabilność)."""
    draws = [_draw(date(2023, 1, 6) + timedelta(weeks=i)) for i in range(5)]
    parts = split_by_regime(draws)
    assert [d.draw_date for d in parts["R3"]] == [d.draw_date for d in draws]


# ---------------------------------------------------------------------------
# Realny seed CSV — znane liczności reżimów (MEMORY.md W0: 133/389/436)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_split_real_seed_csv_counts() -> None:
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    parts = split_by_regime(draws)
    counts = {k: len(v) for k, v in parts.items()}
    assert sum(counts.values()) == len(draws)
    assert counts == {"R1": 133, "R2": 389, "R3": 436}


# ---------------------------------------------------------------------------
# write_regime_parquet — persystencja + determinizm
# ---------------------------------------------------------------------------

def test_write_regime_parquet_roundtrip(tmp_path: Path) -> None:
    """Zapis → 3 pliki regime_{1,2,3}.parquet; odczyt zwraca te same wiersze."""
    draws = [
        _draw(date(2013, 5, 3)),
        _draw(date(2020, 6, 5)),
        _draw(date(2025, 9, 9)),
    ]
    parts = split_by_regime(draws)
    written = write_regime_parquet(parts, artifacts_dir=tmp_path)

    assert {p.name for p in written.values()} == {
        "regime_1.parquet", "regime_2.parquet", "regime_3.parquet"
    }
    for label, path in written.items():
        assert path.exists()
        df = pl.read_parquet(path)
        assert df.height == len(parts[label])


def test_write_regime_parquet_deterministic(tmp_path: Path) -> None:
    """Dwa zapisy tych samych danych → bit-identyczne pliki (DoD-6)."""
    draws = [_draw(date(2023, 1, 6) + timedelta(weeks=i)) for i in range(10)]
    parts = split_by_regime(draws)

    dir_a, dir_b = tmp_path / "a", tmp_path / "b"
    write_regime_parquet(parts, artifacts_dir=dir_a)
    write_regime_parquet(parts, artifacts_dir=dir_b)

    for name in ("regime_1.parquet", "regime_2.parquet", "regime_3.parquet"):
        assert (dir_a / name).read_bytes() == (dir_b / name).read_bytes()
