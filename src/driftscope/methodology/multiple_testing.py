"""Multiple testing correction — family-aware FDR (W6, preregistration §5, DoD-3).

Two hypothesis families with different dependence → different procedures (preregistration_v5 §5):

**Family A — global time-series (12 hypotheses):** 4 tests (ADF, KPSS, Bayesian CP, Welch)
× 3 regimes. Correction: **Benjamini-Hochberg** FDR α=0.05 (primary) + **Storey q-values**
(secondary sanity — estimates pi0, less conservative when there are many true H1).

**Family B — per-number (150 hypotheses, ratified v7 §0(A)):** the per-number family =
EXCLUSIVELY exact-binomial: 50 numbers × 3 regimes. Correction: **Benjamini-Yekutieli** FDR
α=0.05 (primary) — valid under ARBITRARY dependence (the 5/50 counts are negatively
correlated), where the PRDS assumption for BH is uncertain; **BH** as secondary (a less
conservative reference point). Storey REJECTED for Family B (unstable under a dominant
null). The OMNIBUS detectors (chi² §5, gap GoF §5b, co-occurrence §5c — 1 p-value/regime each)
do NOT enter the per-number Family B (a v5 category error corrected in v7):
they form complementary families reported SEPARATELY, feeding the Disagreement Protocol (§6.5).

The engine is agnostic: it takes p-values + labels and returns an `FDRResult` (q-values +
rejection mask). BH/BY via `statsmodels.stats.multitest.multipletests`; Storey is our own
(~15 LOC). DoD-3 = this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import numpy.typing as npt
from statsmodels.stats.multitest import multipletests

Method = Literal["bh", "by", "storey"]

# Family sizes (preregistration_v7 §5; Family B count corrected v7 §0(A): 450 → 150).
FAMILY_A_SIZE = 12    # 4 omnibus tests × 3 regimes
FAMILY_B_SIZE = 150   # 50 numbers × 3 regimes (exact-binomial only; chi²/gap/cooc separate)

_DEFAULT_ALPHA = 0.05
_STOREY_LAMBDA = 0.5  # pi0 estimation threshold (Storey 2002)


@dataclass(frozen=True)
class FDRResult:
    """The FDR correction result for one hypothesis family."""

    method: str
    alpha: float
    labels: list[str]
    p_values: npt.NDArray[np.float64]
    q_values: npt.NDArray[np.float64]          # adjusted p-values (monotone)
    reject: npt.NDArray[np.bool_]              # bool mask: q <= alpha
    # secondary: e.g. {"storey": q-values}
    secondary: dict[str, npt.NDArray[np.float64]] = field(default_factory=dict)

    @property
    def n_reject(self) -> int:
        return int(self.reject.sum())

    def rejected_labels(self) -> list[str]:
        return [lbl for lbl, r in zip(self.labels, self.reject) if r]


# ---------------------------------------------------------------------------
# Base procedures (adjusted p-values / q-values)
# ---------------------------------------------------------------------------

def bh_adjusted(
    pvals: npt.NDArray[np.float64], alpha: float = _DEFAULT_ALPHA
) -> npt.NDArray[np.float64]:
    """Benjamini-Hochberg adjusted p-values (q-values). PRDS-dependent."""
    if pvals.size == 0:
        return np.empty(0)
    _, q, _, _ = multipletests(pvals, alpha=alpha, method="fdr_bh")
    return q


def by_adjusted(
    pvals: npt.NDArray[np.float64], alpha: float = _DEFAULT_ALPHA
) -> npt.NDArray[np.float64]:
    """Benjamini-Yekutieli adjusted p-values — valid under ARBITRARY dependence."""
    if pvals.size == 0:
        return np.empty(0)
    _, q, _, _ = multipletests(pvals, alpha=alpha, method="fdr_by")
    return q


def storey_qvalues(
    pvals: npt.NDArray[np.float64], lam: float = _STOREY_LAMBDA
) -> npt.NDArray[np.float64]:
    """Storey (2002/2003) q-values with pi0 estimation = #{p>lam}/(m·(1−lam)).

    Less conservative than BH when the fraction of true H1 is large (pi0 < 1). For
    Family A as a secondary sanity check. Returns q-values in the original order of `pvals`.
    """
    m = pvals.size
    if m == 0:
        return np.empty(0)
    pi0 = min(1.0, float((pvals > lam).sum()) / (m * (1.0 - lam))) if lam < 1.0 else 1.0
    pi0 = max(pi0, 1.0 / m)  # guard: not zero

    order = np.argsort(pvals)
    p_sorted = pvals[order]
    ranks = np.arange(1, m + 1)
    q_sorted = pi0 * m * p_sorted / ranks
    # enforce monotonicity from the largest p (backward cummin)
    q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0.0, 1.0)
    q = np.empty(m)
    q[order] = q_sorted
    return q


# ---------------------------------------------------------------------------
# Per-family correction (preregistration_v5 §5)
# ---------------------------------------------------------------------------

def _as_arrays(
    pvals: npt.NDArray[np.float64] | list[float], labels: list[str] | None
) -> tuple[npt.NDArray[np.float64], list[str]]:
    p = np.asarray(pvals, dtype=float)
    if labels is None:
        labels = [f"h{i}" for i in range(p.size)]
    if len(labels) != p.size:
        raise ValueError(f"len(labels)={len(labels)} != len(pvals)={p.size}")
    if p.size and (p.min() < 0.0 or p.max() > 1.0):
        raise ValueError("p-values must be in [0, 1]")
    return p, list(labels)


def correct_family_a(
    pvals: npt.NDArray[np.float64] | list[float],
    labels: list[str] | None = None,
    alpha: float = _DEFAULT_ALPHA,
) -> FDRResult:
    """Family A: BH primary + Storey secondary (preregistration_v5 §5)."""
    p, lbls = _as_arrays(pvals, labels)
    q = bh_adjusted(p, alpha)
    return FDRResult(
        method="benjamini_hochberg",
        alpha=alpha,
        labels=lbls,
        p_values=p,
        q_values=q,
        reject=q <= alpha,
        secondary={"storey": storey_qvalues(p)},
    )


def correct_family_b(
    pvals: npt.NDArray[np.float64] | list[float],
    labels: list[str] | None = None,
    alpha: float = _DEFAULT_ALPHA,
) -> FDRResult:
    """Family B: Benjamini-Yekutieli primary + BH secondary (preregistration_v5 §5)."""
    p, lbls = _as_arrays(pvals, labels)
    q = by_adjusted(p, alpha)
    return FDRResult(
        method="benjamini_yekutieli",
        alpha=alpha,
        labels=lbls,
        p_values=p,
        q_values=q,
        reject=q <= alpha,
        secondary={"bh": bh_adjusted(p, alpha)},
    )
