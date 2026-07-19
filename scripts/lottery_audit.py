"""CLI for the World Lottery Audit (reporting/lottery_audit.py).

Runs the blind audit for each configured game (Powerball, Mega Millions) and prints
the ground-truth replication table: documented matrix change vs blind BOCPD onset
(delta in days) vs the Family B pre/post contrast (recovered matrix delta).

Run:
    python scripts/lottery_audit.py
"""
from __future__ import annotations

from driftscope.reporting.lottery_audit import GAME_CONFIGS, run_lottery_audit


def _fmt_symbols(symbols: tuple[int, ...]) -> str:
    if not symbols:
        return "-"
    if len(symbols) > 6:
        return f"{{{symbols[0]}..{symbols[-1]}}} ({len(symbols)})"
    return "{" + ",".join(str(s) for s in symbols) + "}"


def main() -> None:
    for game in GAME_CONFIGS:
        row = run_lottery_audit(game)
        print(f"== {row.game}: n={row.n_draws}, pool={row.pool_size}, "
              f"warmup={row.warmup}, threshold={row.bocpd_threshold}")
        print(f"   BOCPD max(cp_prob) = {row.bocpd_max_prob:.3f}; "
              f"onsets above threshold: {[str(o) for o in row.onsets]}")
        for ea in row.events:
            onset = (f"{ea.onset_date} (delta {ea.onset_delta_days:+d} d)"
                     if ea.onset_date else "MISS")
            print(f"   EVENT {ea.event.label:38s} rule={ea.event.rule_date}")
            print(f"         BOCPD onset: {onset}")
            print(f"         Family B contrast: appeared={_fmt_symbols(ea.fb_appeared)} "
                  f"vanished={_fmt_symbols(ea.fb_vanished)} "
                  f"-> {'CONFIRMS' if ea.fb_confirms else 'silent'}")
        print(f"   spurious onsets (outside every attribution window): "
              f"{[str(o) for o in row.spurious_onsets] or 'NONE'}")
        print(f"   events detected (>=1 pillar): {row.n_events_detected}/{len(row.events)}")
        print()


if __name__ == "__main__":
    main()
