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
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.methodology.h1_classical import run_bocpd

BASE_SEED = 42
N_TRIALS = 200
REGIME = "R3"


def calibrate(field: str, n_draws: int) -> None:
    seeds = make_worker_seeds(BASE_SEED, N_TRIALS)
    max_probs = np.empty(N_TRIALS)
    for i, seq in enumerate(seeds):
        rng = np.random.default_rng(seq)
        draws = generate_uniform_draws(n_draws, REGIME, rng)
        res = run_bocpd(draws, field=field, hazard=0.005)
        max_probs[i] = res.statistic  # statistic == max(cp_prob)

    p95 = float(np.percentile(max_probs, 95))
    p99 = float(np.percentile(max_probs, 99))
    print(f"--- field={field} (n={n_draws}, trials={N_TRIALS}) ---")
    print(f"  mean   = {max_probs.mean():.4f}")
    print(f"  median = {np.median(max_probs):.4f}")
    print(f"  max    = {max_probs.max():.4f}")
    print(f"  p90    = {np.percentile(max_probs, 90):.4f}")
    print(f"  p95    = {p95:.4f}")
    print(f"  p99    = {p99:.4f}")
    # FPR przy starym progu 0.3
    fpr_old = float(np.mean(max_probs > 0.3))
    print(f"  FPR @ 0.3 (stary prog) = {fpr_old:.4f}")
    print(f"  FPR @ p95              = {float(np.mean(max_probs > p95)):.4f}")


if __name__ == "__main__":
    for n_draws in (436, 958):
        for field in ("euron", "main"):
            calibrate(field, n_draws)
