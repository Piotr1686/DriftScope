"""End-to-end audit orchestrator (W7) — co framework ORZEKA na realnym EuroJackpot.

Spina zwalidowane komponenty DoD-1..6 w jeden przebieg na realnym strumieniu losowan:

  POSITIVE CONTROL (euron, filar temporalny/H1): `run_bocpd(draws, "euron")` wykrywa
    zmiany puli euronumerow 2014/2022 (ground truth DoD-1b).
  NEGATIVE CONTROL (main 1-50, 3 filary Disagreement): trzy NIEZALEZNE rodziny detektorow
    (H1/temporal, MMD/distributional, co-occurrence/joint) na puli glownej. Oczekiwane
    0/3 — pula glowna nie ma pre-rejestrowanego sygnalu (DoD-1 negative control).
  HONEST WATCHLIST (DoD-5): Family B FDR (per-number exact binomial) + konwergencja →
    `build_watchlist`. Na czystym neg. control → **None** (honest null, nie pusta lista).

**Decyzja projektowa (gating "H1 family → 1 werdykt filaru"):** filar `h1` reprezentuje
BOCPD per-stream (`bocpd_detector`). Uzasadnienie: BOCPD jest skalibrowany per-pole
(FPR≈0.05, preregistration_v6 §0/§2), ma zwalidowany positive/negative control i jest
detektorem hooka W8. ADF/KPSS/Welch/ACF operuja na pochodnych szeregach SKALARNYCH
(euron_mean, ...) i pelnia role DIAGNOSTYCZNA, nie glosujacego filaru — OR-agregacja
skorelowanych pod-testow H1 zawyzylaby FPR filaru. DoD-4 pozostaje 3/3.

**Granularnosc (uczciwe odwzorowanie sygnalu na realnych danych):** MMD i co-occurrence
czytaja pule GLOWNA (1-50, niezmienna przez cala historie); realny sygnal EuroJackpot
(zmiana puli) jest w EURON. Dlatego pelny 3-filarowy Disagreement aplikuje sie do puli
glownej jako NEGATIVE CONTROL, a euron jest pokryty osobno przez filar temporalny (BOCPD,
positive control). Framework potwierdza znany sygnal (euron) i NIE halucynuje sygnalu tam,
gdzie go nie ma (main — 3 niezalezne rodziny zgodnie 0/3).

**Family B (czesciowe domkniecie licznika §5):** rdzen = 50 per-number exact-binomial
p-values (pre-rejestrowane §5 Family B; count_k ~ Binomial(n, 5/50) pod uniform). Rozmiar
rodziny dla tego przebiegu jest KONKRETNY (`AuditReport.family_b_size`), nie referencyjny
450 (ktory zakladal 3 rezimy × 3 testy). Pelne domkniecie (gap GoF §5b per-liczba +
co-occurrence pary jako dodatkowi czlonkowie rodziny) — przy regime-split (regime_split.py
to wciaz stub) i pelnym sweepie raportowym.

Modul orkiestruje gotowe, niezaleznie zwalidowane komponenty — sam nie wprowadza nowych
decyzji metodologicznych (NIE podlega dyscyplinie prereg §0).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.stats import binomtest  # type: ignore[import-untyped]

from driftscope.adaptive.honest_watchlist import (
    WatchlistCandidate,
    WatchlistEntry,
    watchlist_or_message,
)
from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.h1_classical import run_bocpd
from driftscope.methodology.k4_mmd import mmd_uniform_detector
from driftscope.methodology.multiple_testing import FDRResult, correct_family_b
from driftscope.reporting.disagreement import (
    DisagreementVerdict,
    classify_from_results,
    run_pillars,
)

_MAIN_POOL_SIZE = 50
_P_NUMBER_PRESENT = 5.0 / 50.0  # P(liczba k w losowaniu) = 5/50 pod uniform (symetria)
_DEFAULT_ALPHA = 0.05
_DEFAULT_N_PERM = 999


# ---------------------------------------------------------------------------
# Filar H1 — BOCPD jako reprezentant per-stream (decyzja gating)
# ---------------------------------------------------------------------------

def bocpd_detector(
    field: Literal["main", "euron"] = "euron",
    *,
    alpha_unused: float = _DEFAULT_ALPHA,  # zachowanie sygnatury; prog BOCPD jest per-pole
) -> Detector:
    """Fabryka detektora H1 = BOCPD na zadanym polu (czysta funkcja `draws`, DoD-6).

    `run_bocpd` zwraca `reject_h0` wg per-pole progu skalibrowanego na FPR≈0.05
    (preregistration_v6 §2). To reprezentant filaru `h1` w Disagreement Protocol —
    zob. docstring modulu (decyzja gating). `alpha_unused` istnieje dla spojnosci
    sygnatury z innymi fabrykami; prog BOCPD nie jest parametrem alpha.
    """
    def detector(draws: list[DrawRecord]) -> TestResult:
        return run_bocpd(draws, field=field)

    return detector


def default_pillar_detectors(
    *,
    alpha: float = _DEFAULT_ALPHA,
    n_perm: int = _DEFAULT_N_PERM,
) -> dict[str, Detector]:
    """Trzy filary Disagreement na puli GLOWNEJ (negative control na realnych danych).

    - `h1`           — BOCPD(field="main") (filar temporalny; reprezentant H1).
    - `mmd`          — MMD² okna obserwacji vs uniform reference (window=25, §3/v6).
    - `cooccurrence` — max-pair, curveball null (§5c).

    window=25 (nie §3 oryginalne 200): na pelnym strumieniu ~958 daje ~38 okien
    non-overlap (robustna kalibracja); 200 → tylko ~4 okna (preregistration_v4 §3,
    korekta real-data). Wszystkie czytaja pule glowna — niezmienna przez cala historie,
    wiec sluza jako negative control niezaleznie od rezimu.
    """
    return {
        "h1": bocpd_detector(field="main"),
        "mmd": mmd_uniform_detector(window=25, n_perm=n_perm, alpha=alpha),
        "cooccurrence": cooccurrence_detector(n_perm=n_perm, alpha=alpha),
    }


# ---------------------------------------------------------------------------
# Family B — per-number exact binomial (pre-rejestrowane §5)
# ---------------------------------------------------------------------------

def family_b_per_number_pvalues(
    draws: list[DrawRecord],
) -> tuple[list[str], npt.NDArray[np.float64]]:
    """Per-number exact-binomial p-values dla puli glownej (Family B, §5).

    Dla kazdej liczby k ∈ 1..50: count_k = #{losowania zawierajace k}. Pod uniform
    P(k w losowaniu) = 5/50, wiec count_k ~ Binomial(n, 5/50). Dwustronny exact test
    per liczba → 50 p-values (wejscie do FDR Family B, Benjamini-Yekutieli).

    Returns: (labels ["number_1".."number_50"], p_values (50,)).
    """
    n = len(draws)
    counts = np.zeros(_MAIN_POOL_SIZE, dtype=np.int64)
    for d in draws:
        # Incydencja: kazda liczba liczona RAZ na losowanie (model Binomial = obecnosc,
        # nie krotnosc) — odporne na ewentualne duplikaty w obrebie losowania.
        for k in set(d.main_numbers):
            counts[k - 1] += 1
    pvals = np.array(
        [
            binomtest(
                int(counts[k]), n, _P_NUMBER_PRESENT, alternative="two-sided"
            ).pvalue
            for k in range(_MAIN_POOL_SIZE)
        ],
        dtype=float,
    )
    labels = [f"number_{k + 1}" for k in range(_MAIN_POOL_SIZE)]
    return labels, pvals


# ---------------------------------------------------------------------------
# Raport audytu
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditReport:
    """Werdykt frameworka na pojedynczym strumieniu losowan (pos + neg control + gate)."""

    positive_control: TestResult              # BOCPD euron (ground truth 2014/2022)
    negative_control: dict[str, TestResult]   # 3 filary na puli glownej
    verdict: DisagreementVerdict              # Disagreement Protocol (DoD-4) nad neg. control
    family_b: FDRResult                       # per-number FDR (DoD-3)
    watchlist: list[WatchlistEntry] | None    # DoD-5: None = honest null
    watchlist_message: str

    @property
    def family_b_size(self) -> int:
        """Konkretny rozmiar rodziny B dla tego przebiegu (zamiast referencyjnych 450)."""
        return len(self.family_b.labels)

    def summary(self) -> str:
        """Czytelne podsumowanie do raportu (report.qmd / CLI)."""
        pc = self.positive_control
        cps = list(
            zip(
                pc.metadata.get("top_changepoint_dates", []),
                pc.metadata.get("top_changepoint_probs", []),
            )
        )
        cp_str = ", ".join(f"{d} (p={p:.2f})" for d, p in cps[:3]) or "brak"
        neg = " ".join(
            f"{k}={'reject' if r.reject_h0 else 'ok'}"
            for k, r in self.negative_control.items()
        )
        wl = (
            "None (honest null)"
            if self.watchlist is None
            else f"{len(self.watchlist)} wpis(ow)"
        )
        return (
            "DriftScope audit — werdykt na strumieniu:\n"
            f"  POSITIVE CONTROL (euron/BOCPD): reject={pc.reject_h0}; "
            f"top CP: {cp_str}\n"
            f"  NEGATIVE CONTROL (main/3 filary): {self.verdict.fraction} "
            f"({self.verdict.label}); [{neg}]\n"
            f"  Family B (per-number FDR, {self.family_b.method}): "
            f"{self.family_b.n_reject}/{self.family_b_size} odrzucen\n"
            f"  WATCHLIST (DoD-5): {wl}\n"
            f"  -> {self.watchlist_message}"
        )


def run_audit(
    draws: list[DrawRecord],
    *,
    alpha: float = _DEFAULT_ALPHA,
    pillar_detectors: dict[str, Detector] | None = None,
    n_perm: int = _DEFAULT_N_PERM,
    min_convergence: int = 1,
) -> AuditReport:
    """Pelny audyt strumienia: positive + negative control + honest watchlist gate.

    1. Positive control: BOCPD(euron) — wykrycie zmian puli 2014/2022 (DoD-1b).
    2. Negative control: 3 filary Disagreement na puli glownej → klasyfikacja (DoD-4).
    3. Family B FDR: per-number exact-binomial + Benjamini-Yekutieli (DoD-3).
    4. Watchlist: kandydaci = liczby odrzucone przez Family B, opatrzcone werdyktem
       konwergencji neg. control; `build_watchlist` → None gdy zaden nie przejdzie
       gate'u (FDR q≤alpha ORAZ konwergencja ≥min_convergence). Na czystym neg. control
       Family B nie odrzuca nic → honest null (DoD-5).

    `pillar_detectors`: nadpisanie 3 filarow (testy wstrzykuja szybkie warianty);
    None → `default_pillar_detectors(alpha, n_perm)`.
    """
    positive = run_bocpd(draws, field="euron")

    detectors = (
        pillar_detectors
        if pillar_detectors is not None
        else default_pillar_detectors(alpha=alpha, n_perm=n_perm)
    )
    pillars = run_pillars(draws, detectors)
    verdict = classify_from_results(pillars)

    labels, pvals = family_b_per_number_pvalues(draws)
    family_b = correct_family_b(pvals, labels, alpha=alpha)

    # Kandydaci do watchlisty = TYLKO liczby odrzucone przez Family B (DoD-3). Kazdy
    # niesie werdykt konwergencji neg. control (DoD-4). Oba gate'y egzekwowane w
    # `watchlist_or_message`; na uniform main Family B nie odrzuca nic → brak kandydatow.
    candidates = [
        WatchlistCandidate(
            label=f"main:{lbl}",
            regime="full",
            verdict=verdict,
            q_value=float(q),
            detail="per-number exact binomial (Family B)",
        )
        for lbl, q, rej in zip(family_b.labels, family_b.q_values, family_b.reject)
        if rej
    ]
    watchlist, message = watchlist_or_message(
        candidates, alpha=alpha, min_convergence=min_convergence
    )

    return AuditReport(
        positive_control=positive,
        negative_control=pillars,
        verdict=verdict,
        family_b=family_b,
        watchlist=watchlist,
        watchlist_message=message,
    )
