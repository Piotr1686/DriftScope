"""Smoke testy reporting/plots_interactive.py — figury Plotly buduja sie i zapisuja HTML."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from driftscope.core.types import DrawRecord
from driftscope.reporting.plots_interactive import (
    interactive_bocpd_figure,
    interactive_control_comparison,
)


def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2020, 1, 7),
) -> list[DrawRecord]:
    """n DrawRecord z losowymi euronumerami z euron_pool (wzorzec z test_plots_static)."""
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
    """Strumien z wszczepionym change-pointem puli euron (1-8 → 8-12) po 200 losowaniach."""
    pre = _make_draws(list(range(1, 9)), 200, seed=10, start_date=date(2014, 1, 3))
    post_start = pre[-1].draw_date + timedelta(weeks=1)
    post = _make_draws(list(range(8, 13)), 200, seed=11, start_date=post_start)
    return pre + post


def test_interactive_bocpd_figure_returns_figure() -> None:
    """Zwraca go.Figure z >=1 sladem (krzywa cp_prob)."""
    draws = _planted_changepoint_draws()

    fig = interactive_bocpd_figure(draws, field="euron")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # co najmniej krzywa cp_prob


def test_interactive_bocpd_figure_saves_html(tmp_path: Path) -> None:
    """out_path zapisuje niepusty samodzielny HTML z plotly div."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "bocpd_euron.html"

    interactive_bocpd_figure(draws, field="euron", out_path=out)

    assert out.exists()
    assert out.stat().st_size > 0
    html = out.read_text(encoding="utf-8")
    assert "plotly" in html.lower()


def test_interactive_bocpd_figure_main_field(tmp_path: Path) -> None:
    """Pole 'main' (N=50, K=5) buduje sie tak samo jak euron."""
    draws = _make_draws(list(range(1, 13)), 150, seed=3)
    out = tmp_path / "bocpd_main.html"

    fig = interactive_bocpd_figure(draws, field="main", out_path=out)

    assert isinstance(fig, go.Figure)
    assert out.exists()
    assert out.stat().st_size > 0


def test_interactive_control_comparison_two_panels(tmp_path: Path) -> None:
    """Figura pos/neg control ma 2 panele (subplot) i zapisuje HTML."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "control_comparison.html"

    fig = interactive_control_comparison(draws, out_path=out)

    assert isinstance(fig, go.Figure)
    # 2 osie y (subplot 2 wiersze) → "yaxis" + "yaxis2"
    assert fig.layout.yaxis is not None and fig.layout.yaxis2 is not None
    assert out.exists()
    assert out.stat().st_size > 0


def test_interactive_bocpd_figure_no_out_path_does_not_write(tmp_path: Path, monkeypatch) -> None:
    """Bez out_path nie powstaje zaden plik — funkcja zwraca tylko Figure."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    fig = interactive_bocpd_figure(draws, field="euron")

    assert isinstance(fig, go.Figure)
    assert list(tmp_path.iterdir()) == []  # nic nie zapisane
