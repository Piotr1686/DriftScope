"""Multi Multi audit — second real-world case study (reusability showcase, reporting layer).

A second number game (Multi Multi 20-of-80) run through EXACTLY the same negative-control
battery as the EuroJackpot audit — proof that the framework is reusable beyond the flagship
case. The detectors derive pool/k from the records (`DrawRecord.generic`, pool_size=80), no
new methodology (reuse of `prng_benchmark.run_battery` + `h1_classical.run_bocpd` — the
reporting layer is NOT subject to the prereg §0 discipline).

BOCPD is O(T^2) → the audit is computed on a LIMITED window of the last `window` draws (default
2000; the full 16827 excluded by budget). The BOCPD(pool=80) threshold = 0.34 (calibrated on
n=2000, FPR~=0.05 under a uniform-iid null; `_MAIN_REJECT_THRESHOLD_BY_POOL`), so the 2000
window is length-matched to the calibration. Expected result: **clear** — Multi Multi is a
well-tested RNG with no pre-registered signal (an honest null like the 1-50 negative control in EJ).
The verdict = the Disagreement Protocol over the 3 core pillars (BOCPD/MMD/cooc, FLAG >=2/3),
so a lone reject of a single pillar at alpha=0.05 does NOT overturn the verdict.

Presentation (table/CSV) lives in `scripts/multimulti_audit.py` (CLI).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import driftscope
from driftscope.ingestion.lotto_scraper import load_generic_seed_csv
from driftscope.methodology.h1_classical import run_bocpd
from driftscope.reporting.disagreement import DisagreementVerdict, classify
from driftscope.reporting.prng_benchmark import BenchmarkRow, run_battery

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_MM_SEED_PATH = _ROOT / "data" / "seed" / "multimulti_history.csv"
_MM_POOL_SIZE = 80
_DEFAULT_WINDOW = 2000  # BOCPD O(T^2) + length-matched to the 0.34 threshold calibration


@dataclass(frozen=True)
class MultiMultiAuditRow:
    """One row of the MM audit: BOCPD (temporal pillar) + negative-control battery.

    Composition: `battery` carries Family B (per-number exact binomial) + MMD + co-occurrence
    + IT (supplement); the `bocpd_*` fields add the H1 pillar (BOCPD on the main pool).

    The verdict = the Disagreement Protocol over the 3 CORE pillars (BOCPD->h1 / MMD /
    co-occurrence): "FLAG" only on convergence >=2/3, a lone pillar (1/3) = clear
    (an expected false-positive at alpha=0.05, NOT a finding — consistent with report.qmd §4/§6).
    IT = a supplement (not a pillar), Family B = a separate FDR gate — both reported in the
    matrix, but OUTSIDE the verdict. `BenchmarkRow.flagged` (PRNG) applies the SAME >=2 rule, but
    on the triple {Family B, MMD, co-occurrence} — the PRNG battery has no BOCPD/h1 pillar, so the
    marginal axis is carried there by Family B (see `prng_benchmark.BenchmarkRow.core_votes`).
    """

    source: str
    n: int
    window: int
    bocpd_reject: bool
    bocpd_max_prob: float
    bocpd_threshold: float
    battery: BenchmarkRow

    @property
    def disagreement(self) -> DisagreementVerdict:
        """Disagreement classification over the 3 core pillars (reuse of DoD-4 classify)."""
        return classify(
            {
                "h1": self.bocpd_reject,  # BOCPD = the temporal H1 family (see PILLARS)
                "mmd": self.battery.mmd_reject,
                "cooccurrence": self.battery.cooc_reject,
            }
        )

    @property
    def core_fraction(self) -> str:
        """Fraction of agreeing core pillars ('0/3'..'3/3') for reports."""
        return self.disagreement.fraction

    @property
    def flagged(self) -> bool:
        """Whether core-pillar convergence is >=2/3 (Disagreement, NOT a naive OR)."""
        return self.disagreement.n_agree >= 2

    @property
    def verdict(self) -> str:
        return "FLAG" if self.flagged else "clear"


def run_multimulti_audit(
    *,
    window: int = _DEFAULT_WINDOW,
    n_perm: int = 499,
    alpha: float = 0.05,
    seed_csv: Path | None = None,
) -> MultiMultiAuditRow:
    """Multi Multi negative-control audit on a window of the last `window` draws.

    Loads the real MM stream (`load_generic_seed_csv`, pool_size=80), slices to the last
    `window` draws, and computes: BOCPD(field="main") + the full battery (`run_battery` reuse).
    All detectors derive pool/k from the records (steps 1–5). Expected: clear
    (Disagreement; a lone pillar 1/3 = clear, NOT a finding).

    `seed_csv`: path override (tests/other sources); None → `data/seed/multimulti_history.csv`.
    """
    path = seed_csv if seed_csv is not None else _MM_SEED_PATH
    draws = load_generic_seed_csv(path, pool_size=_MM_POOL_SIZE)
    # BOCPD is sequential, and "window = last N" assumes chronological order.
    # The real MM seed has 2 historical date inversions (2010) — we sort defensively, so the
    # window and change-point detection are independent of the order in the source file.
    draws.sort(key=lambda d: d.draw_date)
    recent = draws[-window:] if 0 < window < len(draws) else draws

    bocpd = run_bocpd(recent, field="main")
    battery = run_battery("Multi Multi", "real", recent, alpha=alpha, n_perm=n_perm)

    return MultiMultiAuditRow(
        source="Multi Multi (20/80)",
        n=len(recent),
        window=window,
        bocpd_reject=bocpd.reject_h0,
        bocpd_max_prob=float(bocpd.statistic),
        bocpd_threshold=float(bocpd.metadata["reject_threshold"]),
        battery=battery,
    )
