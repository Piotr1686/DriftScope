"""End-to-end audit orchestrator (W7) — co framework ORZEKA na realnym EuroJackpot.

Spina zwalidowane komponenty DoD-1..6 w jeden przebieg na realnym strumieniu losowan:

  POSITIVE CONTROL (euron, filar temporalny/H1): `run_bocpd(draws, "euron")` wykrywa
    zmiany puli euronumerow 2014/2022 (ground truth DoD-1b). FULL-STREAM — sygnal to
    przejscie MIEDZY rezimami, ciecie per-rezim by go zniszczylo (preregistration_v7 §1c).
  NEGATIVE CONTROL (main 1-50, 3 filary Disagreement): trzy NIEZALEZNE rodziny detektorow
    (H1/temporal, MMD/distributional, co-occurrence/joint) na puli glownej, liczone PER
    REZIM (R1/R2/R3) — test stacjonarnosci WEWNATRZ rezimu (H0 §1). Oczekiwane 0/3 w kazdym
    rezimie — pula glowna nie ma pre-rejestrowanego sygnalu (DoD-1 negative control).
  HONEST WATCHLIST (DoD-5): Family B FDR (per-number exact binomial) + konwergencja →
    `build_watchlist`. Na czystym neg. control → **None** (honest null, nie pusta lista).

**Decyzja projektowa (gating "H1 family → 1 werdykt filaru"):** filar `h1` reprezentuje
BOCPD per-stream (`bocpd_detector`). Uzasadnienie: BOCPD jest skalibrowany per-pole
(FPR≈0.05, preregistration_v7 §2), ma zwalidowany positive/negative control i jest
detektorem hooka W8. ADF/KPSS/Welch/ACF operuja na pochodnych szeregach SKALARNYCH
(euron_mean, ...) i pelnia role DIAGNOSTYCZNA, nie glosujacego filaru — OR-agregacja
skorelowanych pod-testow H1 zawyzylaby FPR filaru. DoD-4 pozostaje 3/3.

**Granularnosc per-rezim (preregistration_v7 §0(B)/§1c):** negative control (3 filary) i
Family B liczone OSOBNO w kazdym rezimie regul (R1/R2/R3) — H0 §1 jest pre-rejestrowana
per rezim ("stacjonarny uniform i.i.d. WEWNATRZ rezimu"). Pula glowna 1-50 jest strukturalnie
niezmienna przez wszystkie rezimy, wiec kazdy rezim to NIEZALEZNY negative control. Positive
control (euron) pozostaje full-stream (wykrywa przejscia miedzy rezimami).

**Family B (per-number, licznik ratyfikowany v7 §0(A)):** rodzina = WYLACZNIE per-number
exact-binomial p-values (count_k ~ Binomial(n, 5/50) pod uniform), 50 liczb × #niepustych
rezimow = na realnych danych **150** (zamiast referencyjnych 450 — chi²/gap/cooc to detektory
OMNIBUS, nie per-liczba, raportowane osobno jako rodziny komplementarne). Pula p-values ze
wszystkich rezimow tworzy JEDNA rodzine, korygowana raz Benjamini-Yekutieli (v7 §5).

Modul orkiestruje gotowe, niezaleznie zwalidowane komponenty — sam nie wprowadza nowych
decyzji metodologicznych (NIE podlega dyscyplinie prereg §0).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.stats import binomtest

from driftscope.adaptive.honest_watchlist import (
    WatchlistCandidate,
    WatchlistEntry,
    watchlist_or_message,
)
from driftscope.core.types import Detector, DrawRecord, TestResult
from driftscope.ingestion.regime_split import REGIME_LABELS, split_by_regime
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.h1_classical import run_bocpd
from driftscope.methodology.k4_mmd import mmd_uniform_detector
from driftscope.methodology.multiple_testing import FDRResult, correct_family_b
from driftscope.reporting.disagreement import (
    DisagreementVerdict,
    classify_from_results,
    run_pillars,
)

_MAIN_POOL_SIZE = 50  # fallback dla pustej listy; w praktyce pool czytany z draws[0].pool_size
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
    (preregistration_v7 §2). To reprezentant filaru `h1` w Disagreement Protocol —
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
    """Trzy filary Disagreement na puli GLOWNEJ (negative control, stosowane per rezim).

    - `h1`           — BOCPD(field="main") (filar temporalny; reprezentant H1).
    - `mmd`          — MMD² okna obserwacji vs uniform reference (window=25, §3/v7).
    - `cooccurrence` — max-pair, curveball null (§5c).

    window=25 (nie §3 oryginalne 200): na pelnym strumieniu non-overlap daje robustna
    kalibracje (preregistration_v4 §3, korekta real-data). UWAGA per-rezim: R1 (n=133)
    daje tylko ~5 okien MMD — granica wykonalnosci (§3 "Ograniczenie danych"); wynik R1
    raportowany z ta uwaga, ale detektor nie crashuje. Wszystkie czytaja pule glowna.
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
    # Pula/k wyprowadzone z rekordow (EJ=50/5 → P=0.10; MM=80/20 → P=0.25).
    pool = draws[0].pool_size if draws else _MAIN_POOL_SIZE
    k_drawn = len(draws[0].main_numbers) if draws else 5
    p_present = k_drawn / pool
    counts = np.zeros(pool, dtype=np.int64)
    for d in draws:
        # Incydencja: kazda liczba liczona RAZ na losowanie (model Binomial = obecnosc,
        # nie krotnosc) — odporne na ewentualne duplikaty w obrebie losowania.
        for k in set(d.main_numbers):
            counts[k - 1] += 1
    pvals = np.array(
        [
            binomtest(
                int(counts[k]), n, p_present, alternative="two-sided"
            ).pvalue
            for k in range(pool)
        ],
        dtype=float,
    )
    labels = [f"number_{k + 1}" for k in range(pool)]
    return labels, pvals


# ---------------------------------------------------------------------------
# Raport audytu
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeAudit:
    """Negative control pojedynczego rezimu regul (3 filary na puli glownej WEWNATRZ rezimu)."""

    regime: str                               # "R1" / "R2" / "R3" (prereg_v7 §1)
    n_draws: int                              # liczba losowan w rezimie
    negative_control: dict[str, TestResult]   # 3 filary Disagreement (h1/mmd/cooccurrence)
    verdict: DisagreementVerdict              # Disagreement Protocol (DoD-4) dla tego rezimu


@dataclass(frozen=True)
class AuditReport:
    """Werdykt frameworka na strumieniu: pos control (full) + neg control per-rezim + gate."""

    positive_control: TestResult              # BOCPD euron full-stream (ground truth 2014/2022)
    regime_audits: dict[str, RegimeAudit]     # neg control per rezim (R1/R2/R3; tylko niepuste)
    family_b: FDRResult                       # per-number FDR pooled nad rezimami (DoD-3)
    watchlist: list[WatchlistEntry] | None    # DoD-5: None = honest null
    watchlist_message: str

    @property
    def family_b_size(self) -> int:
        """Konkretny rozmiar rodziny B (50 × #niepustych rezimow; realnie 150)."""
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
        lines = [
            "DriftScope audit — stream verdict:",
            f"  POSITIVE CONTROL (euron/BOCPD, full-stream): reject={pc.reject_h0}; "
            f"top change-points: {cp_str}",
            "  NEGATIVE CONTROL (main 1-50 / 3 pillars, per regime):",
        ]
        for label in REGIME_LABELS:
            ra = self.regime_audits.get(label)
            if ra is None:
                continue
            neg = " ".join(
                f"{k}={'reject' if r.reject_h0 else 'ok'}"
                for k, r in ra.negative_control.items()
            )
            lines.append(
                f"    {label} (n={ra.n_draws}): {ra.verdict.fraction} "
                f"({ra.verdict.label}); [{neg}]"
            )
        wl = (
            "None (honest null)"
            if self.watchlist is None
            else f"{len(self.watchlist)} entry(ies)"
        )
        lines.append(
            f"  Family B (per-number FDR, {self.family_b.method}): "
            f"{self.family_b.n_reject}/{self.family_b_size} rejected"
        )
        lines.append(f"  WATCHLIST (DoD-5): {wl}")
        lines.append(f"  -> {self.watchlist_message}")
        return "\n".join(lines)


def run_audit(
    draws: list[DrawRecord],
    *,
    alpha: float = _DEFAULT_ALPHA,
    pillar_detectors: dict[str, Detector] | None = None,
    n_perm: int = _DEFAULT_N_PERM,
    min_convergence: int = 1,
) -> AuditReport:
    """Pelny audyt strumienia: positive control (full) + per-rezim neg control + honest gate.

    1. Positive control: BOCPD(euron) FULL-STREAM — wykrycie zmian puli 2014/2022 (DoD-1b).
    2. Negative control PER REZIM: dla kazdego niepustego rezimu (R1/R2/R3) 3 filary
       Disagreement na puli glownej → klasyfikacja (DoD-4). Reszta rezimow pominieta.
    3. Family B FDR: per-number exact-binomial per rezim, POOLED w jedna rodzine (labels
       "Rk:number_j") + Benjamini-Yekutieli raz nad cala rodzina (DoD-3, v7 §5).
    4. Watchlist: kandydaci = liczby odrzucone przez Family B, kazda z werdyktem konwergencji
       SWOJEGO rezimu; `build_watchlist` → None gdy zaden nie przejdzie gate'u (FDR q≤alpha
       ORAZ konwergencja ≥min_convergence). Na czystym neg. control → honest null (DoD-5).

    `pillar_detectors`: nadpisanie 3 filarow (testy wstrzykuja szybkie warianty);
    stosowane do KAZDEGO rezimu. None → `default_pillar_detectors(alpha, n_perm)`.
    """
    positive = run_bocpd(draws, field="euron")

    detectors = (
        pillar_detectors
        if pillar_detectors is not None
        else default_pillar_detectors(alpha=alpha, n_perm=n_perm)
    )

    regimes = split_by_regime(draws)
    regime_audits: dict[str, RegimeAudit] = {}
    pooled_labels: list[str] = []
    pooled_pvals: list[npt.NDArray[np.float64]] = []

    for label in REGIME_LABELS:
        regime_draws = regimes.get(label, [])
        if not regime_draws:  # rezim bez losowan — pominiety (np. niepelny strumien)
            continue
        pillars = run_pillars(regime_draws, detectors)
        regime_audits[label] = RegimeAudit(
            regime=label,
            n_draws=len(regime_draws),
            negative_control=pillars,
            verdict=classify_from_results(pillars),
        )
        lbls, pvals = family_b_per_number_pvalues(regime_draws)
        pooled_labels.extend(f"{label}:{lbl}" for lbl in lbls)
        pooled_pvals.append(pvals)

    pvals_all = (
        np.concatenate(pooled_pvals) if pooled_pvals else np.array([], dtype=float)
    )
    family_b = correct_family_b(pvals_all, pooled_labels, alpha=alpha)

    # Kandydaci do watchlisty = liczby odrzucone przez Family B (DoD-3). Kazdy niesie werdykt
    # konwergencji SWOJEGO rezimu (DoD-4; label = "Rk:number_j"). Oba gate'y egzekwowane w
    # `watchlist_or_message`; na uniform main Family B nie odrzuca nic → brak kandydatow.
    candidates = [
        WatchlistCandidate(
            label=lbl,
            regime=lbl.split(":", 1)[0],
            verdict=regime_audits[lbl.split(":", 1)[0]].verdict,
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
        regime_audits=regime_audits,
        family_b=family_b,
        watchlist=watchlist,
        watchlist_message=message,
    )
