"""Cross-validate the UK Lotto mirror against the OFFICIAL national-lottery.co.uk sample.

PROVENANCE AUDIT — the full UK Lotto history (1994→present) cannot be fetched from the
official site: it is 403-walled for non-browser clients and its CSV export caps at ~180
days. The stream therefore comes from a mirror (see scripts/convert_uk_seed.py), and this
script is the evidence that the mirror is faithful.

Inputs:
    data/seed/uk_lotto_official_sample.csv  — 64 records straight from the official export
                                              (2026-01-28..2026-07-22, Tier-1)
    data/seed/_uk_raw.csv                   — the raw mirror download (not committed)

Match key = (draw_date, round/draw_session). Compares the 6 main numbers as a SET (order is
irrelevant — the seed format sorts ascending) plus the bonus ball.

Recorded result (2026-07-24): main numbers match on 64/64 records. The ONLY discrepancy is
the bonus ball on 2026-06-13, where the mirror crosses the two sessions (official 44/6 vs
mirror 6/44) — the main numbers of both sessions are correct. The bonus ball is not part of
the seed output, so the audited stream is unaffected.

Run:
    python scripts/validate_uk_mirror.py [official_csv] [mirror_csv]
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import driftscope

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_SEED_DIR = _ROOT / "data" / "seed"

Record = tuple[frozenset[int], int]


def load_official(path: Path) -> dict[tuple[str, str], Record]:
    """Official export: DrawDate (DD-Mon-YYYY), Round, Ball 1..6, Bonus Ball."""
    out: dict[tuple[str, str], Record] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            iso = datetime.strptime(r["DrawDate"].strip(), "%d-%b-%Y").date().isoformat()
            balls = frozenset(int(r[f"Ball {i}"]) for i in range(1, 7))
            out[(iso, r["Round"].strip())] = (balls, int(r["Bonus Ball"]))
    return out


def load_mirror(path: Path) -> dict[tuple[str, str], Record]:
    """Mirror export: date (ISO), main_numbers ("n n n n n n"), extra_numbers, draw_session."""
    out: dict[tuple[str, str], Record] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            session = (r["draw_session"] or "1").strip() or "1"
            balls = frozenset(int(x) for x in r["main_numbers"].split())
            extra = r["extra_numbers"].strip()
            out[(r["date"].strip(), session)] = (balls, int(extra) if extra else -1)
    return out


def main() -> int:
    official_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        _SEED_DIR / "uk_lotto_official_sample.csv"
    )
    mirror_path = Path(sys.argv[2]) if len(sys.argv) > 2 else _SEED_DIR / "_uk_raw.csv"
    if not mirror_path.exists():
        print(f"mirror not found: {mirror_path} (re-download to reproduce)")
        return 2

    off = load_official(official_path)
    mir = load_mirror(mirror_path)

    missing = sorted(k for k in off if k not in mir)
    bad_main = [
        (k, sorted(b), sorted(mir[k][0])) for k, (b, _) in off.items()
        if k in mir and mir[k][0] != b
    ]
    bad_bonus = [
        (k, x, mir[k][1]) for k, (_, x) in off.items() if k in mir and mir[k][1] != x
    ]

    print(f"official records : {len(off)}")
    print(f"mirror records   : {len(mir)}")
    print(f"compared         : {len(off) - len(missing)}/{len(off)}")
    print(f"missing in mirror: {len(missing)} {missing[:5]}")
    print(f"main-number mismatches: {len(bad_main)}")
    for row in bad_main[:5]:
        print(f"    {row}")
    print(f"bonus-ball mismatches : {len(bad_bonus)}")
    for row in bad_bonus[:5]:
        print(f"    {row}")

    # Structural profile of the mirror stream (matrix change + format change).
    dates = sorted(k[0] for k in mir)
    print(f"\nstream: {dates[0]} .. {dates[-1]}  n={len(mir)}")
    print(f"draw_session distribution: {dict(Counter(k[1] for k in mir))}")
    segments = (("pre ", "1900-01-01", "2015-10-09"), ("post", "2015-10-10", "2999-01-01"))
    for label, lo, hi in segments:
        seg = [b for (d, _), (b, _) in mir.items() if lo <= d <= hi]
        if seg:
            allb = set().union(*seg)
            print(f"  {label} 2015-10-10: n={len(seg):4d} ball max={max(allb)}")

    # The seed stream carries ONLY main numbers, so bonus defects do not disqualify it.
    ok = not missing and not bad_main
    print(f"\nVERDICT (main numbers): {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
