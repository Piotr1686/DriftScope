"""Plotly interactive charts — interactive counterparts of the BOCPD figures (W7/W9).

Interactive (hover/zoom/pan) versions of the figures from `plots_static.py`, embedded in
the Quarto report as native Plotly charts. The same data (`compute_bocpd_curve`) and the
same marker semantics (CP ONLY above the reject threshold) as the static figures — the
difference is SOLELY in the presentation layer (interaction instead of PNG).

Palette consistent with `plots_static.py` (real=#0EA5E9, control=#94A3B8, change-point=#EF4444).
A pure Plotly module — no matplotlib (interactive does not pull in the Agg backend).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]

from driftscope.core.types import DrawRecord
from driftscope.methodology.h1_classical import compute_bocpd_curve, run_bocpd

# Palette (duplicated from plots_static — deliberately, so interactive does not import matplotlib)
_COLOR_REAL = "#0EA5E9"
_COLOR_CONTROL = "#94A3B8"
_COLOR_CP = "#EF4444"


def _add_bocpd_panel(
    fig: go.Figure,
    draws: list[DrawRecord],
    field: Literal["main", "euron"],
    *,
    row: int | None = None,
    col: int | None = None,
) -> bool:
    """Add one interactive BOCPD panel to `fig`. Returns reject_h0.

    Replicates the `plots_static._render_bocpd_panel` semantics: the cp_prob curve, a shaded
    warm-up zone, a horizontal reject-threshold line, CP markers ONLY for peaks above the
    threshold (for the negative control none passes → a clean panel). `row`/`col` route the
    traces to a specific subplot (None → a single panel).
    """
    cp_probs, _rl_map, warmup, threshold = compute_bocpd_curve(draws, field)
    result = run_bocpd(draws, field)
    meta = result.metadata

    x = list(range(len(cp_probs)))
    # add_trace/add_vrect/add_hline accept row/col only when non-None → we build kwargs.
    rc = {k: v for k, v in (("row", row), ("col", col)) if v is not None}

    fig.add_trace(
        go.Scatter(
            x=x,
            y=list(cp_probs),
            mode="lines",
            name=f"cp_prob ({field})",
            line={"color": _COLOR_REAL, "width": 1.4},
            hovertemplate="draw %{x}<br>cp_prob=%{y:.3f}<extra></extra>",
        ),
        **rc,
    )

    if warmup > 0:
        fig.add_vrect(
            x0=0,
            x1=warmup,
            fillcolor=_COLOR_CONTROL,
            opacity=0.25,
            line_width=0,
            annotation_text=f"warm-up (n={warmup})",
            annotation_position="top left",
            **rc,
        )

    fig.add_hline(
        y=threshold,
        line={"color": _COLOR_CP, "width": 1.0, "dash": "dash"},
        opacity=0.7,
        annotation_text=f"reject threshold = {threshold:.2f}",
        annotation_position="top right",
        **rc,
    )

    # Markers ONLY for detected CPs (prob > threshold) — clean for the negative control.
    date_to_idx = {str(d.draw_date): i for i, d in enumerate(draws)}
    detected_idx: list[int] = []
    detected_prob: list[float] = []
    detected_date: list[str] = []
    for date_str, prob in zip(
        meta["top_changepoint_dates"], meta["top_changepoint_probs"]
    ):
        if date_str in date_to_idx and prob > threshold:
            detected_idx.append(date_to_idx[date_str])
            detected_prob.append(float(prob))
            detected_date.append(date_str)

    if detected_idx:
        fig.add_trace(
            go.Scatter(
                x=detected_idx,
                y=detected_prob,
                mode="markers",
                name="change-point",
                marker={"color": _COLOR_CP, "size": 11, "symbol": "circle"},
                text=detected_date,
                hovertemplate="change-point<br>%{text}<br>cp_prob=%{y:.3f}<extra></extra>",
            ),
            **rc,
        )

    return bool(result.reject_h0)


def _write_html(fig: go.Figure, out_path: Path | str) -> Path:
    """Write a standalone HTML with plotly.js via CDN (lightweight, does not inline ~3.5 MB)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
    return out_path


def interactive_bocpd_figure(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    out_path: Path | str | None = None,
) -> go.Figure:
    """Interactive BOCPD `cp_prob` curve with change-point markers (static counterpart).

    Hover reveals the draw index + cp_prob; CP markers (red) carry the draw date.
    For the 'euron' field the detected CPs ≈ 2014-11-28 and 2022-03-29 (ground truth DoD-1b).

    out_path: None → only the `Figure` (to embed in Quarto); given → write a standalone
    HTML (`plotly.js` via CDN). Always returns the `Figure`.
    """
    fig = go.Figure()
    _add_bocpd_panel(fig, draws, field)
    fig.update_layout(
        title=f"DriftScope — BOCPD detects pool changes (field '{field}')",
        xaxis_title="draw index",
        yaxis_title="cp_prob",
        yaxis_range=[0, 1],
        hovermode="x unified",
        template="plotly_white",
    )
    if out_path is not None:
        _write_html(fig, out_path)
    return fig


def interactive_control_comparison(
    draws: list[DrawRecord],
    out_path: Path | str | None = None,
) -> go.Figure:
    """Interactive positive vs negative control (2 panels) — a visual proof of DoD-1.

    Top panel: euron (positive control) — BOCPD detects the 2014/2022 pool changes.
    Bottom panel: main 1-50 (negative control) — a flat curve, no peak crosses the
    threshold. Counterpart of `plots_static.plot_control_comparison`, but with hover/zoom.

    out_path: None → only the `Figure`; given → write a standalone HTML (CDN).
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12,
        subplot_titles=(
            "POSITIVE CONTROL — euron (pool 1-8/10/12)",
            "NEGATIVE CONTROL — main (pool 1-50)",
        ),
    )
    _add_bocpd_panel(fig, draws, "euron", row=1, col=1)
    _add_bocpd_panel(fig, draws, "main", row=2, col=1)

    fig.update_yaxes(range=[0, 1], title_text="cp_prob")
    fig.update_xaxes(title_text="draw index", row=2, col=1)
    fig.update_layout(
        title="DriftScope — positive vs negative control (BOCPD)",
        template="plotly_white",
        height=720,
        showlegend=False,
    )
    if out_path is not None:
        _write_html(fig, out_path)
    return fig
