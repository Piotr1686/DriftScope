"""Disagreement Protocol (W7, DoD-4) — classifying a signal by pillar agreement.

Each detected signal (per regime) is classified by how many of the THREE
independent detector families reject H0 (preregistration_v6 §6.5):

  3/3 -> 'fully convergent signal'  (primary finding — all pillars agree)
  2/3 -> 'convergent signal'
  1/3 -> 'single-pillar signal, requires DriftSim power context'
  0/3 -> 'no signal'

**The three pillars (DoD-4 = 3/3, preregistration_v6 §6.5):**
- `h1`           — the global/temporal family (ADF, KPSS, BOCPD, Welch, ACF from
                   h1_classical + recurrence §5b + permutation/serial §5). Recurrence and
                   permutation are NOT a separate 4th pillar — they fall under the H1 pillar.
- `mmd`          — two-sample MMD² on frequency vectors (k4_mmd §3).
- `cooccurrence` — pair co-occurrence test (max-pair, curveball null §5c).

Why 3, not 4: §6.5 proves the mutual NON-redundancy of exactly these three families
(the clean Disagreement Protocol cell: pair_corr is seen ONLY by co-occurrence → 1/3).
The module is reporting-only (NOT methodology/) → not subject to the prereg §0 discipline.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from driftscope.core.types import Detector, DrawRecord, TestResult

# The three DoD-4 pillars — canonical order (stable for reports).
PILLARS: tuple[str, str, str] = ("h1", "mmd", "cooccurrence")

# Mapping from the number of agreeing pillars -> label (preregistration_v6 §6.5).
_LABELS: dict[int, str] = {
    3: "fully convergent signal",
    2: "convergent signal",
    1: "single-pillar signal, requires DriftSim power context",
    0: "no signal",
}


@dataclass(frozen=True)
class DisagreementVerdict:
    """Disagreement Protocol verdict for a single signal (DoD-4)."""

    n_agree: int
    n_pillars: int
    label: str
    agreeing: tuple[str, ...]

    @property
    def fraction(self) -> str:
        """A '3/3', '2/3', ... representation for reports."""
        return f"{self.n_agree}/{self.n_pillars}"

    @property
    def is_primary_finding(self) -> bool:
        """True only when ALL pillars agree (full convergence)."""
        return self.n_agree == self.n_pillars and self.n_pillars > 0


def classify(verdicts: Mapping[str, bool]) -> DisagreementVerdict:
    """Classify a signal by the number of pillars rejecting H0 (DoD-4).

    `verdicts`: a mapping pillar -> reject_h0 (bool). Must contain EXACTLY the 3 pillars
    from PILLARS (missing/extra = error — the protocol is defined over the full set).
    """
    missing = set(PILLARS) - set(verdicts)
    if missing:
        raise ValueError(
            f"Missing verdicts for pillars: {sorted(missing)}. All required: {PILLARS}"
        )
    extra = set(verdicts) - set(PILLARS)
    if extra:
        raise ValueError(f"Unknown pillars: {sorted(extra)}. Allowed: {PILLARS}")

    agreeing = tuple(p for p in PILLARS if verdicts[p])
    n = len(agreeing)
    return DisagreementVerdict(
        n_agree=n,
        n_pillars=len(PILLARS),
        label=_LABELS[n],
        agreeing=agreeing,
    )


def classify_from_results(results: Mapping[str, TestResult]) -> DisagreementVerdict:
    """Like `classify`, but pulls `reject_h0` out of each pillar's TestResult."""
    return classify({pillar: result.reject_h0 for pillar, result in results.items()})


def run_pillars(
    draws: list[DrawRecord], detectors: Mapping[str, Detector]
) -> dict[str, TestResult]:
    """Run each pillar's detector on the SAME draw stream.

    `detectors`: a mapping pillar -> Detector (Callable[[list[DrawRecord]], TestResult],
    the interface from driftsim.calibration). Must cover all PILLARS. Returns the raw
    TestResult per pillar — for `classify_from_results` or reporting details.
    """
    missing = set(PILLARS) - set(detectors)
    if missing:
        raise ValueError(
            f"Missing detectors for pillars: {sorted(missing)}. Required: {PILLARS}"
        )
    return {pillar: detectors[pillar](draws) for pillar in PILLARS}
