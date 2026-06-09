"""Generyczna pula (Multi Multi 20-z-80, gra 2) — loader CSV + wyprowadzanie pool/k.

Reusability frameworka poza EuroJackpot opiera sie na dwoch niezmiennikach:
  1. `load_generic_seed_csv` wczytuje dowolny CSV `draw_date + n1..nK` → DrawRecord.generic
     niosacy `pool_size` (agnostyczny co do liczby kolumn liczb).
  2. Detektory wyprowadzaja pule/k z rekordow (`draws[0].pool_size` / `main_numbers`),
     a nie z twardych stalych — wiec na pool=80 raportuja 80 liczb, nie 50.

Ciezka kalibracja FPR (200 trials) zyje w `scripts/calibrate_mmd_pool.py` (artifact, NIE
unit test). Tu tylko szybkie niezmienniki strukturalne + semantyka werdyktu runnera MM
(Disagreement >=2/3 po filarach rdzeniowych, nie naiwny OR).
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
_MM_N = 16827  # liczba losowan w seed CSV (1996-2026)


# ---------------------------------------------------------------------------
# load_generic_seed_csv — realny MM seed
# ---------------------------------------------------------------------------

def test_load_mm_shape() -> None:
    """Realny MM CSV → 16827 rekordow generycznych, pool=80, k=20."""
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    assert len(draws) == _MM_N
    assert all(d.pool_size == _MM_POOL for d in draws)
    assert all(len(d.main_numbers) == _MM_K for d in draws)
    assert draws[0].numbers is not None  # ksztalt generyczny, nie EJ


def test_load_mm_numbers_in_range() -> None:
    """Wszystkie liczby w 1..80 (walidacja DrawRecord._validate_shape nie odrzucila)."""
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    for d in draws[:200]:  # probka — pelny zbior waliduje sam loader przy konstrukcji
        assert all(1 <= v <= _MM_POOL for v in d.main_numbers)


def test_load_mm_recent_window_chronological() -> None:
    """Ogon strumienia (okno runnera = ostatnie 2000) jest chronologiczny.

    Realny MM seed ma 2 historyczne inwersje dat (2010) — globalnie NIE jest w pelni
    posortowany — ale okno runnera (`draws[-2000:]`) jest czyste, a `run_multimulti_audit`
    i tak sortuje defensywnie (BOCPD sekwencyjny). Tu zabezpieczamy realny niezmiennik:
    nie wprowadzac w przyszlosci nieuporzadkowania do najnowszych losowan.
    """
    draws = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    tail = [d.draw_date for d in draws[-2000:]]
    assert tail == sorted(tail)


def test_load_mm_deterministic() -> None:
    """Dwa odczyty daja identyczne rekordy (DoD-6)."""
    a = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    b = load_generic_seed_csv(_MM_CSV, pool_size=_MM_POOL)
    assert [d.main_numbers for d in a] == [d.main_numbers for d in b]
    assert [d.draw_date for d in a] == [d.draw_date for d in b]


# ---------------------------------------------------------------------------
# Loader agnostyczny co do liczby kolumn (gra 3+)
# ---------------------------------------------------------------------------

def test_load_generic_arbitrary_pool(tmp_path: Path) -> None:
    """Loader dziala dla dowolnego k/pool (np. mini-gra 3-z-10), nie tylko MM 20/80."""
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
# Detektory wyprowadzaja pule z rekordow (nie twarde 50)
# ---------------------------------------------------------------------------

def test_family_b_derives_pool_from_records() -> None:
    """family_b_per_number_pvalues raportuje pool=80 liczb dla rekordow generycznych."""
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
# Werdykt runnera MM = Disagreement po 3 filarach rdzeniowych (NIE naiwny OR)
# ---------------------------------------------------------------------------

def _mm_row(
    *,
    bocpd: bool = False,
    mmd: bool = False,
    cooc: bool = False,
    it: bool = False,
    family_b_reject: int = 0,
) -> MultiMultiAuditRow:
    """Syntetyczny wiersz audytu MM z zadanymi flagami detektorow (zero obliczen)."""
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
    """Regresja na pierwotny bug: samotny MMD (1/3) = clear, NIE FLAG (OR klamal)."""
    row = _mm_row(mmd=True)
    assert row.core_fraction == "1/3"
    assert row.verdict == "clear"
    assert not row.flagged


def test_mm_verdict_zero_pillars_clear() -> None:
    """0/3 = clear (honest null bez zadnego rejecta)."""
    row = _mm_row()
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"


def test_mm_verdict_two_pillars_flag() -> None:
    """Konwergencja 2/3 (BOCPD+MMD) = FLAG."""
    row = _mm_row(bocpd=True, mmd=True)
    assert row.core_fraction == "2/3"
    assert row.verdict == "FLAG"
    assert row.flagged


def test_mm_verdict_three_pillars_flag() -> None:
    """Pelna konwergencja 3/3 = FLAG (fully convergent signal)."""
    row = _mm_row(bocpd=True, mmd=True, cooc=True)
    assert row.core_fraction == "3/3"
    assert row.verdict == "FLAG"
    assert row.disagreement.is_primary_finding


def test_mm_verdict_it_supplement_outside_verdict() -> None:
    """IT (suplement, nie filar) sam NIE przewraca werdyktu — core 0/3 = clear."""
    row = _mm_row(it=True)
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"


def test_mm_verdict_family_b_outside_verdict() -> None:
    """Family B (osobna bramka FDR) sama NIE przewraca werdyktu — core 0/3 = clear."""
    row = _mm_row(family_b_reject=3)
    assert row.core_fraction == "0/3"
    assert row.verdict == "clear"
