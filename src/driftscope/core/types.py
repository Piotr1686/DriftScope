"""Pydantic data models: DrawRecord, RegimeSpec, TestResult + Detector alias."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from pydantic import BaseModel, model_validator


class DrawRecord(BaseModel):
    """A single lottery draw record (generalized — EuroJackpot or generic).

    Two mutually exclusive shapes (XOR), both exposing the common interface
    `main_numbers` that every detector reads:

    * **EuroJackpot** (back-compat): `main_1..5` + `euron_1..2`; `pool_size` defaults to 50.
      Main pool 5-of-50 + 2 euro numbers. Created as before (explicit fields).
    * **Generic** (Multi Multi 20-of-80, PRNG, ...): `numbers` (a k-of-`pool_size` list),
      without euro numbers. Created via `DrawRecord.generic(...)`.

    `pool_size` (the main pool size) is carried BY the record, so detectors derive the
    pool/k from the data (`draws[0].pool_size`, `len(draws[0].main_numbers)`) instead of
    hard-coded constants — this is the reusability mechanism for other games (DoD: zero EJ
    regression at pool_size=50).
    """

    draw_date: date
    # EuroJackpot (optional — None for a generic record)
    main_1: int | None = None
    main_2: int | None = None
    main_3: int | None = None
    main_4: int | None = None
    main_5: int | None = None
    euron_1: int | None = None
    euron_2: int | None = None
    # Generic (None for an EuroJackpot record)
    numbers: list[int] | None = None
    pool_size: int = 50

    @model_validator(mode="after")
    def _validate_shape(self) -> DrawRecord:
        """Enforces the EJ/generic XOR + number ranges relative to `pool_size`."""
        ej_fields = [self.main_1, self.main_2, self.main_3, self.main_4, self.main_5]
        has_ej = any(v is not None for v in ej_fields)
        has_generic = self.numbers is not None

        if has_ej and has_generic:
            raise ValueError(
                "DrawRecord: provide EITHER main_1..5 (EJ) OR numbers (generic), not both"
            )
        if not has_ej and not has_generic:
            raise ValueError("DrawRecord: requires main_1..5 (EJ) or numbers (generic)")

        if has_ej:
            if any(v is None for v in ej_fields):
                raise ValueError("DrawRecord (EJ): all of main_1..5 must be provided")
            for v in ej_fields:
                assert v is not None  # for mypy (checked above)
                if not 1 <= v <= self.pool_size:
                    raise ValueError(f"main number {v} out of 1-{self.pool_size}")
            for e in (self.euron_1, self.euron_2):
                if e is not None and not 1 <= e <= 12:
                    raise ValueError(f"euro number {e} out of 1-12")
        else:
            assert self.numbers is not None  # for mypy (has_generic)
            for v in self.numbers:
                if not 1 <= v <= self.pool_size:
                    raise ValueError(f"number {v} out of 1-{self.pool_size}")
        return self

    @classmethod
    def generic(
        cls, draw_date: date, numbers: list[int], pool_size: int
    ) -> DrawRecord:
        """Generic-record constructor (Multi Multi / PRNG) — k-of-`pool_size`, no euron."""
        return cls(draw_date=draw_date, numbers=list(numbers), pool_size=pool_size)

    @property
    def main_numbers(self) -> list[int]:
        """Common detector interface: main numbers (EJ 5-of-50 or generic k-of-pool)."""
        if self.numbers is not None:
            return self.numbers
        return [self.main_1, self.main_2, self.main_3, self.main_4, self.main_5]  # type: ignore[list-item]

    @property
    def euronumbers(self) -> list[int]:
        """Euro numbers (EJ only). A generic record has no euron → ValueError."""
        if self.euron_1 is None or self.euron_2 is None:
            raise ValueError("a generic DrawRecord has no euro numbers")
        return [self.euron_1, self.euron_2]


class RegimeSpec(BaseModel):
    """Definition of a time regime (a slice of draws)."""

    name: str
    start_date: date
    end_date: date | None = None


class TestResult(BaseModel):
    """Statistical test result — a shared format for all H1/K4 tests."""

    test_name: str
    series_label: str = ""
    statistic: float
    p_value: float
    reject_h0: bool
    regime: str | None = None
    metadata: dict[str, Any] = {}


# Shared detector interface (the calibration harness is DETECTOR-AGNOSTIC): a pure function
# of the draw stream → TestResult. A single source of truth for calibration / methodology /
# reporting (instead of local re-declarations in every module).
Detector = Callable[[list[DrawRecord]], TestResult]
