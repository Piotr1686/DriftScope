"""Fetch public randomness beacon digests into the seed CSV cache — CLI (Path B2).

Populates the committed caches that back `BeaconStream`:

    data/seed/drand_beacon.csv   drand League of Entropy, 32 B/round, 30 s cadence
    data/seed/nist_beacon.csv    NIST Randomness Beacon 2.0, 64 B/pulse, 60 s cadence

The cached CSV — not a seed — is what makes these streams reproducible (DoD-6): a beacon has
no state we can re-derive, so the frozen digest file IS the artifact. Re-running this script
with a different `--end-*` produces a DIFFERENT stream; that is intended, and the committed
file is the one the benchmark and report refer to.

Sizing: the benchmark maps 7 u64 (56 B) per draw, so parity with the synthetic sources at
n_draws=1500 needs 84 000 B = 2625 drand rounds or 1313 NIST pulses. `--n-draws` computes
this for you and adds headroom.

Run:
    python scripts/fetch_beacons.py both --n-draws 1500
    python scripts/fetch_beacons.py drand --n-draws 1500 --out data/seed/
    python scripts/fetch_beacons.py nist --end-index 1868000 --n-draws 1500
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from driftscope.ingestion.beacon_streams import (
    BeaconPulse,
    bytes_needed_for_draws,
    fetch_drand_rounds,
    fetch_nist_pulses,
    load_beacon_csv,
    write_beacon_csv,
)

#: digest width per source, in bytes
_DRAND_WIDTH = 32
_NIST_WIDTH = 64

#: fetch a little more than the arithmetic minimum — rejection sampling in `randbelow` can in
#: principle consume an extra u64, and a stream that dies mid-benchmark is worse than 2% waste
_HEADROOM = 1.02


def _n_units(n_draws: int, width: int) -> int:
    return int(math.ceil(bytes_needed_for_draws(n_draws) * _HEADROOM / width))


def _report(path: Path, pulses: list[BeaconPulse], label: str) -> None:
    stream = load_beacon_csv(path, label)
    print(
        f"  {label}: {len(pulses)} values "
        f"(index {pulses[0].index}..{pulses[-1].index}, "
        f"{pulses[0].timestamp} .. {pulses[-1].timestamp})\n"
        f"     -> {path}  [{stream.capacity_draws} draws of capacity]"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", choices=("drand", "nist", "both"))
    ap.add_argument("--n-draws", type=int, default=1500,
                    help="draw-count parity target with the synthetic sources (default: 1500)")
    ap.add_argument("--out", type=Path, default=Path("data/seed"),
                    help="output directory (default: data/seed)")
    ap.add_argument("--end-round", type=int, default=None,
                    help="drand: last round to fetch (default: latest)")
    ap.add_argument("--end-index", type=int, default=None,
                    help="NIST: last pulse index to fetch (default: last)")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    want = {"drand", "nist"} if args.source == "both" else {args.source}

    if "drand" in want:
        n = _n_units(args.n_draws, _DRAND_WIDTH)
        print(f"drand: fetching {n} rounds (~{n * _DRAND_WIDTH} B)...")
        pulses = fetch_drand_rounds(n, end_round=args.end_round)
        path = args.out / "drand_beacon.csv"
        write_beacon_csv(path, pulses)
        _report(path, pulses, "drand")

    if "nist" in want:
        n = _n_units(args.n_draws, _NIST_WIDTH)
        print(f"NIST: fetching {n} pulses (~{n * _NIST_WIDTH} B)...")
        pulses = fetch_nist_pulses(n, end_index=args.end_index)
        path = args.out / "nist_beacon.csv"
        write_beacon_csv(path, pulses)
        _report(path, pulses, "NIST")

    return 0


if __name__ == "__main__":
    sys.exit(main())
