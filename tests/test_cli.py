"""CLI smoke testy — `driftscope run` wpina pipeline.run_audit (W7/W8)."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from driftscope.cli import app

runner = CliRunner()

_SEED_CSV = Path(__file__).parent.parent / "data" / "seed" / "eurojackpot_history.csv"


def test_cli_help() -> None:
    """--help startuje szybko (lazy importy) i pokazuje komende run."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout


@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_cli_run_audit_no_figures(tmp_path: Path) -> None:
    """`run --no-figures --no-hook` wykonuje audyt i drukuje werdykt (szybkie n_perm)."""
    result = runner.invoke(
        app,
        ["run", "--seed-csv", str(_SEED_CSV), "--n-perm", "49", "--no-figures", "--no-hook"],
    )
    assert result.exit_code == 0, result.output
    assert "POSITIVE CONTROL" in result.output
    assert "NEGATIVE CONTROL" in result.output
    assert "WATCHLIST" in result.output


@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_cli_run_generates_figures(tmp_path: Path) -> None:
    """`run --figures` zapisuje figury do --out-dir."""
    result = runner.invoke(
        app,
        ["run", "--seed-csv", str(_SEED_CSV), "--n-perm", "49", "--figures", "--no-hook",
         "--out-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "control_comparison.png").exists()
    assert (tmp_path / "bocpd_euron.png").exists()
