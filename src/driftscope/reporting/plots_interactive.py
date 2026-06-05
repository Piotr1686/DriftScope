"""Plotly interactive charts — interaktywne odpowiedniki figur BOCPD (W7/W9).

Interaktywne (hover/zoom/pan) wersje figur ze `plots_static.py`, osadzane w Quarto
report jako natywne wykresy Plotly. Te same dane (`compute_bocpd_curve`) i ta sama
semantyka markerow (CP TYLKO ponad progiem reject) co figury static — roznica jest
WYLACZNIE w warstwie prezentacji (interakcja zamiast PNG).

Paleta spojna ze `plots_static.py` (real=#0EA5E9, control=#94A3B8, change-point=#EF4444).
Modul czysto Plotly — bez matplotlib (interactive nie ciagnie backendu Agg).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]

from driftscope.core.types import DrawRecord
from driftscope.methodology.h1_classical import compute_bocpd_curve, run_bocpd

# Paleta (zduplikowana ze plots_static — celowo, by interactive nie importowal matplotlib)
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
    """Dodaje jeden interaktywny panel BOCPD do `fig`. Zwraca reject_h0.

    Replikuje semantyke `plots_static._render_bocpd_panel`: krzywa cp_prob, zacieniona
    strefa warm-up, pozioma linia progu reject, markery CP TYLKO dla pikow przekraczajacych
    prog (dla negative control zaden nie przechodzi → panel czysty). `row`/`col` kieruja
    slady do konkretnego subplotu (None → pojedynczy panel).
    """
    cp_probs, _rl_map, warmup, threshold = compute_bocpd_curve(draws, field)
    result = run_bocpd(draws, field)
    meta = result.metadata

    x = list(range(len(cp_probs)))
    # add_trace/add_vrect/add_hline akceptuja row/col tylko gdy nie-None → budujemy kwargs.
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

    # Markery TYLKO dla wykrytych CP (prob > prog) — czyste dla negative control.
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
    """Zapisuje samodzielny HTML z plotly.js przez CDN (lekki, nie inline'uje ~3.5 MB)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs="cdn", full_html=True)
    return out_path


def interactive_bocpd_figure(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    out_path: Path | str | None = None,
) -> go.Figure:
    """Interaktywna krzywa BOCPD `cp_prob` z markerami change-pointow (analog static).

    Hover ujawnia indeks losowania + cp_prob; markery CP (czerwone) niosa date losowania.
    Dla pola 'euron' wykryte CP ≈ 2014-11-28 i 2022-03-29 (ground truth DoD-1b).

    out_path: None → tylko `Figure` (do osadzenia w Quarto); podane → zapis samodzielnego
    HTML (`plotly.js` z CDN). Zawsze zwraca `Figure`.
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
    """Interaktywny positive vs negative control (2 panele) — wizualny dowod DoD-1.

    Gorny panel: euron (positive control) — BOCPD wykrywa zmiany puli 2014/2022.
    Dolny panel: main 1-50 (negative control) — krzywa plaska, zaden pik nie przekracza
    progu. Analog `plots_static.plot_control_comparison`, ale z hover/zoom.

    out_path: None → tylko `Figure`; podane → zapis samodzielnego HTML (CDN).
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
