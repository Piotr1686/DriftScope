"""RANDAO withholding audit tests (beacon_chain.py + randao_audit.py, Path B3).

Two things must hold before a real-data verdict means anything:
  - SENSITIVITY: a planted withholding signature at the epoch tail is detected,
  - SPECIFICITY: uniformly scattered misses are NOT, and neither is the benign position-0
    epoch-transition confound, which must not be able to fire the tail test.

Network scanning is not exercised here — tests stay offline. The scan LOADER's consistency
checks are tested instead, since a corrupted scan is what would silently poison a real verdict.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from driftscope.ingestion.beacon_chain import (
    SLOTS_PER_EPOCH,
    MissedSlot,
    RateLimiter,
    ScanMeta,
    SlotScanError,
    _slot_present,
    load_scan,
    scan_slot_range,
    write_scan,
)
from driftscope.reporting.randao_audit import (
    LAST_POSITION,
    audit_randao,
    detectable_fraction,
    power_at,
)

_RNG_SEED = 42


def _meta(n_slots: int, n_missed: int, start: int = 0) -> ScanMeta:
    return ScanMeta(
        start_slot=start,
        end_slot=start + n_slots,
        n_slots=n_slots,
        n_missed=n_missed,
        node="test",
        fetched_at="2026-07-20T00:00:00+00:00",
    )


def _missed_from_positions(positions: list[int], start: int = 0) -> list[MissedSlot]:
    """Builds missed-slot records placing each requested position in its own epoch."""
    out = []
    for i, pos in enumerate(positions):
        slot = start + i * SLOTS_PER_EPOCH + pos
        out.append(
            MissedSlot(
                slot=slot, epoch=slot // SLOTS_PER_EPOCH, position=slot % SLOTS_PER_EPOCH
            )
        )
    return sorted(out, key=lambda m: m.slot)


# ---------------------------------------------------------------------------
# Specificity — honest chain must read clear
# ---------------------------------------------------------------------------

def test_uniform_misses_read_clear() -> None:
    """Misses scattered uniformly over positions 1-31 → no withholding signature."""
    import random

    rng = random.Random(_RNG_SEED)
    positions = [rng.randrange(1, SLOTS_PER_EPOCH) for _ in range(800)]
    missed = _missed_from_positions(positions)
    res = audit_randao(missed, _meta(n_slots=800 * SLOTS_PER_EPOCH, n_missed=len(missed)))
    assert not res.reject_h0
    assert res.verdict == "clear"


def test_position_zero_confound_cannot_fire_tail_test() -> None:
    """A massive position-0 excess must NOT trip the tail test.

    This is the confound-isolation guarantee: benign epoch-transition misses pile up at the
    FRONT of the epoch, and the null reference deliberately excludes position 0, so no amount
    of them can be mistaken for withholding at the back.
    """
    import random

    rng = random.Random(_RNG_SEED)
    positions = [rng.randrange(1, SLOTS_PER_EPOCH) for _ in range(500)] + [0] * 2000
    missed = _missed_from_positions(positions)
    res = audit_randao(missed, _meta(n_slots=2500 * SLOTS_PER_EPOCH, n_missed=len(missed)))
    assert res.confound_count == 2000
    assert res.confound_ratio > 10.0          # confound clearly visible...
    assert not res.reject_h0                  # ...but the verdict is unaffected
    assert "pos_0" in res.family_b_reject     # ...and the omnibus surfaces it rather than hiding it


# ---------------------------------------------------------------------------
# Sensitivity — planted withholding must be caught
# ---------------------------------------------------------------------------

def test_planted_tail_withholding_detected() -> None:
    """Excess misses planted at the last slot → FLAG (positive control)."""
    import random

    rng = random.Random(_RNG_SEED)
    positions = [rng.randrange(1, SLOTS_PER_EPOCH) for _ in range(500)] + [LAST_POSITION] * 60
    missed = _missed_from_positions(positions)
    res = audit_randao(missed, _meta(n_slots=560 * SLOTS_PER_EPOCH, n_missed=len(missed)))
    assert res.reject_h0
    assert res.verdict == "FLAG"
    assert res.last_count > res.last_expected


def test_detection_threshold_matches_power_claim() -> None:
    """An attack at the claimed detectable fraction is caught far more often than not.

    Guards the headline number: the reported bound must not overstate what the test can do.
    """
    import random

    n_ref = 800
    phi = detectable_fraction(n_ref)
    rng = random.Random(_RNG_SEED)

    hits = 0
    trials = 40
    for _ in range(trials):
        n_attack = int(round(phi * n_ref))
        positions = [rng.randrange(1, SLOTS_PER_EPOCH) for _ in range(n_ref - n_attack)]
        positions += [LAST_POSITION] * n_attack
        missed = _missed_from_positions(positions)
        res = audit_randao(missed, _meta(n_slots=n_ref * SLOTS_PER_EPOCH, n_missed=len(missed)))
        hits += int(res.reject_h0)
    assert hits / trials >= 0.6  # nominal 0.80; loose bound to stay robust at 40 trials


def test_power_is_monotone() -> None:
    """More data and stronger attacks both increase power; the bound tightens with n."""
    assert power_at(800, 0.05) > power_at(200, 0.05)
    assert power_at(800, 0.10) > power_at(800, 0.02)
    assert detectable_fraction(2000) < detectable_fraction(500)


# ---------------------------------------------------------------------------
# Scan persistence — a corrupted scan must not silently poison a verdict
# ---------------------------------------------------------------------------

def test_scan_roundtrip(tmp_path: Path) -> None:
    missed = _missed_from_positions([1, 5, 31, 0])
    meta = _meta(n_slots=4 * SLOTS_PER_EPOCH, n_missed=4)
    csv_path, meta_path = tmp_path / "m.csv", tmp_path / "m.json"
    write_scan(csv_path, meta_path, missed, meta)
    loaded, loaded_meta = load_scan(csv_path, meta_path)
    assert loaded == missed
    assert loaded_meta == meta


def test_scan_count_mismatch_rejected(tmp_path: Path) -> None:
    """Row count disagreeing with the metadata denominator → error, not a silent wrong rate."""
    missed = _missed_from_positions([1, 5])
    csv_path, meta_path = tmp_path / "m.csv", tmp_path / "m.json"
    write_scan(csv_path, meta_path, missed, _meta(n_slots=64, n_missed=2))
    meta_path.write_text(json.dumps({**json.loads(meta_path.read_text()), "n_missed": 99}))
    with pytest.raises(ValueError):
        load_scan(csv_path, meta_path)


def test_scan_slot_outside_range_rejected(tmp_path: Path) -> None:
    """A slot outside the scanned window → error (the denominator would not cover it)."""
    missed = _missed_from_positions([1], start=10_000)
    csv_path, meta_path = tmp_path / "m.csv", tmp_path / "m.json"
    write_scan(csv_path, meta_path, missed, _meta(n_slots=64, n_missed=1, start=0))
    with pytest.raises(ValueError):
        load_scan(csv_path, meta_path)


# ---------------------------------------------------------------------------
# Fetch robustness — a throttled server must never manufacture a miss
# ---------------------------------------------------------------------------

def _mock_client(handler: object) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))  # type: ignore[arg-type]


def test_rate_limit_never_counts_as_missed_slot() -> None:
    """A server returning only 429 → SlotScanError, never a False (= "missed") verdict.

    This is the single most dangerous failure mode in the whole audit: throttling correlates
    with nothing in particular, but if 429s were recorded as misses they would enter the
    position histogram as fabricated evidence.
    """
    limiter = RateLimiter(1000.0)

    async def run() -> None:
        async with _mock_client(lambda req: httpx.Response(429)) as client:
            with pytest.raises(SlotScanError):
                await _slot_present(client, "http://node", 42, limiter, attempts=2)

    asyncio.run(run())
    assert limiter.rate < 1000.0  # throttling was observed and the rate was cut


def test_transport_error_never_counts_as_missed_slot() -> None:
    """A transport failure is "unknown", not "missed"."""
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    async def run() -> None:
        async with _mock_client(boom) as client:
            with pytest.raises(SlotScanError):
                await _slot_present(client, "http://node", 42, RateLimiter(1000.0), attempts=2)

    asyncio.run(run())


def test_404_is_authoritative_miss_and_200_is_present() -> None:
    """The two authoritative answers are honoured exactly."""
    async def run() -> None:
        limiter = RateLimiter(1000.0)
        async with _mock_client(lambda req: httpx.Response(404)) as client:
            assert await _slot_present(client, "http://node", 1, limiter) is False
        payload = {"data": {"header": {"message": {"slot": "1"}}}}
        async with _mock_client(lambda req: httpx.Response(200, json=payload)) as client:
            assert await _slot_present(client, "http://node", 1, limiter) is True
        # a 200 with an empty payload also means "no block here"
        async with _mock_client(lambda req: httpx.Response(200, json={"data": None})) as client:
            assert await _slot_present(client, "http://node", 1, limiter) is False

    asyncio.run(run())


def test_rate_limiter_backs_off_with_floor() -> None:
    """Throttling halves the rate but never drives it to zero (which would stall the scan)."""
    limiter = RateLimiter(64.0)
    for _ in range(20):
        limiter.throttled()
    assert limiter.rate == RateLimiter.FLOOR


def test_rate_limiter_recovers_after_backoff() -> None:
    """Sustained success creeps the rate back up — AIMD, not pure backoff.

    Without this a short throttling burst would pin a multi-hour scan at the floor forever;
    that regression cost a real scan run before it was fixed.
    """
    limiter = RateLimiter(40.0)
    limiter.throttled()
    limiter.throttled()
    depressed = limiter.rate
    assert depressed < 40.0

    for _ in range(RateLimiter.RECOVERY_INTERVAL * 5):
        limiter.succeeded()
    assert limiter.rate > depressed
    assert limiter.rate <= limiter.target  # never overshoots the configured target


def test_rate_limiter_recovery_needs_a_streak() -> None:
    """A single success does not undo a backoff (otherwise it would oscillate)."""
    limiter = RateLimiter(40.0)
    limiter.throttled()
    after = limiter.rate
    limiter.succeeded()
    assert limiter.rate == after


def test_resume_range_mismatch_rejected(tmp_path: Path) -> None:
    """Resuming against a different range → error, not a silently spliced record."""
    missed = _missed_from_positions([1])
    meta = ScanMeta(start_slot=0, end_slot=64, n_slots=32, n_missed=1,
                    node="test", fetched_at="t", cursor=32)

    async def run() -> None:
        with pytest.raises(ValueError):
            await scan_slot_range(1000, 2000, resume_from=(missed, meta))

    asyncio.run(run())


def test_scan_meta_completeness() -> None:
    """`complete` distinguishes a finished scan from a checkpointed partial one."""
    partial = ScanMeta(0, 64, 32, 1, "test", "t", cursor=32)
    done = ScanMeta(0, 64, 64, 1, "test", "t", cursor=64)
    assert not partial.complete
    assert done.complete
