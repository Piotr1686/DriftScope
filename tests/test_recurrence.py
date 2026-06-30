"""Recurrence / gap analysis tests (W6, preregistration §5b).

Verifies: gap extraction, KS vs Geometric, Nelson-Aalen (monotonicity + linearity),
EVT max-gap, FPR ≈ α calibration on the null, the complementary profile (catches autocorr,
blind to freq_shift — conditions on the margin), pure-function determinism (DoD-6).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.recurrence import (
    _ks_vs_geometric,
    evt_max_gap_pvalue,
    gap_recurrence_test,
    nelson_aalen,
    nelson_aalen_linearity_deviation,
    number_gaps,
    recurrence_detector,
)


def _draws_with_positions(positions: set[int], n: int, number: int = 7) -> list[DrawRecord]:
    """n draws where `number` appears exactly at indices `positions` (the rest = others)."""
    d0 = date(2022, 3, 25)
    recs: list[DrawRecord] = []
    for t in range(n):
        if t in positions:
            main = [number, 1, 2, 3, 4] if number not in (1, 2, 3, 4) else [number, 10, 20, 30, 40]
        else:
            main = [10, 20, 30, 40, 50]  # without `number`
        recs.append(
            DrawRecord(
                draw_date=d0 + timedelta(days=3 * t),
                main_1=main[0], main_2=main[1], main_3=main[2],
                main_4=main[3], main_5=main[4], euron_1=1, euron_2=2,
            )
        )
    return recs


# ---------------------------------------------------------------------------
# Gaps
# ---------------------------------------------------------------------------

def test_number_gaps_exact() -> None:
    """Gaps = differences of consecutive appearance indices."""
    draws = _draws_with_positions({2, 5, 6, 10}, n=12, number=7)
    gaps = number_gaps(draws, 7)
    assert list(gaps) == [3, 1, 4]  # 5-2, 6-5, 10-6


def test_number_gaps_empty_for_rare() -> None:
    """< 2 appearances → no gaps."""
    draws = _draws_with_positions({3}, n=12, number=7)
    assert number_gaps(draws, 7).size == 0


# ---------------------------------------------------------------------------
# KS vs Geometric
# ---------------------------------------------------------------------------

def test_ks_zero_for_too_few_gaps() -> None:
    assert _ks_vs_geometric(np.array([5]), 0.1) == 0.0
    assert _ks_vs_geometric(np.empty(0), 0.1) == 0.0


def test_ks_large_for_non_geometric() -> None:
    """Clumped gaps (all short + one huge) → large KS vs Geometric(0.1)."""
    clumped = np.array([1, 1, 1, 1, 1, 60])
    geom_like = np.random.default_rng(0).geometric(0.1, size=200)
    assert _ks_vs_geometric(clumped, 0.1) > _ks_vs_geometric(geom_like, 0.1)


# ---------------------------------------------------------------------------
# Nelson-Aalen + EVT
# ---------------------------------------------------------------------------

def test_nelson_aalen_monotone() -> None:
    """The cumulative hazard is non-decreasing."""
    gaps = np.random.default_rng(1).geometric(0.1, size=100)
    _, cumhaz = nelson_aalen(gaps)
    assert np.all(np.diff(cumhaz) >= -1e-12)


def test_nelson_aalen_linearity_deviation_sane() -> None:
    """Deviation from linearity: 0 for a degenerate case (<3 unique gaps), >0 for curvature.

    Scattered values, one event each, give a harmonic (concave) cumulative
    hazard → a positive deviation from the line joining the endpoints.
    """
    assert nelson_aalen_linearity_deviation(np.array([5, 5, 40, 40])) == 0.0  # 2 unique
    curved = np.arange(1, 40, 2)  # 20 unique values → concave cumhaz
    assert nelson_aalen_linearity_deviation(curved) > 0.0


def test_evt_max_gap_pvalue_sane() -> None:
    """p ∈ [0,1]; a longer max-gap → a smaller p."""
    short = np.array([5, 8, 10, 12, 9, 7])
    long = np.array([5, 8, 10, 12, 9, 80])
    _, p_short = evt_max_gap_pvalue(short, 0.1)
    _, p_long = evt_max_gap_pvalue(long, 0.1)
    assert 0.0 <= p_long <= p_short <= 1.0


# ---------------------------------------------------------------------------
# Detector — calibration + complementary profile
# ---------------------------------------------------------------------------

def test_recurrence_fpr_on_null() -> None:
    """FPR ≈ α on the uniform null (the draw-order shuffle calibrates correctly). Deterministic."""
    det = recurrence_detector(n_perm=99)
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(s))).reject_h0
        for s in range(40)
    )
    fpr = rejects / 40
    assert fpr <= 0.12, f"FPR(null)={fpr} — possible miscalibration"


def test_recurrence_detects_autocorr() -> None:
    """Catches autocorr (clumping) — the main target of the recurrence test."""
    det = recurrence_detector(n_perm=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_recurrence_blind_to_freq_shift() -> None:
    """Blind to freq_shift (purely marginal) — the draw-order shuffle conditions on the margin.

    A complementarity FEATURE: the marginal is caught by chi²/MMD; recurrence adds time.
    """
    det = recurrence_detector(n_perm=99)
    rejects = sum(
        det(
            generate_planted_draws(436, "R3", "freq_shift", 0.10, np.random.default_rng(s))
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4, f"expected ~floor (blind to marginal), power={rejects/20}"


# ---------------------------------------------------------------------------
# Determinism (DoD-6) + guards
# ---------------------------------------------------------------------------

def test_detector_is_pure_function() -> None:
    """Two fresh instances on the same `draws` → identical p-value (DoD-6)."""
    draws = generate_planted_draws(200, "R2", "autocorr", 0.20, np.random.default_rng(4))
    r1 = recurrence_detector(n_perm=99)(draws)
    r2 = recurrence_detector(n_perm=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic
    assert r1.metadata["top_number"] == r2.metadata["top_number"]


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(3, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        gap_recurrence_test(draws, n_perm=99)
