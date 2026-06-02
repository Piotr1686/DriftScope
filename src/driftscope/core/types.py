"""Pydantic modele danych: DrawRecord, RegimeSpec, TestResult + alias Detector."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator


class DrawRecord(BaseModel):
    """Jeden rekord losowania EuroJackpot."""

    draw_date: date
    main_1: int
    main_2: int
    main_3: int
    main_4: int
    main_5: int
    euron_1: int
    euron_2: int

    @field_validator("main_1", "main_2", "main_3", "main_4", "main_5")
    @classmethod
    def validate_main(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError(f"main number {v} out of range 1-50")
        return v

    @field_validator("euron_1", "euron_2")
    @classmethod
    def validate_euron(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError(f"euro number {v} out of range 1-12")
        return v

    @property
    def main_numbers(self) -> list[int]:
        return [self.main_1, self.main_2, self.main_3, self.main_4, self.main_5]

    @property
    def euronumbers(self) -> list[int]:
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
