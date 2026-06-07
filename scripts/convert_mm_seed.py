"""Konwersja surowego CSV Multi Multi (wynikilotto.net.pl) → seed format DriftScope.

Zrodlo (Tier-1): https://www.wynikilotto.net.pl/download/multi_multi.csv
Format zrodlowy (bez naglowka):
    draw_no, DD.MM.YYYY, HH:MM, n1..n20, plus
    - n1..n20: 20 liczb glownych 1-80 (Multi Multi 20-z-80)
    - plus:    liczba dodatkowa "Multi Plus" (IGNOROWANA — negative control = 20 glownych)
    - HH:MM:   godzina losowania (2 losowania/dzien; IGNOROWANA — kolejnosc = porzadek pliku)

Format docelowy (z naglowkiem, ISO 8601):
    draw_date,n1,n2,...,n20

Uruchomienie:
    python scripts/convert_mm_seed.py data/seed/_mm_raw.csv data/seed/multimulti_history.csv
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

N_MAIN = 20  # liczby glowne Multi Multi (20 z 80)


def convert(src: Path, dst: Path) -> int:
    """Konwertuje surowy CSV MM → seed format. Zwraca liczbe losowan."""
    rows: list[list[str]] = []
    with src.open("r", encoding="utf-8", newline="") as f:
        for raw in csv.reader(f):
            if not raw or len(raw) < 3 + N_MAIN:
                continue
            iso = datetime.strptime(raw[1].strip(), "%d.%m.%Y").date().isoformat()
            nums = [f"{int(x):d}" for x in raw[3 : 3 + N_MAIN]]
            if len(nums) != N_MAIN:
                raise ValueError(f"losowanie {raw[0]}: oczekiwano {N_MAIN} liczb, mam {len(nums)}")
            for v in (int(x) for x in nums):
                if not 1 <= v <= 80:
                    raise ValueError(f"losowanie {raw[0]}: liczba {v} poza 1-80")
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
    print(f"OK: {n} losowan -> {dst_path}")
