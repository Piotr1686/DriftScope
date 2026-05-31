"""DriftSim planted signals — wstrzykiwanie znanych sygnalow w null (W2).

Plant = honest null (`null_uniform`) + kontrolowane odchylenie od stacjonarnosci
uniform na puli GLOWNEJ (1-50; frequency vector Δ⁴⁹, preregistration_v2 §3).
Euronumery i kalendarz pozostaja nullowe — sygnal jest izolowany w jednym wymiarze.

5 typow sygnalu × 4 effect sizes = 20 scenariuszy + 1 null = 21 datasetow/rezim
(× 3 rezimy = 63 unikalne; preregistration_v2 §6).

Sygnaly (preregistration_v3 §6 — wszystkie siatki PINNED):
  1. freq_shift  — p_k = 1/50 + δ      δ ∈ {0.01,0.02,0.05,0.10}
  2. autocorr    — boost recurrence ρ  ρ ∈ {0.05,0.10,0.15,0.20}
  3. trend       — p_k(t)=1/50+β·t/T   β ∈ {0.01,0.02,0.05,0.10}
  4. seasonality — kontrast Tue/Fri c  c ∈ {0.01,0.02,0.05,0.10}
                   GUARD: tylko R3; w R1/R2 degeneruje do null (§6).
  5. pair_corr   — forced-frac p        p ∈ {0.01,0.02,0.05,0.10}
                   MARGINESY ZACHOWANE (czysty sygnal joint; §6 — re-design v5).

Siatki β (trend) i c (seasonality) zostaly doprecyzowane w preregistration_v3
(§0/§6, 2026-05-30) — v2 zostawial je nie-pinowane; v3 ratyfikuje wartosci powyzej
jako rewizje czysta PRZED kalibracja W3.

Mechanizm pair_corr przeprojektowany w preregistration_v5 (W6, 2026-05-31): parametr
to teraz forced-fraction p (NIE mnoznik lift), a konstrukcja ZACHOWUJE marginesy (zob.
`_sample_pair_corr`). Stary mechanizm (lift, "force pare + 3 uniform") przeciekal do
marginesow (P(planted)=0.1+0.9·p) i dawal forced-frac 0.0008..0.0082 — ponizej progu
detekcji kazdego testu (finding W6). Nowy izoluje sygnal w wymiarze JOINT: chi²/MMD
dowodliwie slepe (marginesy uniform), test wspolwystapien (§5c) lapie.
"""
from __future__ import annotations

from typing import Literal

import numpy as np

from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import (
    Regime,
    generate_uniform_draws,
    sample_euron,
    synthetic_dates,
)

SignalType = Literal["freq_shift", "autocorr", "trend", "seasonality", "pair_corr"]

# Siatki effect sizes per sygnal (preregistration_v3 §6 — wszystkie PINNED).
EFFECT_SIZES: dict[SignalType, tuple[float, ...]] = {
    "freq_shift": (0.01, 0.02, 0.05, 0.10),   # δ    (PINNED od v2)
    "autocorr": (0.05, 0.10, 0.15, 0.20),     # ρ    (PINNED od v2)
    "trend": (0.01, 0.02, 0.05, 0.10),        # β    (PINNED w v3)
    "seasonality": (0.01, 0.02, 0.05, 0.10),  # c    (PINNED w v3)
    "pair_corr": (0.01, 0.02, 0.05, 0.10),    # forced-frac p, margin-preserving (v5)
}

_MAIN_POOL_SIZE = 50
_MAIN_DRAW = 5

# Liczby noszace sygnal (dowolne, ustalone dla reprodukowalnosci; indeksy 1-based).
PLANTED_MAIN = 7          # sygnaly #1, #3, #4 modyfikuja te liczbe
PLANTED_PAIR = (7, 13)    # sygnal #5: ta para wspolwystepuje czesciej

# Pula 48 liczb poza para (1-based) — uzywana przy wymuszaniu pary i kompensacji marginesu.
_PAIR_OTHERS = np.array(
    [k for k in range(1, _MAIN_POOL_SIZE + 1) if k not in PLANTED_PAIR], dtype=np.int64
)

# Bazowe P(obie liczby pary w jednym losowaniu 5/50) pod nullem:
#   C(48,3)/C(50,5) = (5·4)/(50·49) = 20/2450 ≈ 0.00816
_PAIR_BASE_PROB = (_MAIN_DRAW * (_MAIN_DRAW - 1)) / (_MAIN_POOL_SIZE * (_MAIN_POOL_SIZE - 1))

_WEEKDAY_FRIDAY = 4
_WEEKDAY_TUESDAY = 1


def _sample_main_weighted(weights: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """5 z 50 bez zwracania wg wag (rosnaco, 1-based). Wagi normalizowane wewnatrz."""
    p = weights / weights.sum()
    return np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False, p=p) + 1)


def _weights_for(
    signal: SignalType,
    effect: float,
    t: int,
    n_draws: int,
    weekday: int,
    prev_main: np.ndarray | None,
) -> np.ndarray:
    """Wektor wag (len 50) dla losowania t pod danym sygnalem marginalnym."""
    w = np.full(_MAIN_POOL_SIZE, 1.0 / _MAIN_POOL_SIZE)
    idx = PLANTED_MAIN - 1

    if signal == "freq_shift":
        w[idx] += effect
    elif signal == "trend":
        frac = t / (n_draws - 1) if n_draws > 1 else 1.0
        w[idx] += effect * frac
    elif signal == "autocorr":
        if prev_main is not None:
            for k in prev_main:
                w[k - 1] += effect  # boost recurrence liczb z poprzedniego losowania
    elif signal == "seasonality":
        # Kontrast Tue/Fri: piatek +c, wtorek -c na liczbie planted (clip > 0).
        delta = effect if weekday == _WEEKDAY_FRIDAY else -effect
        w[idx] = max(w[idx] + delta, 1e-6)

    return w


def _sample_pair_corr(forced_frac: float, rng: np.random.Generator) -> np.ndarray:
    """Sygnal #5 (margin-preserving): podnosi wspolwystapienie PLANTED_PAIR, NIE marginesy.

    Mieszanka 3-komponentowa (forced_frac = p ∈ [0, 0.1], preregistration_v5 §6):
      - z p:       wymus pare {i,j} + 3 liczby z pozostalych 48,
      - z 9p:      wymus BRAK obu i,j (5 liczb z pozostalych 48) — kompensata marginesu,
      - z (1−10p): zwykly uniform 5/50.
    Wagi gwarantuja P(i)=P(j)=P(dowolnej innej)=0.1 DOKLADNIE (margines uniform), podczas
    gdy P(i,j razem) rosnie z ~0.00816 do 0.918·p+0.00816 (np. ~6.6× przy p=0.05). Dzieki
    temu sygnal jest izolowany w wymiarze JOINT: chi²/MMD (marginalne) slepe, test
    wspolwystapien (§5c) lapie. Konstrukcja wymaga p ≤ 0.1 (wtedy 1−10p ≥ 0).
    """
    i, j = PLANTED_PAIR
    r = rng.random()
    if r < forced_frac:
        # Wymus pare + 3 z pozostalych 48.
        extra = rng.choice(_PAIR_OTHERS, size=_MAIN_DRAW - 2, replace=False)
        return np.sort(np.array([i, j, *extra]))
    if r < 10.0 * forced_frac:
        # Wymus brak obu (5 z pozostalych 48) — utrzymuje margines i,j na 0.1.
        return np.sort(rng.choice(_PAIR_OTHERS, size=_MAIN_DRAW, replace=False))
    # Zwykle losowanie uniform 5/50.
    return np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False) + 1)


def generate_planted_draws(
    n_draws: int,
    regime: Regime,
    signal: SignalType,
    effect_size: float,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generuje `n_draws` losowan z wstrzyknietym sygnalem `signal` o `effect_size`.

    Pula glowna nosi sygnal; euron i daty sa nullowe (preregistration_v3 §3/§6).
    Determinizm w pelni przez `rng` (DoD-6).

    GUARD signal #4: `signal="seasonality"` w R1/R2 degeneruje do czystego nullu
    (kontrast Tue/Fri nie istnieje — losowania tylko w piatki; §6). Slot zachowany
    jako dodatkowy negative control.

    Args:
        n_draws: liczba losowan (> 0).
        regime: "R1" | "R2" | "R3" — pula euron + kalendarz.
        signal: typ sygnalu (zob. SignalType / EFFECT_SIZES).
        effect_size: wartosc z siatki §6 dla danego sygnalu.
        rng: generator NumPy (jedyne zrodlo losowosci).

    Returns:
        Lista `n_draws` rekordow `DrawRecord` w porzadku chronologicznym.

    Raises:
        ValueError: nieznany sygnal, effect_size spoza siatki §6, lub n_draws <= 0.
    """
    if signal not in EFFECT_SIZES:
        raise ValueError(f"Nieznany sygnal: {signal!r} (oczekiwano {list(EFFECT_SIZES)})")
    if effect_size not in EFFECT_SIZES[signal]:
        raise ValueError(
            f"effect_size {effect_size} spoza siatki §6 dla {signal!r}: "
            f"{EFFECT_SIZES[signal]}"
        )
    if n_draws <= 0:
        raise ValueError(f"n_draws musi byc > 0, otrzymano {n_draws}")

    # GUARD signal #4 — poza R3 brak etykiety dnia → null.
    if signal == "seasonality" and regime != "R3":
        return generate_uniform_draws(n_draws, regime, rng)

    dates = synthetic_dates(n_draws, regime)
    records: list[DrawRecord] = []
    prev_main: np.ndarray | None = None

    for t, draw_date in enumerate(dates):
        if signal == "pair_corr":
            main = _sample_pair_corr(effect_size, rng)
        else:
            w = _weights_for(
                signal, effect_size, t, n_draws, draw_date.weekday(), prev_main
            )
            main = _sample_main_weighted(w, rng)
        euron_1, euron_2 = sample_euron(regime, rng)
        prev_main = main
        records.append(
            DrawRecord(
                draw_date=draw_date,
                main_1=int(main[0]),
                main_2=int(main[1]),
                main_3=int(main[2]),
                main_4=int(main[3]),
                main_5=int(main[4]),
                euron_1=euron_1,
                euron_2=euron_2,
            )
        )

    return records


def enumerate_scenarios() -> list[tuple[str, float | None]]:
    """21 scenariuszy per rezim: 20 (5 sygnalow × 4 effect) + 1 null (§6).

    Null reprezentowany jako ("null", None). × 3 rezimy = 63 unikalne datasety.
    """
    scenarios: list[tuple[str, float | None]] = []
    for signal, sizes in EFFECT_SIZES.items():
        for size in sizes:
            scenarios.append((signal, size))
    scenarios.append(("null", None))
    return scenarios
