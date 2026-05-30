"""Pre-flight environment sanity check dla DriftScope.

Weryfikuje: Numba 0.65.x na Win11 + numpy 2.x, kluczowe importy pakietow,
CPU parallelism via joblib. Odpowiada za Os 0 z Hardware Transcendence Stack.

Uruchomienie: pytest tests/test_environment.py -v
"""
import sys
import importlib

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Python + NumPy wersje
# ---------------------------------------------------------------------------

def test_python_version() -> None:
    """Python musi byc 3.10.x."""
    assert sys.version_info[:2] == (3, 10), (
        f"Wymagany Python 3.10.x, znaleziono {sys.version}"
    )


def test_numpy_major_version() -> None:
    """NumPy musi byc 2.x (wymagane przez numba 0.65.x)."""
    major = int(np.__version__.split(".")[0])
    assert major >= 2, f"Wymagany NumPy 2.x, znaleziono {np.__version__}"


# ---------------------------------------------------------------------------
# Numba — import, wersja, JIT
# ---------------------------------------------------------------------------

def test_numba_import() -> None:
    """Numba musi byc importowalna."""
    importlib.import_module("numba")


def test_numba_version() -> None:
    """Numba musi byc 0.65.x (zweryfikowana na Win11 + numpy 2.x, 2026-05-17)."""
    import numba
    parts = numba.__version__.split(".")
    major, minor = int(parts[0]), int(parts[1])
    assert (major, minor) == (0, 65), (
        f"Wymagana Numba 0.65.x, znaleziono {numba.__version__}"
    )


def test_numba_njit_basic() -> None:
    """@njit musi kompilowac i wykonac prosty loop na numpy array."""
    from numba import njit

    @njit(cache=False)
    def _sum(arr: np.ndarray) -> float:  # type: ignore[type-arg]
        total = 0.0
        for i in range(len(arr)):
            total += arr[i]
        return total

    result = _sum(np.ones(50, dtype=np.float64))
    assert result == pytest.approx(50.0, abs=1e-9)


def test_numba_njit_cache_true() -> None:
    """cache=True musi dzialac — wymagane przez permutation engine."""
    from numba import njit

    @njit(cache=True)
    def _add(a: float, b: float) -> float:
        return a + b

    assert _add(1.0, 2.0) == pytest.approx(3.0, abs=1e-9)


def test_numba_frequency_vector() -> None:
    """Numba musi obsluzyc wzorzec frequency vector (core primitive DriftScope)."""
    from numba import njit

    @njit(cache=False)
    def _freq_vec(draws: np.ndarray, n_bins: int) -> np.ndarray:  # type: ignore[type-arg]
        counts = np.zeros(n_bins)
        for d in draws:
            counts[int(d) - 1] += 1.0
        return counts / len(draws)

    rng = np.random.default_rng(42)
    draws = rng.integers(1, 51, size=200).astype(np.float64)
    freq = _freq_vec(draws, 50)

    assert freq.shape == (50,)
    assert abs(freq.sum() - 1.0) < 1e-9, "Wektor czestosci nie sumuje sie do 1.0"


# ---------------------------------------------------------------------------
# Kluczowe importy projektu
# ---------------------------------------------------------------------------

def test_key_imports() -> None:
    """Wszystkie pakiety projektu musza byc importowalne."""
    required = [
        "polars",
        "statsmodels",
        "ruptures",
        "scipy",
        "sklearn",
        "pydantic",
        "pydantic_settings",
        "typer",
        "matplotlib",
        "pyarrow",
        "joblib",
        "httpx",
        "selectolax",
        "tenacity",
        "psutil",
    ]
    missing = [p for p in required if not _try_import(p)]
    assert not missing, f"Brakujace pakiety: {missing}"


def _try_import(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def test_polars_version() -> None:
    """Polars musi byc 1.x."""
    import polars as pl
    major = int(pl.__version__.split(".")[0])
    assert major >= 1, f"Wymagany Polars 1.x, znaleziono {pl.__version__}"


# ---------------------------------------------------------------------------
# CPU parallelism
# ---------------------------------------------------------------------------

def test_joblib_parallel_loky() -> None:
    """joblib.Parallel(backend='loky') musi dzialac — wymagane dla pipeline."""
    from joblib import Parallel, delayed

    def _square(x: int) -> int:
        return x * x

    results = Parallel(n_jobs=2, backend="loky")(
        delayed(_square)(i) for i in range(4)
    )
    assert sorted(results) == [0, 1, 4, 9]


# ---------------------------------------------------------------------------
# Windows-specyficzne
# ---------------------------------------------------------------------------

def test_windows_msvc() -> None:
    """Na Windows: vcruntime140.dll musi byc obecna (wymagana przez Numba)."""
    if sys.platform != "win32":
        pytest.skip("Test tylko dla Windows")
    import ctypes
    try:
        ctypes.WinDLL("vcruntime140.dll")
    except OSError:
        pytest.fail(
            "vcruntime140.dll nie znaleziona — zainstaluj MSVC Redist 2015-2022"
        )
