"""Smoke testy reporting/plots_static.py — figury renderują się headless (Agg)."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np

from driftscope.core.types import DrawRecord
from driftscope.reporting.plots_static import (
    plot_bocpd_changepoints,
    plot_control_comparison,
)


def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2020, 1, 7),
) -> list[DrawRecord]:
    """n DrawRecord z losowymi euronumerami z euron_pool (wzorzec z test_h1_invariants)."""
    rng = np.random.default_rng(seed)
    draws = []
    for i in range(n):
        main = sorted(int(x) for x in rng.choice(range(1, 51), 5, replace=False))
        euron = sorted(int(x) for x in rng.choice(euron_pool, 2, replace=False))
        draws.append(
            DrawRecord(
                draw_date=start_date + timedelta(weeks=i),
                main_1=main[0], main_2=main[1], main_3=main[2],
                main_4=main[3], main_5=main[4],
                euron_1=euron[0], euron_2=euron[1],
            )
        )
    return draws


def _planted_changepoint_draws() -> list[DrawRecord]:
    """Strumień z wszczepionym change-pointem puli euron (1-8 → 8-12) po 200 losowaniach."""
    pre = _make_draws(list(range(1, 9)), 200, seed=10, start_date=date(2014, 1, 3))
    post_start = pre[-1].draw_date + timedelta(weeks=1)
    post = _make_draws(list(range(8, 13)), 200, seed=11, start_date=post_start)
    return pre + post


def test_plot_bocpd_changepoints_saves_png(tmp_path: Path) -> None:
    """Figura renderuje się, plik PNG zapisany i niepusty (bez wyjątku, headless)."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "bocpd_euron.png"

    result = plot_bocpd_changepoints(draws, field="euron", out_path=out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_bocpd_changepoints_default_path(tmp_path: Path, monkeypatch) -> None:
    """Domyślna ścieżka = artifacts/bocpd_{field}.png; katalog tworzony w razie braku."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    result = plot_bocpd_changepoints(draws, field="euron")

    assert result == Path("artifacts") / "bocpd_euron.png"
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_bocpd_changepoints_main_field(tmp_path: Path) -> None:
    """Pole 'main' (N=50, K=5) renderuje się tak samo jak euron."""
    draws = _make_draws(list(range(1, 13)), 150, seed=3)
    out = tmp_path / "bocpd_main.png"

    result = plot_bocpd_changepoints(draws, field="main", out_path=out)

    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_control_comparison_saves_png(tmp_path: Path) -> None:
    """Figura pos/neg control (2 panele euron+main) renderuje się i zapisuje."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "control_comparison.png"

    result = plot_control_comparison(draws, out_path=out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_control_comparison_default_path(tmp_path: Path, monkeypatch) -> None:
    """Domyślna ścieżka = artifacts/control_comparison.png."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    result = plot_control_comparison(draws)

    assert result == Path("artifacts") / "control_comparison.png"
    assert result.exists()
