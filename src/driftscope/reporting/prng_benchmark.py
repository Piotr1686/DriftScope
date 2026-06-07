"""PRNG benchmark — battery reuse + ground-truth sources (wow Opcja α, reporting layer).

Warstwa reporting/analysis: zna detektory (`pipeline`/`methodology`) ORAZ generatory
(`ingestion.rng_streams`). Aplikuje DOKLADNIE ten sam battery negative-control co audyt
EuroJackpot na strumienie z GROUND-TRUTH labelem i zwraca strukturalne wiersze macierzy
detekcji. Prezentacja (tabela/CSV) zyje w `scripts/prng_benchmark.py` (CLI) i `report.qmd`.

Cel: zamienic honest-null audytu w dowod CZULOSCI — ten sam framework, ktory nie znajduje
nic w EuroJackpot, zapala sie na PRNG z wstrzyknietym defektem i milczy na krypto-PRNG.
Zero nowej methodology (reuse `pipeline` — NIE podlega dyscyplinie prereg §0).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import driftscope
from driftscope.core.config import settings
from driftscope.core.types import DrawRecord
from driftscope.ingestion.lotto_scraper import load_seed_csv
from driftscope.ingestion.rng_streams import (
    AESCtrDrbgStream,
    ChaCha20Stream,
    MT19937Stream,
    Xorshift64Stream,
    draws_from_stream,
)
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.k4_mmd import mmd_uniform_detector
from driftscope.methodology.multiple_testing import correct_family_b
from driftscope.pipeline import family_b_per_number_pvalues
from driftscope.reporting.information_theory import information_detector

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_DEFAULT_FAVOR = (7, 0.15)  # defekt marginalny: numer 7 nadreprezentowany w 15% losowan
_DEFAULT_PERIOD = 50  # defekt period-truncation: cykl 50 losowan powtarzany (zamrozone czestosci)


@dataclass(frozen=True)
class BenchmarkRow:
    """Jeden wiersz macierzy detekcji: zrodlo + ground-truth label + wyniki batterny."""

    source: str
    klass: str                # "good" | "crypto" | "DEFECT" | "real"
    n: int
    family_b_reject: int      # liczba odrzuconych liczb (per-number FDR)
    family_b_size: int
    family_b_min_q: float
    mmd_reject: bool
    mmd_p: float
    cooc_reject: bool
    cooc_p: float
    it_reject: bool           # suplement IT (LZ76 sekwencyjny) — sila: period-truncation
    it_p: float

    @property
    def flagged(self) -> bool:
        """Czy KTORYKOLWIEK detektor zaplonal (FLAG vs clear)."""
        return (
            self.family_b_reject > 0
            or self.mmd_reject
            or self.cooc_reject
            or self.it_reject
        )

    @property
    def verdict(self) -> str:
        return "FLAG" if self.flagged else "clear"


def run_battery(
    source: str,
    klass: str,
    draws: list[DrawRecord],
    *,
    alpha: float = 0.05,
    n_perm: int = 499,
) -> BenchmarkRow:
    """Battery negative-control na puli glownej: Family B (binomial FDR) + MMD + co-occurrence.

    Te same detektory co `pipeline.default_pillar_detectors` / `family_b_per_number_pvalues`
    — zero duplikacji methodology.
    """
    labels, pvals = family_b_per_number_pvalues(draws)
    fb = correct_family_b(pvals, labels, alpha=alpha)
    mmd = mmd_uniform_detector(window=25, n_perm=n_perm, alpha=alpha)(draws)
    cooc = cooccurrence_detector(n_perm=n_perm, alpha=alpha)(draws)
    it = information_detector(n_perm=n_perm, alpha=alpha)(draws)
    min_q = float(fb.q_values.min()) if fb.q_values.size else 1.0
    return BenchmarkRow(
        source=source,
        klass=klass,
        n=len(draws),
        family_b_reject=fb.n_reject,
        family_b_size=len(fb.labels),
        family_b_min_q=min_q,
        mmd_reject=mmd.reject_h0,
        mmd_p=float(mmd.p_value),
        cooc_reject=cooc.reject_h0,
        cooc_p=float(cooc.p_value),
        it_reject=it.reject_h0,
        it_p=float(it.p_value),
    )


def build_sources(
    n_draws: int,
    seed: int,
    *,
    favor: tuple[int, float] = _DEFAULT_FAVOR,
    period: int = _DEFAULT_PERIOD,
    seed_csv: Path | None = None,
) -> list[tuple[str, str, list[DrawRecord]]]:
    """Zrodla (nazwa, ground-truth label, draws) — symetryczna macierz showcase.

    Dwa good (MT19937/Xorshift64) + dwa crypto (ChaCha20/AES-CTR-DRBG) → oczekiwany clear;
    dwa DEFECT na tym samym MT base → oczekiwany FLAG, kazdy przez INNY mechanizm:
      - `+bias(k)`  — defekt marginalny (jeden numer nadreprezentowany; Family B/MMD),
      - `+period(p)`— period-truncation (zamrozone czestosci cyklu; Family B over-dispersion).

    Dolacza realny EuroJackpot, jesli seed CSV istnieje (domyslnie z config). Real = honest
    null audytu (oczekiwany clear, jak negative control 1-50).
    """
    sources: list[tuple[str, str, list[DrawRecord]]] = [
        ("MT19937", "good", draws_from_stream(MT19937Stream(seed), n_draws)),
        ("Xorshift64", "good", draws_from_stream(Xorshift64Stream(seed), n_draws)),
        ("ChaCha20", "crypto", draws_from_stream(ChaCha20Stream(seed), n_draws)),
        ("AES-CTR-DRBG", "crypto", draws_from_stream(AESCtrDrbgStream(seed), n_draws)),
        (
            f"MT19937+bias({favor[0]})",
            "DEFECT",
            draws_from_stream(MT19937Stream(seed), n_draws, favor=favor),
        ),
        (
            f"MT19937+period({period})",
            "DEFECT",
            draws_from_stream(MT19937Stream(seed), n_draws, period=period),
        ),
    ]
    path = seed_csv if seed_csv is not None else _ROOT / settings.data_seed_path
    if path.exists():
        sources.append(("EuroJackpot", "real", load_seed_csv(path)))
    return sources


def run_benchmark(
    *,
    n_draws: int = 1500,
    n_perm: int = 499,
    alpha: float = 0.05,
    seed: int = 42,
    favor: tuple[int, float] = _DEFAULT_FAVOR,
    period: int = _DEFAULT_PERIOD,
    seed_csv: Path | None = None,
) -> list[BenchmarkRow]:
    """Pelny benchmark: battery na kazdym zrodle → lista wierszy macierzy detekcji."""
    return [
        run_battery(name, klass, draws, alpha=alpha, n_perm=n_perm)
        for name, klass, draws in build_sources(
            n_draws, seed, favor=favor, period=period, seed_csv=seed_csv
        )
    ]
