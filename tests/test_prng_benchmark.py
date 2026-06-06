"""Testy benchmarku PRNG (reporting/prng_benchmark.py, wow Opcja α).

Walidacja KONTRAKTU wow: framework zapala sie na defekcie (sensitivity) i milczy na
good/crypto (specificity). Maly n_perm/n_draws + bez seed CSV (czysto syntetyczne).
"""
from pathlib import Path

from driftscope.ingestion.rng_streams import MT19937Stream, draws_from_stream
from driftscope.reporting.prng_benchmark import run_battery, run_benchmark


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
