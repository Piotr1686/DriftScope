"""Artifact smoke tests — stub (post-pipeline).

Wymaga wygenerowanych artefaktow (oznaczone @pytest.mark.requires_artifacts).
Wzorzec testow z PROJECT_BRIEF.md §6.3.
"""
import pytest


@pytest.mark.requires_artifacts
@pytest.mark.skip(reason="Wymaga wygenerowanych artefaktow — uruchom po pipeline")
def test_driftsim_runs_nonempty() -> None:
    import glob
    import polars as pl
    paths = glob.glob("artifacts/driftsim_runs/*.parquet")
    assert len(paths) > 0
    assert pl.scan_parquet("artifacts/driftsim_runs/*.parquet").select(pl.count()).collect().item() > 0


@pytest.mark.requires_artifacts
@pytest.mark.skip(reason="Wymaga wygenerowanych artefaktow — uruchom po pipeline")
def test_report_html_exists() -> None:
    import os
    assert os.path.getsize("docs/report.html") > 1024
