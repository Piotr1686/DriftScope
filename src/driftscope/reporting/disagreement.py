"""Disagreement Protocol (W7, DoD-4) — klasyfikacja sygnalu wg zgodnosci filarow.

Kazdy wykryty sygnal (per rezim) jest klasyfikowany wg tego, ile z TRZECH
niezaleznych rodzin detektorow odrzuca H0 (preregistration_v6 §6.5):

  3/3 -> 'fully convergent signal'  (primary finding — wszystkie filary zgodne)
  2/3 -> 'convergent signal'
  1/3 -> 'single-pillar signal, requires DriftSim power context'
  0/3 -> 'no signal'

**Trzy filary (DoD-4 = 3/3, preregistration_v6 §6.5):**
- `h1`           — rodzina globalna/temporalna (ADF, KPSS, BOCPD, Welch, ACF z
                   h1_classical + recurrence §5b + permutation/serial §5). Recurrence i
                   permutation NIE sa osobnym 4. filarem — wchodza pod filar temporalny H1.
- `mmd`          — dwuprobkowy MMD² na frequency vectors (k4_mmd §3).
- `cooccurrence` — test wspolwystapien par (max-pair, curveball null §5c).

Dlaczego 3, nie 4: §6.5 dowodzi wzajemnej NIE-redundancji wlasnie tych trzech rodzin
(czysta komorka Disagreement Protocol: pair_corr widzi WYLACZNIE co-occurrence → 1/3).
Modul jest reporting-only (NIE methodology/) → nie podlega dyscyplinie prereg §0.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from driftscope.core.types import Detector, DrawRecord, TestResult

# Trzy filary DoD-4 — kolejnosc kanoniczna (stabilna dla raportow).
PILLARS: tuple[str, str, str] = ("h1", "mmd", "cooccurrence")

# Mapowanie liczby zgodnych filarow -> etykieta (preregistration_v6 §6.5).
_LABELS: dict[int, str] = {
    3: "fully convergent signal",
    2: "convergent signal",
    1: "single-pillar signal, requires DriftSim power context",
    0: "no signal",
}


@dataclass(frozen=True)
class DisagreementVerdict:
    """Werdykt Disagreement Protocol dla pojedynczego sygnalu (DoD-4)."""

    n_agree: int
    n_pillars: int
    label: str
    agreeing: tuple[str, ...]

    @property
    def fraction(self) -> str:
        """Reprezentacja '3/3', '2/3', ... do raportow."""
        return f"{self.n_agree}/{self.n_pillars}"

    @property
    def is_primary_finding(self) -> bool:
        """True tylko gdy WSZYSTKIE filary zgodne (pelna konwergencja)."""
        return self.n_agree == self.n_pillars and self.n_pillars > 0


def classify(verdicts: Mapping[str, bool]) -> DisagreementVerdict:
    """Klasyfikuje sygnal wg liczby filarow odrzucajacych H0 (DoD-4).

    `verdicts`: mapping filar -> reject_h0 (bool). Musi zawierac DOKLADNIE 3 filary
    z PILLARS (brak/nadmiar = blad — protokol jest zdefiniowany nad pelnym kompletem).
    """
    missing = set(PILLARS) - set(verdicts)
    if missing:
        raise ValueError(
            f"Brak werdyktow dla filarow: {sorted(missing)}. Wymagane wszystkie: {PILLARS}"
        )
    extra = set(verdicts) - set(PILLARS)
    if extra:
        raise ValueError(f"Nieznane filary: {sorted(extra)}. Dozwolone: {PILLARS}")

    agreeing = tuple(p for p in PILLARS if verdicts[p])
    n = len(agreeing)
    return DisagreementVerdict(
        n_agree=n,
        n_pillars=len(PILLARS),
        label=_LABELS[n],
        agreeing=agreeing,
    )


def classify_from_results(results: Mapping[str, TestResult]) -> DisagreementVerdict:
    """Jak `classify`, ale wyciaga `reject_h0` z TestResult kazdego filaru."""
    return classify({pillar: result.reject_h0 for pillar, result in results.items()})


def run_pillars(
    draws: list[DrawRecord], detectors: Mapping[str, Detector]
) -> dict[str, TestResult]:
    """Uruchamia detektor kazdego filaru na TYM SAMYM strumieniu losowan.

    `detectors`: mapping filar -> Detector (Callable[[list[DrawRecord]], TestResult],
    interfejs z driftsim.calibration). Musi pokrywac wszystkie PILLARS. Zwraca surowe
    TestResult per filar — do `classify_from_results` lub raportowania szczegolow.
    """
    missing = set(PILLARS) - set(detectors)
    if missing:
        raise ValueError(
            f"Brak detektorow dla filarow: {sorted(missing)}. Wymagane: {PILLARS}"
        )
    return {pillar: detectors[pillar](draws) for pillar in PILLARS}
