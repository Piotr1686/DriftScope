"""Cryptographic PRNG benchmark side-by-side — CLI (wow Opcja α, reusability showcase).

Cienki wrapper nad `driftscope.reporting.prng_benchmark.run_benchmark`: aplikuje ten sam
battery detektorow co audyt EuroJackpot na strumienie z GROUND-TRUTH labelem i drukuje
macierz "ktory test wykrywa jaki defekt per RNG":

    MT19937      (good, non-crypto)     -> oczekiwany CLEAR
    Xorshift64   (good, non-crypto)     -> oczekiwany CLEAR
    ChaCha20     (crypto)               -> oczekiwany CLEAR  (specificity)
    AES-CTR-DRBG (crypto)               -> oczekiwany CLEAR  (specificity)
    MT19937+bias (defekt marginalny)    -> oczekiwany FLAG   (sensitivity)
    MT19937+period (period-truncation)  -> oczekiwany FLAG   (sensitivity)
    EuroJackpot  (real, main 1-50)      -> oczekiwany CLEAR  (honest null audytu)

Uruchomienie:
    python scripts/prng_benchmark.py
    python scripts/prng_benchmark.py --n-draws 1500 --n-perm 499 --out artifacts/prng_benchmark.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from driftscope.reporting.prng_benchmark import BenchmarkRow, run_benchmark


def _to_table(rows: list[BenchmarkRow]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "source": r.source,
                "class": r.klass,
                "n": r.n,
                "familyB_reject": f"{r.family_b_reject}/{r.family_b_size}",
                "familyB_min_q": round(r.family_b_min_q, 4),
                "mmd_reject": r.mmd_reject,
                "mmd_p": round(r.mmd_p, 4),
                "cooc_reject": r.cooc_reject,
                "cooc_p": round(r.cooc_p, 4),
                "it_reject": r.it_reject,
                "it_p": round(r.it_p, 4),
                "verdict": r.verdict,
            }
            for r in rows
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DriftScope PRNG benchmark side-by-side")
    parser.add_argument("--n-draws", type=int, default=1500, help="losowan per syntetyczny RNG")
    parser.add_argument("--n-perm", type=int, default=499, help="permutacje MMD/co-occurrence/IT")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--favor-number", type=int, default=7, help="numer defektu (nadreprezentowany)"
    )
    parser.add_argument("--favor-prob", type=float, default=0.15, help="prawd. defektu")
    parser.add_argument(
        "--period", type=int, default=50, help="dlugosc cyklu defektu period-truncation"
    )
    parser.add_argument("--out", type=Path, default=None, help="opcjonalny zapis CSV")
    args = parser.parse_args()

    rows = run_benchmark(
        n_draws=args.n_draws,
        n_perm=args.n_perm,
        alpha=args.alpha,
        seed=args.seed,
        favor=(args.favor_number, args.favor_prob),
        period=args.period,
    )
    for r in rows:
        print(f"  {r.source:18s} [{r.klass:6s}] -> {r.verdict}")

    table = _to_table(rows)
    print("\n=== DriftScope PRNG benchmark - defect detection matrix ===")
    # ASCII tables: konsola Win (cp1250) nie zniesie domyslnych ramek unicode polars.
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=40, set_ascii_tables=True):
        print(table)

    defects_flagged = all(r.flagged for r in rows if r.klass == "DEFECT")
    good_clear = all(not r.flagged for r in rows if r.klass != "DEFECT")
    print(
        f"\nSensitivity (defekt -> FLAG): {'OK' if defects_flagged else 'MISS'} | "
        f"Specificity (good/crypto/real -> clear): {'OK' if good_clear else 'MISS'}"
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        table.write_csv(args.out)
        print(f"\nZapisano: {args.out}")


if __name__ == "__main__":
    main()
