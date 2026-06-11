"""Krok 6 PoC - DriftScope permutation engine benchmark
Core Risk: Numba JIT dla permutation engine na Win11 (i5-12500H, 12C/16T)

Trzy warianty:
  A: NumPy sequential loop (baseline szybkosci jednego testu)
  B: NumPy + joblib.Parallel (row-per-perm, obecna intuicja z briefu)
  C: Numba JIT calego loopa permutacji (prawidlowy wzorzec uzycia Numby)

Wnioski z C sa kluczowe: joblib.Parallel powinen dzialac nad
konfigami (50 testow x 3 rezimy), nie nad pojedynczymi permutacjami.
Numba kontroluje tight loop wewnatrz kazdego joba.

Skala: 1000 perms (10% prod) -> skalujemy wyniki x10 do szacunku.
"""
import sys
import time
import numpy as np
from joblib import Parallel, delayed

N_DRAWS = 1500
N_PERMS_POC = 1000
N_JOBS = -1
SCALE_TO_PROD = 10        # 10k prod perms
N_CONFIGS_PROD = 150      # ~50 testow x 3 rezimy (upper bound)
OVERNIGHT_H = 18

_rng = np.random.default_rng(42)
DRAWS = _rng.integers(1, 51, size=(N_DRAWS, 5))  # module-level -> picklable


# --- NumPy helpers (module-level) -------------------------------------------
def _chi2_np(arr):
    counts = np.bincount(arr.ravel(), minlength=51)[1:]
    exp = arr.size / 50.0
    return float(np.sum((counts - exp) ** 2 / exp))


def _perm_numpy(seed):
    idx = np.random.default_rng(seed).permutation(N_DRAWS)
    return _chi2_np(DRAWS[idx])


def _all_perms_numpy(n_perms, start_seed):
    """Jeden job: caly loop n_perms permutacji - czysty NumPy."""
    results = np.empty(n_perms)
    for i in range(n_perms):
        idx = np.random.default_rng(start_seed + i).permutation(N_DRAWS)
        results[i] = _chi2_np(DRAWS[idx])
    return results


# --- Numba helpers -----------------------------------------------------------
try:
    from numba import njit as _njit
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False
    def _njit(*a, **kw):
        return (lambda f: f) if not a or not callable(a[0]) else a[0]


@_njit(cache=True)
def _all_perms_numba_core(draws, n_perms, start_seed):
    """Numba JIT calego loopa permutacji - prawidlowy wzorzec."""
    n, m = draws.shape[0], draws.shape[1]
    results = np.empty(n_perms)
    for k in range(n_perms):
        np.random.seed((start_seed + k) % 2147483647)
        idx = np.random.permutation(n)
        counts = np.zeros(50, dtype=np.int64)
        for i in range(n):
            for j in range(m):
                counts[draws[idx[i], j] - 1] += 1
        exp = (n * m) / 50.0
        chi2 = 0.0
        for c in counts:
            d = c - exp
            chi2 += d * d / exp
        results[k] = chi2
    return results


def _all_perms_numba(n_perms, start_seed):
    """Wrapper (module-level) dla joblib."""
    return _all_perms_numba_core(DRAWS, n_perms, start_seed)


# --- WARIANT A: NumPy sequential loop ----------------------------------------
print("=== WARIANT A: NumPy sequential (1 konfiguracja) ===")
t_a = None
try:
    _all_perms_numpy(10, 0)                      # warmup
    t0 = time.perf_counter()
    _all_perms_numpy(N_PERMS_POC, 0)
    t_a = time.perf_counter() - t0
    print(f"  {N_PERMS_POC} perms: {t_a:.2f}s  |  {N_PERMS_POC/t_a:.0f} perms/s")
except Exception as exc:
    print(f"  FAIL: {exc}")


# --- WARIANT B: NumPy + joblib, row-per-perm (stary pomysl) ------------------
print("\n=== WARIANT B: NumPy + joblib per-perm (stary wzorzec) ===")
t_b = None
try:
    _perm_numpy(0)                               # warmup
    t0 = time.perf_counter()
    Parallel(n_jobs=N_JOBS)(delayed(_perm_numpy)(i) for i in range(N_PERMS_POC))
    t_b = time.perf_counter() - t0
    print(f"  {N_PERMS_POC} perms: {t_b:.2f}s  |  {N_PERMS_POC/t_b:.0f} perms/s")
except Exception as exc:
    print(f"  FAIL: {exc}")


# --- WARIANT C: Numba JIT calego loopa + joblib nad konfiguracjami -----------
print("\n=== WARIANT C: Numba JIT loop + joblib nad konfiguracjami ===")
t_c_1core = None
t_c_parallel = None
n_fake_configs = 8          # symulacja: 8 konfiguracji w rownoleglosci
perms_per_config = N_PERMS_POC // n_fake_configs
if not _HAS_NUMBA:
    print("  SKIP: numba not installed")
else:
    try:
        print("  Kompilacja JIT...", end=" ", flush=True)
        t_jit = time.perf_counter()
        _all_perms_numba_core(DRAWS, 2, 0)       # compile
        _all_perms_numba_core(DRAWS, 2, 1)       # cache confirm
        print(f"{time.perf_counter()-t_jit:.2f}s")

        # 1-core: jeden job, N_PERMS_POC permutacji
        t0 = time.perf_counter()
        _all_perms_numba(N_PERMS_POC, 0)
        t_c_1core = time.perf_counter() - t0
        print(f"  1-core ({N_PERMS_POC} perms): {t_c_1core:.2f}s  |  "
              f"{N_PERMS_POC/t_c_1core:.0f} perms/s")

        # parallel: 8 joblib-jobow, kazdy robi perms_per_config permutacji
        t0 = time.perf_counter()
        Parallel(n_jobs=N_JOBS)(
            delayed(_all_perms_numba)(perms_per_config, k * perms_per_config)
            for k in range(n_fake_configs)
        )
        t_c_parallel = time.perf_counter() - t0
        total_c = n_fake_configs * perms_per_config
        print(f"  {n_fake_configs}-job parallel ({total_c} perms): "
              f"{t_c_parallel:.2f}s  |  {total_c/t_c_parallel:.0f} perms/s")

    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"  FAIL: {exc}")


# --- RAPORT ------------------------------------------------------------------
print("\n=== RAPORT PoC ===")
numba_ver = "N/A"
if _HAS_NUMBA:
    import numba
    numba_ver = numba.__version__
print(f"  Python {sys.version.split()[0]} | numpy {np.__version__} | numba {numba_ver}")
print(f"  A NumPy seq:      {'OK' if t_a else 'FAIL'}")
print(f"  B NumPy joblib:   {'OK' if t_b else 'FAIL'}")
print(f"  C Numba 1-core:   {'OK' if t_c_1core else 'FAIL'}")
print(f"  C Numba parallel: {'OK' if t_c_parallel else 'FAIL'}")

if t_a and t_c_1core:
    sp_1core = t_a / t_c_1core
    print(f"\n  Speedup Numba vs NumPy (1-core): {sp_1core:.2f}x")

if t_b and t_c_parallel:
    total_c = n_fake_configs * perms_per_config
    # Skalujemy C do pelnego testu: 1 config x 10k perms
    t_per_perm_c = t_c_parallel / total_c
    t_per_perm_b = t_b / N_PERMS_POC
    sp_parallel = t_per_perm_b / t_per_perm_c
    print(f"  Speedup Numba vs NumPy (parallel): {sp_parallel:.2f}x")

# Szacunek pelnaa pipeline: SCALE x N_CONFIGS_PROD konfiguracji
print(f"\n  Szacunek pelnej pipeline ({SCALE_TO_PROD}k perms x {N_CONFIGS_PROD} konfiguracii):")
if t_a:
    est_a = t_a * SCALE_TO_PROD * N_CONFIGS_PROD / 3600
    print(f"    NumPy seq (bez parallelism): {est_a:.1f}h")
if t_b:
    # joblib per-perm: throughput = N_PERMS_POC/t_b perms/s total
    est_b = (N_CONFIGS_PROD * SCALE_TO_PROD * N_PERMS_POC) / (N_PERMS_POC / t_b) / 3600
    print(f"    NumPy + joblib per-perm:     {est_b:.1f}h")
if t_c_parallel:
    total_c = n_fake_configs * perms_per_config
    throughput_c = total_c / t_c_parallel
    est_c = (N_CONFIGS_PROD * SCALE_TO_PROD * N_PERMS_POC) / throughput_c / 3600
    print(f"    Numba JIT + joblib configs:  {est_c:.1f}h")

# Werdykt
print()
if t_c_parallel:
    total_c = n_fake_configs * perms_per_config
    throughput_c = total_c / t_c_parallel
    est_c = (N_CONFIGS_PROD * SCALE_TO_PROD * N_PERMS_POC) / throughput_c / 3600
    if _HAS_NUMBA and t_c_1core and (t_a / t_c_1core) >= 3 and est_c <= OVERNIGHT_H:
        print("  OK Numba JIT (loop) skuteczna + pipeline w overnight limicie.")
        print("  DECYZJA: brief wymaga korekty wzorca uzycia Numby:")
        print("    -> joblib.Parallel nad konfigami (nie per-perm)")
        print("    -> @njit na calym loopie permutacji")
        print("  Idz do Kroku 7 po zapisaniu PoC Results do briefu.")
    elif est_c <= OVERNIGHT_H:
        print("  OK Pipeline miesci sie w overnight limicie.")
        print("  Wzorzec Numba+joblib (configs) dziala. Idz do Kroku 7.")
    else:
        print("  UWAGA Pipeline przekracza overnight limit.")
        print("  Rozwaize: redukcje N_CONFIGS lub importance sampling (§6.2 CPU Transcendence).")
elif t_b:
    est_b = (N_CONFIGS_PROD * SCALE_TO_PROD * N_PERMS_POC) / (N_PERMS_POC / t_b) / 3600
    if est_b <= OVERNIGHT_H:
        print("  OK NumPy + joblib wystarczy (Numba JIT opcjonalna).")
    else:
        print("  UWAGA Numba JIT konieczna ale nie dziala. Sprawdz srodowisko.")
else:
    print("  BLAD Kluczowe warianty failed. Sprawdz srodowisko.")
