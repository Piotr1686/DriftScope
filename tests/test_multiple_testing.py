"""Testy family-aware FDR (W6, preregistration §5, DoD-3).

Weryfikuje: monotonicznosc i zakres q-values, BY ⊇ konserwatyzm vs BH, Storey pi0,
kontrole FDR na nullu, moc przy wstrzyknietych sygnalach, walidacje wejscia.
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
# Wlasciwosci q-values
# ---------------------------------------------------------------------------

def test_adjusted_in_range() -> None:
    p = np.array([0.001, 0.01, 0.03, 0.2, 0.5, 0.9])
    for q in (bh_adjusted(p), by_adjusted(p), storey_qvalues(p)):
        assert (q >= 0.0).all() and (q <= 1.0).all()


def test_by_more_conservative_than_bh() -> None:
    """Benjamini-Yekutieli >= Benjamini-Hochberg elementwise (czynnik c(m) = Σ1/i)."""
    rng = np.random.default_rng(0)
    p = np.sort(rng.uniform(0, 0.3, size=40))
    q_bh, q_by = bh_adjusted(p), by_adjusted(p)
    assert (q_by >= q_bh - 1e-12).all()


def test_storey_le_bh_with_many_signals() -> None:
    """Storey (pi0<1) nie bardziej konserwatywny niz BH gdy duzo prawdziwych H1."""
    # 30 silnych sygnalow + 10 nullowych → pi0 < 1
    p = np.concatenate([np.full(30, 1e-4), np.random.default_rng(1).uniform(0, 1, 10)])
    q_storey, q_bh = storey_qvalues(p), bh_adjusted(p)
    assert (q_storey <= q_bh + 1e-12).all()


def test_storey_pi0_near_one_for_pure_null() -> None:
    """Dla czystego nullu pi0 ≈ 1 → Storey ≈ BH (nie istotnie luzniejszy)."""
    p = np.random.default_rng(2).uniform(0, 1, size=500)
    q_storey, q_bh = storey_qvalues(p), bh_adjusted(p)
    # przy pi0≈1 Storey ~ BH; dopuszczamy maly margines
    assert np.median(q_storey) >= 0.4 * np.median(q_bh)


# ---------------------------------------------------------------------------
# Kontrola FDR na nullu + moc
# ---------------------------------------------------------------------------

def test_fdr_control_on_null_family_b() -> None:
    """Family B (BY) na 150 nullowych p-values: znikoma liczba falszywych odrzucen."""
    p = np.random.default_rng(3).uniform(0, 1, size=FAMILY_B_SIZE)
    res = correct_family_b(p)
    assert res.n_reject <= 2, f"BY na nullu odrzucil {res.n_reject} (oczek ~0)"


def test_power_on_planted_signals() -> None:
    """Wstrzykniete silne sygnaly (p≈0) sa odrzucane mimo korekcji."""
    p = np.concatenate([np.full(5, 1e-6), np.random.default_rng(4).uniform(0, 1, 145)])
    res = correct_family_b(p)
    assert res.n_reject >= 5  # 5 silnych przechodzi nawet przez BY
    assert all(res.reject[:5])


# ---------------------------------------------------------------------------
# API rodzin
# ---------------------------------------------------------------------------

def test_family_a_has_storey_secondary() -> None:
    p = [0.001, 0.02, 0.04, 0.3] + [0.6] * 8  # 12 hip (Family A)
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
# Walidacja wejscia + brzegi
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
