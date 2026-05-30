"""Smoke test srodowiska DriftScope.

Weryfikuje: importy wszystkich zaleznosci, Numba JIT, CPU/RAM, GPU (informacyjnie).
Uruchomienie: python scripts/smoke_test.py
"""
import sys
import subprocess


def _check_import(module: str) -> tuple[bool, str]:
    try:
        mod = __import__(module)
        version = getattr(mod, "__version__", "?")
        return True, version
    except ImportError as exc:
        return False, str(exc)


def _check_numba_jit() -> tuple[bool, str]:
    try:
        import numpy as np
        from numba import njit

        @njit(cache=False)
        def _warmup(arr):  # type: ignore[no-untyped-def]
            total = 0.0
            for i in range(len(arr)):
                total += arr[i]
            return total

        arr = np.ones(100, dtype=np.float64)
        result = float(_warmup(arr))
        return True, f"JIT OK — sum(ones(100)) = {result:.0f}"
    except Exception as exc:
        return False, str(exc)


def _check_cpu() -> str:
    try:
        import psutil
        cores = psutil.cpu_count(logical=True)
        ram_gb = psutil.virtual_memory().total / 1e9
        return f"{cores} watkow logicznych | RAM {ram_gb:.1f} GB"
    except ImportError:
        return "psutil nie zainstalowany"


def _check_gpu() -> str:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return f"GPU obecne (pipeline CPU-only, VRAM nieuzywane): {out}"
    except FileNotFoundError:
        return "nvidia-smi nie znalezione — OK dla pipeline CPU-only"
    except Exception as exc:
        return f"nvidia-smi blad: {exc}"


PACKAGES: list[tuple[str, str]] = [
    ("numpy",          "numpy"),
    ("numba",          "numba"),
    ("joblib",         "joblib"),
    ("statsmodels",    "statsmodels"),
    ("ruptures",       "ruptures"),
    ("scipy",          "scipy"),
    ("sklearn",        "sklearn"),
    ("polars",         "polars"),
    ("pydantic",       "pydantic"),
    ("pydantic-settings", "pydantic_settings"),
    ("typer",          "typer"),
    ("matplotlib",     "matplotlib"),
    ("plotly",         "plotly"),
    ("httpx",          "httpx"),
    ("selectolax",     "selectolax"),
    ("tenacity",       "tenacity"),
    ("pyarrow",        "pyarrow"),
    ("psutil",         "psutil"),
]


def main() -> int:
    print("=" * 62)
    print("DriftScope — SMOKE TEST")
    print("=" * 62)
    print(f"\n[Python] {sys.version.split()[0]} na {sys.platform}")

    print("\n[Pakiety]")
    missing: list[str] = []
    for label, module in PACKAGES:
        ok, version = _check_import(module)
        status = "OK  " if ok else "BRAK"
        print(f"  {label:<22} {status}  {version}")
        if not ok:
            missing.append(label)

    print("\n[Numba JIT]")
    ok, msg = _check_numba_jit()
    print(f"  {'OK  ' if ok else 'FAIL'}  {msg}")

    print("\n[CPU / RAM]")
    print(f"  {_check_cpu()}")

    print("\n[GPU]")
    print(f"  {_check_gpu()}")

    print("\n" + "=" * 62)
    if not missing and ok:
        print("WYNIK: srodowisko gotowe. Uruchom: pytest tests/test_environment.py")
    else:
        if missing:
            print(f"BRAKUJACE PAKIETY: {missing}")
            print("Uruchom: pip install -e '.[dev]'")
        if not ok:
            print("Numba JIT FAIL — sprawdz test_environment.py")
    print("=" * 62)
    return 0 if (not missing and ok) else 1


if __name__ == "__main__":
    sys.exit(main())
