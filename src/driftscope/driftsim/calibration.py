"""DriftSim calibration — sensitivity/specificity przez Monte Carlo (W3).

Mierzy power (sensitivity = P(detekcja | sygnal obecny)) i FPR (= 1 - specificity,
mierzony na nullu) detektorow wzgledem planted signals z `planted_signals.py`.
Wejscie do Decision Gate W5 (kryterium: power > 70% dla wykrywalnych sygnalow).

Harness jest DETECTOR-AGNOSTYCZNY: `Detector = Callable[[list[DrawRecord]], TestResult]`.
Power/FPR liczone przez powtarzanie scenariusza na niezaleznych strumieniach RNG
(`make_worker_seeds`) i zliczanie `reject_h0`.

Detektor W3 (`chi2_main_uniformity`): chi-squared goodness-of-fit na czestosciach
puli glownej (Family B chi-squared, preregistration_v3 §5).

Empiryczny wynik kalibracji (zwalidowany testem) — co chi² wykrywa, a co nie:
- WYKRYWA freq_shift i trend — bezposrednie odchylenie marginalne.
- WYKRYWA tez autocorr i seasonality — NIE przez zmiane sredniego marginalu, lecz
  przez NADMIERNA DYSPERSJE zliczen: clumping/runs (autocorr) oraz kontrast Tue/Fri
  (seasonality) zwiekszaja wariancje liczebnosci ponad multinomial → chi² odrzuca.
- SLEPY na pair_corr — zmienia tylko wspolwystapienia jednej pary (joint), marginal
  pozostaje ~uniform → power ≈ FPR. Wymaga dedykowanego testu wspolwystapien (W6).

Harness jest detector-agnostyczny: kolejne testy (MMD W4, recurrence/co-occurrence
W6) wepna sie tym samym interfejsem `Detector`.

Detektor W4 (`k4_mmd.mmd_uniform_detector`): MMD² (Gaussian RBF na frequency vectors
Δ⁴⁹ per okno) obserwacji vs swiezo wygenerowany uniform reference; okna NIENAKLADAJACE
sie (warunek wymienialnosci permutacyjnej). Empiryczny wynik kalibracji (zwalidowany,
window=25, 2026-05-31):
- WYKRYWA freq_shift (~1.0), trend (R2/R3 ~1.0; R1 ~0.31), autocorr (R2/R3 0.68/0.82;
  R1 slaby ~0.26), seasonality (R3 ~0.88; R1/R2 = null wg guard #4).
- SLEPY na pair_corr (power ≈ FPR ~0.05 we wszystkich rezimach) — TAK SAMO jak chi².
  Marginalny wektor czestosci nie niesie informacji o joint → ani chi², ani MMD nie
  lapia wspolwystapien. **Wniosek: dedykowany test wspolwystapien (W6) jest KONIECZNY,
  nie opcjonalny** (odpowiada na otwarte pytanie z W3).
- R1 (n=133) jest na granicy danych dla MMD okiennego (5 okien) — power systematycznie
  nizsza niz R2/R3.
Uzycie: `estimate_rejection_rate(sig, eff, reg, detector=mmd_uniform_detector(window=25))`.

Domyslne n per rezim = realne liczby losowan z seed CSV (W0, MEMORY.md 2026-05-26):
R1=133, R2=389, R3=436 — kalibracja odzwierciedla faktyczna moc na danych.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy.stats import chisquare

from driftscope.core.seeds import make_worker_seeds
from driftscope.core.types import DrawRecord, TestResult
from driftscope.driftsim.null_uniform import Regime, generate_uniform_draws
from driftscope.driftsim.planted_signals import (
    EFFECT_SIZES,
    SignalType,
    generate_planted_draws,
)

Detector = Callable[[list[DrawRecord]], TestResult]

_MAIN_POOL_SIZE = 50

# Realne n per rezim (seed CSV, W0). Domyslny rozmiar proby kalibracyjnej.
REGIME_N: dict[str, int] = {"R1": 133, "R2": 389, "R3": 436}

_DEFAULT_N_TRIALS = 200
_DEFAULT_ALPHA = 0.05


# ---------------------------------------------------------------------------
# Detektor W3 — chi-squared uniformity na puli glownej (preregistration_v3 §5)
# ---------------------------------------------------------------------------

def chi2_main_uniformity(draws: list[DrawRecord], alpha: float = _DEFAULT_ALPHA) -> TestResult:
    """chi-squared GoF: H0 = liczby glowne ~ Uniform(1..50). reject_h0 ⇔ p < alpha."""
    counts = np.zeros(_MAIN_POOL_SIZE, dtype=float)
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
# Estymacja Monte Carlo
# ---------------------------------------------------------------------------

def _scenario_draws(
    signal: str,
    effect_size: float | None,
    regime: Regime,
    n_draws: int,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generuje jeden dataset scenariusza. signal=='null' → czysty null."""
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
    """Frakcja `n_trials` niezaleznych datasetow, w ktorych detektor odrzuca H0.

    Dla signal!='null' = power (sensitivity). Dla signal=='null' = FPR (1-specificity).
    Strumienie RNG niezalezne przez make_worker_seeds(base_seed, n_trials) (DoD-6).
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
    """Krzywa power vs effect-size dla jednego sygnalu w jednym rezimie.

    Zwraca {effect_size: power} po siatce §6 (EFFECT_SIZES[signal]).
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
    """FPR detektora na nullu w danym rezimie (specificity = 1 - FPR)."""
    return estimate_rejection_rate(
        "null", None, regime, detector, n_trials, n_draws, base_seed
    )


def calibrate_all(
    detector: Detector = chi2_main_uniformity,
    n_trials: int = _DEFAULT_N_TRIALS,
    base_seed: int = 42,
) -> dict[tuple[str, str], dict[float, float] | float]:
    """Pelny sweep: krzywe power dla 5 sygnalow × 3 rezimy + FPR null per rezim.

    Ciezki (artifact generation, NIE unit test). Klucz: (signal|"null", regime).
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
