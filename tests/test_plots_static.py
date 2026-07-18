"""Smoke tests for reporting/plots_static.py — figures render headless (Agg)."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np

from driftscope.core.types import DrawRecord
from driftscope.reporting.plots_static import (
    animate_bocpd_hook,
    plot_bocpd_changepoints,
    plot_control_comparison,
)


def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2020, 1, 7),
) -> list[DrawRecord]:
    """n DrawRecord with random euro numbers from euron_pool (pattern from test_h1_invariants)."""
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


def test_plot_bocpd_changepoints_saves_png(tmp_path: Path) -> None:
    """Figure renders, PNG file saved and non-empty (no exception, headless)."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "bocpd_euron.png"

    result = plot_bocpd_changepoints(draws, field="euron", out_path=out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_bocpd_changepoints_default_path(tmp_path: Path, monkeypatch) -> None:
    """Default path = artifacts/bocpd_{field}.png; directory created if missing."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    result = plot_bocpd_changepoints(draws, field="euron")

    assert result == Path("artifacts") / "bocpd_euron.png"
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_bocpd_changepoints_main_field(tmp_path: Path) -> None:
    """The 'main' field (N=50, K=5) renders the same way as euron."""
    draws = _make_draws(list(range(1, 13)), 150, seed=3)
    out = tmp_path / "bocpd_main.png"

    result = plot_bocpd_changepoints(draws, field="main", out_path=out)

    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_control_comparison_saves_png(tmp_path: Path) -> None:
    """The pos/neg control figure (2 panels euron+main) renders and saves."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "control_comparison.png"

    result = plot_control_comparison(draws, out_path=out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_control_comparison_default_path(tmp_path: Path, monkeypatch) -> None:
    """Default path = artifacts/control_comparison.png."""
    monkeypatch.chdir(tmp_path)
    draws = _make_draws(list(range(1, 13)), 120, seed=7)

    result = plot_control_comparison(draws)

    assert result == Path("artifacts") / "control_comparison.png"
    assert result.exists()


def test_animate_bocpd_hook_saves_file(tmp_path: Path) -> None:
    """Hook animation saves a file (.webm when ffmpeg; .gif fallback). Small/fast."""
    draws = _planted_changepoint_draws()
    out = tmp_path / "hook.webm"

    result = animate_bocpd_hook(draws, "euron", out_path=out, fps=5, n_frames=6)

    assert result.exists()
    assert result.stat().st_size > 0
    assert result.suffix in {".webm", ".gif"}  # .gif = fallback without ffmpeg
