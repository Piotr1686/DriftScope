"""Typer CLI entrypoint — `driftscope run` (end-to-end audit).

Uruchamia `pipeline.run_audit` na seed CSV i drukuje werdykt (positive/negative control
+ honest watchlist). Opcjonalnie generuje figury (control comparison + BOCPD) i hook .webm.
Ciezkie importy (matplotlib/numba) sa lazy — szybki start CLI dla --help.

Uwaga: BEZ `from __future__ import annotations` — typer wymaga runtime'owych anotacji
(stringized annotations lamia detekcje bool dla flag --figures/--no-figures).
"""
from pathlib import Path
from typing import Optional

import typer

from driftscope.core.config import settings

app = typer.Typer(help="DriftScope — stationarity audit for discrete streams.")


@app.callback()
def _main() -> None:
    """DriftScope — audyt niestacjonarnosci strumieni dyskretnych."""
    # Callback wymusza strukture grupy (subkomenda `run` zamiast kolapsu single-command).


@app.command()
def run(
    seed_csv: Optional[Path] = typer.Option(
        None, "--seed-csv", help="Sciezka do seed CSV (domyslnie z config: data_seed_path)."
    ),
    n_perm: int = typer.Option(999, "--n-perm", help="Liczba permutacji dla MMD/co-occurrence."),
    figures: bool = typer.Option(True, help="Generuj figury PNG."),
    hook: bool = typer.Option(
        False, help="Generuj hook .webm (wolniejsze; wymaga ffmpeg)."
    ),
    out_dir: Optional[Path] = typer.Option(
        None, "--out-dir", help="Katalog wyjsciowy figur (domyslnie z config: artifacts_dir)."
    ),
) -> None:
    """Uruchom pelny audyt DriftScope na seed CSV i wydrukuj werdykt."""
    from driftscope.ingestion.lotto_scraper import load_seed_csv
    from driftscope.pipeline import run_audit

    csv_path = seed_csv if seed_csv is not None else settings.data_seed_path
    draws = load_seed_csv(csv_path)
    typer.echo(f"Wczytano {len(draws)} losowan z {csv_path}")

    report = run_audit(draws, n_perm=n_perm)
    typer.echo("")
    typer.echo(report.summary())

    target = out_dir if out_dir is not None else settings.artifacts_dir
    if figures:
        from driftscope.reporting.plots_static import (
            plot_bocpd_changepoints,
            plot_control_comparison,
        )

        target.mkdir(parents=True, exist_ok=True)
        p_cmp = plot_control_comparison(draws, out_path=target / "control_comparison.png")
        p_boc = plot_bocpd_changepoints(draws, "euron", out_path=target / "bocpd_euron.png")
        typer.echo(f"\nFigury: {p_cmp}, {p_boc}")

    if hook:
        from driftscope.reporting.plots_static import animate_bocpd_hook

        target.mkdir(parents=True, exist_ok=True)
        p_hook = animate_bocpd_hook(draws, "euron", out_path=target / "hook_euron.webm")
        typer.echo(f"Hook: {p_hook}")


if __name__ == "__main__":
    app()
