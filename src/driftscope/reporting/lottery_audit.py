"""World Lottery Audit — blind replication on official government draw histories.

Third/fourth real-world case studies (reusability showcase, reporting layer): Powerball
(5-of-69) and Mega Millions (5-of-75) from NY Open Data (data.ny.gov), each carrying
DOCUMENTED matrix changes that serve as ground truth — the same positive-control design
as the EuroJackpot 2014/2022 pool changes, replicated across games the framework has
never seen. No new methodology (reuse of `h1_classical` BOCPD + `pipeline` Family B +
`multiple_testing` BY — the reporting layer is NOT subject to the prereg §0 discipline).

Design decisions (all data-independent, fixed before reading results):

1. **Coverage warm-up.** The prereg-v6 warm-up `N//K` was sized for EJ euron (N/K=6);
   for k=5 games it grossly under-covers: the coupon-collector phase (every first-ever
   appearance of a symbol spikes cp_prob) lasts ~(N/k)·ln N draws. Warm-up here =
   ceil((N/k)·(ln N + 0.5772)) — the coupon-collector expectation. Thresholds in
   `_MAIN_REJECT_THRESHOLD_BY_POOL` for pools 69/75 are calibrated AT this warm-up
   (200 trials, uniform-iid null, FPR≈0.05; see scripts/calibrate_bocpd_threshold.py).

2. **Onset localization, not argmax.** A pool EXPANSION produces a change signature
   smeared over months (new symbols keep debuting — measured: MM 2013 last debut +189
   days; PB 2015 last debut +81 days — plus posterior re-equilibration). The blind CP
   estimate per above-threshold segment is therefore its ONSET (first crossing), and a
   detected onset is attributed to a documented event when it falls within
   [event, event + ATTRIBUTION_DAYS]. Onsets outside every attribution window count
   against specificity.

3. **Family B pre/post contrast recovers the matrix delta.** With the stream loaded at
   pool = historical max, a window under the OLD matrix flags the not-yet-introduced
   symbols as under-represented (two-sided exact binomial, BY-corrected), a window under
   the NEW matrix stops flagging them (growth) or starts flagging retired symbols
   (shrink). The contrast of under-represented sets across the event =
   (appeared, vanished) — the exact matrix delta, recovered from counts alone. This is
   the complementarity pillar: BOCPD is nearly blind to symbol RETIREMENT (evidence of
   absence accumulates slowly), Family B nails it.

Presentation (table/CLI) lives in scripts/lottery_audit.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import numpy.typing as npt

import driftscope
from driftscope.core.types import DrawRecord
from driftscope.ingestion.lotto_scraper import load_generic_seed_csv
from driftscope.methodology.h1_classical import compute_bocpd_curve
from driftscope.methodology.multiple_testing import correct_family_b
from driftscope.pipeline import family_b_per_number_pvalues

_ROOT = Path(driftscope.__file__).resolve().parents[2]

#: An onset within this many days AFTER a documented event is attributed to it
#: (measured smear: last new-symbol debut +81d (PB) / +189d (MM) + re-equilibration).
ATTRIBUTION_DAYS = 365

#: Family B contrast window (draws) on each side of an event.
FB_WINDOW = 300


@dataclass(frozen=True)
class MatrixChangeEvent:
    """A documented matrix change (ground truth): label + first draw under new rules."""

    label: str
    rule_date: date


@dataclass(frozen=True)
class GameConfig:
    """One audited game: seed CSV (generic format) + pool max + documented events."""

    name: str
    seed_filename: str
    pool_size: int  # historical maximum (matrix changes stay inside the stream)
    events: tuple[MatrixChangeEvent, ...]


GAME_CONFIGS: dict[str, GameConfig] = {
    "powerball": GameConfig(
        name="Powerball (5/69 white)",
        seed_filename="powerball_history.csv",
        pool_size=69,
        events=(
            MatrixChangeEvent("white 59->69 (2015 matrix change)", date(2015, 10, 7)),
        ),
    ),
    "megamillions": GameConfig(
        name="Mega Millions (5/75 white)",
        seed_filename="megamillions_history.csv",
        pool_size=75,
        events=(
            MatrixChangeEvent("white 52->56 (2005 matrix change)", date(2005, 6, 24)),
            MatrixChangeEvent("white 56->75 (2013 matrix change)", date(2013, 10, 22)),
            MatrixChangeEvent("white 75->70 shrink (2017 matrix change)", date(2017, 10, 31)),
        ),
    ),
}


def coverage_warmup(pool_size: int, k: int) -> int:
    """Coupon-collector warm-up: expected draws to see every symbol, ceil((N/k)·H_N)."""
    return math.ceil((pool_size / k) * (math.log(pool_size) + 0.5772))


@dataclass(frozen=True)
class EventAudit:
    """Ground-truth comparison for one documented matrix change."""

    event: MatrixChangeEvent
    onset_date: date | None       # earliest attributed BOCPD onset (None = BOCPD miss)
    onset_delta_days: int | None  # onset - rule_date
    fb_appeared: tuple[int, ...]  # symbols under-represented BEFORE but not AFTER
    fb_vanished: tuple[int, ...]  # symbols under-represented AFTER but not BEFORE
    fb_confirms: bool             # the contrast is non-empty (Family B sees the change)


@dataclass(frozen=True)
class LotteryAuditRow:
    """One game's audit: blind BOCPD onsets vs ground truth + Family B contrasts."""

    game: str
    n_draws: int
    pool_size: int
    warmup: int
    bocpd_max_prob: float
    bocpd_threshold: float
    onsets: tuple[date, ...]          # ALL above-threshold segment onsets (blind)
    events: tuple[EventAudit, ...]
    spurious_onsets: tuple[date, ...]  # onsets outside every attribution window

    @property
    def n_events_detected(self) -> int:
        """Events caught by >=1 pillar (BOCPD onset OR Family B contrast)."""
        return sum(1 for e in self.events if e.onset_date is not None or e.fb_confirms)


def _segment_onsets(
    cp_probs: npt.NDArray[np.float64], threshold: float, warmup: int, dates: list[date]
) -> list[date]:
    """First-crossing dates of above-threshold segments (ignoring the warm-up)."""
    onsets: list[date] = []
    above = False
    for t in range(warmup, len(cp_probs)):
        if cp_probs[t] > threshold and not above:
            onsets.append(dates[t])
            above = True
        elif cp_probs[t] <= threshold:
            above = False
    return onsets


def _under_represented(
    draws: list[DrawRecord], pool_size: int, alpha: float
) -> set[int]:
    """Symbols significantly UNDER-represented vs uniform(pool) (two-sided FB + BY)."""
    labels, pvals = family_b_per_number_pvalues(draws)
    fdr = correct_family_b(pvals, labels, alpha=alpha)
    n = len(draws)
    k = len(draws[0].main_numbers)
    expected = n * k / pool_size
    counts = np.zeros(pool_size, dtype=np.int64)
    for d in draws:
        for v in set(d.main_numbers):
            counts[v - 1] += 1
    return {
        i + 1
        for i, rejected in enumerate(fdr.reject)
        if rejected and counts[i] < expected
    }


def run_lottery_audit(
    game: str,
    *,
    seed_csv: Path | None = None,
    alpha: float = 0.05,
    fb_window: int = FB_WINDOW,
) -> LotteryAuditRow:
    """Full blind audit of one game vs its documented matrix changes.

    BOCPD runs on the FULL stream with the coverage warm-up and the pool-calibrated
    threshold; onsets are extracted blind and only then compared with the documented
    events. Family B contrasts use `fb_window` draws on each side of each event.
    """
    cfg = GAME_CONFIGS[game]
    path = seed_csv if seed_csv is not None else _ROOT / "data" / "seed" / cfg.seed_filename
    draws = load_generic_seed_csv(path, pool_size=cfg.pool_size)
    draws.sort(key=lambda d: d.draw_date)

    k = len(draws[0].main_numbers)
    warmup = coverage_warmup(cfg.pool_size, k)
    cp_probs, _rl, warmup, threshold = compute_bocpd_curve(
        draws, field="main", hazard=0.005, warmup=warmup
    )
    dates = [d.draw_date for d in draws]
    onsets = _segment_onsets(cp_probs, threshold, warmup, dates)

    attributed: set[date] = set()
    event_audits: list[EventAudit] = []
    for ev in cfg.events:
        window_end = ev.rule_date + timedelta(days=ATTRIBUTION_DAYS)
        mine = [o for o in onsets if ev.rule_date <= o <= window_end]
        onset = min(mine) if mine else None
        attributed.update(mine)

        idx = next(i for i, d in enumerate(dates) if d >= ev.rule_date)
        pre = draws[max(0, idx - fb_window) : idx]
        post = draws[idx : idx + fb_window]
        pre_under = _under_represented(pre, cfg.pool_size, alpha)
        post_under = _under_represented(post, cfg.pool_size, alpha)
        appeared = tuple(sorted(pre_under - post_under))
        vanished = tuple(sorted(post_under - pre_under))

        event_audits.append(
            EventAudit(
                event=ev,
                onset_date=onset,
                onset_delta_days=(onset - ev.rule_date).days if onset else None,
                fb_appeared=appeared,
                fb_vanished=vanished,
                fb_confirms=bool(appeared or vanished),
            )
        )

    spurious = tuple(o for o in onsets if o not in attributed)
    return LotteryAuditRow(
        game=cfg.name,
        n_draws=len(draws),
        pool_size=cfg.pool_size,
        warmup=warmup,
        bocpd_max_prob=float(cp_probs[warmup:].max()),
        bocpd_threshold=threshold,
        onsets=tuple(onsets),
        events=tuple(event_audits),
        spurious_onsets=spurious,
    )
