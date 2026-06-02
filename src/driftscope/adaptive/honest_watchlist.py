"""Adaptive watchlist (W7, DoD-5) — HONEST gate nad wynikami pipeline'u.

Komponent celowo minimalny i defensywny (PROJECT_BRIEF §5 Krok 10: self-value < 20%
scope). Buduje watchliste wzorcow „wartych dalszego monitorowania" WYLACZNIE z sygnalow,
ktore przeszly pelny rygor:

  1. **DoD-3 (FDR):** q-value <= alpha po korekcji multiple-testing (`multiple_testing`).
  2. **DoD-4 (konwergencja):** sygnal widziany przez >= `min_convergence` filarow
     (DisagreementVerdict z `reporting.disagreement`).

Jesli ZADEN wzorzec nie spelnia gate'u → `build_watchlist` zwraca **None** (NIE pusta liste):
honest null — „brak zwalidowanego sygnalu, brak watchlisty". To rdzen DoD-5: adaptive
warstwa milczy, gdy metodologia nie dostarczyla dowodu (zadna ekstrapolacja na sile).

**Dlaczego primary gate to FDR, a konwergencja jest PARAMETREM (`min_convergence=1`):**
czysta komorka pair_corr to **1/3** (tylko co-occurrence; chi²/MMD/H1 dowodliwie slepe —
preregistration_v6 §6.5). Twardy prog >=2/3 odrzucilby ten REALNY, zwalidowany sygnal.
Stad domyslnie wystarczy >=1 filar + przejscie FDR; caller moze zaostrzyc do >=2 lub 3.

Ten modul NIE jest predykcja liczb (pivot predykcyjny ANULOWANY — Sciezka A, audyt).
Watchlista = audytowy artefakt „te wzorce przeszly wszystkie bramki rygoru".
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from driftscope.reporting.disagreement import DisagreementVerdict

_DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class WatchlistCandidate:
    """Kandydat do watchlisty: sygnal + jego werdykty rygoru (DoD-3 + DoD-4)."""

    label: str                      # identyfikator wzorca, np. "R3:number_37:gap"
    regime: str                     # rezim, w ktorym wykryto
    verdict: DisagreementVerdict    # DoD-4: ile filarow zgodnych
    q_value: float                  # DoD-3: FDR-skorygowany q-value
    detail: str = ""                # opcjonalny opis (typ sygnalu, lokalizacja)


@dataclass(frozen=True)
class WatchlistEntry:
    """Wpis watchlisty — wzorzec, ktory PRZESZEDL gate DoD-3 + DoD-4."""

    label: str
    regime: str
    convergence: str                # DisagreementVerdict.fraction, np. "3/3"
    agreeing: tuple[str, ...]       # ktore filary zapalily
    q_value: float
    detail: str

    @property
    def is_primary_finding(self) -> bool:
        """True gdy pelna konwergencja (wszystkie filary) — najmocniejszy wpis."""
        num, _, den = self.convergence.partition("/")
        return num == den


def build_watchlist(
    candidates: Sequence[WatchlistCandidate],
    *,
    alpha: float = _DEFAULT_ALPHA,
    min_convergence: int = 1,
) -> list[WatchlistEntry] | None:
    """Zwraca watchliste zwalidowanych wzorcow albo None (honest null).

    Gate per kandydat: `q_value <= alpha` (DoD-3 FDR) ORAZ `verdict.n_agree >=
    min_convergence` (DoD-4 konwergencja). Jesli zaden nie przechodzi → **None**
    (nie pusta lista) — sygnalizuje brak zwalidowanego sygnalu (DoD-5).

    Wynik sortowany po q_value rosnaco (najmocniejszy dowod pierwszy).
    """
    if min_convergence < 0:
        raise ValueError(f"min_convergence musi byc >= 0 (jest {min_convergence})")

    qualifying = [
        c
        for c in candidates
        if c.q_value <= alpha and c.verdict.n_agree >= min_convergence
    ]
    if not qualifying:
        return None

    qualifying.sort(key=lambda c: c.q_value)
    return [
        WatchlistEntry(
            label=c.label,
            regime=c.regime,
            convergence=c.verdict.fraction,
            agreeing=c.verdict.agreeing,
            q_value=c.q_value,
            detail=c.detail,
        )
        for c in qualifying
    ]


def watchlist_or_message(
    candidates: Sequence[WatchlistCandidate],
    *,
    alpha: float = _DEFAULT_ALPHA,
    min_convergence: int = 1,
) -> tuple[list[WatchlistEntry] | None, str]:
    """Jak `build_watchlist`, ale dolacza explicit message (DoD-5: None z komunikatem)."""
    watchlist = build_watchlist(
        candidates, alpha=alpha, min_convergence=min_convergence
    )
    if watchlist is None:
        msg = (
            f"Honest null: zaden z {len(candidates)} kandydatow nie przeszedl gate "
            f"(FDR q<={alpha} ORAZ konwergencja >={min_convergence}/3). "
            "Brak watchlisty — metodologia nie dostarczyla zwalidowanego sygnalu."
        )
        return None, msg
    n_primary = sum(e.is_primary_finding for e in watchlist)
    msg = (
        f"{len(watchlist)} wzorzec(ow) przeszlo gate DoD-3+DoD-4 "
        f"({n_primary} primary 3/3). Sortowane po q-value."
    )
    return watchlist, msg
