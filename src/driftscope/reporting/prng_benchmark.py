"""PRNG benchmark — battery reuse + ground-truth sources (wow Option α, reporting layer).

A reporting/analysis layer: it knows the detectors (`pipeline`/`methodology`) AND the
generators (`ingestion.rng_streams`). It applies EXACTLY the same negative-control battery as
the EuroJackpot audit to streams with a GROUND-TRUTH label and returns structured rows of the
detection matrix. Presentation (table/CSV) lives in the CLI script + `report.qmd`.

Goal: turn the audit's honest-null into a proof of SENSITIVITY — the same framework that finds
nothing in EuroJackpot lights up on a PRNG with an injected defect and stays silent on crypto-PRNGs.
No new methodology (reuse of `pipeline` — NOT subject to the prereg §0 discipline).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import driftscope
from driftscope.core.config import settings
from driftscope.core.types import DrawRecord
from driftscope.ingestion.beacon_streams import load_beacon_csv
from driftscope.ingestion.lotto_scraper import load_seed_csv
from driftscope.ingestion.rng_streams import (
    AESCtrDrbgStream,
    ChaCha20Stream,
    MT19937Stream,
    Xorshift64Stream,
    draws_from_stream,
)
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.k4_mmd import mmd_uniform_detector
from driftscope.methodology.multiple_testing import correct_family_b
from driftscope.pipeline import family_b_per_number_pvalues
from driftscope.reporting.information_theory import information_detector

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_DEFAULT_FAVOR = (7, 0.15)  # marginal defect: number 7 over-represented in 15% of draws
_DEFAULT_PERIOD = 50  # period-truncation defect: a 50-draw cycle repeated (frozen frequencies)

#: Real public randomness beacons (label, cached digest CSV) — see ingestion/beacon_streams.py.
#: Ethereum RANDAO is deliberately absent: auditing its mix for uniformity tests the wrong
#: hypothesis (withholding biases downstream duty assignment, not the bits) and its historical
#: state is pruned on public nodes. RANDAO is audited for manipulability separately.
_BEACON_SOURCES = (("drand", "drand_beacon.csv"), ("NIST-Beacon", "nist_beacon.csv"))


@dataclass(frozen=True)
class BenchmarkRow:
    """One row of the detection matrix: source + ground-truth label + battery results."""

    source: str
    klass: str                # "good" | "crypto" | "DEFECT" | "real"
    n: int
    family_b_reject: int      # number of rejected numbers (per-number FDR)
    family_b_size: int
    family_b_min_q: float
    mmd_reject: bool
    mmd_p: float
    cooc_reject: bool
    cooc_p: float
    it_reject: bool           # IT supplement (LZ76 sequential) — strength: period-truncation
    it_p: float

    @property
    def core_votes(self) -> int:
        """Number of INDEPENDENT core families rejecting H0 (three orthogonal axes).

        Family B (per-number binomial FDR = the MARGINAL axis), MMD (the DISTRIBUTIONAL axis),
        co-occurrence (the PAIR / joint axis). These three are mutually non-redundant in the
        spirit of the Disagreement Protocol (§6.5). IT (LZ76) = a supplement (non-voting).

        Note: in the PRNG battery the marginal family is carried by Family B (no separate
        BOCPD/h1 pillar — this is a negative-control battery on the main pool, not the full
        pipeline). In `MultiMultiAuditRow` the marginal pillar is BOCPD/h1, and Family B is a
        separate FDR gate outside the verdict — hence a different triple under the same >=2 rule.
        """
        return (
            int(self.family_b_reject > 0)
            + int(self.mmd_reject)
            + int(self.cooc_reject)
        )

    @property
    def flagged(self) -> bool:
        """FLAG only on convergence of >=2 independent core families.

        Consistent with reporting/disagreement.py and `MultiMultiAuditRow`: a single family is
        NOT a finding (a lone pillar = clear, an expected false-positive at alpha). The earlier
        naive OR — a borderline SINGLE detector falsely flipped real/crypto to FLAG, undermining
        the very specificity claim the benchmark is meant to prove. Sensitivity is preserved:
        bias(k) and period(p) light up Family B + MMD (>=2). IT = a supplement (non-voting).
        """
        return self.core_votes >= 2

    @property
    def verdict(self) -> str:
        return "FLAG" if self.flagged else "clear"


def run_battery(
    source: str,
    klass: str,
    draws: list[DrawRecord],
    *,
    alpha: float = 0.05,
    n_perm: int = 499,
) -> BenchmarkRow:
    """Negative-control battery on the main pool: Family B (binomial FDR) + MMD + co-occurrence.

    The same detectors as `pipeline.default_pillar_detectors` / `family_b_per_number_pvalues`
    — no methodology duplication.

    Family B is computed on the FULL stream (50 numbers), NOT per-regime — a parity decision:
    synthetic PRNGs have no calendar regimes, so the battery is applied IDENTICALLY to each
    source (= the reusability claim §5). The per-regime EJ headline (150) lives in
    `pipeline.run_audit`/`report.qmd §4`; both read real EJ as clear (the 1-50 pool is
    invariant across the 2014/2022 CPs). See the caveat in `report.qmd §5`.
    """
    labels, pvals = family_b_per_number_pvalues(draws)
    fb = correct_family_b(pvals, labels, alpha=alpha)
    mmd = mmd_uniform_detector(window=25, n_perm=n_perm, alpha=alpha)(draws)
    cooc = cooccurrence_detector(n_perm=n_perm, alpha=alpha)(draws)
    it = information_detector(n_perm=n_perm, alpha=alpha)(draws)
    min_q = float(fb.q_values.min()) if fb.q_values.size else 1.0
    return BenchmarkRow(
        source=source,
        klass=klass,
        n=len(draws),
        family_b_reject=fb.n_reject,
        family_b_size=len(fb.labels),
        family_b_min_q=min_q,
        mmd_reject=mmd.reject_h0,
        mmd_p=float(mmd.p_value),
        cooc_reject=cooc.reject_h0,
        cooc_p=float(cooc.p_value),
        it_reject=it.reject_h0,
        it_p=float(it.p_value),
    )


def build_sources(
    n_draws: int,
    seed: int,
    *,
    favor: tuple[int, float] = _DEFAULT_FAVOR,
    period: int = _DEFAULT_PERIOD,
    seed_csv: Path | None = None,
) -> list[tuple[str, str, list[DrawRecord]]]:
    """Sources (name, ground-truth label, draws) — a symmetric showcase matrix.

    Two good (MT19937/Xorshift64) + two crypto (ChaCha20/AES-CTR-DRBG) → expected clear;
    two DEFECT on the same MT base → expected FLAG, each via a DIFFERENT mechanism:
      - `+bias(k)`  — a marginal defect (one number over-represented; Family B/MMD),
      - `+period(p)`— period-truncation (frozen cycle frequencies; Family B over-dispersion).

    Appends real public BEACONS (drand, NIST) if their digest caches exist → expected clear.
    These extend the specificity axis beyond generators we manufacture ourselves: third-party
    entropy (threshold BLS / hardware), no seed under our control. A beacon cache is finite, so
    a source is CLAMPED to its capacity rather than raising — the actual count is reported in
    the `n` column, keeping any parity gap visible instead of aborting the whole benchmark.

    Appends real EuroJackpot if the seed CSV exists (from config by default). Real = the audit's
    honest null (expected clear, like the 1-50 negative control).
    """
    sources: list[tuple[str, str, list[DrawRecord]]] = [
        ("MT19937", "good", draws_from_stream(MT19937Stream(seed), n_draws)),
        ("Xorshift64", "good", draws_from_stream(Xorshift64Stream(seed), n_draws)),
        ("ChaCha20", "crypto", draws_from_stream(ChaCha20Stream(seed), n_draws)),
        ("AES-CTR-DRBG", "crypto", draws_from_stream(AESCtrDrbgStream(seed), n_draws)),
        (
            f"MT19937+bias({favor[0]})",
            "DEFECT",
            draws_from_stream(MT19937Stream(seed), n_draws, favor=favor),
        ),
        (
            f"MT19937+period({period})",
            "DEFECT",
            draws_from_stream(MT19937Stream(seed), n_draws, period=period),
        ),
    ]
    for label, fname in _BEACON_SOURCES:
        bpath = _ROOT / "data" / "seed" / fname
        if not bpath.exists():
            continue
        stream = load_beacon_csv(bpath, label)
        n_avail = min(n_draws, stream.capacity_draws)
        if n_avail > 0:
            sources.append((label, "beacon", draws_from_stream(stream, n_avail)))

    path = seed_csv if seed_csv is not None else _ROOT / settings.data_seed_path
    if path.exists():
        sources.append(("EuroJackpot", "real", load_seed_csv(path)))
    return sources


def run_benchmark(
    *,
    n_draws: int = 1500,
    n_perm: int = 499,
    alpha: float = 0.05,
    seed: int = 42,
    favor: tuple[int, float] = _DEFAULT_FAVOR,
    period: int = _DEFAULT_PERIOD,
    seed_csv: Path | None = None,
) -> list[BenchmarkRow]:
    """Full benchmark: battery on each source → list of detection-matrix rows."""
    return [
        run_battery(name, klass, draws, alpha=alpha, n_perm=n_perm)
        for name, klass, draws in build_sources(
            n_draws, seed, favor=favor, period=period, seed_csv=seed_csv
        )
    ]
