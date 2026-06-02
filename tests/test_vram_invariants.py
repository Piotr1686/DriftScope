"""Testy niezmiennikow zasobow dla DriftScope (pipeline CPU-only).

Nazwa pliku zachowana z template; "VRAM" repurposed na RAM/resource invariants
(VRAM budget N/A — pipeline CPU-only, zob. §6.1 PROJECT_BRIEF.md).

Fixtures:
  load_pipeline   — dict z komponentami pipeline (placeholders do W1)
  sample_input    — lista DrawRecord-compatible dictow (200 losowan)
"""
import os

import numpy as np
import polars as pl
import psutil
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_input() -> list[dict]:  # type: ignore[type-arg]
    """200 losowan EuroJackpot-compatible (main 1-50, euron 1-12).

    Zgodne ze schema DrawRecord (types.py, W1):
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
    """Wektor czestosci p w delta^49 dla liczb glownych 1-50."""
    all_main = [n for draw in sample_input for n in draw["main"]]
    arr = np.array(all_main, dtype=np.int32)
    counts = np.bincount(arr, minlength=51)[1:]   # indeksy 1-50
    return counts.astype(np.float64) / counts.sum()


@pytest.fixture
def load_pipeline() -> dict:  # type: ignore[type-arg]
    """Placeholders komponentow pipeline — wypelniane implementacja w W1/W4.

    Klucze odpowiadaja modulom src/driftscope/methodology/.
    """
    return {
        "h1_classical": None,    # wypelnic w W1
        "k4_mmd": None,          # wypelnic w W4
        "permutation": None,     # wypelnic w W1 / W6
        "multiple_testing": None,
        "driftsim": None,
    }


# ---------------------------------------------------------------------------
# Testy schemat fixtures
# ---------------------------------------------------------------------------

def test_sample_input_schema(sample_input: list[dict]) -> None:  # type: ignore[type-arg]
    """sample_input musi miec poprawna strukture (DrawRecord-compatible)."""
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
    """Wektor czestosci musi miec ksztalt (50,) i sumowac sie do 1."""
    assert sample_frequency_vector.shape == (50,)
    assert sample_frequency_vector.min() >= 0.0
    assert abs(sample_frequency_vector.sum() - 1.0) < 1e-9


def test_load_pipeline_keys(load_pipeline: dict) -> None:  # type: ignore[type-arg]
    """load_pipeline musi zwracac dict z kluczami pipeline."""
    assert isinstance(load_pipeline, dict)
    for key in ("h1_classical", "k4_mmd", "permutation"):
        assert key in load_pipeline


# ---------------------------------------------------------------------------
# RAM budget niezmienniki (§6.1 PROJECT_BRIEF.md)
# ---------------------------------------------------------------------------

def _rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / 1e6


def test_ram_ingestion_budget(sample_input: list[dict]) -> None:  # type: ignore[type-arg]
    """Fixture ingestion (200 losowan → Polars DataFrame) < 100 MB RAM budget."""
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
        f"Ingestion fixture zuzylo {delta_mb:.1f} MB > 100 MB budget (§6.1)"
    )


def test_ram_baseline_below_h1_budget() -> None:
    """Biezacy RSS procesu musi byc < 500 MB (H1 single run budget, §6.1).

    Placeholder — po implementacji h1_classical.py test bedzie weryfikowal
    rzeczywiste zuzycie RAM w trakcie H1 run.
    """
    rss = _rss_mb()
    assert rss < 500, (
        f"RSS {rss:.1f} MB > 500 MB H1 budget. Sprawdz co jest zaladowane."
    )


def test_frequency_vector_mmd_memory() -> None:
    """Macierz kernela MMD dla N=500 (max) musi zmiescie sie w <800 MB."""
    n = 500
    # Symulacja macierzy kernela N×N float64
    matrix_mb = (n * n * 8) / 1e6   # 8 bajtow na float64
    assert matrix_mb < 800, (
        f"Macierz {n}×{n} to {matrix_mb:.1f} MB > 800 MB MMD budget"
    )
