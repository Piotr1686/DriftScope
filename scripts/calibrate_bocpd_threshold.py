"""Kalibracja progu reject_h0 dla BOCPD (h1_classical.run_bocpd).

Magiczny prog `max_cp_prob > 0.3` zastapiony empirycznym 95. percentylem rozkladu
max(cp_prob[warmup:]) pod nullem uniform-iid (FPR ~= 0.05). Rozklad nullowy zalezy
od (N, K), wiec kalibrujemy osobno dla pol 'euron' (N=12, K=2) i 'main' (N=50, K=5).

Warm-up = N // K (preregistration_v6 §0): pomija transient burn-in, w ktorym cp_prob
sztucznie rosnie zanim pula symboli zostanie "zobaczona" (argmax pod nullem ~= 4-7).

Uruchomienie:
    python scripts/calibrate_bocpd_threshold.py
"""
from __future__ import annotations

import numpy as np

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import (
    generate_generic_uniform,
    generate_uniform_draws,
)
from driftscope.methodology.h1_classical import (
    _MAIN_REJECT_THRESHOLD_BY_POOL,
    run_bocpd,
)

BASE_SEED = 42
N_TRIALS = 200
REGIME = "R3"


def _report(label: str, n_draws: int, max_probs: np.ndarray) -> None:
    p95 = float(np.percentile(max_probs, 95))
    p99 = float(np.percentile(max_probs, 99))
    print(f"--- {label} (n={n_draws}, trials={N_TRIALS}) ---")
    print(f"  mean   = {max_probs.mean():.4f}")
    print(f"  median = {np.median(max_probs):.4f}")
    print(f"  max    = {max_probs.max():.4f}")
    print(f"  p90    = {np.percentile(max_probs, 90):.4f}")
    print(f"  p95    = {p95:.4f}")
    print(f"  p99    = {p99:.4f}")
    print(f"  FPR @ p95 = {float(np.mean(max_probs > p95)):.4f}")


def calibrate(field: str, n_draws: int) -> None:
    """Kalibracja EuroJackpot (pole euron N=12/K=2 lub main N=50/K=5)."""
    seeds = make_worker_seeds(BASE_SEED, N_TRIALS)
    max_probs = np.empty(N_TRIALS)
    for i, seq in enumerate(seeds):
        rng = np.random.default_rng(seq)
        draws = generate_uniform_draws(n_draws, REGIME, rng)
        res = run_bocpd(draws, field=field, hazard=0.005)
        max_probs[i] = res.statistic  # statistic == max(cp_prob)
    _report(f"field={field}", n_draws, max_probs)


def calibrate_generic(pool_size: int, k: int, n_draws: int) -> None:
    """Kalibracja progu BOCPD dla generycznej puli main (np. Multi Multi N=80, K=20).

    Placeholder progu (1.0) wstrzykiwany przed wywolaniem, bo `run_bocpd(field='main')`
    odpytuje slownik progow — `res.statistic` (max cp_prob) jest jednak NIEZALEZNY od progu.
    p95 wpisac recznie do `_MAIN_REJECT_THRESHOLD_BY_POOL[pool_size]` w h1_classical.py.
    """
    _MAIN_REJECT_THRESHOLD_BY_POOL.setdefault(pool_size, 1.0)
    seeds = make_worker_seeds(BASE_SEED, N_TRIALS)
    max_probs = np.empty(N_TRIALS)
    for i, seq in enumerate(seeds):
        rng = np.random.default_rng(seq)
        draws = generate_generic_uniform(n_draws, pool_size, k, rng)
        res = run_bocpd(draws, field="main", hazard=0.005)
        max_probs[i] = res.statistic
    _report(f"generic pool={pool_size} k={k} (warmup={pool_size // k})", n_draws, max_probs)


if __name__ == "__main__":
    for n_draws in (436, 958):
        for field in ("euron", "main"):
            calibrate(field, n_draws)
    # Multi Multi (20-z-80) — druga gra, negative control. Prog NIEzalezny od dlugosci serii.
    for n_mm in (2000, 5000):
        calibrate_generic(pool_size=80, k=20, n_draws=n_mm)
