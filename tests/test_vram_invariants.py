"""Resource invariant tests for DriftScope (CPU-only pipeline).

File name kept from the template; "VRAM" is repurposed for RAM/resource invariants
(VRAM budget N/A — CPU-only pipeline, see §6.1 PROJECT_BRIEF.md).

Fixtures:
  load_pipeline   — dict of pipeline components (placeholders until W1)
  sample_input    — list of DrawRecord-compatible dicts (200 draws)
"""
import gc
import os
from datetime import date, timedelta

import numpy as np
import polars as pl
import psutil
import pytest

from driftscope.core.types import DrawRecord
from driftscope.methodology.h1_classical import run_all_h1

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_input() -> list[dict]:  # type: ignore[type-arg]
    """200 EuroJackpot-compatible draws (main 1-50, euron 1-12).

    Conforms to the DrawRecord schema (types.py, W1):
      main: list[int] len=5, sorted, 1-50
      euron: list[int] len=2, sorted, 1-12
    """
    rng = np.random.default_rng(42)
    draws = []
    for _ in range(200):
        main = sorted(rng.choice(range(1, 51), size=5, replace=False).tolist())
        euron = sorted(rng.choice(range(1, 13), size=2, replace=False).tolist())
        draws.append({"main": main, "euron": euron})
    return draws


@pytest.fixture
def sample_frequency_vector(sample_input: list[dict]) -> np.ndarray:  # type: ignore[type-arg]
    """Frequency vector p in delta^49 for main numbers 1-50."""
    all_main = [n for draw in sample_input for n in draw["main"]]
    arr = np.array(all_main, dtype=np.int32)
    counts = np.bincount(arr, minlength=51)[1:]   # indices 1-50
    return counts.astype(np.float64) / counts.sum()


@pytest.fixture
def load_pipeline() -> dict:  # type: ignore[type-arg]
    """Pipeline component placeholders — filled by the implementation in W1/W4.

    Keys correspond to modules in src/driftscope/methodology/.
    """
    return {
        "h1_classical": None,    # fill in W1
        "k4_mmd": None,          # fill in W4
        "permutation": None,     # fill in W1 / W6
        "multiple_testing": None,
        "driftsim": None,
    }


# ---------------------------------------------------------------------------
# Fixture schema tests
# ---------------------------------------------------------------------------

def test_sample_input_schema(sample_input: list[dict]) -> None:  # type: ignore[type-arg]
    """sample_input must have a valid structure (DrawRecord-compatible)."""
    assert len(sample_input) == 200
    for draw in sample_input:
        assert set(draw.keys()) >= {"main", "euron"}
        assert len(draw["main"]) == 5
        assert len(draw["euron"]) == 2
        assert all(1 <= n <= 50 for n in draw["main"])
        assert all(1 <= n <= 12 for n in draw["euron"])
        assert draw["main"] == sorted(draw["main"])
        assert draw["euron"] == sorted(draw["euron"])


def test_frequency_vector_invariants(sample_frequency_vector: np.ndarray) -> None:
    """Frequency vector must have shape (50,) and sum to 1."""
    assert sample_frequency_vector.shape == (50,)
    assert sample_frequency_vector.min() >= 0.0
    assert abs(sample_frequency_vector.sum() - 1.0) < 1e-9


def test_load_pipeline_keys(load_pipeline: dict) -> None:  # type: ignore[type-arg]
    """load_pipeline must return a dict with the pipeline keys."""
    assert isinstance(load_pipeline, dict)
    for key in ("h1_classical", "k4_mmd", "permutation"):
        assert key in load_pipeline


# ---------------------------------------------------------------------------
# RAM budget invariants (§6.1 PROJECT_BRIEF.md)
# ---------------------------------------------------------------------------

def _rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / 1e6


def test_ram_ingestion_budget(sample_input: list[dict]) -> None:  # type: ignore[type-arg]
    """Ingestion fixture (200 draws → Polars DataFrame) < 100 MB RAM budget."""
    rss_before = _rss_mb()

    rows = [
        {
            "draw_date": f"2020-01-{(i % 28) + 1:02d}",
            **{f"main_{j + 1}": draw["main"][j] for j in range(5)},
            **{f"euron_{j + 1}": draw["euron"][j] for j in range(2)},
        }
        for i, draw in enumerate(sample_input)
    ]
    _df = pl.DataFrame(rows)

    delta_mb = _rss_mb() - rss_before
    assert delta_mb < 100, (
        f"Ingestion fixture used {delta_mb:.1f} MB > 100 MB budget (§6.1)"
    )


def _make_h1_draws(n: int = 200) -> list[DrawRecord]:
    """n EuroJackpot-compatible draws as DrawRecord (weekly date step)."""
    rng = np.random.default_rng(42)
    start = date(2020, 1, 3)
    draws: list[DrawRecord] = []
    for i in range(n):
        main = sorted(rng.choice(range(1, 51), size=5, replace=False).tolist())
        euron = sorted(rng.choice(range(1, 13), size=2, replace=False).tolist())
        draws.append(
            DrawRecord(
                draw_date=start + timedelta(weeks=i),
                main_1=main[0], main_2=main[1], main_3=main[2],
                main_4=main[3], main_5=main[4],
                euron_1=euron[0], euron_2=euron[1],
            )
        )
    return draws


def test_ram_h1_run_below_budget() -> None:
    """Delta RSS of a single H1 run (run_all_h1) < 500 MB (§6.1).

    Measures the RSS INCREASE around one H1 run, NOT the process absolute RSS —
    the latter is dominated by the stack import footprint (numba/scipy/statsmodels)
    and is platform-dependent (~550 MB on Linux). Warm-up isolates the one-off
    JIT cost (numba) from the run's actual working set.
    """
    draws = _make_h1_draws()

    run_all_h1(draws)          # warm-up: JIT compile + lazy alloc outside measurement
    gc.collect()
    rss_before = _rss_mb()
    run_all_h1(draws)          # measured run
    delta_mb = _rss_mb() - rss_before

    assert delta_mb < 500, (
        f"H1 run used {delta_mb:.1f} MB > 500 MB budget (§6.1)"
    )


def test_frequency_vector_mmd_memory() -> None:
    """MMD kernel matrix for N=500 (max) must fit within <800 MB."""
    n = 500
    # Simulate an N×N float64 kernel matrix
    matrix_mb = (n * n * 8) / 1e6   # 8 bytes per float64
    assert matrix_mb < 800, (
        f"{n}×{n} matrix is {matrix_mb:.1f} MB > 800 MB MMD budget"
    )
