"""PRNG benchmark tests (reporting/prng_benchmark.py, wow Option α).

Validates the wow CONTRACT: the framework fires on a defect (sensitivity) and stays
silent on good/crypto (specificity). Small n_perm/n_draws + no seed CSV (purely synthetic).
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
    """BenchmarkRow with selected families fired (remaining fields = neutral)."""
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
    """A lone core family (1 vote) = clear, NOT FLAG (>=2 rule, consistent with MM)."""
    for kwargs in ({"mmd_reject": True}, {"cooc_reject": True}, {"family_b_reject": 4}):
        row = _row(**kwargs)  # type: ignore[arg-type]
        assert row.core_votes == 1
        assert row.verdict == "clear"
        assert not row.flagged


def test_verdict_lone_it_is_clear_non_voting() -> None:
    """IT (supplement) does NOT vote on its own — core_votes=0 → clear."""
    row = _row(it_reject=True)
    assert row.core_votes == 0
    assert row.verdict == "clear"


def test_verdict_two_core_families_flag() -> None:
    """>=2 core families (Family B + MMD, like bias) = FLAG."""
    row = _row(family_b_reject=1, mmd_reject=True)
    assert row.core_votes == 2
    assert row.verdict == "FLAG"
    assert row.flagged


def test_verdict_three_core_families_flag() -> None:
    """Full convergence of 3 families (like period-truncation) = FLAG."""
    row = _row(family_b_reject=25, mmd_reject=True, cooc_reject=True)
    assert row.core_votes == 3
    assert row.flagged


def test_defect_flagged_and_good_clear() -> None:
    """DEFECT -> FLAG (sensitivity); good/crypto -> clear (specificity)."""
    rows = run_benchmark(n_draws=600, n_perm=99, seed=1, seed_csv=None)
    by_class: dict[str, list] = {r.klass: [] for r in rows}
    for r in rows:
        by_class[r.klass].append(r)

    # Both defect mechanisms present (marginal bias + period-truncation).
    defect_sources = {r.source for r in by_class["DEFECT"]}
    assert any("bias" in s for s in defect_sources)
    assert any("period" in s for s in defect_sources)

    # Sensitivity: every DEFECT fired (both mechanisms).
    assert all(r.flagged for r in by_class["DEFECT"])
    # Specificity: no good/crypto fired (both crypto: ChaCha20 + AES-CTR-DRBG).
    assert all(not r.flagged for r in by_class.get("good", []))
    assert all(not r.flagged for r in by_class.get("crypto", []))
    # Specificity on entropy we did NOT manufacture: real published beacons (drand, NIST).
    # Skipped when the digest caches are absent (scripts/fetch_beacons.py not run).
    assert all(not r.flagged for r in by_class.get("beacon", []))

    # IT supplement (sequential LZ76): ITS strength is period-truncation (serial structure),
    # blind to marginal bias (order-shuffle preserves the multiset). Complementary to the battery.
    it_by_source = {r.source: r.it_reject for r in rows}
    assert any("period" in s and rej for s, rej in it_by_source.items()), "IT should catch period"
    assert not any(r.it_reject for r in by_class.get("good", []))
    assert not any(r.it_reject for r in by_class.get("crypto", []))


def test_run_benchmark_without_real_csv(tmp_path: Path) -> None:
    """Non-existent seed CSV → no 'real' row.

    Beacon rows are NOT affected: they load from their own committed digest caches, not from
    `seed_csv`, so they still appear here when those caches exist.
    """
    rows = run_benchmark(n_draws=300, n_perm=49, seed_csv=tmp_path / "nope.csv")
    assert all(r.klass != "real" for r in rows)
    assert {"good", "crypto", "DEFECT"} <= {r.klass for r in rows}


def test_run_battery_fields() -> None:
    """run_battery returns a coherent BenchmarkRow (n, family_b_size, verdict)."""
    draws = draws_from_stream(MT19937Stream(3), 300)
    row = run_battery("MT19937", "good", draws, n_perm=49)
    assert row.n == 300
    assert row.family_b_size == 50
    assert row.verdict in {"FLAG", "clear"}
    assert 0.0 <= row.mmd_p <= 1.0 and 0.0 <= row.cooc_p <= 1.0
