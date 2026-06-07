"""Testy audytu informacyjno-teoretycznego (reporting/information_theory.py, wow opcja #3).

Weryfikuje: kanoniczne wlasnosci zlozonosci LZ76, kalibracje FPR ≤ α na nullu, moc na
strukturze SZEREGOWEJ (autocorr), slepote na czysty marginal (freq_shift) — dowod
komplementarnosci order-shuffle nulla — oraz determinizm (DoD-6).
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.reporting.information_theory import (
    information_detector,
    information_test,
    lz76_complexity,
)

# ---------------------------------------------------------------------------
# Kanoniczne wlasnosci zlozonosci Lempel-Ziv 1976
# ---------------------------------------------------------------------------

def _arr(*xs: int) -> np.ndarray:
    return np.array(xs, dtype=np.int32)


def test_lz76_single_symbol() -> None:
    """Pojedynczy symbol → c = 1 (granica dolna)."""
    assert lz76_complexity(_arr(7)) == 1


def test_lz76_constant_sequence() -> None:
    """Ciag staly (same powtorzenia) → c = 2, niezaleznie od dlugosci."""
    assert lz76_complexity(_arr(3, 3, 3, 3, 3, 3)) == 2
    assert lz76_complexity(np.full(100, 9, dtype=np.int32)) == 2


def test_lz76_all_distinct_maximal() -> None:
    """Same rozne symbole → c = n (zlozonosc maksymalna)."""
    seq = _arr(1, 2, 3, 4, 5, 6, 7)
    assert lz76_complexity(seq) == seq.shape[0]


def test_lz76_structure_below_random() -> None:
    """Strukturalny (periodyczny) ciag jest MNIEJ zlozony niz jego losowa permutacja."""
    rng = np.random.default_rng(0)
    periodic = np.tile(_arr(1, 2, 3, 4), 50)              # okres 4
    shuffled = periodic[rng.permutation(periodic.shape[0])]
    assert lz76_complexity(periodic) < lz76_complexity(shuffled)


# ---------------------------------------------------------------------------
# Kalibracja FPR <= alpha na nullu + moc
# ---------------------------------------------------------------------------

def test_fpr_on_null() -> None:
    """FPR ≤ α=0.05 (± margines MC) na nullu uniform. Deterministyczne (stale seedy)."""
    det = information_detector(n_perm=199)
    n_trials = 60
    rejects = sum(
        det(generate_uniform_draws(436, "R3", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(11, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.10, f"FPR={fpr} > prog (margines MC nad α=0.05)"


def test_detects_autocorr() -> None:
    """Czuly na strukture SZEREGOWA (autocorr) — order-shuffle ja lamie → lewy ogon."""
    det = information_detector(n_perm=199)
    draws = generate_planted_draws(436, "R3", "autocorr", 0.20, np.random.default_rng(3))
    assert det(draws).reject_h0 is True


def test_blind_to_freq_shift() -> None:
    """Slepy na czysty marginal (freq_shift) — order-shuffle zachowuje multiset → ~floor.

    Dowod komplementarnosci: marginal lapia chi²/MMD, nie IT (~FPR).
    """
    det = information_detector(n_perm=99)
    rejects = sum(
        det(
            generate_planted_draws(436, "R3", "freq_shift", 0.10, np.random.default_rng(s))
        ).reject_h0
        for s in range(20)
    )
    assert rejects <= 4


# ---------------------------------------------------------------------------
# Metadata cross-check + determinizm (DoD-6) + guardy
# ---------------------------------------------------------------------------

def test_metadata_fields_present() -> None:
    """TestResult niesie LZ76 (raw/norm) + bz2 cross-check w spojnych granicach."""
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(1))
    res = information_test(draws, n_perm=99, seed=0)
    assert res.test_name == "lz76_sequential"
    assert 0.0 < res.metadata["bz2_ratio"] <= 1.0
    assert 0.0 <= res.metadata["bz2_p"] <= 1.0
    assert res.metadata["lz76_raw"] >= 1
    assert res.statistic == pytest.approx(res.metadata["lz76_norm"])


def test_detector_is_pure_function() -> None:
    """DoD-6: identyczne draws → identyczny wynik (seed z digestu zawartosci)."""
    draws = generate_planted_draws(200, "R3", "autocorr", 0.20, np.random.default_rng(4))
    r1 = information_detector(n_perm=99)(draws)
    r2 = information_detector(n_perm=99)(draws)
    assert r1.p_value == r2.p_value
    assert r1.statistic == r2.statistic


def test_too_few_draws_raises() -> None:
    draws = generate_uniform_draws(1, "R2", np.random.default_rng(0))
    with pytest.raises(ValueError):
        information_test(draws, n_perm=99)
