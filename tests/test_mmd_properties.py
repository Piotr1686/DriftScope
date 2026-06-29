"""Testy wlasciwosci MMD (W4).

Weryfikuje: frequency vectors Δ⁴⁹, wlasciwosci MMD² (zero dla tego samego rozkladu,
dodatni dla roznych), median heuristic (anti-leakage), kalibracje permutacyjna oraz
prog stabilnosci FPR ≤ 7.5% na shuffled null przy N=200 (preregistration_v3 §3).
"""
from __future__ import annotations

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.calibration import estimate_rejection_rate
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.driftsim.planted_signals import generate_planted_draws
from driftscope.methodology.k4_mmd import (
    frequency_vector,
    median_heuristic,
    mmd_permutation_test,
    mmd_rbf_squared,
    mmd_uniform_detector,
    sliding_frequency_vectors,
)

# ---------------------------------------------------------------------------
# Frequency vectors p ∈ Δ⁴⁹
# ---------------------------------------------------------------------------

def test_frequency_vector_is_on_simplex() -> None:
    """Wektor czestosci ma wymiar 50 i sumuje sie do 1 (p ∈ Δ⁴⁹)."""
    draws = generate_uniform_draws(100, "R2", np.random.default_rng(0))
    p = frequency_vector(draws)
    assert p.shape == (50,)
    assert p.sum() == pytest.approx(1.0)
    assert (p >= 0).all()


def test_sliding_windows_shape_and_simplex() -> None:
    """Liczba okien = floor((n-w)/step)+1; kazdy wiersz na simpleksie."""
    draws = generate_uniform_draws(389, "R2", np.random.default_rng(1))
    vecs = sliding_frequency_vectors(draws, window=25, step=25)
    assert vecs.shape == ((389 - 25) // 25 + 1, 50)
    assert np.allclose(vecs.sum(axis=1), 1.0)


def test_sliding_window_too_large_raises() -> None:
    draws = generate_uniform_draws(20, "R2", np.random.default_rng(2))
    with pytest.raises(ValueError):
        sliding_frequency_vectors(draws, window=25, step=25)


# ---------------------------------------------------------------------------
# MMD² — wlasciwosci estymatora
# ---------------------------------------------------------------------------

def test_mmd_zero_for_identical_distributions() -> None:
    """MMD² ~ 0 dla dwoch prob z TEGO SAMEGO rozkladu; istotnie mniejszy niz dla roznych."""
    rng = np.random.default_rng(3)
    X = rng.normal(size=(40, 50))
    Y = rng.normal(size=(40, 50))           # ten sam rozklad
    Z = rng.normal(loc=2.0, size=(40, 50))  # przesuniety rozklad
    bw = median_heuristic(X)
    mmd_same = mmd_rbf_squared(X, Y, bw)
    mmd_diff = mmd_rbf_squared(X, Z, bw)
    assert abs(mmd_same) < 0.05          # blisko zera (estymator nieobciazony, moze byc < 0)
    assert mmd_diff > 0.3                # wyraznie dodatni dla roznych rozkladow
    assert mmd_diff > 10 * abs(mmd_same)


def test_mmd_self_is_near_zero() -> None:
    """MMD²(X, X) ~ 0 (nieobciazony estymator wyklucza diagonale)."""
    rng = np.random.default_rng(4)
    X = rng.normal(size=(30, 50))
    bw = median_heuristic(X)
    assert abs(mmd_rbf_squared(X, X, bw)) < 0.05


def test_median_heuristic_positive() -> None:
    """Bandwidth > 0 dla niezdegenerowanych danych; fallback 1.0 dla <2 punktow."""
    rng = np.random.default_rng(5)
    X = rng.normal(size=(20, 50))
    assert median_heuristic(X) > 0.0
    assert median_heuristic(X[:1]) == 1.0  # degeneracja → fallback


# ---------------------------------------------------------------------------
# Test permutacyjny
# ---------------------------------------------------------------------------

def test_permutation_pvalue_in_range_and_detects_shift() -> None:
    """p-value ∈ (0,1]; test odrzuca dla wyraznie roznych rozkladow."""
    rng = np.random.default_rng(6)
    X = rng.normal(size=(30, 50))
    Z = rng.normal(loc=1.5, size=(30, 50))
    res = mmd_permutation_test(X, Z, n_perm=199, rng=rng)
    assert 0.0 < res.p_value <= 1.0
    assert res.reject_h0 is True
    assert res.test_name == "mmd_rbf_permutation"


def test_permutation_does_not_reject_same_distribution() -> None:
    """Dla prob z tego samego rozkladu p-value nieistotne (brak odrzucenia)."""
    rng = np.random.default_rng(7)
    X = rng.normal(size=(40, 50))
    Y = rng.normal(size=(40, 50))
    res = mmd_permutation_test(X, Y, n_perm=199, rng=rng)
    assert res.reject_h0 is False


# ---------------------------------------------------------------------------
# Detector — guard non-overlap + power sanity
# ---------------------------------------------------------------------------

def test_detector_rejects_overlapping_windows() -> None:
    """step < window lamie wymienialnosc permutacyjna → zabronione (FPR ~1.0)."""
    with pytest.raises(ValueError, match="non-overlap"):
        mmd_uniform_detector(window=25, step=5)


def test_detector_detects_freq_shift() -> None:
    """Detektor odrzuca H0 na strumieniu z silnym freq_shift (δ=0.10)."""
    det = mmd_uniform_detector(window=25, n_perm=199)
    draws = generate_planted_draws(389, "R2", "freq_shift", 0.10, np.random.default_rng(8))
    assert det(draws).reject_h0 is True


def test_mmd_blind_to_pair_corr() -> None:
    """MMD (frequency-vector, marginalny) jest slepy na pair_corr — power ≈ FPR.

    pair_corr (v5, margin-preserving) trzyma czestosci marginalne ~uniform, wiec MMD²
    na wektorach czestosci nie widzi sygnalu (caly jest w wymiarze JOINT). Dopelnia
    test_chi2_blind_to_pair_correlation (test_driftsim_calibration) i
    test_serial_blind_to_pair_corr (test_permutation_null): OBA filary marginalne (H1,
    MMD) sa dowodliwie slepe; lapie tylko co-occurrence (test_detects_planted_pair_corr_
    showcase). To uzasadnia, ze 'must agree' NIE jest twardym progiem (clean cell = 1/3).
    Deterministyczne (estimate_rejection_rate: base_seed=42 + seed detektora z hash draws).
    """
    det = mmd_uniform_detector(window=25, n_perm=99)
    pair_power = estimate_rejection_rate("pair_corr", 0.10, "R2", det, n_trials=50)
    freq_power = estimate_rejection_rate("freq_shift", 0.10, "R2", det, n_trials=50)
    assert pair_power < 0.15, f"MMD nie powinien widziec pair_corr (power={pair_power})"
    assert freq_power > 0.70, f"MMD powinien widziec freq_shift (power={freq_power})"
    assert pair_power < freq_power


# ---------------------------------------------------------------------------
# Prog stabilnosci §3 — FPR ≤ 7.5% na shuffled null
# ---------------------------------------------------------------------------

def test_mmd_stability_n200_fpr() -> None:
    """FPR ≤ 7.5% na nullu uniform przy rozmiarze OKNA N=200 (preregistration_v3 §3).

    "N=200" = rozmiar okna, nie dlugosc strumienia. Okna nienakladajace sie (step=window)
    to warunek wymienialnosci permutacyjnej; test permutacyjny z `+1` jest dowodliwie
    konserwatywny (E[FPR] ≤ α=0.05). Strumien = 2000 losowan → 10 okien: przy N=200
    potrzeba >=~10 okien dla stabilnej estymaty (5 okien daje liberalny, szumny FPR).

    UWAGA metodologiczna: realny strumien EuroJackpot (~958) daje przy window=200 tylko
    ~4 okna non-overlap — zbyt cienko. Wdrozona konfiguracja kalibracji to window=25
    (wiele okien; zob. test_mmd_fpr_window25). W pelni deterministyczne (stale seedy).
    """
    det = mmd_uniform_detector(window=200, n_perm=199)
    n_trials = 80
    rejects = sum(
        det(generate_uniform_draws(2000, "R2", np.random.default_rng(seq))).reject_h0
        for seq in make_worker_seeds(7, n_trials)
    )
    fpr = rejects / n_trials
    assert fpr <= 0.075, f"FPR={fpr} przekracza prog stabilnosci §3 (7.5%)"


def test_mmd_fpr_window25() -> None:
    """FPR ≤ 7.5% na WDROZONEJ konfiguracji kalibracji (window=25).

    To faktyczny operating point harnessu DriftSim (window=25 → R2=15, R3=17 okien
    non-overlap). FPR liczony pooled na R2+R3 (mniejsza wariancja MC). W pelni
    deterministyczne (stale seedy + seed detektora z hash draws → czysta funkcja).
    """
    det = mmd_uniform_detector(window=25, n_perm=199)
    n_trials = 100
    rejects = 0
    for regime, n in (("R2", 389), ("R3", 436)):
        rejects += sum(
            det(generate_uniform_draws(n, regime, np.random.default_rng(seq))).reject_h0
            for seq in make_worker_seeds(7, n_trials)
        )
    fpr = rejects / (2 * n_trials)
    assert fpr <= 0.075, f"FPR(window=25, R2+R3 pooled)={fpr} przekracza 7.5%"
