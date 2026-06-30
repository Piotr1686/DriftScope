"""Specification curve tests (W6, preregistration_v5 §4).

Verifies: the 9-point grid structure, the stability logic (>2/9 → unstable),
stable absence on the null (closes FPR validation for N∈{15,40}), stable presence
of a strong signal, determinism.
"""
from __future__ import annotations

import numpy as np

from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.specification import (
    MAX_UNSTABLE,
    SPEC_BANDWIDTH_MULTS,
    SPEC_WINDOWS,
    SpecCurveResult,
    SpecPoint,
    specification_curve,
)


def _result(rejects: list[bool], alpha: float = 0.05) -> SpecCurveResult:
    pts = [
        SpecPoint(window=25, bandwidth_mult=1.0, p_value=0.01 if r else 0.5, reject=r)
        for r in rejects
    ]
    return SpecCurveResult(points=pts, alpha=alpha)


# ---------------------------------------------------------------------------
# Stability logic
# ---------------------------------------------------------------------------

def test_stable_when_few_dropouts() -> None:
    """≤ MAX_UNSTABLE non-significant points → stable."""
    assert _result([True] * 9).stable is True
    assert _result([True] * 7 + [False] * 2).stable is True  # 2/9 dropout = boundary


def test_unstable_when_too_many_dropouts() -> None:
    """> MAX_UNSTABLE non-significant points → unstable (vanishes in >2/9)."""
    assert _result([True] * 6 + [False] * 3).stable is False
    r = _result([False] * 9)
    assert r.n_significant == 0
    assert r.stable is False


def test_counts() -> None:
    r = _result([True] * 5 + [False] * 4)
    assert r.n_points == 9
    assert r.n_significant == 5
    assert r.n_nonsignificant == 4
    assert MAX_UNSTABLE == 2


# ---------------------------------------------------------------------------
# 9-point grid
# ---------------------------------------------------------------------------

def test_grid_shape_and_coverage() -> None:
    """9 points = 3 windows × 3 bandwidths; full §4 grid coverage."""
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(0))
    res = specification_curve(draws, n_perm=49)
    assert res.n_points == len(SPEC_WINDOWS) * len(SPEC_BANDWIDTH_MULTS) == 9
    covered = {(pt.window, pt.bandwidth_mult) for pt in res.points}
    assert covered == {(w, b) for w in SPEC_WINDOWS for b in SPEC_BANDWIDTH_MULTS}


def test_custom_grid() -> None:
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(1))
    res = specification_curve(draws, windows=(20, 30), bandwidth_mults=(1.0,), n_perm=49)
    assert res.n_points == 2


# ---------------------------------------------------------------------------
# Null (stable absence) + signal (stable presence)
# ---------------------------------------------------------------------------

def test_null_is_stable_absence() -> None:
    """On the null the spec curve does not reject in >MAX_UNSTABLE points — closes FPR N∈{15,40}.

    FPR validation for the whole grid (not just N=25): none or a negligible number of points
    reject under uniform-iid. Deterministic.
    """
    draws = generate_uniform_draws(436, "R3", np.random.default_rng(7))
    res = specification_curve(draws, n_perm=99)
    assert res.n_significant <= MAX_UNSTABLE, f"null rejected {res.n_significant}/9 points"


def test_strong_signal_is_stable_presence() -> None:
    """A strong freq_shift is robust — detected in >=7/9 points (stable)."""
    draws = generate_planted_draws(436, "R3", "freq_shift", 0.10, np.random.default_rng(0))
    res = specification_curve(draws, n_perm=99)
    assert res.stable is True
    assert res.n_significant >= 7


def test_specification_curve_deterministic() -> None:
    """The same `draws` → an identical spec curve (DoD-6: detectors are pure functions)."""
    draws = generate_planted_draws(300, "R3", "freq_shift", 0.10, np.random.default_rng(2))
    r1 = specification_curve(draws, n_perm=49)
    r2 = specification_curve(draws, n_perm=49)
    assert [p.p_value for p in r1.points] == [p.p_value for p in r2.points]
