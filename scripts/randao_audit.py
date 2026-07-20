"""RANDAO withholding audit — CLI (Path B3).

Asks whether Ethereum validators are manipulating the beacon chain's randomness by withholding
blocks. The trace withholding leaves is a MISSED SLOT at the tail of an epoch, so the audit
tests the position-within-epoch distribution of misses — not the RANDAO mix itself, which stays
marginally uniform under the attack (see src/driftscope/ingestion/beacon_streams.py).

Requires a slot scan:
    python scripts/fetch_beacon_chain.py --epochs 5000

Run:
    python scripts/randao_audit.py
    python scripts/randao_audit.py --alpha 0.05 --out artifacts/randao_audit.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from driftscope.ingestion.beacon_chain import SLOTS_PER_EPOCH, load_scan
from driftscope.reporting.randao_audit import (
    CONFOUNDED_POSITION,
    LAST_POSITION,
    TAIL_POSITIONS,
    RandaoAuditResult,
    audit_randao,
)


def _profile_table(res: RandaoAuditResult) -> pl.DataFrame:
    mean = res.last_expected
    return pl.DataFrame(
        {
            "position": list(range(SLOTS_PER_EPOCH)),
            "misses": list(res.counts),
            "vs_expected": [round(c / mean, 2) if mean else 0.0 for c in res.counts],
            "note": [
                "epoch-transition confound (excluded from null)" if i == CONFOUNDED_POSITION
                else "LAST SLOT - primary test" if i == LAST_POSITION
                else "tail set - secondary" if i in TAIL_POSITIONS
                else ""
                for i in range(SLOTS_PER_EPOCH)
            ],
        }
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", type=Path, default=Path("data/seed/randao_missed_slots.csv"))
    ap.add_argument("--meta", type=Path, default=Path("data/seed/randao_scan_meta.json"))
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.scan.exists():
        print(f"missing scan: {args.scan}\nrun: python scripts/fetch_beacon_chain.py --epochs 5000")
        return 1

    missed, meta = load_scan(args.scan, args.meta)
    res = audit_randao(missed, meta, alpha=args.alpha)

    print("\n=== DriftScope - RANDAO withholding audit ===\n")
    print(f"  scanned      {res.n_slots} slots ({res.n_slots // SLOTS_PER_EPOCH} epochs), "
          f"slots [{meta.start_slot}, {meta.end_slot})")
    print(f"  missed       {res.n_missed} ({res.miss_rate:.4%})")
    print(f"  reference    {res.n_reference} misses at positions 1-31 "
          f"(position 0 excluded: {res.confound_count} misses, "
          f"{res.confound_ratio:.1f}x the reference mean)\n")

    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=48, set_ascii_tables=True):
        print(_profile_table(res))

    print(f"\n  PRIMARY   position {LAST_POSITION}: {res.last_count} misses vs "
          f"{res.last_expected:.1f} expected -> p = {res.last_p:.4f}")
    print(f"  secondary tail {TAIL_POSITIONS[0]}-{TAIL_POSITIONS[-1]}: {res.tail_count} vs "
          f"{res.tail_expected:.1f} expected -> p = {res.tail_p:.4f}")
    print(f"  omnibus   Family B rejects: "
          f"{', '.join(res.family_b_reject) if res.family_b_reject else 'none'}")

    print(f"\n  VERDICT: {res.verdict}")
    print(f"  Power: at 80% power this scan would have detected an attacker withholding\n"
          f"         1 block per {res.detectable_period:.0f} epochs "
          f"({res.detectable_attacks:.0f} withholds, {res.detectable_phi:.1%} of all misses).")
    if not res.reject_h0:
        print("  Read as: no withholding signature detected AT OR ABOVE that intensity.\n"
              "           This bounds the attack, it does not certify its absence.")

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        _profile_table(res).write_csv(args.out)
        print(f"\nSaved: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
