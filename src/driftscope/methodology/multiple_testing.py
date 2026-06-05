"""Multiple testing correction — family-aware FDR (W6, preregistration §5, DoD-3).

Dwie rodziny hipotez o roznej strukturze zaleznosci → rozne procedury (preregistration_v5 §5):

**Family A — global time-series (12 hipotez):** 4 testy (ADF, KPSS, Bayesian CP, Welch)
× 3 rezimy. Korekcja: **Benjamini-Hochberg** FDR α=0.05 (primary) + **Storey q-values**
(secondary sanity — estymuje pi0, mniej konserwatywny gdy duzo prawdziwych H1).

**Family B — per-number (450+ hipotez):** 50 liczb × 3 testy (chi-squared, exact binomial,
gap GoF §5b) × 3 rezimy. Korekcja: **Benjamini-Yekutieli** FDR α=0.05 (primary) — wazna
przy DOWOLNEJ strukturze zaleznosci (zliczenia 5/50 ujemnie skorelowane, gapy wspolzalezne),
gdzie zalozenie PRDS dla BH jest niepewne; **BH** jako secondary (mniej konserwatywny punkt
odniesienia). Storey ODRZUCONY dla Family B (niestabilny przy dominujacym nullu).
Test wspolwystapien (§5c) zasila Family B jako dodatkowa rodzina per-rezim (licznik
hipotez domykany przy pelnej integracji raportowej).

Silnik jest agnostyczny: przyjmuje p-values + etykiety, zwraca `FDRResult` (q-values +
maska odrzucen). BH/BY przez `statsmodels.stats.multitest.multipletests`; Storey wlasny
(~15 LOC). DoD-3 = ten modul.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import numpy.typing as npt
from statsmodels.stats.multitest import multipletests

Method = Literal["bh", "by", "storey"]

# Rozmiary rodzin (preregistration_v5 §5) — referencyjne, walidowane przy pelnym sweepie.
FAMILY_A_SIZE = 12    # 4 testy × 3 rezimy
FAMILY_B_SIZE = 450   # 50 liczb × 3 testy × 3 rezimy (+ co-occurrence: dodatkowa rodzina)

_DEFAULT_ALPHA = 0.05
_STOREY_LAMBDA = 0.5  # prog estymacji pi0 (Storey 2002)


@dataclass(frozen=True)
class FDRResult:
    """Wynik korekcji FDR dla jednej rodziny hipotez."""

    method: str
    alpha: float
    labels: list[str]
    p_values: npt.NDArray[np.float64]
    q_values: npt.NDArray[np.float64]          # adjusted p-values (monotoniczne)
    reject: npt.NDArray[np.bool_]              # maska bool: q <= alpha
    # secondary: np. {"storey": q-values}
    secondary: dict[str, npt.NDArray[np.float64]] = field(default_factory=dict)

    @property
    def n_reject(self) -> int:
        return int(self.reject.sum())

    def rejected_labels(self) -> list[str]:
        return [lbl for lbl, r in zip(self.labels, self.reject) if r]


# ---------------------------------------------------------------------------
# Procedury bazowe (adjusted p-values / q-values)
# ---------------------------------------------------------------------------

def bh_adjusted(
    pvals: npt.NDArray[np.float64], alpha: float = _DEFAULT_ALPHA
) -> npt.NDArray[np.float64]:
    """Benjamini-Hochberg adjusted p-values (q-values). PRDS-zalezne."""
    if pvals.size == 0:
        return np.empty(0)
    _, q, _, _ = multipletests(pvals, alpha=alpha, method="fdr_bh")
    return q


def by_adjusted(
    pvals: npt.NDArray[np.float64], alpha: float = _DEFAULT_ALPHA
) -> npt.NDArray[np.float64]:
    """Benjamini-Yekutieli adjusted p-values — wazne przy DOWOLNEJ zaleznosci."""
    if pvals.size == 0:
        return np.empty(0)
    _, q, _, _ = multipletests(pvals, alpha=alpha, method="fdr_by")
    return q


def storey_qvalues(
    pvals: npt.NDArray[np.float64], lam: float = _STOREY_LAMBDA
) -> npt.NDArray[np.float64]:
    """Storey (2002/2003) q-values z estymacja pi0 = #{p>lam}/(m·(1−lam)).

    Mniej konserwatywny niz BH gdy frakcja prawdziwych H1 jest duza (pi0 < 1). Dla
    Family A jako secondary sanity. Zwraca q-values w oryginalnej kolejnosci `pvals`.
    """
    m = pvals.size
    if m == 0:
        return np.empty(0)
    pi0 = min(1.0, float((pvals > lam).sum()) / (m * (1.0 - lam))) if lam < 1.0 else 1.0
    pi0 = max(pi0, 1.0 / m)  # guard: nie zerowy

    order = np.argsort(pvals)
    p_sorted = pvals[order]
    ranks = np.arange(1, m + 1)
    q_sorted = pi0 * m * p_sorted / ranks
    # wymus monotonicznosc od najwiekszego p (cummin wstecz)
    q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0.0, 1.0)
    q = np.empty(m)
    q[order] = q_sorted
    return q


# ---------------------------------------------------------------------------
# Korekcja per-rodzina (preregistration_v5 §5)
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
        raise ValueError("p-values musza byc w [0, 1]")
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
