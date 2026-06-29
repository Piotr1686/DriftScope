"""Specification curve analysis (W6, preregistration_v5 §4).

Checks the ROBUSTNESS of the MMD result against arbitrary analytical choices: instead of a
single configuration we report a grid and require that the signal not depend on a single
choice. The grid (preregistration_v5 §4 — corrected from {100,200,400} after W4):

    window N ∈ {15, 25, 40}  ×  bandwidth ∈ {0.5×, 1×, 2×} median heuristic  =  9 points

**Stability criterion (§4):** the signal is UNSTABLE (→ not reported) if it disappears in
**> 2/9** points (p > α). Symmetrically: on the null the spec curve should be "stably
insignificant" (≤ 2/9 false rejections) — this closes the FPR validation for N ∈ {15, 40},
which v5 §4 left unvalidated (until now only N=25; see test_specification).

The spec curve uses `mmd_uniform_detector(window, bandwidth_mult)` per point (the same null
and framing as the rest of MMD). Determinism (DoD-6): each detector is a pure function of `draws`.
"""
from __future__ import annotations

from dataclasses import dataclass

from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import Regime
from driftscope.methodology.k4_mmd import DEFAULT_N_PERM, mmd_uniform_detector

# Grid §4 (preregistration_v5). Window fitted to real n (non-overlap).
SPEC_WINDOWS: tuple[int, ...] = (15, 25, 40)
SPEC_BANDWIDTH_MULTS: tuple[float, ...] = (0.5, 1.0, 2.0)
# Max number of insignificant points at which the signal is still "stable" (§4: disappears in >2/9).
MAX_UNSTABLE = 2
_DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class SpecPoint:
    """One spec-curve point: (window, bandwidth_mult) → p-value / decision."""

    window: int
    bandwidth_mult: float
    p_value: float
    reject: bool


@dataclass(frozen=True)
class SpecCurveResult:
    """Spec curve result (9 points) + stability assessment (§4)."""

    points: list[SpecPoint]
    alpha: float

    @property
    def n_points(self) -> int:
        return len(self.points)

    @property
    def n_significant(self) -> int:
        return sum(pt.reject for pt in self.points)

    @property
    def n_nonsignificant(self) -> int:
        return self.n_points - self.n_significant

    @property
    def stable(self) -> bool:
        """The signal is stable: it disappears (p>α) in at most MAX_UNSTABLE points (§4)."""
        return self.n_nonsignificant <= MAX_UNSTABLE


def specification_curve(
    draws: list[DrawRecord],
    windows: tuple[int, ...] = SPEC_WINDOWS,
    bandwidth_mults: tuple[float, ...] = SPEC_BANDWIDTH_MULTS,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = _DEFAULT_ALPHA,
    ref_regime: Regime = "R2",
    base_seed: int = 20260531,
) -> SpecCurveResult:
    """Computes the MMD spec curve over the grid `windows` × `bandwidth_mults` (§4).

    Each point = `mmd_uniform_detector(window, bandwidth_mult)` on the same `draws`.
    Returns a `SpecCurveResult` with 9 (by default) points and a `stable` assessment.
    """
    points: list[SpecPoint] = []
    for window in windows:
        for bw_mult in bandwidth_mults:
            detector = mmd_uniform_detector(
                window=window,
                n_perm=n_perm,
                alpha=alpha,
                ref_regime=ref_regime,
                base_seed=base_seed,
                bandwidth_mult=bw_mult,
            )
            res = detector(draws)
            points.append(
                SpecPoint(
                    window=window,
                    bandwidth_mult=bw_mult,
                    p_value=res.p_value,
                    reject=res.reject_h0,
                )
            )
    return SpecCurveResult(points=points, alpha=alpha)
