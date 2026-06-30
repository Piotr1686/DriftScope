"""End-to-end audit orchestrator (W7) — what the framework ASSERTS on real EuroJackpot.

Ties the validated DoD-1..6 components into a single run over a real draw stream:

  POSITIVE CONTROL (euron, temporal/H1 pillar): `run_bocpd(draws, "euron")` detects
    the euronumber pool changes of 2014/2022 (ground truth DoD-1b). FULL-STREAM — the
    signal is the transition BETWEEN regimes, a per-regime split would destroy it
    (preregistration_v7 §1c).
  NEGATIVE CONTROL (main 1-50, 3 Disagreement pillars): three INDEPENDENT detector
    families (H1/temporal, MMD/distributional, co-occurrence/joint) on the main pool,
    computed PER REGIME (R1/R2/R3) — a stationarity test WITHIN a regime (H0 §1).
    Expected 0/3 in each regime — the main pool has no pre-registered signal
    (DoD-1 negative control).
  HONEST WATCHLIST (DoD-5): Family B FDR (per-number exact binomial) + convergence →
    `build_watchlist`. On a clean neg. control → **None** (honest null, not an empty list).

**Design decision (gating "H1 family → 1 pillar verdict"):** the `h1` pillar represents
BOCPD per-stream (`bocpd_detector`). Rationale: BOCPD is calibrated per-field
(FPR≈0.05, preregistration_v7 §2), has a validated positive/negative control, and is the
W8 hook detector. ADF/KPSS/Welch/ACF operate on derived SCALAR series
(euron_mean, ...) and play a DIAGNOSTIC role, not a voting pillar — OR-aggregating
correlated H1 sub-tests would inflate the pillar FPR. DoD-4 stays 3/3.

**Per-regime granularity (preregistration_v7 §0(B)/§1c):** the negative control (3 pillars)
and Family B are computed SEPARATELY in each regime by rule (R1/R2/R3) — H0 §1 is
pre-registered per regime ("stationary uniform i.i.d. WITHIN a regime"). The main pool 1-50
is structurally invariant across all regimes, so each regime is an INDEPENDENT negative
control. The positive control (euron) stays full-stream (it detects transitions between regimes).

**Family B (per-number, count ratified v7 §0(A)):** the family = EXCLUSIVELY per-number
exact-binomial p-values (count_k ~ Binomial(n, 5/50) under uniform), 50 numbers × #non-empty
regimes = on real data **150** (instead of the reference 450 — chi²/gap/cooc are OMNIBUS
detectors, not per-number, reported separately as complementary families). The pool of
p-values from all regimes forms ONE family, corrected once with Benjamini-Yekutieli (v7 §5).

This module orchestrates ready, independently validated components — it introduces no new
methodological decisions itself (NOT subject to the prereg §0 discipline).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.stats import binomtest

from driftscope.adaptive.honest_watchlist import (
    WatchlistCandidate,
    WatchlistEntry,
    watchlist_or_message,
)
from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.ingestion.regime_split import REGIME_LABELS, split_by_regime
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.h1_classical import run_bocpd
from driftscope.methodology.k4_mmd import mmd_uniform_detector
from driftscope.methodology.multiple_testing import FDRResult, correct_family_b
from driftscope.reporting.disagreement import (
    DisagreementVerdict,
    classify_from_results,
    run_pillars,
)

_MAIN_POOL_SIZE = 50  # fallback for an empty list; in practice read from draws[0].pool_size
_DEFAULT_ALPHA = 0.05
_DEFAULT_N_PERM = 999


# ---------------------------------------------------------------------------
# H1 pillar — BOCPD as the per-stream representative (gating decision)
# ---------------------------------------------------------------------------

def bocpd_detector(
    field: Literal["main", "euron"] = "euron",
    *,
    alpha_unused: float = _DEFAULT_ALPHA,  # signature consistency; the BOCPD threshold is per-field
) -> Detector:
    """Factory for the H1 detector = BOCPD on the given field (pure function of `draws`, DoD-6).

    `run_bocpd` returns `reject_h0` per the per-field threshold calibrated to FPR≈0.05
    (preregistration_v7 §2). This is the representative of the `h1` pillar in the
    Disagreement Protocol — see the module docstring (gating decision). `alpha_unused`
    exists for signature consistency with the other factories; the BOCPD threshold is
    not an alpha parameter.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        return run_bocpd(draws, field=field)

    return detector


def default_pillar_detectors(
    *,
    alpha: float = _DEFAULT_ALPHA,
    n_perm: int = _DEFAULT_N_PERM,
) -> dict[str, Detector]:
    """Three Disagreement pillars on the MAIN pool (negative control, applied per regime).

    - `h1`           — BOCPD(field="main") (temporal pillar; H1 representative).
    - `mmd`          — MMD² of observation windows vs uniform reference (window=25, §3/v7).
    - `cooccurrence` — max-pair, curveball null (§5c).

    window=25 (not the original §3 value of 200): on the full non-overlap stream it gives
    robust calibration (preregistration_v4 §3, real-data correction). NOTE per regime: R1
    (n=133) yields only ~5 MMD windows — the feasibility boundary (§3 "Data limitation");
    the R1 result is reported with this caveat, but the detector does not crash. All read
    the main pool.
    """
    return {
        "h1": bocpd_detector(field="main"),
        "mmd": mmd_uniform_detector(window=25, n_perm=n_perm, alpha=alpha),
        "cooccurrence": cooccurrence_detector(n_perm=n_perm, alpha=alpha),
    }


# ---------------------------------------------------------------------------
# Family B — per-number exact binomial (pre-registered §5)
# ---------------------------------------------------------------------------

def family_b_per_number_pvalues(
    draws: list[DrawRecord],
) -> tuple[list[str], npt.NDArray[np.float64]]:
    """Per-number exact-binomial p-values for the main pool (Family B, §5).

    For each number k ∈ 1..50: count_k = #{draws containing k}. Under uniform
    P(k in a draw) = 5/50, so count_k ~ Binomial(n, 5/50). A two-sided exact test
    per number → 50 p-values (input to the Family B FDR, Benjamini-Yekutieli).

    Returns: (labels ["number_1".."number_50"], p_values (50,)).
    """
    n = len(draws)
    # Pool/k derived from the records (EJ=50/5 → P=0.10; MM=80/20 → P=0.25).
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    k_drawn = len(draws[0].main_numbers) if draws else 5
    p_present = k_drawn / pool
    counts = np.zeros(pool, dtype=np.int64)
    for d in draws:
        # Incidence: each number counted ONCE per draw (the Binomial model = presence,
        # not multiplicity) — robust to any duplicates within a draw.
        for k in set(d.main_numbers):
            counts[k - 1] += 1
    pvals = np.array(
        [
            binomtest(
                int(counts[k]), n, p_present, alternative="two-sided"
            ).pvalue
            for k in range(pool)
        ],
        dtype=float,
    )
    labels = [f"number_{k + 1}" for k in range(pool)]
    return labels, pvals


# ---------------------------------------------------------------------------
# Audit report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeAudit:
    """Negative control of a single rule regime (3 pillars on the main pool WITHIN the regime)."""

    regime: str                               # "R1" / "R2" / "R3" (prereg_v7 §1)
    n_draws: int                              # number of draws in the regime
    negative_control: dict[str, TestResult]   # 3 Disagreement pillars (h1/mmd/cooccurrence)
    verdict: DisagreementVerdict              # Disagreement Protocol (DoD-4) for this regime


@dataclass(frozen=True)
class AuditReport:
    """Framework verdict on a stream: pos control (full) + neg control per-regime + gate."""

    positive_control: TestResult              # BOCPD euron full-stream (ground truth 2014/2022)
    regime_audits: dict[str, RegimeAudit]     # neg control per regime (R1/R2/R3; non-empty only)
    family_b: FDRResult                       # per-number FDR pooled over regimes (DoD-3)
    watchlist: list[WatchlistEntry] | None    # DoD-5: None = honest null
    watchlist_message: str

    @property
    def family_b_size(self) -> int:
        """Concrete Family B size (50 × #non-empty regimes; 150 in practice)."""
        return len(self.family_b.labels)

    def summary(self) -> str:
        """A readable summary for the report (report.qmd / CLI)."""
        pc = self.positive_control
        cps = list(
            zip(
                pc.metadata.get("top_changepoint_dates", []),
                pc.metadata.get("top_changepoint_probs", []),
            )
        )
        cp_str = ", ".join(f"{d} (p={p:.2f})" for d, p in cps[:3]) or "none"
        lines = [
            "DriftScope audit — stream verdict:",
            f"  POSITIVE CONTROL (euron/BOCPD, full-stream): reject={pc.reject_h0}; "
            f"top change-points: {cp_str}",
            "  NEGATIVE CONTROL (main 1-50 / 3 pillars, per regime):",
        ]
        for label in REGIME_LABELS:
            ra = self.regime_audits.get(label)
            if ra is None:
                continue
            neg = " ".join(
                f"{k}={'reject' if r.reject_h0 else 'ok'}"
                for k, r in ra.negative_control.items()
            )
            lines.append(
                f"    {label} (n={ra.n_draws}): {ra.verdict.fraction} "
                f"({ra.verdict.label}); [{neg}]"
            )
        wl = (
            "None (honest null)"
            if self.watchlist is None
            else f"{len(self.watchlist)} entry(ies)"
        )
        lines.append(
            f"  Family B (per-number FDR, {self.family_b.method}): "
            f"{self.family_b.n_reject}/{self.family_b_size} rejected"
        )
        lines.append(f"  WATCHLIST (DoD-5): {wl}")
        lines.append(f"  -> {self.watchlist_message}")
        return "\n".join(lines)


def run_audit(
    draws: list[DrawRecord],
    *,
    alpha: float = _DEFAULT_ALPHA,
    pillar_detectors: dict[str, Detector] | None = None,
    n_perm: int = _DEFAULT_N_PERM,
    min_convergence: int = 1,
) -> AuditReport:
    """Full stream audit: positive control (full) + per-regime neg control + honest gate.

    1. Positive control: BOCPD(euron) FULL-STREAM — detecting the 2014/2022 pool changes (DoD-1b).
    2. Negative control PER REGIME: for each non-empty regime (R1/R2/R3) 3 Disagreement
       pillars on the main pool → classification (DoD-4). The other regimes are skipped.
    3. Family B FDR: per-number exact-binomial per regime, POOLED into one family (labels
       "Rk:number_j") + Benjamini-Yekutieli once over the whole family (DoD-3, v7 §5).
    4. Watchlist: candidates = numbers rejected by Family B, each with the convergence verdict
       of ITS OWN regime; `build_watchlist` → None when none passes the gate (FDR q≤alpha
       AND convergence ≥min_convergence). On a clean neg. control → honest null (DoD-5).

    `pillar_detectors`: override the 3 pillars (tests inject fast variants);
    applied to EVERY regime. None → `default_pillar_detectors(alpha, n_perm)`.
    """
    positive = run_bocpd(draws, field="euron")

    detectors = (
        pillar_detectors
        if pillar_detectors is not None
        else default_pillar_detectors(alpha=alpha, n_perm=n_perm)
    )

    regimes = split_by_regime(draws)
    regime_audits: dict[str, RegimeAudit] = {}
    pooled_labels: list[str] = []
    pooled_pvals: list[npt.NDArray[np.float64]] = []

    for label in REGIME_LABELS:
        regime_draws = regimes.get(label, [])
        if not regime_draws:  # regime with no draws — skipped (e.g. an incomplete stream)
            continue
        pillars = run_pillars(regime_draws, detectors)
        regime_audits[label] = RegimeAudit(
            regime=label,
            n_draws=len(regime_draws),
            negative_control=pillars,
            verdict=classify_from_results(pillars),
        )
        lbls, pvals = family_b_per_number_pvalues(regime_draws)
        pooled_labels.extend(f"{label}:{lbl}" for lbl in lbls)
        pooled_pvals.append(pvals)

    pvals_all = (
        np.concatenate(pooled_pvals) if pooled_pvals else np.array([], dtype=float)
    )
    family_b = correct_family_b(pvals_all, pooled_labels, alpha=alpha)

    # Watchlist candidates = numbers rejected by Family B (DoD-3). Each carries the convergence
    # verdict of ITS OWN regime (DoD-4; label = "Rk:number_j"). Both gates are enforced in
    # `watchlist_or_message`; on a uniform main pool Family B rejects nothing → no candidates.
    candidates = [
        WatchlistCandidate(
            label=lbl,
            regime=lbl.split(":", 1)[0],
            verdict=regime_audits[lbl.split(":", 1)[0]].verdict,
            q_value=float(q),
            detail="per-number exact binomial (Family B)",
        )
        for lbl, q, rej in zip(family_b.labels, family_b.q_values, family_b.reject)
        if rej
    ]
    watchlist, message = watchlist_or_message(
        candidates, alpha=alpha, min_convergence=min_convergence
    )

    return AuditReport(
        positive_control=positive,
        regime_audits=regime_audits,
        family_b=family_b,
        watchlist=watchlist,
        watchlist_message=message,
    )
