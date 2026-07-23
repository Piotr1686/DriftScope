"""Generate README marketing graphics into `docs/assets/` (reproducibly).

Usage:
    python scripts/make_readme_assets.py

Produces:
  * docs/assets/story_bocpd.png      — positive control (euron) annotated with "rule change"
  * docs/assets/story_control.png    — positive vs negative control (side-by-side)
  * docs/assets/story_prng.png       — PRNG heatmap (CLEAR/FLAG) — sensitivity showcase

Captions are fully English (the README front-door is public/EN). BOCPD figures use
`reporting.plots_static`; the PRNG heatmap reads `artifacts/prng_benchmark.csv` with a
fallback to hard-coded values (parity with the README).
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from driftscope.ingestion.lotto_scraper import load_seed_csv  # noqa: E402
from driftscope.methodology.h1_classical import compute_bocpd_curve  # noqa: E402
from driftscope.reporting.plots_static import (  # noqa: E402
    _COLOR_CONTROL,
    _COLOR_CP,
    _COLOR_REAL,
    plot_control_comparison,
)

ASSETS = Path("docs/assets")
ASSETS.mkdir(parents=True, exist_ok=True)


def _story_bocpd(draws: list) -> Path:
    """Annotated BOCPD curve (euron) — story hero: peaks = 2014/2022 rule changes."""
    cp_probs, _rl, warmup, threshold = compute_bocpd_curve(draws, "euron")
    date_to_idx = {str(d.draw_date): i for i, d in enumerate(draws)}
    idx_2014 = date_to_idx.get("2014-11-28")
    idx_2022 = date_to_idx.get("2022-03-29")

    fig, ax = plt.subplots(figsize=(11, 4.6))
    x = list(range(len(cp_probs)))
    ax.plot(x, cp_probs, color=_COLOR_REAL, lw=1.3, label="detector confidence (change-point)")
    if warmup > 0:
        ax.axvspan(0, warmup, color=_COLOR_CONTROL, alpha=0.25, label=f"warm-up (n={warmup})")
    ax.axhline(threshold, color=_COLOR_CP, ls="--", lw=1.0, alpha=0.7,
               label=f"alarm threshold = {threshold:.2f}")

    # "Rule change" annotations with arrows pointing at the peaks.
    annotations = [
        (idx_2014, "1st draw with a '9'\nRULE CHANGE 2014", -60),
        (idx_2022, "1st draw with an '11'\nRULE CHANGE 2022", -60),
    ]
    for idx, text, dy in annotations:
        if idx is None:
            continue
        prob = cp_probs[idx]
        ax.plot(idx, prob, "o", color=_COLOR_CP, ms=9, zorder=6)
        ax.annotate(
            text, xy=(idx, prob), xytext=(idx, prob + 0.28),
            ha="center", va="bottom", fontsize=9, fontweight="bold", color="#B91C1C",
            arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1.4),
            zorder=7,
        )

    ax.set_ylim(0, 1)
    ax.set_xlim(0, len(cp_probs))
    ax.set_xlabel("draw index  (2012  →  2026)")
    ax.set_ylabel("P(change-point here)")
    ax.set_title("The detector was given raw numbers — no dates, no labels.\n"
                 "It pointed at both moments the rules secretly changed.",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    out = ASSETS / "story_bocpd.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def _load_prng_rows() -> list[dict]:
    csv_path = Path("artifacts/prng_benchmark.csv")
    if csv_path.exists():
        with csv_path.open(newline="") as fh:
            return list(csv.DictReader(fh))
    # Hard-coded fallback (parity with the README).
    clear = dict(familyB_reject="0/50", mmd_reject="false", cooc_reject="false", verdict="clear")
    return [
        dict(source="MT19937", **{"class": "good"}, **clear),
        dict(source="Xorshift64", **{"class": "good"}, **clear),
        dict(source="ChaCha20", **{"class": "crypto"}, **clear),
        dict(source="AES-CTR-DRBG", **{"class": "crypto"}, **clear),
        dict(source="MT19937+bias(7)", **{"class": "DEFECT"}, familyB_reject="1/50",
             mmd_reject="true", cooc_reject="false", verdict="FLAG"),
        dict(source="MT19937+period(50)", **{"class": "DEFECT"}, familyB_reject="27/50",
             mmd_reject="true", cooc_reject="true", verdict="FLAG"),
        dict(source="EuroJackpot", **{"class": "real"}, **clear),
    ]


def _story_prng() -> Path:
    """PRNG heatmap: CLEAR (green) vs FLAG (red) across 3 detectors + verdict."""
    rows = _load_prng_rows()
    detectors = ["Family B\n(per-number)", "MMD\n(distribution)", "Co-occurrence\n(pairs)"]
    keys = ["familyB_reject", "mmd_reject", "cooc_reject"]

    green, red = "#16A34A", "#DC2626"

    def fired(row: dict, key: str) -> bool:
        v = row[key]
        if key == "familyB_reject":
            return v.split("/")[0] != "0"
        return v.strip().lower() == "true"

    n = len(rows)
    fig, ax = plt.subplots(figsize=(9.5, 0.62 * n + 1.6))
    ax.set_xlim(0, len(detectors))
    ax.set_ylim(0, n)
    ax.invert_yaxis()

    for r, row in enumerate(rows):
        for c, key in enumerate(keys):
            hit = fired(row, key)
            ax.add_patch(plt.Rectangle((c, r), 1, 1, facecolor=(red if hit else green),
                                       edgecolor="white", lw=2, alpha=0.92))
            ax.text(c + 0.5, r + 0.5, "DETECTED" if hit else "silent",
                    ha="center", va="center", fontsize=8,
                    color="white", fontweight="bold")

    # Row labels (source + class) on the left.
    cls_color = {"good": "#334155", "crypto": "#334155", "real": "#334155", "DEFECT": "#B91C1C"}
    for r, row in enumerate(rows):
        cls = row["class"]
        label = row["source"]
        ax.text(-0.12, r + 0.5, label, ha="right", va="center", fontsize=9,
                fontweight="bold" if cls == "DEFECT" else "normal",
                color=cls_color.get(cls, "#334155"))
        ax.text(-0.12, r + 0.5, "", ha="right", va="center")
        # Verdict on the right.
        verdict = row["verdict"]
        vcol = red if verdict.upper() == "FLAG" else green
        ax.text(len(detectors) + 0.12, r + 0.5, verdict.upper(),
                ha="left", va="center", fontsize=9, fontweight="bold", color=vcol)

    ax.set_xticks([c + 0.5 for c in range(len(detectors))])
    ax.set_xticklabels(detectors, fontsize=9)
    ax.xaxis.set_ticks_position("top")
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Same instrument, generators with a known answer key:\n"
                 "silent on good & crypto RNGs, fires on planted defects — and shows the KIND.",
                 fontsize=11, fontweight="bold", pad=28)
    fig.tight_layout()
    out = ASSETS / "story_prng.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    draws = load_seed_csv()
    print(f"loaded {len(draws)} draws")
    p1 = _story_bocpd(draws)
    print(f"wrote {p1}")
    p2 = plot_control_comparison(draws, out_path=ASSETS / "story_control.png")
    print(f"wrote {p2}")
    p3 = _story_prng()
    print(f"wrote {p3}")


if __name__ == "__main__":
    main()
