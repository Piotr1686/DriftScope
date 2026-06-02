"""Testy Disagreement Protocol (W7, DoD-4).

Walidacja klasyfikacji sygnalu wg zgodnosci 3 filarow (H1 / MMD / co-occurrence)
do komorek 3/3, 2/3, 1/3, 0/3 (preregistration_v6 §6.5).
"""
from __future__ import annotations

import pytest

from driftscope.core.types import DrawRecord, TestResult
from driftscope.reporting.disagreement import (
    PILLARS,
    DisagreementVerdict,
    classify,
    classify_from_results,
    run_pillars,
)


def _verdict_dict(h1: bool, mmd: bool, cooc: bool) -> dict[str, bool]:
    return {"h1": h1, "mmd": mmd, "cooccurrence": cooc}


def _result(reject: bool, name: str = "stub") -> TestResult:
    return TestResult(
        test_name=name,
        statistic=1.0,
        p_value=0.01 if reject else 0.5,
        reject_h0=reject,
    )


def _draw() -> DrawRecord:
    return DrawRecord(
        draw_date="2024-01-05",  # type: ignore[arg-type]
        main_1=1, main_2=2, main_3=3, main_4=4, main_5=5,
        euron_1=1, euron_2=2,
    )


# --- 4 komorki protokolu ----------------------------------------------------

def test_full_convergence_3_of_3() -> None:
    """Wszystkie filary odrzucaja H0 → 3/3, primary finding."""
    v = classify(_verdict_dict(True, True, True))
    assert v.n_agree == 3
    assert v.fraction == "3/3"
    assert v.label == "fully convergent signal"
    assert v.is_primary_finding
    assert v.agreeing == ("h1", "mmd", "cooccurrence")


def test_convergent_2_of_3() -> None:
    """Dwa z trzech filarow → 2/3, NIE primary finding."""
    v = classify(_verdict_dict(True, False, True))
    assert v.n_agree == 2
    assert v.fraction == "2/3"
    assert v.label == "convergent signal"
    assert not v.is_primary_finding
    assert v.agreeing == ("h1", "cooccurrence")


def test_clean_cell_pair_corr_1_of_3() -> None:
    """Czysta komorka §6.5: pair_corr widzi WYLACZNIE co-occurrence → 1/3.

    chi²/MMD/H1 dowodliwie slepe na sygnal joint margin-preserving (marginesy
    uniform); tylko filar co-occurrence odrzuca H0.
    """
    v = classify(_verdict_dict(False, False, True))
    assert v.n_agree == 1
    assert v.fraction == "1/3"
    assert v.label == "single-pillar signal, requires DriftSim power context"
    assert v.agreeing == ("cooccurrence",)


def test_no_signal_0_of_3() -> None:
    """Zaden filar nie odrzuca → 0/3, brak sygnalu."""
    v = classify(_verdict_dict(False, False, False))
    assert v.n_agree == 0
    assert v.fraction == "0/3"
    assert v.label == "no signal"
    assert v.agreeing == ()
    assert not v.is_primary_finding


# --- walidacja wejscia ------------------------------------------------------

def test_missing_pillar_raises() -> None:
    with pytest.raises(ValueError, match="Brak werdyktow"):
        classify({"h1": True, "mmd": False})  # brak cooccurrence


def test_unknown_pillar_raises() -> None:
    with pytest.raises(ValueError, match="Nieznane filary"):
        classify({"h1": True, "mmd": False, "cooccurrence": True, "recurrence": True})


# --- z TestResult -----------------------------------------------------------

def test_classify_from_results() -> None:
    """classify_from_results wyciaga reject_h0 z TestResult kazdego filaru."""
    results = {
        "h1": _result(True, "bocpd"),
        "mmd": _result(False, "mmd"),
        "cooccurrence": _result(True, "cooccurrence"),
    }
    v = classify_from_results(results)
    assert v.n_agree == 2
    assert v.agreeing == ("h1", "cooccurrence")


# --- integracja run_pillars (reuse Detector interface) ----------------------

def test_run_pillars_runs_each_detector_on_same_stream() -> None:
    """run_pillars uruchamia detektor per filar na tym samym strumieniu."""
    draws = [_draw()]
    detectors = {
        "h1": lambda d: _result(len(d) > 0, "h1"),
        "mmd": lambda d: _result(False, "mmd"),
        "cooccurrence": lambda d: _result(True, "cooccurrence"),
    }
    results = run_pillars(draws, detectors)
    assert set(results) == set(PILLARS)
    v = classify_from_results(results)
    assert v.n_agree == 2  # h1 (niepuste) + cooccurrence


def test_run_pillars_missing_detector_raises() -> None:
    with pytest.raises(ValueError, match="Brak detektorow"):
        run_pillars([_draw()], {"h1": lambda d: _result(True)})


# --- niezmienniki -----------------------------------------------------------

def test_verdict_is_frozen() -> None:
    v = classify(_verdict_dict(True, True, True))
    assert isinstance(v, DisagreementVerdict)
    with pytest.raises(Exception):
        v.n_agree = 0  # type: ignore[misc]
