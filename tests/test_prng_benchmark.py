"""Testy benchmarku PRNG (reporting/prng_benchmark.py, wow Opcja α).

Walidacja KONTRAKTU wow: framework zapala sie na defekcie (sensitivity) i milczy na
good/crypto (specificity). Maly n_perm/n_draws + bez seed CSV (czysto syntetyczne).
"""
from pathlib import Path

from driftscope.ingestion.rng_streams import MT19937Stream, draws_from_stream
from driftscope.reporting.prng_benchmark import BenchmarkRow, run_battery, run_benchmark


def _row(
    *,
    family_b_reject: int = 0,
    mmd_reject: bool = False,
    cooc_reject: bool = False,
    it_reject: bool = False,
) -> BenchmarkRow:
    """BenchmarkRow z wybranymi rodzinami zapalonymi (reszta pol = neutralna)."""
    return BenchmarkRow(
        source="synthetic",
        klass="DEFECT",
        n=100,
        family_b_reject=family_b_reject,
        family_b_size=50,
        family_b_min_q=0.0 if family_b_reject else 1.0,
        mmd_reject=mmd_reject,
        mmd_p=0.001 if mmd_reject else 0.5,
        cooc_reject=cooc_reject,
        cooc_p=0.001 if cooc_reject else 0.5,
        it_reject=it_reject,
        it_p=0.001 if it_reject else 0.5,
    )


def test_verdict_lone_core_family_is_clear() -> None:
    """Samotna rodzina rdzeniowa (1 glos) = clear, NIE FLAG (zasada >=2, spojna z MM)."""
    for kwargs in ({"mmd_reject": True}, {"cooc_reject": True}, {"family_b_reject": 4}):
        row = _row(**kwargs)  # type: ignore[arg-type]
        assert row.core_votes == 1
        assert row.verdict == "clear"
        assert not row.flagged


def test_verdict_lone_it_is_clear_non_voting() -> None:
    """IT (suplement) sam NIE glosuje — core_votes=0 → clear."""
    row = _row(it_reject=True)
    assert row.core_votes == 0
    assert row.verdict == "clear"


def test_verdict_two_core_families_flag() -> None:
    """>=2 rodziny rdzeniowe (Family B + MMD, jak bias) = FLAG."""
    row = _row(family_b_reject=1, mmd_reject=True)
    assert row.core_votes == 2
    assert row.verdict == "FLAG"
    assert row.flagged


def test_verdict_three_core_families_flag() -> None:
    """Pelna konwergencja 3 rodzin (jak period-truncation) = FLAG."""
    row = _row(family_b_reject=25, mmd_reject=True, cooc_reject=True)
    assert row.core_votes == 3
    assert row.flagged


def test_defect_flagged_and_good_clear() -> None:
    """DEFECT -> FLAG (sensitivity); good/crypto -> clear (specificity)."""
    rows = run_benchmark(n_draws=600, n_perm=99, seed=1, seed_csv=None)
    by_class: dict[str, list] = {r.klass: [] for r in rows}
    for r in rows:
        by_class[r.klass].append(r)

    # Oba mechanizmy defektu obecne (bias marginalny + period-truncation).
    defect_sources = {r.source for r in by_class["DEFECT"]}
    assert any("bias" in s for s in defect_sources)
    assert any("period" in s for s in defect_sources)

    # Sensitivity: kazdy DEFECT zaplonal (oba mechanizmy).
    assert all(r.flagged for r in by_class["DEFECT"])
    # Specificity: zaden good/crypto nie zaplonal (oba krypto: ChaCha20 + AES-CTR-DRBG).
    assert all(not r.flagged for r in by_class.get("good", []))
    assert all(not r.flagged for r in by_class.get("crypto", []))

    # Suplement IT (LZ76 sekwencyjny): JEGO sila to period-truncation (struktura szeregowa),
    # slepy na bias marginalny (order-shuffle zachowuje multiset). Komplementarny do baterii.
    it_by_source = {r.source: r.it_reject for r in rows}
    assert any("period" in s and rej for s, rej in it_by_source.items()), "IT winien lapac period"
    assert not any(r.it_reject for r in by_class.get("good", []))
    assert not any(r.it_reject for r in by_class.get("crypto", []))


def test_run_benchmark_without_real_csv(tmp_path: Path) -> None:
    """Nieistniejacy seed CSV → brak wiersza 'real' (czysto syntetyczne zrodla)."""
    rows = run_benchmark(n_draws=300, n_perm=49, seed_csv=tmp_path / "nope.csv")
    assert all(r.klass != "real" for r in rows)
    assert {"good", "crypto", "DEFECT"} <= {r.klass for r in rows}


def test_run_battery_fields() -> None:
    """run_battery zwraca spojny BenchmarkRow (n, family_b_size, verdict)."""
    draws = draws_from_stream(MT19937Stream(3), 300)
    row = run_battery("MT19937", "good", draws, n_perm=49)
    assert row.n == 300
    assert row.family_b_size == 50
    assert row.verdict in {"FLAG", "clear"}
    assert 0.0 <= row.mmd_p <= 1.0 and 0.0 <= row.cooc_p <= 1.0
