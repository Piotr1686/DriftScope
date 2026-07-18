"""Smoke tests for reporting/plots_interactive.py — Plotly figures build and save HTML."""
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
    """n DrawRecord with random euro numbers from euron_pool (pattern from test_plots_static)."""
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
    """Stream with a planted euron pool change-point (1-8 → 8-12) after 200 draws."""
    pre = _make_draws(list(range(1, 9)), 200, seed=10, start_date=date(2014, 1, 3))
    post_start = pre[-1].draw_date + timedelta(weeks=1)
    post = _make_draws(list(range(8, 13)), 200, seed=11, start_date=post_start)
    return pre + post


def test_interactive_bocpd_figure_returns_figure() -> None:
    """Returns a go.Figure with >=1 trace (the cp_prob curve)."""
    draws = _planted_changepoint_draws()

    fig = interactive_bocpd_figure(draws, field="euron")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # at least the cp_prob curve


def test_interactive_bocpd_figure_saves_html(tmp_path: Path) -> None:
    """out_path writes a non-empty standalone HTML with a plotly div."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "bocpd_euron.html"

    interactive_bocpd_figure(draws, field="euron", out_path=out)

    assert out.exists()
    assert out.stat().st_size > 0
    html = out.read_text(encoding="utf-8")
    assert "plotly" in html.lower()


def test_interactive_bocpd_figure_main_field(tmp_path: Path) -> None:
    """The 'main' field (N=50, K=5) builds the same way as euron."""
    draws = _make_draws(list(range(1, 13)), 150, seed=3)
    out = tmp_path / "bocpd_main.html"

    fig = interactive_bocpd_figure(draws, field="main", out_path=out)

    assert isinstance(fig, go.Figure)
    assert out.exists()
    assert out.stat().st_size > 0


def test_interactive_control_comparison_two_panels(tmp_path: Path) -> None:
    """The pos/neg control figure has 2 panels (subplot) and saves HTML."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "control_comparison.html"

    fig = interactive_control_comparison(draws, out_path=out)

    assert isinstance(fig, go.Figure)
    # 2 y-axes (subplot 2 rows) → "yaxis" + "yaxis2"
    assert fig.layout.yaxis is not None and fig.layout.yaxis2 is not None
    assert out.exists()
    assert out.stat().st_size > 0


def test_interactive_bocpd_figure_no_out_path_does_not_write(tmp_path: Path, monkeypatch) -> None:
    """Without out_path no file is created — the function only returns a Figure."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    fig = interactive_bocpd_figure(draws, field="euron")

    assert isinstance(fig, go.Figure)
    assert list(tmp_path.iterdir()) == []  # nothing saved
