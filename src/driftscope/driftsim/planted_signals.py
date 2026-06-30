"""DriftSim planted signals — injecting known signals into the null (W2).

Plant = honest null (`null_uniform`) + a controlled deviation from uniform
stationarity on the MAIN pool (1-50; frequency vector Δ⁴⁹, preregistration_v2 §3).
Euronumbers and the calendar stay null — the signal is isolated in one dimension.

5 signal types × 4 effect sizes = 20 scenarios + 1 null = 21 datasets/regime
(× 3 regimes = 63 unique; preregistration_v2 §6).

Signals (preregistration_v3 §6 — all grids PINNED):
  1. freq_shift  — p_k = 1/50 + δ      δ ∈ {0.01,0.02,0.05,0.10}
  2. autocorr    — recurrence boost ρ  ρ ∈ {0.05,0.10,0.15,0.20}
  3. trend       — p_k(t)=1/50+β·t/T   β ∈ {0.01,0.02,0.05,0.10}
  4. seasonality — Tue/Fri contrast c  c ∈ {0.01,0.02,0.05,0.10}
                   GUARD: R3 only; in R1/R2 it degenerates to the null (§6).
  5. pair_corr   — forced-frac p        p ∈ {0.01,0.02,0.05,0.10}
                   MARGINS PRESERVED (clean joint signal; §6 — re-design v5).

The β (trend) and c (seasonality) grids were pinned down in preregistration_v3
(§0/§6, 2026-05-30) — v2 left them un-pinned; v3 ratifies the values above as a
clean revision BEFORE the W3 calibration.

The pair_corr mechanism was re-designed in preregistration_v5 (W6, 2026-05-31): the
parameter is now the forced-fraction p (NOT a lift multiplier), and the construction
PRESERVES the margins (see `_sample_pair_corr`). The old mechanism (lift, "force a
pair + 3 uniform") leaked into the margins (P(planted)=0.1+0.9·p) and produced a
forced-frac of 0.0008..0.0082 — below every test's detection floor (finding W6). The
new one isolates the signal in the JOINT dimension: chi²/MMD provably blind (margins
uniform), the co-occurrence test (§5c) catches it.
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import numpy.typing as npt

from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import (
    Regime,
    generate_uniform_draws,
    sample_euron,
    synthetic_dates,
)

SignalType = Literal["freq_shift", "autocorr", "trend", "seasonality", "pair_corr"]

# Effect-size grids per signal (preregistration_v3 §6 — all PINNED).
EFFECT_SIZES: dict[SignalType, tuple[float, ...]] = {
    "freq_shift": (0.01, 0.02, 0.05, 0.10),   # δ    (PINNED since v2)
    "autocorr": (0.05, 0.10, 0.15, 0.20),     # ρ    (PINNED since v2)
    "trend": (0.01, 0.02, 0.05, 0.10),        # β    (PINNED in v3)
    "seasonality": (0.01, 0.02, 0.05, 0.10),  # c    (PINNED in v3)
    "pair_corr": (0.01, 0.02, 0.05, 0.10),    # forced-frac p, margin-preserving (v5)
}

_MAIN_POOL_SIZE = 50
_MAIN_DRAW = 5

# Numbers carrying the signal (arbitrary, fixed for reproducibility; 1-based indices).
PLANTED_MAIN = 7          # signals #1, #3, #4 modify this number
PLANTED_PAIR = (7, 13)    # signal #5: this pair co-occurs more often

# Pool of 48 numbers outside the pair (1-based) — used to force the pair and compensate the margin.
_PAIR_OTHERS = np.array(
    [k for k in range(1, _MAIN_POOL_SIZE + 1) if k not in PLANTED_PAIR], dtype=np.int64
)

# Baseline P(both pair numbers in one 5/50 draw) under the null:
#   C(48,3)/C(50,5) = (5·4)/(50·49) = 20/2450 ≈ 0.00816
_PAIR_BASE_PROB = (_MAIN_DRAW * (_MAIN_DRAW - 1)) / (_MAIN_POOL_SIZE * (_MAIN_POOL_SIZE - 1))

_WEEKDAY_FRIDAY = 4
_WEEKDAY_TUESDAY = 1


def _sample_main_weighted(
    weights: npt.NDArray[np.float64], rng: np.random.Generator
) -> npt.NDArray[np.int64]:
    """5 of 50 without replacement by weights (ascending, 1-based). Weights normalized inside."""
    p = weights / weights.sum()
    return np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False, p=p) + 1)


def _weights_for(
    signal: SignalType,
    effect: float,
    t: int,
    n_draws: int,
    weekday: int,
    prev_main: npt.NDArray[np.int64] | None,
) -> npt.NDArray[np.float64]:
    """Weight vector (len 50) for draw t under the given marginal signal."""
    w = np.full(_MAIN_POOL_SIZE, 1.0 / _MAIN_POOL_SIZE)
    idx = PLANTED_MAIN - 1

    if signal == "freq_shift":
        w[idx] += effect
    elif signal == "trend":
        frac = t / (n_draws - 1) if n_draws > 1 else 1.0
        w[idx] += effect * frac
    elif signal == "autocorr":
        if prev_main is not None:
            for k in prev_main:
                w[k - 1] += effect  # boost recurrence of numbers from the previous draw
    elif signal == "seasonality":
        # Tue/Fri contrast: Friday +c, Tuesday -c on the planted number (clip > 0).
        delta = effect if weekday == _WEEKDAY_FRIDAY else -effect
        w[idx] = max(w[idx] + delta, 1e-6)

    return w


def _sample_pair_corr(forced_frac: float, rng: np.random.Generator) -> npt.NDArray[np.int64]:
    """Signal #5 (margin-preserving): raises co-occurrence of PLANTED_PAIR, NOT the margins.

    3-component mixture (forced_frac = p ∈ [0, 0.1], preregistration_v5 §6):
      - with p:       force the pair {i,j} + 3 numbers from the remaining 48,
      - with 9p:      force the ABSENCE of both i,j (5 from the remaining 48) — margin compensation,
      - with (1−10p): an ordinary uniform 5/50.
    The weights guarantee P(i)=P(j)=P(any other)=0.1 EXACTLY (uniform margin), while
    P(i,j together) rises from ~0.00816 to 0.918·p+0.00816 (e.g. ~6.6× at p=0.05). This
    isolates the signal in the JOINT dimension: chi²/MMD (marginal) blind, the
    co-occurrence test (§5c) catches it. The construction requires p ≤ 0.1 (then 1−10p ≥ 0).
    """
    i, j = PLANTED_PAIR
    r = rng.random()
    if r < forced_frac:
        # Force the pair + 3 from the remaining 48.
        extra = rng.choice(_PAIR_OTHERS, size=_MAIN_DRAW - 2, replace=False)
        return np.sort(np.array([i, j, *extra]))
    if r < 10.0 * forced_frac:
        # Force the absence of both (5 from the remaining 48) — keeps the i,j margin at 0.1.
        return np.sort(rng.choice(_PAIR_OTHERS, size=_MAIN_DRAW, replace=False))
    # Ordinary uniform 5/50 draw.
    return np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False) + 1)


def generate_planted_draws(
    n_draws: int,
    regime: Regime,
    signal: SignalType,
    effect_size: float,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generate `n_draws` draws with the `signal` injected at `effect_size`.

    The main pool carries the signal; euron and dates are null (preregistration_v3 §3/§6).
    Fully determined by `rng` (DoD-6).

    GUARD signal #4: `signal="seasonality"` in R1/R2 degenerates to a clean null
    (the Tue/Fri contrast does not exist — draws happen only on Fridays; §6). The slot
    is kept as an additional negative control.

    Args:
        n_draws: number of draws (> 0).
        regime: "R1" | "R2" | "R3" — euron pool + calendar.
        signal: signal type (see SignalType / EFFECT_SIZES).
        effect_size: a value from the §6 grid for the given signal.
        rng: NumPy generator (the only source of randomness).

    Returns:
        List of `n_draws` `DrawRecord`s in chronological order.

    Raises:
        ValueError: unknown signal, effect_size outside the §6 grid, or n_draws <= 0.
    """
    if signal not in EFFECT_SIZES:
        raise ValueError(f"Unknown signal: {signal!r} (expected {list(EFFECT_SIZES)})")
    if effect_size not in EFFECT_SIZES[signal]:
        raise ValueError(
            f"effect_size {effect_size} not in §6 grid for {signal!r}: "
            f"{EFFECT_SIZES[signal]}"
        )
    if n_draws <= 0:
        raise ValueError(f"n_draws must be > 0, got {n_draws}")

    # GUARD signal #4 — outside R3 there is no weekday label → null.
    if signal == "seasonality" and regime != "R3":
        return generate_uniform_draws(n_draws, regime, rng)

    dates = synthetic_dates(n_draws, regime)
    records: list[DrawRecord] = []
    prev_main: npt.NDArray[np.int64] | None = None

    for t, draw_date in enumerate(dates):
        if signal == "pair_corr":
            main = _sample_pair_corr(effect_size, rng)
        else:
            w = _weights_for(
                signal, effect_size, t, n_draws, draw_date.weekday(), prev_main
            )
            main = _sample_main_weighted(w, rng)
        euron_1, euron_2 = sample_euron(regime, rng)
        prev_main = main
        records.append(
            DrawRecord(
                draw_date=draw_date,
                main_1=int(main[0]),
                main_2=int(main[1]),
                main_3=int(main[2]),
                main_4=int(main[3]),
                main_5=int(main[4]),
                euron_1=euron_1,
                euron_2=euron_2,
            )
        )

    return records


def enumerate_scenarios() -> list[tuple[str, float | None]]:
    """21 scenarios per regime: 20 (5 signals × 4 effects) + 1 null (§6).

    The null is represented as ("null", None). × 3 regimes = 63 unique datasets.
    """
    scenarios: list[tuple[str, float | None]] = []
    for signal, sizes in EFFECT_SIZES.items():
        for size in sizes:
            scenarios.append((signal, size))
    scenarios.append(("null", None))
    return scenarios
