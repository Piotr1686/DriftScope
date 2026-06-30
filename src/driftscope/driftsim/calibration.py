"""DriftSim calibration — sensitivity/specificity via Monte Carlo (W3).

Measures power (sensitivity = P(detection | signal present)) and FPR (= 1 - specificity,
measured on the null) of detectors against the planted signals from `planted_signals.py`.
Input to the W5 Decision Gate (criterion: power > 70% for detectable signals).

The harness is DETECTOR-AGNOSTIC: `Detector = Callable[[list[DrawRecord]], TestResult]`.
Power/FPR are computed by repeating a scenario over independent RNG streams
(`make_worker_seeds`) and counting `reject_h0`.

W3 detector (`chi2_main_uniformity`): chi-squared goodness-of-fit on the main pool
frequencies (Family B chi-squared, preregistration_v3 §5).

Empirical calibration result (validated by test) — what chi² detects, and what it does not:
- DETECTS freq_shift and trend — direct marginal deviation.
- ALSO detects autocorr and seasonality — NOT through a change in the mean marginal, but
  through OVER-DISPERSION of the counts: clumping/runs (autocorr) and the Tue/Fri contrast
  (seasonality) inflate the count variance beyond multinomial → chi² rejects.
- BLIND to pair_corr — it only changes the co-occurrence of one pair (joint), the marginal
  stays ~uniform → power ≈ FPR. Requires a dedicated co-occurrence test (W6).

The harness is detector-agnostic: later tests (MMD W4, recurrence/co-occurrence W6)
plug into the same `Detector` interface.

W4 detector (`k4_mmd.mmd_uniform_detector`): MMD² (Gaussian RBF on frequency vectors
Δ⁴⁹ per window) of observations vs a freshly generated uniform reference; windows are
NON-OVERLAPPING (permutation exchangeability condition). Empirical calibration result
(validated, window=25, 2026-05-31):
- DETECTS freq_shift (~1.0), trend (R2/R3 ~1.0; R1 ~0.31), autocorr (R2/R3 0.68/0.82;
  R1 weak ~0.26), seasonality (R3 ~0.88; R1/R2 = null per guard #4).
- BLIND to pair_corr (power ≈ FPR ~0.05 in every regime) — SAME as chi². The marginal
  frequency vector carries no information about the joint → neither chi² nor MMD catches
  co-occurrences. **Conclusion: a dedicated co-occurrence test (W6) is NECESSARY,
  not optional** (answers the open question from W3).
- R1 (n=133) is at the data boundary for windowed MMD (5 windows) — power systematically
  lower than R2/R3.
Usage: `estimate_rejection_rate(sig, eff, reg, detector=mmd_uniform_detector(window=25))`.

W6 detector (`cooccurrence.cooccurrence_detector`): test of JOINT pair structure —
max-pair standardized co-occurrence with a curveball null (preserves BOTH margins,
breaks the pairing). Closes the pair_corr gap to which chi²/MMD are blind. After re-designing
the pair_corr mechanism to be MARGIN-PRESERVING (forced-frac p, uniform margins — §6/v5) it
gives a clean Disagreement Protocol cell — the ONLY detector catching this signal. Power
(n_trials=50, n_perm=99):
- p=0.01/0.02/0.05/0.10 → R1: .06/.08/.80/1.0 · R2: .06/.40/1.0/1.0 · R3: .08/.36/1.0/1.0.
- At p=0.10: chi²=0.06, MMD=0.03 (both at the FPR floor — margins preserved → provably
  blind). cooc FPR(null R3)=0.03. Decision Gate (>70%) met for p ≥ 0.05 everywhere.
- The old mechanism (lift) leaked into the margins and produced a forced-frac of 0.0008..0.0082 =
  below the floor (the original W6 finding, fixed in v5; analogous to W0 for δ=0.01).
Usage: `estimate_rejection_rate("pair_corr", 0.10, "R3", detector=cooccurrence_detector())`.

W6 detector (`recurrence.recurrence_detector`): TEMPORAL test — gap GoF (KS of gaps vs
Geometric(q=0.1), permutation-calibrated draw-order shuffle, max_k omnibus + number
localization). The third family (recurrence) alongside the marginal (chi²/MMD) and joint
(co-occurrence). Key property: the shuffle preserves the COUNT → CONDITIONS on the margin.
Profile (validated, n_trials=40/n_perm=99):
- DETECTS autocorr (clumping): R3 ρ=0.20 → 0.78, R2 ρ=0.10 → 0.50; grows with ρ.
- partly seasonality (R3 0.10 → 0.38, periodicity).
- BLIND to freq_shift (0.03) and trend (0.10) — marginal/drift conditioned out by the shuffle;
  BLIND to pair_corr (0.00) — non-temporal. FPR(null)=0.05.
Complementary: the only purely temporal one; per-number KS p-values feed Family B FDR (§5).
Usage: `estimate_rejection_rate("autocorr", 0.20, "R3", detector=recurrence_detector())`.

Default n per regime = the real draw counts from the seed CSV (W0, MEMORY.md 2026-05-26):
R1=133, R2=389, R3=436 — the calibration reflects the actual power on the data.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import chisquare

from driftscope.core.seeds import make_worker_seeds
from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.driftsim.null_uniform import Regime, generate_uniform_draws
from driftscope.driftsim.planted_signals import (
    EFFECT_SIZES,
    SignalType,
    generate_planted_draws,
)

_MAIN_POOL_SIZE = 50

# Real n per regime (seed CSV, W0). Default calibration sample size.
REGIME_N: dict[str, int] = {"R1": 133, "R2": 389, "R3": 436}

_DEFAULT_N_TRIALS = 200
_DEFAULT_ALPHA = 0.05


# ---------------------------------------------------------------------------
# W3 detector — chi-squared uniformity on the main pool (preregistration_v3 §5)
# ---------------------------------------------------------------------------

def chi2_main_uniformity(draws: list[DrawRecord], alpha: float = _DEFAULT_ALPHA) -> TestResult:
    """chi-squared GoF: H0 = main numbers ~ Uniform(1..pool). reject_h0 ⇔ p < alpha.

    The pool size is derived from the records (`draws[0].pool_size`; EJ=50, MM=80).
    """
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    counts = np.zeros(pool, dtype=float)
    for d in draws:
        for n in d.main_numbers:
            counts[n - 1] += 1.0
    stat, pval = chisquare(counts)  # f_exp=None → uniform
    return TestResult(
        test_name="chi2_main_uniformity",
        statistic=float(stat),
        p_value=float(pval),
        reject_h0=bool(pval < alpha),
        metadata={"alpha": alpha, "n_draws": len(draws), "h0": "main pool uniform"},
    )


# ---------------------------------------------------------------------------
# Monte Carlo estimation
# ---------------------------------------------------------------------------

def _scenario_draws(
    signal: str,
    effect_size: float | None,
    regime: Regime,
    n_draws: int,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generate one scenario dataset. signal=='null' → a clean null."""
    if signal == "null":
        return generate_uniform_draws(n_draws, regime, rng)
    assert effect_size is not None
    return generate_planted_draws(n_draws, regime, signal, effect_size, rng)  # type: ignore[arg-type]


def estimate_rejection_rate(
    signal: str,
    effect_size: float | None,
    regime: Regime,
    detector: Detector = chi2_main_uniformity,
    n_trials: int = _DEFAULT_N_TRIALS,
    n_draws: int | None = None,
    base_seed: int = 42,
) -> float:
    """Fraction of `n_trials` independent datasets in which the detector rejects H0.

    For signal!='null' = power (sensitivity). For signal=='null' = FPR (1-specificity).
    RNG streams are independent via make_worker_seeds(base_seed, n_trials) (DoD-6).
    """
    n = n_draws if n_draws is not None else REGIME_N[regime]
    rejects = 0
    for seq in make_worker_seeds(base_seed, n_trials):
        rng = np.random.default_rng(seq)
        draws = _scenario_draws(signal, effect_size, regime, n, rng)
        if detector(draws).reject_h0:
            rejects += 1
    return rejects / n_trials


def calibration_curve(
    signal: SignalType,
    regime: Regime,
    detector: Detector = chi2_main_uniformity,
    n_trials: int = _DEFAULT_N_TRIALS,
    n_draws: int | None = None,
    base_seed: int = 42,
) -> dict[float, float]:
    """Power vs effect-size curve for one signal in one regime.

    Returns {effect_size: power} over the §6 grid (EFFECT_SIZES[signal]).
    """
    return {
        effect: estimate_rejection_rate(
            signal, effect, regime, detector, n_trials, n_draws, base_seed
        )
        for effect in EFFECT_SIZES[signal]
    }


def false_positive_rate(
    regime: Regime,
    detector: Detector = chi2_main_uniformity,
    n_trials: int = _DEFAULT_N_TRIALS,
    n_draws: int | None = None,
    base_seed: int = 42,
) -> float:
    """Detector FPR on the null in the given regime (specificity = 1 - FPR)."""
    return estimate_rejection_rate(
        "null", None, regime, detector, n_trials, n_draws, base_seed
    )


def calibrate_all(
    detector: Detector = chi2_main_uniformity,
    n_trials: int = _DEFAULT_N_TRIALS,
    base_seed: int = 42,
) -> dict[tuple[str, str], dict[float, float] | float]:
    """Full sweep: power curves for 5 signals × 3 regimes + null FPR per regime.

    Heavy (artifact generation, NOT a unit test). Key: (signal|"null", regime).
    """
    out: dict[tuple[str, str], dict[float, float] | float] = {}
    regimes: tuple[Regime, ...] = ("R1", "R2", "R3")
    for regime in regimes:
        for signal in EFFECT_SIZES:
            out[(signal, regime)] = calibration_curve(
                signal, regime, detector, n_trials, base_seed=base_seed
            )
        out[("null", regime)] = false_positive_rate(
            regime, detector, n_trials, base_seed=base_seed
        )
    return out
