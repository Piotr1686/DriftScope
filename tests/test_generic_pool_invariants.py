"""Generic pool (Multi Multi 20-of-80, game 2) — CSV loader + pool/k derivation.

The framework's reusability beyond EuroJackpot rests on two invariants:
  1. `load_generic_seed_csv` loads any CSV `draw_date + n1..nK` → DrawRecord.generic
     carrying `pool_size` (agnostic to the number of number columns).
  2. Detectors derive the pool/k from the records (`draws[0].pool_size` / `main_numbers`),
     not from hard constants — so on pool=80 they report 80 numbers, not 50.

The heavy FPR calibration (200 trials) lives in `scripts/calibrate_mmd_pool.py` (artifact,
NOT a unit test). Here only fast structural invariants + the MM runner verdict semantics
(Disagreement >=2/3 over the core pillars, not a naive OR).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np

from driftscope.core.types import DrawRecord
from driftscope.ingestion.lotto_scraper import load_generic_seed_csv
from driftscope.pipeline import family_b_per_number_pvalues
from driftscope.reporting.multimulti_audit import MultiMultiAuditRow
from driftscope.reporting.prng_benchmark import BenchmarkRow

_MM_CSV = Path(__file__).parent.parent / "data" / "seed" / "multimulti_history.csv"
_MM_POOL = 80
_MM_K = 20
_MM_N = 16827  # number of draws in the seed CSV (1996-2026)


# ---------------------------------------------------------------------------
# load_generic_seed_csv — real MM seed
# ---------------------------------------------------------------------------

def test_load_mm_shape() -> None:
    """Real MM CSV → 16827 generic records, pool=80, k=20."""
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    assert len(draws) == _MM_N
    assert all(d.pool_size == _MM_POOL for d in draws)
    assert all(len(d.main_numbers) == _MM_K for d in draws)
    assert draws[0].numbers is not None  # generic shape, not EJ


def test_load_mm_numbers_in_range() -> None:
    """All numbers in 1..80 (DrawRecord._validate_shape did not reject)."""
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    for d in draws[:200]:  # sample — the full set is validated by the loader at construction
        assert all(1 <= v <= _MM_POOL for v in d.main_numbers)


def test_load_mm_recent_window_chronological() -> None:
    """The stream tail (runner window = last 2000) is chronological.

    The real MM seed has 2 historical date inversions (2010) — globally it is NOT fully
    sorted — but the runner window (`draws[-2000:]`) is clean, and `run_multimulti_audit`
    sorts defensively anyway (sequential BOCPD). Here we guard the real invariant: do not
    introduce disorder into the most recent draws in the future.
    """
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    tail = [d.draw_date for d in draws[-2000:]]
    assert tail == sorted(tail)


def test_load_mm_deterministic() -> None:
    """Two reads yield identical records (DoD-6)."""
    a = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    b = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    assert [d.main_numbers for d in a] == [d.main_numbers for d in b]
    assert [d.draw_date for d in a] == [d.draw_date for d in b]


# ---------------------------------------------------------------------------
# Loader agnostic to the number of columns (game 3+)
# ---------------------------------------------------------------------------

def test_load_generic_arbitrary_pool(tmp_path: Path) -> None:
    """Loader works for any k/pool (e.g. a mini 3-of-10 game), not only MM 20/80."""
    csv = tmp_path / "mini.csv"
    csv.write_text(
        "draw_date,a,b,c\n2020-01-01,1,5,10\n2020-01-02,2,3,9\n",
        encoding="utf-8",
    )
    draws = load_generic_seed_csv(csv, pool_size=10)
    assert len(draws) == 2
    assert draws[0].pool_size == 10
    assert draws[0].main_numbers == [1, 5, 10]
    assert draws[1].draw_date == date(2020, 1, 2)


# ---------------------------------------------------------------------------
# Detectors derive the pool from the records (not a hard 50)
# ---------------------------------------------------------------------------

def test_family_b_derives_pool_from_records() -> None:
    """family_b_per_number_pvalues reports pool=80 numbers for generic records."""
    rng = np.random.default_rng(0)
    draws = [
        DrawRecord.generic(
            draw_date=date(2022, 4, 1),
            numbers=sorted(int(x) for x in rng.choice(80, size=20, replace=False) + 1),
            pool_size=80,
        )
        for _ in range(50)
    ]
    labels, pvals = family_b_per_number_pvalues(draws)
    assert len(labels) == 80
    assert pvals.shape == (80,)
    assert labels[0] == "number_1"
    assert labels[-1] == "number_80"


# ---------------------------------------------------------------------------
# MM runner verdict = Disagreement over the 3 core pillars (NOT a naive OR)
# ---------------------------------------------------------------------------

def _mm_row(
    *,
    bocpd: bool = False,
    mmd: bool = False,
    cooc: bool = False,
    it: bool = False,
    family_b_reject: int = 0,
) -> MultiMultiAuditRow:
    """Synthetic MM audit row with the given detector flags (zero computation)."""
    battery = BenchmarkRow(
        source="Multi Multi (20/80)",
        klass="real",
        n=2000,
        family_b_reject=family_b_reject,
        family_b_size=80,
        family_b_min_q=0.01 if family_b_reject else 1.0,
        mmd_reject=mmd,
        mmd_p=0.03 if mmd else 0.5,
        cooc_reject=cooc,
        cooc_p=0.02 if cooc else 0.5,
        it_reject=it,
        it_p=0.01 if it else 0.5,
    )
    return MultiMultiAuditRow(
        source="Multi Multi (20/80)",
        n=2000,
        window=2000,
        bocpd_reject=bocpd,
        bocpd_max_prob=0.5 if bocpd else 0.1,
        bocpd_threshold=0.34,
        battery=battery,
    )


def test_mm_verdict_lone_mmd_is_clear() -> None:
    """Regression on the original bug: a lone MMD (1/3) = clear, NOT FLAG (OR lied)."""
    row = _mm_row(mmd=True)
    assert row.core_fraction == "1/3"
    assert row.verdict == "clear"
    assert not row.flagged


def test_mm_verdict_zero_pillars_clear() -> None:
    """0/3 = clear (honest null with no rejects)."""
    row = _mm_row()
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"


def test_mm_verdict_two_pillars_flag() -> None:
    """Convergence 2/3 (BOCPD+MMD) = FLAG."""
    row = _mm_row(bocpd=True, mmd=True)
    assert row.core_fraction == "2/3"
    assert row.verdict == "FLAG"
    assert row.flagged


def test_mm_verdict_three_pillars_flag() -> None:
    """Full convergence 3/3 = FLAG (fully convergent signal)."""
    row = _mm_row(bocpd=True, mmd=True, cooc=True)
    assert row.core_fraction == "3/3"
    assert row.verdict == "FLAG"
    assert row.disagreement.is_primary_finding


def test_mm_verdict_it_supplement_outside_verdict() -> None:
    """IT (supplement, not a pillar) does NOT flip the verdict on its own — core 0/3 = clear."""
    row = _mm_row(it=True)
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"


def test_mm_verdict_family_b_outside_verdict() -> None:
    """Family B (a separate FDR gate) does NOT flip the verdict on its own — core 0/3 = clear."""
    row = _mm_row(family_b_reject=3)
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"
