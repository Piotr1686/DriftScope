"""Convert the raw Multi Multi CSV (wynikilotto.net.pl) → DriftScope seed format.

Source (Tier-1): https://www.wynikilotto.net.pl/download/multi_multi.csv
Source format (no header):
    draw_no, DD.MM.YYYY, HH:MM, n1..n20, plus
    - n1..n20: 20 main numbers 1-80 (Multi Multi 20-of-80)
    - plus:    the extra "Multi Plus" number (IGNORED — negative control = 20 main numbers)
    - HH:MM:   draw time (2 draws/day; IGNORED — ordering = file order)

Target format (with header, ISO 8601):
    draw_date,n1,n2,...,n20

Usage:
    python scripts/convert_mm_seed.py data/seed/_mm_raw.csv data/seed/multimulti_history.csv
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

N_MAIN = 20  # Multi Multi main numbers (20 of 80)


def convert(src: Path, dst: Path) -> int:
    """Convert the raw MM CSV → seed format. Returns the number of draws."""
    rows: list[list[str]] = []
    with src.open("r", encoding="utf-8", newline="") as f:
        for raw in csv.reader(f):
            if not raw or len(raw) < 3 + N_MAIN:
                continue
            iso = datetime.strptime(raw[1].strip(), "%d.%m.%Y").date().isoformat()
            nums = [f"{int(x):d}" for x in raw[3 : 3 + N_MAIN]]
            if len(nums) != N_MAIN:
                raise ValueError(f"draw {raw[0]}: expected {N_MAIN} numbers, got {len(nums)}")
            for v in (int(x) for x in nums):
                if not 1 <= v <= 80:
                    raise ValueError(f"draw {raw[0]}: number {v} out of 1-80")
            rows.append([iso, *nums])

    header = ["draw_date", *[f"n{i + 1}" for i in range(N_MAIN)]]
    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    src_path = Path(sys.argv[1])
    dst_path = Path(sys.argv[2])
    n = convert(src_path, dst_path)
    print(f"OK: {n} draws -> {dst_path}")
