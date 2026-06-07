"""Honest null generator — uczciwy baseline DriftSim (W2).

Generuje strumien losowan EuroJackpot pod H0: stacjonarny, uniform, i.i.d.
w danym rezimie (preregistration_v2 §1). Stanowi fundament DriftSim: planted
signals (`planted_signals.py`) = ten null + wstrzykniety sygnal.

Czysty modul: zna tylko `DrawRecord` i RNG. Nie zna ingestion ani reporting.

Pule (preregistration_v2 §1):
- R1: 5/50 + 2/8   (2012-03-23 → 2014-10-03)
- R2: 5/50 + 2/10  (2014-10-10 → 2022-03-18)
- R3: 5/50 + 2/12  (2022-03-25 → obecnie; dwa losowania/tydzien: wtorek + piatek)

Daty sa SYNTETYCZNE (tygodniowe od kotwicy rezimu) — null nie modeluje real-data,
tylko proces generatywny. Etykieta dnia (wtorek/piatek) istnieje WYLACZNIE w R3
(guard signal #4, preregistration_v2 §6): w R1/R2 wszystkie losowania to piatki.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

import numpy as np

from driftscope.core.types import DrawRecord

# Rozmiar puli euronumerow per rezim (gorna granica wlacznie; preregistration_v2 §1)
EURON_POOL_SIZE: dict[str, int] = {"R1": 8, "R2": 10, "R3": 12}

_MAIN_POOL_SIZE = 50  # pula glowna 1-50 — niezmienna we wszystkich rezimach (negative control)
_MAIN_DRAW = 5        # 5 liczb glownych bez zwracania
_EURON_DRAW = 2       # 2 euronumery bez zwracania

# Kotwice synthetic — piatki rozpoczynajace kazdy rezim (dowolne, byle monotoniczne).
# R3 generuje pary wtorek/piatek (od 2022 EuroJackpot losuje dwa razy w tygodniu).
_REGIME_ANCHOR_FRIDAY: dict[str, date] = {
    "R1": date(2012, 3, 23),   # piatek
    "R2": date(2014, 10, 10),  # piatek
    "R3": date(2022, 3, 25),   # piatek (R3: dodajemy wtorki)
}

Regime = Literal["R1", "R2", "R3"]


def synthetic_dates(n_draws: int, regime: Regime) -> list[date]:
    """Monotoniczne daty syntetyczne dla rezimu (wspoldzielone z planted_signals).

    R1/R2: jedno losowanie/tydzien (piatek). R3: dwa/tydzien (wtorek + piatek),
    co tworzy realna etykiete dnia potrzebna dla signal #4 (weekly seasonality).
    """
    anchor_friday = _REGIME_ANCHOR_FRIDAY[regime]
    dates: list[date] = []

    if regime == "R3":
        # Para wtorek/piatek w kazdym tygodniu. Wtorek = piatek - 3 dni.
        first_tuesday = anchor_friday - timedelta(days=3)
        week = 0
        while len(dates) < n_draws:
            tuesday = first_tuesday + timedelta(weeks=week)
            dates.append(tuesday)
            if len(dates) < n_draws:
                dates.append(tuesday + timedelta(days=3))  # piatek
            week += 1
    else:
        for i in range(n_draws):
            dates.append(anchor_friday + timedelta(weeks=i))

    return dates[:n_draws]


def sample_euron(regime: Regime, rng: np.random.Generator) -> tuple[int, int]:
    """Losuje 2 euronumery (bez zwracania, rosnaco) z puli rezimu.

    Wspoldzielone z planted_signals: sygnaly dotykaja puli glownej, euron pozostaje
    nullowy. +1 bo rng.choice zwraca indeksy 0-based, a liczby sa 1-based.
    """
    euron = np.sort(rng.choice(EURON_POOL_SIZE[regime], size=_EURON_DRAW, replace=False) + 1)
    return int(euron[0]), int(euron[1])


def generate_uniform_draws(
    n_draws: int,
    regime: Regime,
    rng: np.random.Generator,
) -> list[DrawRecord]:
    """Generuje `n_draws` losowan i.i.d. uniform dla danego rezimu.

    Kazde losowanie: 5 z 50 (bez zwracania, rosnaco) + 2 z puli euron rezimu
    (bez zwracania, rosnaco). Daty syntetyczne (zob. `synthetic_dates`).

    Determinizm: w pelni okreslony przez `rng`. Reprodukowalny strumien:
        from driftscope.core.seeds import make_worker_seeds
        seq = make_worker_seeds(BASE_SEED, 1)[0]
        draws = generate_uniform_draws(n, "R2", np.random.default_rng(seq))

    Args:
        n_draws: liczba losowan do wygenerowania (> 0).
        regime: "R1" | "R2" | "R3" — wyznacza pule euronumerow i kalendarz.
        rng: generator NumPy (jedyne zrodlo losowosci).

    Returns:
        Lista `n_draws` rekordow `DrawRecord` w porzadku chronologicznym.

    Raises:
        ValueError: gdy `regime` nieznany lub `n_draws` <= 0.
    """
    if regime not in EURON_POOL_SIZE:
        raise ValueError(f"Nieznany rezim: {regime!r} (oczekiwano R1/R2/R3)")
    if n_draws <= 0:
        raise ValueError(f"n_draws musi byc > 0, otrzymano {n_draws}")

    dates = synthetic_dates(n_draws, regime)
    records: list[DrawRecord] = []

    for draw_date in dates:
        # +1 bo rng.choice zwraca indeksy 0-based, a liczby sa 1-based.
        main = np.sort(rng.choice(_MAIN_POOL_SIZE, size=_MAIN_DRAW, replace=False) + 1)
        euron_1, euron_2 = sample_euron(regime, rng)
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


# Kotwica dla strumieni generycznych (gra inna niz EJ; np. Multi Multi). Daty syntetyczne —
# generator modeluje proces generatywny, nie kalendarz konkretnej gry.
_GENERIC_ANCHOR = date(2015, 1, 2)  # piatek


def generate_generic_uniform(
    n_draws: int,
    pool_size: int,
    k: int,
    rng: np.random.Generator,
    anchor: date = _GENERIC_ANCHOR,
) -> list[DrawRecord]:
    """Generuje `n_draws` losowan i.i.d. uniform k-z-`pool_size` (gra generyczna, bez euron).

    Honest null dla gier innych niz EuroJackpot (Multi Multi 20-z-80, reference dla MMD,
    kalibracja BOCPD nowej puli). Kazde losowanie: `k` liczb z 1..`pool_size` bez zwracania,
    rosnaco. Rekordy generyczne (`DrawRecord.generic`) niosa `pool_size`, wiec detektory
    wyprowadzaja pule/k z danych.

    Determinizm: w pelni okreslony przez `rng` (DoD-6).

    Args:
        n_draws: liczba losowan (> 0).
        pool_size: rozmiar puli glownej (> k).
        k: liczb na losowanie (> 0).
        rng: generator NumPy (jedyne zrodlo losowosci).
        anchor: data startowa (daty syntetyczne, tygodniowe).

    Returns:
        Lista `n_draws` rekordow generycznych w porzadku chronologicznym.

    Raises:
        ValueError: gdy `n_draws` <= 0, `k` <= 0 lub `k` > `pool_size`.
    """
    if n_draws <= 0:
        raise ValueError(f"n_draws musi byc > 0, otrzymano {n_draws}")
    if k <= 0 or k > pool_size:
        raise ValueError(f"k={k} poza (0, pool_size={pool_size}]")

    records: list[DrawRecord] = []
    for i in range(n_draws):
        nums = np.sort(rng.choice(pool_size, size=k, replace=False) + 1)
        records.append(
            DrawRecord.generic(
                draw_date=anchor + timedelta(weeks=i),
                numbers=[int(x) for x in nums],
                pool_size=pool_size,
            )
        )
    return records
