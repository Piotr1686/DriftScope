"""Specification curve analysis (W6, preregistration_v5 §4).

Sprawdza ROBUSTNOSC wyniku MMD wzgledem arbitralnych wyborow analitycznych: zamiast
jednej konfiguracji raportujemy siatke i wymagamy, by sygnal nie zalezal od pojedynczego
wyboru. Siatka (preregistration_v5 §4 — skorygowana z {100,200,400} po W4):

    window N ∈ {15, 25, 40}  ×  bandwidth ∈ {0.5×, 1×, 2×} median heuristic  =  9 punktow

**Kryterium stabilnosci (§4):** sygnal NIESTABILNY (→ nie raportowany) jesli znika w
**> 2/9** punktach (p > α). Symetrycznie: na nullu spec curve powinna byc "stabilnie
nieistotna" (≤ 2/9 falszywych odrzucen) — to zamyka walidacje FPR dla N ∈ {15, 40},
ktore v5 §4 zostawial niezwalidowane (dotad tylko N=25; zob. test_specification).

Spec curve uzywa `mmd_uniform_detector(window, bandwidth_mult)` per punkt (ten sam null
i framing co reszta MMD). Determinizm (DoD-6): kazdy detektor jest czysta funkcja `draws`.
"""
from __future__ import annotations

from dataclasses import dataclass

from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import Regime
from driftscope.methodology.k4_mmd import DEFAULT_N_PERM, mmd_uniform_detector

# Siatka §4 (preregistration_v5). Window dopasowane do realnego n (non-overlap).
SPEC_WINDOWS: tuple[int, ...] = (15, 25, 40)
SPEC_BANDWIDTH_MULTS: tuple[float, ...] = (0.5, 1.0, 2.0)
# Maks. liczba punktow nieistotnych przy ktorej sygnal nadal "stabilny" (§4: znika w >2/9).
MAX_UNSTABLE = 2
_DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class SpecPoint:
    """Jeden punkt spec curve: (window, bandwidth_mult) → p-value / decyzja."""

    window: int
    bandwidth_mult: float
    p_value: float
    reject: bool


@dataclass(frozen=True)
class SpecCurveResult:
    """Wynik spec curve (9 punktow) + ocena stabilnosci (§4)."""

    points: list[SpecPoint]
    alpha: float

    @property
    def n_points(self) -> int:
        return len(self.points)

    @property
    def n_significant(self) -> int:
        return sum(pt.reject for pt in self.points)

    @property
    def n_nonsignificant(self) -> int:
        return self.n_points - self.n_significant

    @property
    def stable(self) -> bool:
        """Sygnal stabilny: znika (p>α) w co najwyzej MAX_UNSTABLE punktach (§4)."""
        return self.n_nonsignificant <= MAX_UNSTABLE


def specification_curve(
    draws: list[DrawRecord],
    windows: tuple[int, ...] = SPEC_WINDOWS,
    bandwidth_mults: tuple[float, ...] = SPEC_BANDWIDTH_MULTS,
    n_perm: int = DEFAULT_N_PERM,
    alpha: float = _DEFAULT_ALPHA,
    ref_regime: Regime = "R2",
    base_seed: int = 20260531,
) -> SpecCurveResult:
    """Liczy spec curve MMD po siatce `windows` × `bandwidth_mults` (§4).

    Kazdy punkt = `mmd_uniform_detector(window, bandwidth_mult)` na tym samym `draws`.
    Zwraca `SpecCurveResult` z 9 (domyslnie) punktami i ocena `stable`.
    """
    points: list[SpecPoint] = []
    for window in windows:
        for bw_mult in bandwidth_mults:
            detector = mmd_uniform_detector(
                window=window,
                n_perm=n_perm,
                alpha=alpha,
                ref_regime=ref_regime,
                base_seed=base_seed,
                bandwidth_mult=bw_mult,
            )
            res = detector(draws)
            points.append(
                SpecPoint(
                    window=window,
                    bandwidth_mult=bw_mult,
                    p_value=res.p_value,
                    reject=res.reject_h0,
                )
            )
    return SpecCurveResult(points=points, alpha=alpha)
