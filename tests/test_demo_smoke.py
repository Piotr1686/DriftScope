"""Streamlit demo smoke test (demo/app.py) — pure builders without the Streamlit runtime.

The demo loads `streamlit` LAZILY (inside `render`/`_cached_rows`), so importing the module
and the data/figure builders work without streamlit installed. We validate the builder
contract (matrix, entropy-lens figure, Turing pair), NOT the server.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("plotly")  # core dep; the demo module imports plotly at top-level

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
    """Importing the module does not require streamlit (loaded lazily in render)."""
    app = _load_app()
    assert hasattr(app, "render")
    assert hasattr(app, "entropy_lens_figure")


def test_entropy_lens_figure_builds() -> None:
    """entropy_lens_figure returns a Plotly figure with the null histogram + obs line."""
    import plotly.graph_objects as go

    app = _load_app()
    draws = generate_uniform_draws(120, "R2", np.random.default_rng(0))
    fig = app.entropy_lens_figure(draws, n_perm=49, seed=1)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # null histogram


def test_detection_table_contract() -> None:
    """detection_table maps BenchmarkRow → rows with an IT column and a verdict."""
    app = _load_app()
    from driftscope.reporting.prng_benchmark import run_battery

    draws = generate_planted_draws(300, "R3", "autocorr", 0.20, np.random.default_rng(2))
    rows = [run_battery("synthetic", "DEFECT", draws, n_perm=49)]
    table = app.detection_table(rows)
    assert table[0]["Source"] == "synthetic"
    assert "IT (LZ) p" in table[0]
    assert table[0]["Verdict"] in {"FLAG", "clear"}


def test_turing_pair_shapes() -> None:
    """turing_pair returns two sequences of sorted 5-number tuples of the given length."""
    app = _load_app()
    real, fake = app.turing_pair(6, seed=3)
    assert len(real) == 6 and len(fake) == 6
    assert all(len(r) == 5 and list(r) == sorted(r) for r in real + fake)
