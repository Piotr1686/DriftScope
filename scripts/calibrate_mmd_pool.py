"""Calibration of the MMD detector FPR for a generic pool (Multi Multi N=80, K=20).

MM plan step 8. The MM runner (`reporting/multimulti_audit`) gave a FLAG via a borderline MMD
(p=0.03) — that verdict came under the OLD, naive OR policy (any pillar fires a FLAG); under
the Disagreement Protocol a lone pillar 1/3 = clear, NOT a finding. A 12-seed pilot FPR
suggested a slight inflation (2/12), so calibration is warranted anyway. `mmd_uniform_detector`
(window=25) was validated for EJ (pool=50, k=5) — this script checks the FPR on an honest
uniform k-of-pool null for pool=80 and sweeps `window` to find a FPR~=0.05 configuration.

Determinism: make_worker_seeds(BASE_SEED, N_TRIALS) — independent streams (DoD-6).

Usage:
    python scripts/calibrate_mmd_pool.py
"""
from __future__ import annotations

import numpy as np

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_generic_uniform
from driftscope.methodology.k4_mmd import mmd_uniform_detector

BASE_SEED = 42
N_TRIALS = 200
N_PERM = 199
ALPHA = 0.05
POOL_SIZE = 80
K = 20
N_DRAWS = 2000
WINDOWS = (25, 40, 50)


def calibrate_mmd(window: int) -> None:
    """MMD FPR on the uniform k-of-pool null for the given window (non-overlap)."""
    detector = mmd_uniform_detector(window=window, n_perm=N_PERM, alpha=ALPHA)
    seeds = make_worker_seeds(BASE_SEED, N_TRIALS)
    pvals = np.empty(N_TRIALS)
    rejects = 0
    for i, seq in enumerate(seeds):
        rng = np.random.default_rng(seq)
        draws = generate_generic_uniform(N_DRAWS, POOL_SIZE, K, rng)
        res = detector(draws)
        pvals[i] = res.p_value
        rejects += int(res.reject_h0)
    n_windows = N_DRAWS // window
    fpr = rejects / N_TRIALS
    # 95% Wilson-ish CI proxy: MC error ~= sqrt(p(1-p)/n)
    mc_err = float(np.sqrt(fpr * (1 - fpr) / N_TRIALS))
    print(
        f"--- MMD window={window} (n_windows={n_windows}, pool={POOL_SIZE}, k={K}, "
        f"n={N_DRAWS}, trials={N_TRIALS}, n_perm={N_PERM}) ---"
    )
    print(f"  FPR @ alpha={ALPHA}: {fpr:.4f}  (+/- {mc_err:.4f} MC)  [{rejects}/{N_TRIALS}]")
    print(f"  p-value: mean={pvals.mean():.4f}  median={np.median(pvals):.4f}  "
          f"min={pvals.min():.4f}  p05={np.percentile(pvals, 5):.4f}")


if __name__ == "__main__":
    for w in WINDOWS:
        calibrate_mmd(w)
