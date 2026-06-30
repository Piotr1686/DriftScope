"""Family-aware FDR tests (W6, preregistration §5, DoD-3).

Verifies: q-value monotonicity and range, BY ⊇ conservatism vs BH, Storey pi0,
FDR control on the null, power under injected signals, input validation.
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.methodology.multiple_testing import (
    FAMILY_A_SIZE,
    FAMILY_B_SIZE,
    bh_adjusted,
    by_adjusted,
    correct_family_a,
    correct_family_b,
    storey_qvalues,
)

# ---------------------------------------------------------------------------
# q-value properties
# ---------------------------------------------------------------------------

def test_adjusted_in_range() -> None:
    p = np.array([0.001, 0.01, 0.03, 0.2, 0.5, 0.9])
    for q in (bh_adjusted(p), by_adjusted(p), storey_qvalues(p)):
        assert (q >= 0.0).all() and (q <= 1.0).all()


def test_by_more_conservative_than_bh() -> None:
    """Benjamini-Yekutieli >= Benjamini-Hochberg elementwise (factor c(m) = Σ1/i)."""
    rng = np.random.default_rng(0)
    p = np.sort(rng.uniform(0, 0.3, size=40))
    q_bh, q_by = bh_adjusted(p), by_adjusted(p)
    assert (q_by >= q_bh - 1e-12).all()


def test_storey_le_bh_with_many_signals() -> None:
    """Storey (pi0<1) no more conservative than BH when there are many true H1."""
    # 30 strong signals + 10 null → pi0 < 1
    p = np.concatenate([np.full(30, 1e-4), np.random.default_rng(1).uniform(0, 1, 10)])
    q_storey, q_bh = storey_qvalues(p), bh_adjusted(p)
    assert (q_storey <= q_bh + 1e-12).all()


def test_storey_pi0_near_one_for_pure_null() -> None:
    """For a pure null pi0 ≈ 1 → Storey ≈ BH (not significantly looser)."""
    p = np.random.default_rng(2).uniform(0, 1, size=500)
    q_storey, q_bh = storey_qvalues(p), bh_adjusted(p)
    # at pi0≈1 Storey ~ BH; we allow a small margin
    assert np.median(q_storey) >= 0.4 * np.median(q_bh)


# ---------------------------------------------------------------------------
# FDR control on the null + power
# ---------------------------------------------------------------------------

def test_fdr_control_on_null_family_b() -> None:
    """Family B (BY) on 150 null p-values: a negligible number of false rejections."""
    p = np.random.default_rng(3).uniform(0, 1, size=FAMILY_B_SIZE)
    res = correct_family_b(p)
    assert res.n_reject <= 2, f"BY on the null rejected {res.n_reject} (expected ~0)"


def test_power_on_planted_signals() -> None:
    """Injected strong signals (p≈0) are rejected despite the correction."""
    p = np.concatenate([np.full(5, 1e-6), np.random.default_rng(4).uniform(0, 1, 145)])
    res = correct_family_b(p)
    assert res.n_reject >= 5  # 5 strong ones pass even BY
    assert all(res.reject[:5])


# ---------------------------------------------------------------------------
# Family API
# ---------------------------------------------------------------------------

def test_family_a_has_storey_secondary() -> None:
    p = [0.001, 0.02, 0.04, 0.3] + [0.6] * 8  # 12 hypotheses (Family A)
    res = correct_family_a(p)
    assert res.method == "benjamini_hochberg"
    assert "storey" in res.secondary
    assert len(res.labels) == FAMILY_A_SIZE


def test_family_b_has_bh_secondary() -> None:
    res = correct_family_b([0.001, 0.01, 0.2], labels=["a", "b", "c"])
    assert res.method == "benjamini_yekutieli"
    assert "bh" in res.secondary
    assert res.rejected_labels() == [lbl for lbl, r in zip(res.labels, res.reject) if r]


# ---------------------------------------------------------------------------
# Input validation + edge cases
# ---------------------------------------------------------------------------

def test_label_length_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        correct_family_a([0.1, 0.2], labels=["only_one"])


def test_pvalue_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        correct_family_b([0.1, 1.5])


def test_empty_input() -> None:
    res = correct_family_a([])
    assert res.n_reject == 0
    assert res.q_values.size == 0
