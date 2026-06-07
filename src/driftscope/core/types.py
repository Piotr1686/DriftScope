"""Pydantic modele danych: DrawRecord, RegimeSpec, TestResult + alias Detector."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from pydantic import BaseModel, model_validator


class DrawRecord(BaseModel):
    """Jeden rekord losowania gry liczbowej (uogólniony — EuroJackpot lub generyczny).

    Dwa wzajemnie wykluczające się ksztalty (XOR), oba eksponują wspólny interfejs
    `main_numbers` czytany przez wszystkie detektory:

    * **EuroJackpot** (back-compat): `main_1..5` + `euron_1..2`; `pool_size` domyslnie 50.
      Pula glowna 5-z-50 + 2 euronumery. Tworzony jak dotychczas (pola jawne).
    * **Generyczny** (Multi Multi 20-z-80, PRNG, ...): `numbers` (lista k-z-`pool_size`),
      bez euronumerów. Tworzony przez `DrawRecord.generic(...)`.

    `pool_size` (rozmiar puli glownej) jest niesiony PRZEZ rekord, wiec detektory wyprowadzają
    pulę/k z danych (`draws[0].pool_size`, `len(draws[0].main_numbers)`) zamiast twardych stalych
    — to mechanizm reusability na inne gry (DoD: zero regresji EJ przy pool_size=50).
    """

    draw_date: date
    # EuroJackpot (opcjonalne — None dla rekordu generycznego)
    main_1: int | None = None
    main_2: int | None = None
    main_3: int | None = None
    main_4: int | None = None
    main_5: int | None = None
    euron_1: int | None = None
    euron_2: int | None = None
    # Generyczne (None dla rekordu EuroJackpot)
    numbers: list[int] | None = None
    pool_size: int = 50

    @model_validator(mode="after")
    def _validate_shape(self) -> DrawRecord:
        """Wymusza XOR EJ/generic + zakresy liczb względem `pool_size`."""
        ej_fields = [self.main_1, self.main_2, self.main_3, self.main_4, self.main_5]
        has_ej = any(v is not None for v in ej_fields)
        has_generic = self.numbers is not None

        if has_ej and has_generic:
            raise ValueError(
                "DrawRecord: podaj ALBO main_1..5 (EJ) ALBO numbers (generic), nie oba"
            )
        if not has_ej and not has_generic:
            raise ValueError("DrawRecord: wymagane main_1..5 (EJ) lub numbers (generic)")

        if has_ej:
            if any(v is None for v in ej_fields):
                raise ValueError("DrawRecord (EJ): wszystkie main_1..5 muszą być podane")
            for v in ej_fields:
                assert v is not None  # dla mypy (sprawdzone wyżej)
                if not 1 <= v <= self.pool_size:
                    raise ValueError(f"main number {v} poza 1-{self.pool_size}")
            for e in (self.euron_1, self.euron_2):
                if e is not None and not 1 <= e <= 12:
                    raise ValueError(f"euro number {e} poza 1-12")
        else:
            assert self.numbers is not None  # dla mypy (has_generic)
            for v in self.numbers:
                if not 1 <= v <= self.pool_size:
                    raise ValueError(f"number {v} poza 1-{self.pool_size}")
        return self

    @classmethod
    def generic(
        cls, draw_date: date, numbers: list[int], pool_size: int
    ) -> DrawRecord:
        """Konstruktor rekordu generycznego (Multi Multi / PRNG) — k-z-`pool_size`, bez euron."""
        return cls(draw_date=draw_date, numbers=list(numbers), pool_size=pool_size)

    @property
    def main_numbers(self) -> list[int]:
        """Wspólny interfejs detektorów: liczby glowne (EJ 5-z-50 lub generic k-z-pool)."""
        if self.numbers is not None:
            return self.numbers
        return [self.main_1, self.main_2, self.main_3, self.main_4, self.main_5]  # type: ignore[list-item]

    @property
    def euronumbers(self) -> list[int]:
        """Euronumery (tylko EJ). Rekord generyczny nie ma euron → ValueError."""
        if self.euron_1 is None or self.euron_2 is None:
            raise ValueError("DrawRecord generyczny nie ma euronumerów")
        return [self.euron_1, self.euron_2]


class RegimeSpec(BaseModel):
    """Definicja reżimu czasowego (wycinek losowan)."""

    name: str
    start_date: date
    end_date: date | None = None


class TestResult(BaseModel):
    """Wynik testu statystycznego — wspólny format dla wszystkich testów H1/K4."""

    test_name: str
    series_label: str = ""
    statistic: float
    p_value: float
    reject_h0: bool
    regime: str | None = None
    metadata: dict[str, Any] = {}


# Wspolny interfejs detektora (harness calibration DETECTOR-AGNOSTYCZNY): czysta funkcja
# strumienia losowan → TestResult. Jedno zrodlo prawdy dla calibration / methodology /
# reporting (zamiast lokalnych re-deklaracji w kazdym module).
Detector = Callable[[list[DrawRecord]], TestResult]
