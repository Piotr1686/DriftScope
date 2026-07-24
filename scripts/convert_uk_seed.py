"""Convert the raw UK Lotto history CSV → DriftScope seed format.

Source (mirror): https://www.lottometrics.app/api/export/draws/uknationallottery/all/csv
Source format (header row present):
    date, main_numbers ("n1 n2 n3 n4 n5 n6"), extra_numbers (bonus ball), draw_session

Target format (ISO 8601, generic seed CSV, chronological):
    uk_lotto_history.csv:  draw_date,n1..n6   (main balls, sorted ascending)

PROVENANCE — the official national-lottery.co.uk export is 403-walled for non-browser
clients and caps at ~180 days, so the full 1994→present history comes from the mirror
above. It was cross-validated against a 64-record official sample
(data/seed/uk_lotto_official_sample.csv, 2026-01-28..2026-07-22): MAIN NUMBERS match on
64/64 records, including the draw_session split. Reproduce with
scripts/validate_uk_mirror.py.

KNOWN MIRROR DEFECT (bounded, outside this converter's output): on 2026-06-13 the mirror
CROSSES THE BONUS BALLS between session 1 and 2 (official 44/6, mirror 6/44); the main
numbers of both sessions are correct. The bonus ball is therefore NOT emitted here — the
World Lottery Audit design derives specificity from spurious onsets, not from a second
stream (see reporting/lottery_audit.py). Emitting a bonus stream would require patching
that date from the official sample first.

TWO DRAWS PER DATE — from 2026-06-10 the game runs two draws on the same date
(`draw_session` 1 and 2; confirmed in the official sample, NOT a mirror artifact). Both
are genuine draws from the same pool, so BOTH are kept; unlike the NY converter, duplicate
dates are expected here and are NOT an error. Ordering = (date, session).

Matrix change stays in the data: the pool grew 49→59 on 2015-10-10. Load the output with
pool_size = 59 (historical maximum); the audit detects the change blind.

Run:
    python scripts/convert_uk_seed.py data/seed/_uk_raw.csv data/seed/uk_lotto_history.csv
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

N_MAIN = 6
POOL_MAX = 59

#: First draw under the expanded 1-59 matrix (documented ground truth).
MATRIX_CHANGE = date(2015, 10, 10)


def convert(src: Path, dst: Path) -> tuple[int, int, int]:
    """Convert the raw UK CSV → seed format.

    Returns (n_draws, n_resorted, n_duplicate_dates).
    """
    rows: list[tuple[str, int, list[int]]] = []
    n_resorted = 0

    with src.open("r", encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            iso = raw["date"].strip()
            session = int((raw["draw_session"] or "1").strip() or "1")
            nums = [int(x) for x in raw["main_numbers"].split()]

            if nums != sorted(nums):
                n_resorted += 1
                nums = sorted(nums)
            if len(set(nums)) != N_MAIN:
                raise ValueError(f"{iso}: expected {N_MAIN} distinct numbers, got {nums}")
            for v in nums:
                if not 1 <= v <= POOL_MAX:
                    raise ValueError(f"{iso}: number {v} out of 1-{POOL_MAX}")
            rows.append((iso, session, nums))

    # Chronological, session-stable. Duplicate dates are EXPECTED (two draws/date since
    # 2026-06-10) — they are counted and reported, never rejected.
    rows.sort(key=lambda t: (t[0], t[1]))
    dates = [r[0] for r in rows]
    n_duplicate_dates = len(dates) - len(set(dates))

    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", *[f"n{i + 1}" for i in range(N_MAIN)]])
        w.writerows([iso, *nums] for iso, _session, nums in rows)

    return len(rows), n_resorted, n_duplicate_dates


if __name__ == "__main__":
    src_path = Path(sys.argv[1])
    dst_path = Path(sys.argv[2])
    n, resorted, dupes = convert(src_path, dst_path)
    print(f"OK: {n} draws -> {dst_path}")
    print(f"    re-sorted rows: {resorted}; duplicate dates (two draws/date): {dupes}")
