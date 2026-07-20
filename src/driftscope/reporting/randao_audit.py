"""RANDAO withholding audit — is anyone manipulating Ethereum's randomness beacon? (Path B3).

An application layer over `ingestion.beacon_chain`: it takes the missed-slot record and asks
whether misses cluster where WITHHOLDING would pay, i.e. at the tail of an epoch.

The hypothesis, precisely
-------------------------
An epoch's final RANDAO mix fixes proposer duties two epochs later. A proposer can only
influence it by NOT publishing — and withholding is only profitable if the attacker can
PREDICT the resulting mix, which requires that no unpredictable contribution follows. That
holds at the epoch's last slot, and extends backwards only across a contiguous tail run the
attacker owns (k tail slots => a choice among 2^k mixes). So the attack's signature is an
EXCESS OF MISSES AT POSITION 31, decaying toward the front of the epoch.

Note what is NOT tested here: the uniformity of the mix itself. Under withholding the attacker
selects among candidates that are each uniform, so the mix's marginal distribution is unchanged
and a uniformity battery on it has no power at all. See `ingestion/beacon_streams.py`.

The benign confound, stated up front
------------------------------------
Position 0 carries a structurally elevated miss rate: the epoch transition (justification,
finalization, rewards, shuffling) is computed on the first slot and slower nodes miss it. This
has nothing to do with RANDAO — and position 0 is the LEAST profitable withholding slot, with
31 unpredictable contributions still to come. Benign and adversarial explanations therefore
point at OPPOSITE ends of the epoch, which is what makes the tail test clean. Position 0 is
excluded from the null reference set (a pre-specified exclusion, identified in a scouting probe
before the test was designed) and reported separately rather than quietly dropped.

Test structure and its honest limits
------------------------------------
  primary   — one-sided binomial on position 31, reference positions 1..31, p0 = 1/31
  secondary — one-sided binomial on the tail set 28..31, p0 = 4/31 (an attacker owning a run)
  omnibus   — per-position binomial + Family B FDR across all 32 positions (reuse of the
              preregistered `methodology.multiple_testing`), which surfaces position 0 rather
              than hiding it

These three are NOT independent pillars and are deliberately not scored as a Disagreement
Protocol triple: they are nested functions of the same position histogram. The primary decides;
the others are context. A `clear` verdict is reported WITH its power bound — "we found nothing"
is worthless without "and here is what we could have found".
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from driftscope.ingestion.beacon_chain import SLOTS_PER_EPOCH, MissedSlot, ScanMeta
from driftscope.methodology.multiple_testing import correct_family_b

#: The epoch's last slot — the only position where a lone attacker can predict the resulting mix.
LAST_POSITION = SLOTS_PER_EPOCH - 1

#: Tail set for the secondary test: an attacker owning a contiguous run of final slots.
TAIL_POSITIONS = (28, 29, 30, 31)

#: Excluded from the null reference — benign epoch-transition misses (see module docstring).
CONFOUNDED_POSITION = 0


@dataclass(frozen=True)
class RandaoAuditResult:
    """Outcome of the withholding audit, with the power bound that makes a null readable."""

    n_slots: int
    n_missed: int
    miss_rate: float
    counts: tuple[int, ...]           # misses per position 0..31
    n_reference: int                  # misses in the null reference set (positions 1..31)

    last_count: int
    last_expected: float
    last_p: float                     # primary, one-sided

    tail_count: int
    tail_expected: float
    tail_p: float                     # secondary, one-sided

    family_b_reject: tuple[str, ...]  # omnibus: positions rejected after FDR
    confound_count: int               # misses at position 0 (reported, not tested)
    confound_ratio: float             # position-0 rate relative to the reference mean

    detectable_phi: float             # smallest attack fraction detectable at 80% power
    detectable_attacks: float         # ... expressed as an attack count
    detectable_period: float          # ... expressed as "1 withheld block per N epochs"
    alpha: float

    @property
    def reject_h0(self) -> bool:
        """Primary test only. The secondary and omnibus are context, not votes."""
        return self.last_p < self.alpha

    @property
    def verdict(self) -> str:
        return "FLAG" if self.reject_h0 else "clear"


def _binom_sf(count: int, n: int, p0: float) -> float:
    """One-sided P(X >= count) under Binomial(n, p0) — upper tail, excess only."""
    if n <= 0:
        return 1.0
    return float(stats.binom.sf(count - 1, n, p0))


def power_at(n_reference: int, phi: float, *, alpha: float = 0.05) -> float:
    """Power to detect an attack fraction `phi` concentrated at the last position."""
    if n_reference <= 0:
        return 0.0
    p0 = 1.0 / (SLOTS_PER_EPOCH - 1)
    crit = stats.binom.isf(alpha, n_reference, p0) + 1
    p1 = p0 * (1 - phi) + phi
    return float(stats.binom.sf(crit - 1, n_reference, p1))


def detectable_fraction(n_reference: int, *, target: float = 0.80, alpha: float = 0.05) -> float:
    """Smallest attack fraction detectable at `target` power — the bound a null result buys."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if power_at(n_reference, mid, alpha=alpha) < target:
            lo = mid
        else:
            hi = mid
    return hi


def audit_randao(
    missed: list[MissedSlot],
    meta: ScanMeta,
    *,
    alpha: float = 0.05,
    power_target: float = 0.80,
) -> RandaoAuditResult:
    """Runs the withholding audit on a persisted slot scan."""
    counts = np.zeros(SLOTS_PER_EPOCH, dtype=np.int64)
    for m in missed:
        counts[m.position] += 1

    # Null reference: positions 1..31 (position 0 excluded as a benign confound).
    reference = counts[1:]
    n_ref = int(reference.sum())
    n_positions = SLOTS_PER_EPOCH - 1

    last_count = int(counts[LAST_POSITION])
    last_p = _binom_sf(last_count, n_ref, 1.0 / n_positions)

    tail_count = int(sum(counts[p] for p in TAIL_POSITIONS))
    tail_p = _binom_sf(tail_count, n_ref, len(TAIL_POSITIONS) / n_positions)

    # Omnibus over ALL 32 positions, including 0 — reuse of the preregistered Family B.
    # Each position is tested against the flat rate over the full epoch.
    total = int(counts.sum())
    pvals = [_binom_sf(int(c), total, 1.0 / SLOTS_PER_EPOCH) for c in counts]
    labels = [f"pos_{i}" for i in range(SLOTS_PER_EPOCH)]
    fdr = correct_family_b(pvals, labels, alpha=alpha)

    ref_mean = n_ref / n_positions if n_positions else 0.0
    phi = detectable_fraction(n_ref, target=power_target, alpha=alpha)
    n_epochs = meta.n_slots / SLOTS_PER_EPOCH

    return RandaoAuditResult(
        n_slots=meta.n_slots,
        n_missed=meta.n_missed,
        miss_rate=meta.n_missed / meta.n_slots if meta.n_slots else 0.0,
        counts=tuple(int(c) for c in counts),
        n_reference=n_ref,
        last_count=last_count,
        last_expected=ref_mean,
        last_p=last_p,
        tail_count=tail_count,
        tail_expected=ref_mean * len(TAIL_POSITIONS),
        tail_p=tail_p,
        family_b_reject=tuple(fdr.rejected_labels()),
        confound_count=int(counts[CONFOUNDED_POSITION]),
        confound_ratio=float(counts[CONFOUNDED_POSITION] / ref_mean) if ref_mean else 0.0,
        detectable_phi=phi,
        detectable_attacks=phi * n_ref,
        detectable_period=n_epochs / (phi * n_ref) if phi * n_ref > 0 else float("inf"),
        alpha=alpha,
    )
