"""Convert official data.ny.gov lottery CSVs (Powerball / Mega Millions) to seed format.

Sources (NY Open Data, official government portal, CC0-like open license):
    Powerball:     https://data.ny.gov/api/views/d6yy-54nr/rows.csv  (draws since 2010-02)
    Mega Millions: https://data.ny.gov/api/views/5xaw-6ayf/rows.csv  (draws since 2002-05)

Source formats (header row present):
    Powerball:     Draw Date, Winning Numbers ("w1 w2 w3 w4 w5 pb"), Multiplier, ...
    Mega Millions: Draw Date, Winning Numbers ("w1 w2 w3 w4 w5"), Mega Ball, Multiplier

Target format (ISO 8601, generic seed CSV, chronological):
    <game>_history.csv:       draw_date,n1..n5   (white balls, sorted ascending)
    <game>_bonus_history.csv: draw_date,n1       (bonus ball, 1-of-N stream)

Notes:
  - White balls are re-sorted defensively: the NY feed contains at least one row with
    unsorted whites (Powerball 2018-01-06) — a data-entry artifact, values are correct.
  - Matrix changes (pool growth AND shrink) stay in the data — load the output with
    pool_size = historical maximum; the audit detects the changes blind.

Run:
    python scripts/convert_ny_lottery.py powerball <raw.csv> data/seed/
    python scripts/convert_ny_lottery.py megamillions <raw.csv> data/seed/
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

N_WHITE = 5

# game -> (white-pool historical max, bonus-pool historical max)
POOL_MAX = {
    "powerball": (69, 39),
    "megamillions": (75, 52),
}


def convert(game: str, src: Path, out_dir: Path) -> tuple[int, int]:
    """Converts a raw NY CSV -> main + bonus seed CSVs. Returns (n_draws, n_resorted)."""
    white_max, bonus_max = POOL_MAX[game]
    rows: list[tuple[str, list[int], int]] = []
    n_resorted = 0

    with src.open("r", encoding="utf-8", newline="") as f:
        for raw in csv.DictReader(f):
            iso = datetime.strptime(raw["Draw Date"].strip(), "%m/%d/%Y").date().isoformat()
            nums = [int(x) for x in raw["Winning Numbers"].split()]
            if game == "powerball":
                white, bonus = nums[:N_WHITE], nums[N_WHITE]
            else:
                white, bonus = nums, int(raw["Mega Ball"])

            if white != sorted(white):
                n_resorted += 1
                white = sorted(white)
            if len(set(white)) != N_WHITE:
                raise ValueError(f"{iso}: expected {N_WHITE} distinct whites, got {white}")
            for v in white:
                if not 1 <= v <= white_max:
                    raise ValueError(f"{iso}: white {v} out of 1-{white_max}")
            if not 1 <= bonus <= bonus_max:
                raise ValueError(f"{iso}: bonus {bonus} out of 1-{bonus_max}")
            rows.append((iso, white, bonus))

    rows.sort(key=lambda t: t[0])
    dates = [r[0] for r in rows]
    if len(set(dates)) != len(dates):
        raise ValueError("duplicate draw dates in source")

    main_path = out_dir / f"{game}_history.csv"
    with main_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", *[f"n{i + 1}" for i in range(N_WHITE)]])
        w.writerows([iso, *white] for iso, white, _ in rows)

    bonus_path = out_dir / f"{game}_bonus_history.csv"
    with bonus_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "n1"])
        w.writerows([iso, bonus] for iso, _, bonus in rows)

    return len(rows), n_resorted


if __name__ == "__main__":
    game_arg = sys.argv[1]
    if game_arg not in POOL_MAX:
        raise SystemExit(f"unknown game {game_arg!r}; expected one of {sorted(POOL_MAX)}")
    n, resorted = convert(game_arg, Path(sys.argv[2]), Path(sys.argv[3]))
    print(f"OK: {n} draws -> {game_arg}_history.csv (+bonus); re-sorted rows: {resorted}")
