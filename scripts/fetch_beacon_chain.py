"""Scan Ethereum beacon chain slot occupancy into the seed cache — CLI (Path B3).

Records which slots in a contiguous range carry a canonical block and which are MISSED. The
missed-slot positions within their epochs are the observable behind the RANDAO withholding
audit (see ingestion/beacon_chain.py for why position, not the mix, is the right target).

Sizing (power analysis, base miss rate ~0.5%, alpha = 0.05, one-sided, 80% power):

    epochs   slots     misses   detects an attacker withholding
      1000    32000       161     1 block per  134 epochs
      3000    96000       484     1 block per  259 epochs
      5000   160000       806     1 block per  353 epochs   <- default
     10000   320000      1612     1 block per  496 epochs

Sensitivity scales as sqrt(n): 3x the data buys only ~1.9x the resolution. The scan issues one
request per slot against a free public node, so concurrency defaults to a deliberately modest 6.

The scan ends `--lag` slots behind head so the range is safely finalised — a recent slot can
still be reorged, and a block that is canonical now but orphaned later would enter the record
as present when it should be missed.

Run:
    python scripts/fetch_beacon_chain.py --epochs 5000
    python scripts/fetch_beacon_chain.py --epochs 1000 --concurrency 4 --out data/seed/
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from driftscope.ingestion.beacon_chain import (
    DEFAULT_CONCURRENCY,
    DEFAULT_NODE,
    DEFAULT_RATE,
    SLOTS_PER_EPOCH,
    fetch_head_slot,
    load_scan,
    scan_slot_range,
    write_scan,
)

#: stay this many slots behind head so the scanned range is finalised (~2 epochs)
DEFAULT_LAG = 64


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--epochs", type=int, default=5000, help="epochs to scan (default: 5000)")
    ap.add_argument("--out", type=Path, default=Path("data/seed"))
    ap.add_argument("--node", default=DEFAULT_NODE)
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    ap.add_argument("--rate", type=float, default=DEFAULT_RATE,
                    help=f"sustained requests per second (default: {DEFAULT_RATE})")
    ap.add_argument("--resume", action="store_true",
                    help="continue an interrupted scan from its checkpoint")
    ap.add_argument("--lag", type=int, default=DEFAULT_LAG,
                    help=f"slots to stay behind head (default: {DEFAULT_LAG})")
    ap.add_argument("--end-slot", type=int, default=None,
                    help="explicit last slot (exclusive); default: head - lag")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "randao_missed_slots.csv"
    meta_path = args.out / "randao_scan_meta.json"

    resume_from = None
    if args.resume and csv_path.exists() and meta_path.exists():
        resume_from = load_scan(csv_path, meta_path)
        start, end = resume_from[1].start_slot, resume_from[1].end_slot
        print(f"resuming at slot {resume_from[1].cursor} "
              f"({resume_from[1].n_slots} slots already scanned)")
    else:
        end = args.end_slot if args.end_slot is not None else fetch_head_slot(args.node) - args.lag
        # align to an epoch boundary so every scanned epoch contributes all 32 positions --
        # a partial epoch would over-represent low positions and fake a front-loaded miss profile
        end -= end % SLOTS_PER_EPOCH
        start = end - args.epochs * SLOTS_PER_EPOCH
        print(f"scanning {args.epochs} epochs: slots [{start}, {end}) "
              f"= {args.epochs * SLOTS_PER_EPOCH} requests at {args.rate:.0f} req/s")

    missed, meta = asyncio.run(
        scan_slot_range(
            start, end,
            node=args.node,
            concurrency=args.concurrency,
            rate=args.rate,
            checkpoint=lambda m, mt: write_scan(csv_path, meta_path, m, mt),
            resume_from=resume_from,
        )
    )
    write_scan(csv_path, meta_path, missed, meta)

    rate = meta.n_missed / meta.n_slots if meta.n_slots else 0.0
    print(f"\n  missed {meta.n_missed}/{meta.n_slots} slots (rate {rate:.4%})")
    print(f"  -> {csv_path}\n  -> {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
