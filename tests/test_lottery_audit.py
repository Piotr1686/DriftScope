"""World Lottery Audit tests (reporting/lottery_audit.py).

Fast units for onset extraction / warm-up formula / config sanity, plus a real-data
money test per game (skipped when the seed CSVs are absent). The real-data expectations
encode the replication contract: every documented matrix change is caught by >=1 pillar
and no spurious onsets appear outside the attribution windows.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from driftscope.reporting.lottery_audit import (
    GAME_CONFIGS,
    _segment_onsets,
    coverage_warmup,
    run_lottery_audit,
)

_SEED_DIR = Path(__file__).parent.parent / "data" / "seed"


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

def test_coverage_warmup_values() -> None:
    """Coupon-collector warm-up: matches the calibrated (pool, k) combos."""
    assert coverage_warmup(69, 5) == 67
    assert coverage_warmup(75, 5) == 74
    assert coverage_warmup(59, 6) == 46
    # Sanity: k=20 covers the pool fast -> much shorter warm-up than k=5.
    assert coverage_warmup(80, 20) < coverage_warmup(80, 5)


def test_segment_onsets_first_crossings_only() -> None:
    """One onset per above-threshold segment; warm-up region ignored."""
    d0 = date(2020, 1, 1)
    dates = [d0 + timedelta(days=i) for i in range(10)]
    #        warmup--v  seg1        seg2 (single point)
    probs = np.array([0.9, 0.1, 0.6, 0.7, 0.2, 0.1, 0.8, 0.3, 0.1, 0.1])
    onsets = _segment_onsets(probs, threshold=0.5, warmup=1, dates=dates)
    assert onsets == [dates[2], dates[6]]  # index 0 is inside warm-up


def test_game_configs_sane() -> None:
    """Events are chronological and pools match the converter maxima."""
    assert GAME_CONFIGS["powerball"].pool_size == 69
    assert GAME_CONFIGS["megamillions"].pool_size == 75
    assert GAME_CONFIGS["uk_lotto"].pool_size == 59
    for cfg in GAME_CONFIGS.values():
        rule_dates = [e.rule_date for e in cfg.events]
        assert rule_dates == sorted(rule_dates)


# ---------------------------------------------------------------------------
# Real-data money tests (replication contract)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not (_SEED_DIR / "powerball_history.csv").exists(), reason="Powerball seed unavailable"
)
def test_powerball_replication_contract() -> None:
    """PB 2015 matrix change: Family B contrast recovers {60..69}; no spurious onsets."""
    row = run_lottery_audit("powerball")
    assert row.n_draws >= 1968
    assert row.spurious_onsets == ()
    assert row.n_events_detected == 1
    ev = row.events[0]
    assert ev.fb_appeared == tuple(range(60, 70))
    assert ev.fb_vanished == ()


@pytest.mark.skipif(
    not (_SEED_DIR / "megamillions_history.csv").exists(),
    reason="Mega Millions seed unavailable",
)
def test_megamillions_replication_contract() -> None:
    """MM: 3/3 events detected; 2013 BOCPD onset day-zero; shrink recovered by Family B."""
    row = run_lottery_audit("megamillions")
    assert row.n_events_detected == 3
    assert row.spurious_onsets == ()

    by_label = {ea.event.label: ea for ea in row.events}
    ev2013 = by_label["white 56->75 (2013 matrix change)"]
    assert ev2013.onset_date == date(2013, 10, 22)  # blind, day-zero
    assert ev2013.onset_delta_days == 0
    assert ev2013.fb_appeared == tuple(range(57, 76))

    ev2017 = by_label["white 75->70 shrink (2017 matrix change)"]
    assert ev2017.onset_date is None  # BOCPD blind to symbol retirement (documented)
    assert ev2017.fb_vanished == (71, 72, 73, 74, 75)

    ev2005 = by_label["white 52->56 (2005 matrix change)"]
    assert ev2005.fb_appeared == (53, 54, 55, 56)


@pytest.mark.skipif(
    not (_SEED_DIR / "uk_lotto_history.csv").exists(), reason="UK Lotto seed unavailable"
)
def test_uk_lotto_replication_contract() -> None:
    """UK Lotto 2015 expansion: BOCPD onset day-zero AND Family B recovers {50..59}.

    The structural twin of the Powerball 2015 event (three days apart), but caught by BOTH
    pillars — the strongest replication in the suite. No spurious onsets anywhere in a
    3200-draw stream spanning 1994->present.
    """
    row = run_lottery_audit("uk_lotto")
    assert row.pool_size == 59
    assert row.warmup == 46
    assert row.n_draws >= 3201
    assert row.spurious_onsets == ()
    assert row.n_events_detected == 1

    ev = row.events[0]
    assert ev.onset_date == date(2015, 10, 10)  # blind, day-zero
    assert ev.onset_delta_days == 0
    assert ev.fb_appeared == tuple(range(50, 60))
    assert ev.fb_vanished == ()


@pytest.mark.skipif(
    not (_SEED_DIR / "uk_lotto_history.csv").exists(), reason="UK Lotto seed unavailable"
)
def test_uk_lotto_seed_integrity() -> None:
    """Seed invariants: the matrix change materialises exactly at the documented boundary.

    Also pins the two-draws-per-date format change (from 2026-06-10): duplicate dates are
    EXPECTED in this stream and must survive conversion (see scripts/convert_uk_seed.py).
    """
    from driftscope.ingestion.lotto_scraper import load_generic_seed_csv

    draws = load_generic_seed_csv(_SEED_DIR / "uk_lotto_history.csv", pool_size=59)
    assert all(len(d.main_numbers) == 6 for d in draws)

    boundary = date(2015, 10, 10)
    pre = [v for d in draws if d.draw_date < boundary for v in d.main_numbers]
    post = [v for d in draws if d.draw_date >= boundary for v in d.main_numbers]
    assert max(pre) == 49  # old matrix never exceeds 49
    assert max(post) == 59  # new matrix reaches 59

    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)
    assert len(dates) - len(set(dates)) == 13  # two draws/date since 2026-06-10
