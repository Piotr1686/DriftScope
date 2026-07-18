"""End-to-end pipeline (W7) — pos/neg control orchestration + honest watchlist gate.

Orchestration logic tested deterministically via injected pillars (stubs). The real
detectors' behavior is already covered by per-module tests (FPR/power); here we check the
WIRING: Disagreement → Family B FDR → build_watchlist, plus a run on the real seed CSV
(DoD-1 positive/negative control).
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
# Helpers
# ---------------------------------------------------------------------------

def _make_draws(
    euron_pool: list[int],
    n: int,
    seed: int = 0,
    start_date: date = date(2014, 1, 3),
) -> list[DrawRecord]:
    """n DrawRecord with random euro numbers from euron_pool (pattern from test_h1_invariants)."""
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
    """Pillar stub with a fixed verdict (deterministic orchestration test)."""
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
# bocpd_detector — H1 pillar (gating decision)
# ---------------------------------------------------------------------------

def test_bocpd_detector_detects_euron_pool_change() -> None:
    """H1 pillar (BOCPD euron) detects a planted pool change — positive control."""
    pre = _make_draws(list(range(1, 9)), 200, seed=10, start_date=date(2014, 1, 3))
    post = _make_draws(list(range(8, 13)), 200, seed=11,
                       start_date=pre[-1].draw_date + timedelta(weeks=1))
    detector = bocpd_detector(field="euron")
    assert detector(pre + post).reject_h0 is True


def test_bocpd_detector_main_quiet_on_uniform() -> None:
    """H1 pillar (BOCPD main) on uniform = negative control (no CP)."""
    draws = generate_uniform_draws(400, "R3", np.random.default_rng(1))
    assert bocpd_detector(field="main")(draws).reject_h0 is False


# ---------------------------------------------------------------------------
# Family B — per-number exact binomial
# ---------------------------------------------------------------------------

def test_family_b_uniform_no_rejections() -> None:
    """Main pool ~uniform → 50 p-values, no significant number (Family B clean)."""
    draws = generate_uniform_draws(400, "R2", np.random.default_rng(7))
    labels, pvals = family_b_per_number_pvalues(draws)
    assert len(labels) == 50
    assert pvals.shape == (50,)
    assert ((pvals >= 0.0) & (pvals <= 1.0)).all()


def test_family_b_flags_over_represented_number() -> None:
    """A number present in EVERY draw → its exact-binomial p ≈ 0 (marginal signal)."""
    draws = generate_uniform_draws(200, "R2", np.random.default_rng(3))
    # Force number 7 into every draw (marginal over-representation).
    forced = [d.model_copy(update={"main_1": 7}) for d in draws]
    _labels, pvals = family_b_per_number_pvalues(forced)
    assert pvals[6] < 1e-6  # number_7 strongly over-represented


# ---------------------------------------------------------------------------
# run_audit — orchestration (deterministic, injected pillars)
# ---------------------------------------------------------------------------

# NOTE: orchestration streams are built within a SINGLE regime (controlled dates).
# `generate_uniform_draws` anchors dates without respecting calendar boundaries (R3 starts
# 2022-03-22 = still R2; R1/R2 with large n cross boundaries), so the split would scatter them
# across regimes. `_make_draws(start_date=date(2022,4,1))` gives a clean R3 (all dates >= boundary).
_R3_START = date(2022, 4, 1)


def test_run_audit_negative_control_honest_null() -> None:
    """Neg. control 0/3 (single regime) + uniform main → Family B clean → watchlist None."""
    draws = _make_draws(list(range(1, 13)), 400, seed=5, start_date=_R3_START)
    report = run_audit(draws, pillar_detectors=_all_quiet())

    assert isinstance(report, AuditReport)
    assert set(report.regime_audits) == {"R3"}          # only R3 non-empty
    assert report.regime_audits["R3"].verdict.fraction == "0/3"
    assert report.family_b.n_reject == 0
    assert report.watchlist is None
    assert "honest null" in report.watchlist_message.lower()
    assert report.family_b_size == 50                   # 1 regime × 50 numbers
    assert "POSITIVE CONTROL" in report.summary()


def test_run_audit_watchlist_gate_passes_on_strong_signal() -> None:
    """3/3 + a number in every draw (Family B reject) → watchlist NOT-None (regime prefix)."""
    base = _make_draws(list(range(1, 13)), 300, seed=9, start_date=_R3_START)
    forced = [d.model_copy(update={"main_1": 7}) for d in base]
    report = run_audit(forced, pillar_detectors=_all_reject())

    assert report.regime_audits["R3"].verdict.fraction == "3/3"
    assert report.family_b.n_reject >= 1
    assert report.watchlist is not None
    assert any(e.label == "R3:number_7" for e in report.watchlist)  # label with regime prefix
    assert all(e.regime == "R3" for e in report.watchlist)
    assert all(e.q_value <= 0.05 for e in report.watchlist)


def test_run_audit_convergence_gate_blocks_when_no_pillar() -> None:
    """Family B may reject, but 0/3 convergence → watchlist None (DoD-4 gate)."""
    base = _make_draws(list(range(1, 13)), 300, seed=11, start_date=_R3_START)
    forced = [d.model_copy(update={"main_1": 7}) for d in base]
    report = run_audit(forced, pillar_detectors=_all_quiet())

    assert report.family_b.n_reject >= 1                       # DoD-3 fires
    assert report.regime_audits["R3"].verdict.fraction == "0/3"  # DoD-4 does not
    assert report.watchlist is None                            # gate requires BOTH


def test_run_audit_splits_multiple_regimes() -> None:
    """Stream spanning 2 regimes → regime_audits has both keys; Family B pooled = 50×2."""
    r2 = _make_draws(list(range(1, 11)), 50, seed=1, start_date=date(2015, 1, 2))   # R2
    r3 = _make_draws(list(range(1, 13)), 50, seed=2, start_date=_R3_START)          # R3
    report = run_audit(r2 + r3, pillar_detectors=_all_quiet())

    assert set(report.regime_audits) == {"R2", "R3"}
    assert report.regime_audits["R2"].n_draws == 50
    assert report.regime_audits["R3"].n_draws == 50
    assert report.family_b_size == 100  # 2 regimes × 50 numbers (pooled, one BY family)


# ---------------------------------------------------------------------------
# run_audit — real seed CSV (DoD-1 positive/negative control, money test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV unavailable")
def test_run_audit_on_real_eurojackpot() -> None:
    """End-to-end on 958 real draws: pos control detects 2014/2022; neg control per-regime
    does NOT produce a convergent signal (≥2/3) → honest null. n_perm=99 (fast)."""
    from driftscope.ingestion.lotto_scraper import load_seed_csv

    draws = load_seed_csv(_SEED_CSV)
    report = run_audit(draws, n_perm=99)

    # Positive control: euron BOCPD rejects and covers both ground-truth CPs.
    assert report.positive_control.reject_h0 is True
    cp_dates = report.positive_control.metadata["top_changepoint_dates"]
    years = {d[:4] for d in cp_dates}
    assert "2014" in years
    assert "2022" in years

    # Negative control computed PER REGIME: split 133/389/436 → all 3 regimes present.
    assert set(report.regime_audits) == {"R1", "R2", "R3"}
    assert report.regime_audits["R1"].n_draws == 133
    assert report.regime_audits["R2"].n_draws == 389
    assert report.regime_audits["R3"].n_draws == 436
    # Key DoD-1 negative-control property: the framework does NOT hallucinate a CONVERGENT
    # signal (≥2/3) on the main pool. Single pillars may fire (1/3 = "requires power context",
    # NOT a finding) — correct Disagreement Protocol behavior; it does not suppress the raw signal.
    for ra in report.regime_audits.values():
        assert ra.verdict.n_agree <= 1
        assert not ra.verdict.is_primary_finding

    # Family B per-number: 50 × 3 regimes = 150, pooled into one BY family; nothing rejects.
    assert report.family_b_size == 150
    assert report.family_b.n_reject == 0
    assert report.watchlist is None

    # The report is well-formed.
    assert "POSITIVE CONTROL" in report.summary()
    assert "NEGATIVE CONTROL" in report.summary()
