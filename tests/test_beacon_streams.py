"""Public randomness beacon adapter tests (beacon_streams.py, Path B2).

Validates the invariants that differ from the PRNG adapters, because a beacon is NOT a seeded
generator:
  - reproducibility comes from the CACHED CSV, not a seed (DoD-6 substitute),
  - the stream is FINITE and exhaustion is loud (never a silent wrap-around, which would forge
    a period-truncation defect identical to the one we inject as a positive control),
  - the committed caches really do cover the benchmark's parity target.

Network fetchers are NOT exercised here — tests must stay offline and deterministic. The
fetchers are covered by scripts/fetch_beacons.py runs whose OUTPUT (the committed CSV) is what
these tests read.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

import driftscope
from driftscope.ingestion.beacon_streams import (
    BeaconExhaustedError,
    BeaconPulse,
    BeaconStream,
    bytes_needed_for_draws,
    load_beacon_csv,
    write_beacon_csv,
)
from driftscope.ingestion.rng_streams import draws_from_stream

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_SEED_DIR = _ROOT / "data" / "seed"
_CACHES = [("drand", _SEED_DIR / "drand_beacon.csv"), ("NIST", _SEED_DIR / "nist_beacon.csv")]

#: parity target with the synthetic benchmark sources
_BENCHMARK_DRAWS = 1500


def _synthetic_pulses(n: int, width: int = 32) -> list[BeaconPulse]:
    """Deterministic fake pulses — structure only, no statistical claim."""
    return [
        BeaconPulse(index=100 + i, timestamp=f"2026-01-01T00:{i:02d}:00+00:00",
                    value_hex=bytes([(i + j) % 256 for j in range(width)]).hex())
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# BeaconStream contract
# ---------------------------------------------------------------------------

def test_capacity_matches_byte_budget() -> None:
    """capacity_draws follows the documented 7 u64 (56 B) per draw budget."""
    pulses = _synthetic_pulses(56)  # 56 * 32 B = 1792 B = exactly 32 draws
    stream = BeaconStream("fake", [p.value for p in pulses])
    assert bytes_needed_for_draws(32) == 1792
    assert stream.capacity_draws == 32


def test_consumption_decrements_capacity() -> None:
    """Drawing consumes the pool — a beacon has no state to regenerate."""
    stream = BeaconStream("fake", [p.value for p in _synthetic_pulses(56)])
    before = stream.capacity_draws
    draws_from_stream(stream, 10)
    assert stream.capacity_draws == before - 10


def test_exhaustion_raises_not_wraps() -> None:
    """Running out of digest bytes → BeaconExhaustedError, never a silent repeat.

    A wrap-around would reproduce the period-truncation defect that `draws_from_stream(period=)`
    injects deliberately — an artefact of the adapter masquerading as a finding.
    """
    stream = BeaconStream("fake", [p.value for p in _synthetic_pulses(10)])
    with pytest.raises(BeaconExhaustedError):
        draws_from_stream(stream, 1000)


def test_empty_digests_rejected() -> None:
    with pytest.raises(ValueError):
        BeaconStream("fake", [])


def test_draw_format_valid() -> None:
    """Beacon-driven draws satisfy the same DrawRecord contract as the PRNG sources."""
    stream = BeaconStream("fake", [p.value for p in _synthetic_pulses(200)])
    for d in draws_from_stream(stream, 50):
        main, euron = d.main_numbers, d.euronumbers
        assert len(set(main)) == 5 and all(1 <= x <= 50 for x in main) and main == sorted(main)
        assert len(set(euron)) == 2 and all(1 <= x <= 12 for x in euron) and euron == sorted(euron)


# ---------------------------------------------------------------------------
# CSV cache — the reproducibility artifact
# ---------------------------------------------------------------------------

def test_csv_roundtrip_is_deterministic(tmp_path: Path) -> None:
    """write → load → draws is bit-identical across reloads (DoD-6 without a seed)."""
    path = tmp_path / "beacon.csv"
    write_beacon_csv(path, _synthetic_pulses(200))
    first = draws_from_stream(load_beacon_csv(path, "fake"), 40)
    second = draws_from_stream(load_beacon_csv(path, "fake"), 40)
    assert first == second


def test_non_increasing_indices_rejected(tmp_path: Path) -> None:
    """A gap is tolerable, a reorder or duplicate is not — it breaks the sequence claim."""
    path = tmp_path / "bad.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(("index", "timestamp", "value_hex"))
        w.writerow((5, "t", "00" * 32))
        w.writerow((5, "t", "11" * 32))  # duplicate index
    with pytest.raises(ValueError):
        load_beacon_csv(path, "fake")


def test_empty_cache_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("index,timestamp,value_hex\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_beacon_csv(path, "fake")


# ---------------------------------------------------------------------------
# Committed caches
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("label", "path"), _CACHES)
def test_committed_cache_covers_benchmark(label: str, path: Path) -> None:
    """The committed digest caches really do cover the benchmark's 1500-draw parity target."""
    if not path.exists():
        pytest.skip(f"{path.name} not fetched — run scripts/fetch_beacons.py both")
    assert load_beacon_csv(path, label).capacity_draws >= _BENCHMARK_DRAWS


@pytest.mark.parametrize(("label", "path"), _CACHES)
def test_committed_cache_digests_uniform_width(label: str, path: Path) -> None:
    """All digests in a cache share one width — a short row would silently shift every
    subsequent draw, since the stream is a flat concatenation."""
    if not path.exists():
        pytest.skip(f"{path.name} not fetched — run scripts/fetch_beacons.py both")
    with path.open(newline="", encoding="utf-8") as fh:
        widths = {len(row["value_hex"]) for row in csv.DictReader(fh)}
    assert len(widths) == 1
