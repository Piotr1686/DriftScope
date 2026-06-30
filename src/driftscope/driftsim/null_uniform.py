"""Honest null generator — DriftSim's honest baseline (W2).

Generates a stream of EuroJackpot draws under H0: stationary, uniform, i.i.d.
within a given regime (preregistration_v2 §1). It is the foundation of DriftSim:
planted signals (`planted_signals.py`) = this null + an injected signal.

Pure module: it knows only `DrawRecord` and the RNG. It knows nothing about
ingestion or reporting.

Pools (preregistration_v2 §1):
- R1: 5/50 + 2/8   (2012-03-23 -> 2014-10-03)
- R2: 5/50 + 2/10  (2014-10-10 -> 2022-03-18)
- R3: 5/50 + 2/12  (2022-03-25 -> present; two draws/week: Tuesday + Friday)

Dates are SYNTHETIC (weekly from the regime anchor) — the null does not model
real data, only the generative process. The weekday label (Tuesday/Friday) exists
ONLY in R3 (guard signal #4, preregistration_v2 §6): in R1/R2 every draw is a Friday.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

import numpy as np

from driftscope.core.types import DrawRecord

# Euronumber pool size per regime (upper bound inclusive; preregistration_v2 §1)
EURON_POOL_SIZE: dict[str, int] = {"R1": 8, "R2": 10, "R3": 12}

_MAIN_POOL_SIZE = 50  # main pool 1-50 — invariant across all regimes (negative control)
_MAIN_DRAW = 5        # 5 main numbers without replacement
_EURON_DRAW = 2       # 2 euronumbers without replacement

# Synthetic anchors — Fridays starting each regime (arbitrary, just monotonic).
# R3 generates Tuesday/Friday pairs (since 2022 EuroJackpot draws twice a week).
_REGIME_ANCHOR_FRIDAY: dict[str, date] = {
    "R1": date(2012, 3, 23),   # Friday
    "R2": date(2014, 10, 10),  # Friday
    "R3": date(2022, 3, 25),   # Friday (R3: we add Tuesdays)
}

Regime = Literal["R1", "R2", "R3"]


def synthetic_dates(n_draws: int, regime: Regime) -> list[date]:
    """Monotonic synthetic dates for a regime (shared with planted_signals).

    R1/R2: one draw/week (Friday). R3: two/week (Tuesday + Friday), which creates
    the real weekday label needed for signal #4 (weekly seasonality).
    """
    anchor_friday = _REGIME_ANCHOR_FRIDAY[regime]
    dates: list[date] = []

    if regime == "R3":
        # Tuesday/Friday pair each week. Tuesday = Friday - 3 days.
        first_tuesday = anchor_friday - timedelta(days=3)
        week = 0
        while len(dates) < n_draws:
            tuesday = first_tuesday + timedelta(weeks=week)
            dates.append(tuesday)
            if len(dates) < n_draws:
                dates.append(tuesday + timedelta(days=3))  # Friday
            week += 1
    else:
        for i in range(n_draws):
            dates.append(anchor_friday + timedelta(weeks=i))

    return dates[:n_draws]


def sample_euron(regime: Regime, rng: np.random.Generator) -> tuple[int, int]:
    """Draw 2 euronumbers (without replacement, ascending) from the regime pool.

    Shared with planted_signals: signals touch the main pool, euron stays null.
    +1 because rng.choice returns 0-based indices while numbers are 1-based.
    """
    euron = np.sort(rng.choice(EURON_POOL_SIZE[regime], size=_EURON_DRAW, replace=False) + 1)
    return int(euron[0]), int(euron[1])


def generate_uniform_draws(
    n_draws: int,
    regime: Regime,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generate `n_draws` i.i.d. uniform draws for the given regime.

    Each draw: 5 of 50 (without replacement, ascending) + 2 of the regime euron
    pool (without replacement, ascending). Dates are synthetic (see `synthetic_dates`).

    Determinism: fully determined by `rng`. Reproducible stream:
        from driftscope.core.seeds import make_worker_seeds
        seq = make_worker_seeds(BASE_SEED, 1)[0]
        draws = generate_uniform_draws(n, "R2", np.random.default_rng(seq))

    Args:
        n_draws: number of draws to generate (> 0).
        regime: "R1" | "R2" | "R3" — determines the euronumber pool and calendar.
        rng: NumPy generator (the only source of randomness).

    Returns:
        List of `n_draws` `DrawRecord`s in chronological order.

    Raises:
        ValueError: when `regime` is unknown or `n_draws` <= 0.
    """
    if regime not in EURON_POOL_SIZE:
        raise ValueError(f"Unknown regime: {regime!r} (expected R1/R2/R3)")
    if n_draws <= 0:
        raise ValueError(f"n_draws must be > 0, got {n_draws}")

    dates = synthetic_dates(n_draws, regime)
    records: list[DrawRecord] = []

    for draw_date in dates:
        # +1 because rng.choice returns 0-based indices while numbers are 1-based.
        main = np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False) + 1)
        euron_1, euron_2 = sample_euron(regime, rng)
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


# Anchor for generic streams (a game other than EJ; e.g. Multi Multi). Synthetic dates —
# the generator models the generative process, not the calendar of a specific game.
_GENERIC_ANCHOR = date(2015, 1, 2)  # Friday


def generate_generic_uniform(
    n_draws: int,
    pool_size: int,
    k: int,
    rng: np.random.Generator,
    anchor: date = _GENERIC_ANCHOR,
) -> list[DrawRecord]:
    """Generate `n_draws` i.i.d. uniform k-of-`pool_size` draws (generic game, no euron).

    Honest null for games other than EuroJackpot (Multi Multi 20-of-80, reference for MMD,
    BOCPD calibration of a new pool). Each draw: `k` numbers from 1..`pool_size` without
    replacement, ascending. Generic records (`DrawRecord.generic`) carry `pool_size`, so
    detectors derive the pool/k from the data.

    Determinism: fully determined by `rng` (DoD-6).

    Args:
        n_draws: number of draws (> 0).
        pool_size: size of the main pool (> k).
        k: numbers per draw (> 0).
        rng: NumPy generator (the only source of randomness).
        anchor: start date (synthetic, weekly dates).

    Returns:
        List of `n_draws` generic records in chronological order.

    Raises:
        ValueError: when `n_draws` <= 0, `k` <= 0, or `k` > `pool_size`.
    """
    if n_draws <= 0:
        raise ValueError(f"n_draws must be > 0, got {n_draws}")
    if k <= 0 or k > pool_size:
        raise ValueError(f"k={k} out of range (0, pool_size={pool_size}]")

    records: list[DrawRecord] = []
    for i in range(n_draws):
        nums = np.sort(rng.choice(pool_size, size=k, replace=False) + 1)
        records.append(
            DrawRecord.generic(
                draw_date=anchor + timedelta(weeks=i),
                numbers=[int(x) for x in nums],
                pool_size=pool_size,
            )
        )
    return records
