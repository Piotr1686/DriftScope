"""Matplotlib static plots — figury publikowalne (W7/W8).

Publikowalne figury + (W8) FuncAnimation → ffmpeg → hook.webm (VP9, 2-5 MB).
Color palette: real=#0EA5E9, control=#94A3B8, change-point=#EF4444.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")  # headless (Win11/CI-safe) — przed importem pyplot

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402

from driftscope.core.types import DrawRecord  # noqa: E402
from driftscope.methodology.h1_classical import (  # noqa: E402
    compute_bocpd_curve,
    run_bocpd,
)

# Paleta (spójna z hookiem W8)
_COLOR_REAL = "#0EA5E9"
_COLOR_CONTROL = "#94A3B8"
_COLOR_CP = "#EF4444"


def _render_bocpd_panel(
    ax: Axes,
    draws: list[DrawRecord],
    field: Literal["main", "euron"],
    title: str,
) -> bool:
    """Rysuje jeden panel BOCPD na `ax`. Zwraca reject_h0 (czy wykryto change-point).

    Markery CP (czerwone) TYLKO dla pikow przekraczajacych prog reject — dla negative
    control zaden nie przechodzi → panel wizualnie czysty (uczciwa ilustracja braku sygnalu).
    """
    cp_probs, _rl_map, warmup, threshold = compute_bocpd_curve(draws, field)
    result = run_bocpd(draws, field)
    meta = result.metadata

    x = list(range(len(cp_probs)))
    ax.plot(x, cp_probs, color=_COLOR_REAL, lw=1.2, label=f"cp_prob ({field})")

    if warmup > 0:
        ax.axvspan(0, warmup, color=_COLOR_CONTROL, alpha=0.25,
                   label=f"warm-up (n={warmup})")

    ax.axhline(threshold, color=_COLOR_CP, ls="--", lw=1.0, alpha=0.7,
               label=f"prog reject = {threshold:.2f}")

    # Markery TYLKO dla wykrytych CP (prob > prog) — czyste dla negative control.
    date_to_idx = {str(d.draw_date): i for i, d in enumerate(draws)}
    detected = [
        (date_to_idx[date_str], prob)
        for date_str, prob in zip(
            meta["top_changepoint_dates"], meta["top_changepoint_probs"]
        )
        if date_str in date_to_idx and prob > threshold
    ]
    for idx, prob in detected:
        ax.plot(idx, prob, "o", color=_COLOR_CP, ms=7, zorder=5)
        ax.annotate(
            str(draws[idx].draw_date), xy=(idx, prob), xytext=(0, 8),
            textcoords="offset points", ha="center", fontsize=8, color=_COLOR_CP,
        )

    verdict = "reject H0 (change-point)" if result.reject_h0 else "no change-point"
    ax.set_ylim(0, 1)
    ax.set_ylabel("cp_prob")
    ax.set_title(f"{title} — {verdict}", fontsize=10)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.2)
    return bool(result.reject_h0)


def plot_bocpd_changepoints(
    draws: list[DrawRecord],
    field: Literal["main", "euron"] = "euron",
    out_path: Path | str | None = None,
) -> Path:
    """Statyczna figura krzywej BOCPD `cp_prob` z zaznaczonymi change-pointami.

    Markery CP (czerwone, #EF4444) tylko dla pikow przekraczajacych prog reject. Dla
    pola 'euron' wykryte CP ≈ 2014-11-28 (1-8→1-10) i 2022-03-29 (1-10→1-12).

    out_path: docelowy PNG. None → `artifacts/bocpd_{field}.png` (katalog tworzony w razie braku).
    """
    fig, ax = plt.subplots(figsize=(11, 4.5))
    _render_bocpd_panel(ax, draws, field, title=f"BOCPD — pole '{field}'")
    ax.set_xlabel("indeks losowania")
    fig.tight_layout()

    if out_path is None:
        out_path = Path("artifacts") / f"bocpd_{field}.png"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_control_comparison(
    draws: list[DrawRecord],
    out_path: Path | str | None = None,
) -> Path:
    """Figura positive vs negative control — wizualny dowod DoD-1 (side-by-side).

    Gorny panel: euron (positive control) — BOCPD wykrywa zmiany puli 2014/2022.
    Dolny panel: main 1-50 (negative control) — krzywa plaska, zaden pik nie przekracza
    progu (framework NIE halucynuje sygnalu tam, gdzie go nie ma).

    Bezposrednio ilustruje headline `pipeline.run_audit`: potwierdzenie znanego sygnalu
    + czysty negative control.

    out_path: None → `artifacts/control_comparison.png`.
    """
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 8), sharex=False)
    _render_bocpd_panel(ax_top, draws, "euron", title="POSITIVE CONTROL — euron (pula 1-8/10/12)")
    _render_bocpd_panel(ax_bot, draws, "main", title="NEGATIVE CONTROL — main (pula 1-50)")
    ax_bot.set_xlabel("indeks losowania")
    fig.suptitle("DriftScope — positive vs negative control (BOCPD)", fontsize=12)
    fig.tight_layout()

    if out_path is None:
        out_path = Path("artifacts") / "control_comparison.png"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
