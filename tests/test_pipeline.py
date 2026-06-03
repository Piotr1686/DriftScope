"""End-to-end pipeline (W7) — orkiestracja pos/neg control + honest watchlist gate.

Logika orkiestracji testowana deterministycznie przez wstrzykiwane filary (stuby).
Zachowanie realnych detektorow jest juz pokryte testami per-modul (FPR/power);
tu sprawdzamy SPIECIE: Disagreement → Family B FDR → build_watchlist, oraz przebieg
na realnym seed CSV (DoD-1 positive/negative control).
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.pipeline import (
    AuditReport,
    bocpd_detector,
    family_b_per_number_pvalues,
    run_audit,
)

_SEED_CSV = Path(__file__).parent.parent / "data" / "seed" / "eurojackpot_history.csv"


# ---------------------------------------------------------------------------
# Helpery
# ---------------------------------------------------------------------------

def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2014, 1, 3),
) -> list[DrawRecord]:
    """n DrawRecord z losowymi euronumerami z euron_pool (wzorzec z test_h1_invariants)."""
    rng = np.random.default_rng(seed)
    draws = []
    for i in range(n):
        main = sorted(int(x) for x in rng.choice(range(1, 51), 5, replace=False))
        euron = sorted(int(x) for x in rng.choice(euron_pool, 2, replace=False))
        draws.append(
            DrawRecord(
                draw_date=start_date + timedelta(weeks=i),
                main_1=main[0], main_2=main[1], main_3=main[2],
                main_4=main[3], main_5=main[4],
                euron_1=euron[0], euron_2=euron[1],
            )
        )
    return draws


def _const_detector(reject: bool) -> Detector:
    """Stub filaru o ustalonym werdykcie (deterministyczny test orkiestracji)."""
    def detector(draws: list[DrawRecord]) -> TestResult:
        return TestResult(
            test_name="stub",
            statistic=0.0,
            p_value=0.0 if reject else 1.0,
            reject_h0=reject,
        )
    return detector


def _all_quiet() -> dict[str, Detector]:
    return {"h1": _const_detector(False), "mmd": _const_detector(False),
            "cooccurrence": _const_detector(False)}


def _all_reject() -> dict[str, Detector]:
    return {"h1": _const_detector(True), "mmd": _const_detector(True),
            "cooccurrence": _const_detector(True)}


# ---------------------------------------------------------------------------
# bocpd_detector — filar H1 (decyzja gating)
# ---------------------------------------------------------------------------

def test_bocpd_detector_detects_euron_pool_change() -> None:
    """Filar H1 (BOCPD euron) wykrywa wszczepiona zmiane puli — positive control."""
    pre = _make_draws(list(range(1, 9)), 200, seed=10, start_date=date(2014, 1, 3))
    post = _make_draws(list(range(8, 13)), 200, seed=11,
                       start_date=pre[-1].draw_date + timedelta(weeks=1))
    detector = bocpd_detector(field="euron")
    assert detector(pre + post).reject_h0 is True


def test_bocpd_detector_main_quiet_on_uniform() -> None:
    """Filar H1 (BOCPD main) na uniform = negative control (brak CP)."""
    draws = generate_uniform_draws(400, "R3", np.random.default_rng(1))
    assert bocpd_detector(field="main")(draws).reject_h0 is False


# ---------------------------------------------------------------------------
# Family B — per-number exact binomial
# ---------------------------------------------------------------------------

def test_family_b_uniform_no_rejections() -> None:
    """Pula glowna ~uniform → 50 p-values, brak liczby istotnej (Family B clean)."""
    draws = generate_uniform_draws(400, "R2", np.random.default_rng(7))
    labels, pvals = family_b_per_number_pvalues(draws)
    assert len(labels) == 50
    assert pvals.shape == (50,)
    assert ((pvals >= 0.0) & (pvals <= 1.0)).all()


def test_family_b_flags_over_represented_number() -> None:
    """Liczba obecna w KAZDYM losowaniu → jej exact-binomial p ≈ 0 (sygnal marginalny)."""
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(3))
    # Wymus liczbe 7 w kazdym losowaniu (nadreprezentacja marginalna).
    forced = [d.model_copy(update={"main_1": 7}) for d in draws]
    _labels, pvals = family_b_per_number_pvalues(forced)
    assert pvals[6] < 1e-6  # number_7 silnie nadreprezentowana


# ---------------------------------------------------------------------------
# run_audit — orkiestracja (deterministyczna, wstrzykniete filary)
# ---------------------------------------------------------------------------

def test_run_audit_negative_control_honest_null() -> None:
    """Neg. control 0/3 + uniform main → Family B nic nie odrzuca → watchlist None."""
    draws = generate_uniform_draws(400, "R3", np.random.default_rng(5))
    report = run_audit(draws, pillar_detectors=_all_quiet())

    assert isinstance(report, AuditReport)
    assert report.verdict.fraction == "0/3"
    assert report.family_b.n_reject == 0
    assert report.watchlist is None
    assert "honest null" in report.watchlist_message.lower()
    assert report.family_b_size == 50
    assert "POSITIVE CONTROL" in report.summary()


def test_run_audit_watchlist_gate_passes_on_strong_signal() -> None:
    """3/3 + liczba w kazdym losowaniu (Family B reject) → watchlist NIE-None."""
    draws = generate_uniform_draws(300, "R2", np.random.default_rng(9))
    forced = [d.model_copy(update={"main_1": 7}) for d in draws]
    report = run_audit(forced, pillar_detectors=_all_reject())

    assert report.verdict.fraction == "3/3"
    assert report.family_b.n_reject >= 1
    assert report.watchlist is not None
    assert any("number_7" in e.label for e in report.watchlist)
    assert all(e.q_value <= 0.05 for e in report.watchlist)


def test_run_audit_convergence_gate_blocks_when_no_pillar() -> None:
    """Family B moze odrzucac, ale 0/3 konwergencji → watchlist None (DoD-4 gate)."""
    draws = generate_uniform_draws(300, "R2", np.random.default_rng(11))
    forced = [d.model_copy(update={"main_1": 7}) for d in draws]
    report = run_audit(forced, pillar_detectors=_all_quiet())

    assert report.family_b.n_reject >= 1     # DoD-3 zapala
    assert report.verdict.fraction == "0/3"  # DoD-4 nie
    assert report.watchlist is None          # gate wymaga OBU


# ---------------------------------------------------------------------------
# run_audit — realny seed CSV (DoD-1 positive/negative control, money test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_run_audit_on_real_eurojackpot() -> None:
    """End-to-end na 958 realnych losowaniach: pos control wykrywa 2014/2022,
    neg control (main) czysty → honest null watchlist. Szybkie detektory (n_perm=99)."""
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    report = run_audit(draws, n_perm=99)

    # Positive control: euron BOCPD odrzuca i pokrywa oba ground-truth CP.
    assert report.positive_control.reject_h0 is True
    cp_dates = report.positive_control.metadata["top_changepoint_dates"]
    years = {d[:4] for d in cp_dates}
    assert "2014" in years
    assert "2022" in years

    # Negative control: Family B na realnej puli glownej nic nie odrzuca → honest null.
    assert report.family_b_size == 50
    assert report.watchlist is None

    # Raport jest dobrze uformowany.
    assert "POSITIVE CONTROL" in report.summary()
    assert "NEGATIVE CONTROL" in report.summary()
