"""Smoke test demo Streamlit (demo/app.py) — czyste buildery bez runtime Streamlit.

Demo laduje `streamlit` LENIWIE (wewnatrz `render`/`_cached_rows`), wiec import modulu i
buildery danych/figur dzialaja bez instalacji streamlit. Walidujemy kontrakt builderow
(macierz, figura entropy-lens, para Turinga), NIE serwer.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("plotly")  # core dep; modul demo importuje plotly na top-level

from driftscope.driftsim.null_uniform import generate_uniform_draws  # noqa: E402
from driftscope.driftsim.planted_signals import generate_planted_draws  # noqa: E402

_APP_PATH = Path(__file__).resolve().parents[1] / "demo" / "app.py"


def _load_app():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("driftscope_demo_app", _APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_imports_without_streamlit() -> None:
    """Import modulu nie wymaga streamlit (ladowany leniwie w render)."""
    app = _load_app()
    assert hasattr(app, "render")
    assert hasattr(app, "entropy_lens_figure")


def test_entropy_lens_figure_builds() -> None:
    """entropy_lens_figure zwraca figure Plotly z histogramem nulla + linia obs."""
    import plotly.graph_objects as go

    app = _load_app()
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    fig = app.entropy_lens_figure(draws, n_perm=49, seed=1)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # histogram nulla


def test_detection_table_contract() -> None:
    """detection_table mapuje BenchmarkRow → wiersze z kolumna IT i werdyktem."""
    app = _load_app()
    from driftscope.reporting.prng_benchmark import run_battery

    draws = generate_planted_draws(300, "R3", "autocorr", 0.20, np.random.default_rng(2))
    rows = [run_battery("synthetic", "DEFECT", draws, n_perm=49)]
    table = app.detection_table(rows)
    assert table[0]["Source"] == "synthetic"
    assert "IT (LZ) p" in table[0]
    assert table[0]["Verdict"] in {"FLAG", "clear"}


def test_turing_pair_shapes() -> None:
    """turing_pair zwraca dwie sekwencje posortowanych krotek 5-liczbowych zadanej dlugosci."""
    app = _load_app()
    real, fake = app.turing_pair(6, seed=3)
    assert len(real) == 6 and len(fake) == 6
    assert all(len(r) == 5 and list(r) == sorted(r) for r in real + fake)
