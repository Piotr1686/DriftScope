"""Testy honest_watchlist (W7, DoD-5).

DoD-5: warstwa adaptive zwraca None (honest null), gdy zaden wzorzec nie przeszedl
gate'u DoD-3 (FDR q<=alpha) + DoD-4 (konwergencja filarow).
"""
from __future__ import annotations

import pytest

from driftscope.adaptive.honest_watchlist import (
    WatchlistCandidate,
    build_watchlist,
    watchlist_or_message,
)
from driftscope.reporting.disagreement import classify


def _verdict(h1: bool, mmd: bool, cooc: bool):
    return classify({"h1": h1, "mmd": mmd, "cooccurrence": cooc})


def _candidate(label: str, q: float, h1=True, mmd=True, cooc=True, regime="R3"):
    return WatchlistCandidate(
        label=label, regime=regime, verdict=_verdict(h1, mmd, cooc), q_value=q
    )


# --- honest null (DoD-5 rdzen) ----------------------------------------------

def test_empty_candidates_returns_none() -> None:
    assert build_watchlist([]) is None


def test_all_fail_fdr_returns_none() -> None:
    """Wszystkie q > alpha (DoD-3 fail) → None, mimo pelnej konwergencji."""
    cands = [_candidate("a", q=0.20), _candidate("b", q=0.50)]
    assert build_watchlist(cands, alpha=0.05) is None


def test_all_fail_convergence_returns_none() -> None:
    """q<=alpha, ale 0/3 (zaden filar) i min_convergence=1 → None."""
    cands = [_candidate("a", q=0.001, h1=False, mmd=False, cooc=False)]
    assert build_watchlist(cands, min_convergence=1) is None


# --- pozytywne przejscie gate'u ---------------------------------------------

def test_primary_finding_3_of_3_passes() -> None:
    cands = [_candidate("R3:freq_shift", q=0.001)]
    wl = build_watchlist(cands)
    assert wl is not None
    assert len(wl) == 1
    assert wl[0].convergence == "3/3"
    assert wl[0].is_primary_finding
    assert wl[0].agreeing == ("h1", "mmd", "cooccurrence")


def test_clean_cell_pair_corr_1_of_3_included_by_default() -> None:
    """Czysta komorka pair_corr (1/3, tylko co-occurrence) + FDR-significant
    MUSI wejsc przy domyslnym min_convergence=1 — to realny zwalidowany sygnal
    (inne filary dowodliwie slepe, §6.5)."""
    cands = [_candidate("R3:pair_corr", q=0.01, h1=False, mmd=False, cooc=True)]
    wl = build_watchlist(cands)  # default min_convergence=1
    assert wl is not None
    assert len(wl) == 1
    assert wl[0].convergence == "1/3"
    assert wl[0].agreeing == ("cooccurrence",)
    assert not wl[0].is_primary_finding


def test_strict_convergence_excludes_single_pillar() -> None:
    """min_convergence=2 odrzuca czysta komorke 1/3 (zaostrzony gate)."""
    cands = [_candidate("R3:pair_corr", q=0.01, h1=False, mmd=False, cooc=True)]
    assert build_watchlist(cands, min_convergence=2) is None


def test_sorted_by_q_value_ascending() -> None:
    cands = [
        _candidate("weak", q=0.04),
        _candidate("strong", q=0.0001),
        _candidate("mid", q=0.01),
    ]
    wl = build_watchlist(cands)
    assert wl is not None
    assert [e.label for e in wl] == ["strong", "mid", "weak"]


def test_mixed_only_qualifying_returned() -> None:
    cands = [
        _candidate("pass", q=0.02),
        _candidate("fail_fdr", q=0.30),
        _candidate("fail_conv", q=0.01, h1=False, mmd=False, cooc=False),
    ]
    wl = build_watchlist(cands)
    assert wl is not None
    assert [e.label for e in wl] == ["pass"]


# --- walidacja + message ----------------------------------------------------

def test_negative_min_convergence_raises() -> None:
    with pytest.raises(ValueError, match="min_convergence"):
        build_watchlist([_candidate("a", q=0.01)], min_convergence=-1)


def test_message_honest_null() -> None:
    wl, msg = watchlist_or_message([_candidate("a", q=0.5)])
    assert wl is None
    assert "Honest null" in msg
    assert "Brak watchlisty" in msg


def test_message_populated() -> None:
    wl, msg = watchlist_or_message([_candidate("a", q=0.001)])
    assert wl is not None
    assert "przeszlo gate" in msg
    assert "1 primary" in msg
