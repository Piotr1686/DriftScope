"""Multi Multi audit — CLI (second real-world case study, reusability showcase).

Cienki wrapper nad `driftscope.reporting.multimulti_audit.run_multimulti_audit`: aplikuje
DOKLADNIE ten sam battery negative-control co audyt EuroJackpot na drugiej, niezaleznej grze
(Multi Multi 20-z-80) i drukuje jednowierszowa macierz detekcji:

    BOCPD(main) + Family B (per-number exact binomial) + MMD + co-occurrence + IT

Werdykt = Disagreement Protocol po 3 filarach rdzeniowych (BOCPD/MMD/cooc): FLAG dopiero
przy konwergencji >=2/3; samotny filar (1/3) = clear (oczekiwany false-positive przy
alpha=0.05, NIE finding). IT = suplement, Family B = osobna bramka FDR (w macierzy, poza
werdyktem). Oczekiwany wynik: CLEAR (honest null — framework nie halucynuje sygnalu).

Uruchomienie:
    python scripts/multimulti_audit.py
    python scripts/multimulti_audit.py --window 2000 --out artifacts/multimulti_audit.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from driftscope.reporting.multimulti_audit import MultiMultiAuditRow, run_multimulti_audit


def _to_table(row: MultiMultiAuditRow) -> pl.DataFrame:
    b = row.battery
    return pl.DataFrame(
        [
            {
                "source": row.source,
                "n": row.n,
                "bocpd_reject": row.bocpd_reject,
                "bocpd_max": round(row.bocpd_max_prob, 4),
                "bocpd_thr": round(row.bocpd_threshold, 4),
                "familyB_reject": f"{b.family_b_reject}/{b.family_b_size}",
                "familyB_min_q": round(b.family_b_min_q, 4),
                "mmd_reject": b.mmd_reject,
                "mmd_p": round(b.mmd_p, 4),
                "cooc_reject": b.cooc_reject,
                "cooc_p": round(b.cooc_p, 4),
                "it_reject": b.it_reject,
                "it_p": round(b.it_p, 4),
                "core_fraction": row.core_fraction,
                "verdict": row.verdict,
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DriftScope Multi Multi audit (second real-world case study)"
    )
    parser.add_argument(
        "--window", type=int, default=2000, help="ostatnie losowania MM (BOCPD O(T^2))"
    )
    parser.add_argument("--n-perm", type=int, default=499, help="permutacje MMD/cooc/IT")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--out", type=Path, default=None, help="opcjonalny zapis CSV")
    args = parser.parse_args()

    row = run_multimulti_audit(window=args.window, n_perm=args.n_perm, alpha=args.alpha)

    print(f"  {row.source} [n={row.n}, window={row.window}] -> {row.verdict}")

    table = _to_table(row)
    print("\n=== DriftScope Multi Multi audit - negative control matrix ===")
    # ASCII tables: konsola Win (cp1250) nie zniesie domyslnych ramek unicode polars.
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=40, set_ascii_tables=True):
        print(table)

    b = row.battery
    print(
        f"\nCore Disagreement (BOCPD/MMD/cooc): {row.core_fraction} "
        f"({row.disagreement.label})"
    )
    print(
        f"Supplements (poza werdyktem): Family B {b.family_b_reject}/{b.family_b_size} | "
        f"IT {'reject' if b.it_reject else 'clear'}"
    )
    print(
        f"Verdict: {row.verdict.upper()} "
        f"(FLAG wymaga konwergencji >=2/3 filarow rdzeniowych - Disagreement Protocol)"
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        table.write_csv(args.out)
        print(f"\nZapisano: {args.out}")


if __name__ == "__main__":
    main()
