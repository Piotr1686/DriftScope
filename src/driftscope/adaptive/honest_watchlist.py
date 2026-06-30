"""Adaptive watchlist (W7, DoD-5) — an HONEST gate over the pipeline results.

A deliberately minimal, defensive component (PROJECT_BRIEF §5 Step 10: self-value < 20%
scope). It builds a watchlist of patterns "worth further monitoring" EXCLUSIVELY from
signals that passed full rigor:

  1. **DoD-3 (FDR):** q-value <= alpha after multiple-testing correction (`multiple_testing`).
  2. **DoD-4 (convergence):** the signal seen by >= `min_convergence` pillars
     (DisagreementVerdict from `reporting.disagreement`).

If NO pattern passes the gate → `build_watchlist` returns **None** (NOT an empty list):
honest null — "no validated signal, no watchlist". This is the core of DoD-5: the adaptive
layer stays silent when the methodology produced no evidence (no extrapolation by force).

**Why the primary gate is FDR, with convergence as a PARAMETER (`min_convergence=1`):**
the clean pair_corr cell is **1/3** (co-occurrence only; chi²/MMD/H1 provably blind —
preregistration_v6 §6.5). A hard >=2/3 threshold would reject this REAL, validated signal.
Hence the default is >=1 pillar + passing FDR; a caller may tighten it to >=2 or 3.

This module is NOT number prediction (the prediction pivot is CANCELLED — Path A, audit).
The watchlist = an audit artifact "these patterns passed all the rigor gates".
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from driftscope.reporting.disagreement import DisagreementVerdict

_DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class WatchlistCandidate:
    """A watchlist candidate: a signal + its rigor verdicts (DoD-3 + DoD-4)."""

    label: str                      # pattern identifier, e.g. "R3:number_37:gap"
    regime: str                     # regime in which it was detected
    verdict: DisagreementVerdict    # DoD-4: how many pillars agree
    q_value: float                  # DoD-3: FDR-corrected q-value
    detail: str = ""                # optional description (signal type, localization)


@dataclass(frozen=True)
class WatchlistEntry:
    """A watchlist entry — a pattern that PASSED the DoD-3 + DoD-4 gate."""

    label: str
    regime: str
    convergence: str                # DisagreementVerdict.fraction, e.g. "3/3"
    agreeing: tuple[str, ...]       # which pillars fired
    q_value: float
    detail: str

    @property
    def is_primary_finding(self) -> bool:
        """True when full convergence (all pillars) — the strongest entry."""
        num, _, den = self.convergence.partition("/")
        return num == den


def build_watchlist(
    candidates: Sequence[WatchlistCandidate],
    *,
    alpha: float = _DEFAULT_ALPHA,
    min_convergence: int = 1,
) -> list[WatchlistEntry] | None:
    """Return a watchlist of validated patterns, or None (honest null).

    Per-candidate gate: `q_value <= alpha` (DoD-3 FDR) AND `verdict.n_agree >=
    min_convergence` (DoD-4 convergence). If none passes → **None** (not an empty
    list) — signals the absence of a validated signal (DoD-5).

    The result is sorted by q_value ascending (strongest evidence first).
    """
    if min_convergence < 0:
        raise ValueError(f"min_convergence must be >= 0 (got {min_convergence})")

    qualifying = [
        c
        for c in candidates
        if c.q_value <= alpha and c.verdict.n_agree >= min_convergence
    ]
    if not qualifying:
        return None

    qualifying.sort(key=lambda c: c.q_value)
    return [
        WatchlistEntry(
            label=c.label,
            regime=c.regime,
            convergence=c.verdict.fraction,
            agreeing=c.verdict.agreeing,
            q_value=c.q_value,
            detail=c.detail,
        )
        for c in qualifying
    ]


def watchlist_or_message(
    candidates: Sequence[WatchlistCandidate],
    *,
    alpha: float = _DEFAULT_ALPHA,
    min_convergence: int = 1,
) -> tuple[list[WatchlistEntry] | None, str]:
    """Like `build_watchlist`, but attaches an explicit message (DoD-5: None with a message)."""
    watchlist = build_watchlist(
        candidates, alpha=alpha, min_convergence=min_convergence
    )
    if watchlist is None:
        msg = (
            f"Honest null: none of {len(candidates)} candidates passed the gate "
            f"(FDR q<={alpha} AND convergence >={min_convergence}/3). "
            "No watchlist — the methodology produced no validated signal."
        )
        return None, msg
    n_primary = sum(e.is_primary_finding for e in watchlist)
    msg = (
        f"{len(watchlist)} pattern(s) passed the DoD-3+DoD-4 gate "
        f"({n_primary} primary 3/3). Sorted by q-value."
    )
    return watchlist, msg
