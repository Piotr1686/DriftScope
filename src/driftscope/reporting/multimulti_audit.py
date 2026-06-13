"""Multi Multi audit — second real-world case study (reusability showcase, reporting layer).

Druga gra liczbowa (Multi Multi 20-z-80) przepuszczona przez DOKLADNIE ten sam battery
negative-control co audyt EuroJackpot — dowod, ze framework jest reusable poza flagship
case. Detektory wyprowadzaja pool/k z rekordow (`DrawRecord.generic`, pool_size=80), zero
nowej methodology (reuse `prng_benchmark.run_battery` + `h1_classical.run_bocpd` — warstwa
reporting NIE podlega dyscyplinie prereg §0).

BOCPD jest O(T^2) → audyt liczony na OGRANICZONYM oknie ostatnich `window` losowan (default
2000; pelne 16827 wykluczone budzetowo). Prog BOCPD(pool=80) = 0.34 (skalibrowany na n=2000,
FPR~=0.05 pod nullem uniform-iid; `_MAIN_REJECT_THRESHOLD_BY_POOL`), wiec okno 2000 jest
length-matched do kalibracji. Oczekiwany wynik: **clear** — Multi Multi to dobrze
przetestowany RNG bez pre-rejestrowanego sygnalu (honest null jak negative control 1-50 w EJ).
Werdykt = Disagreement Protocol po 3 filarach rdzeniowych (BOCPD/MMD/cooc, FLAG >=2/3),
wiec samotny reject jednego filaru przy alpha=0.05 NIE przewraca werdyktu.

Prezentacja (tabela/CSV) zyje w `scripts/multimulti_audit.py` (CLI).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import driftscope
from driftscope.ingestion.lotto_scraper import load_generic_seed_csv
from driftscope.methodology.h1_classical import run_bocpd
from driftscope.reporting.disagreement import DisagreementVerdict, classify
from driftscope.reporting.prng_benchmark import BenchmarkRow, run_battery

_ROOT = Path(driftscope.__file__).resolve().parents[2]
_MM_SEED_PATH = _ROOT / "data" / "seed" / "multimulti_history.csv"
_MM_POOL_SIZE = 80
_DEFAULT_WINDOW = 2000  # BOCPD O(T^2) + length-matched do kalibracji progu 0.34


@dataclass(frozen=True)
class MultiMultiAuditRow:
    """Jeden wiersz audytu MM: BOCPD (filar temporalny) + battery negative-control.

    Kompozycja: `battery` niesie Family B (per-number exact binomial) + MMD + co-occurrence
    + IT (suplement); pola `bocpd_*` dokladaja filar H1 (BOCPD na puli glownej).

    Werdykt = Disagreement Protocol po 3 filarach RDZENIOWYCH (BOCPD->h1 / MMD /
    co-occurrence): "FLAG" dopiero przy konwergencji >=2/3, samotny filar (1/3) = clear
    (oczekiwany false-positive przy alpha=0.05, NIE finding — spojnie z report.qmd §4/§6).
    IT = suplement (nie filar), Family B = osobna bramka FDR — oba raportowane w macierzy,
    ale POZA werdyktem. Kontrast do `BenchmarkRow.flagged` (OR), ktory jest poprawny dla
    benchmarku sensitivity/specificity na PRNG z ground-truth labelem.
    """

    source: str
    n: int
    window: int
    bocpd_reject: bool
    bocpd_max_prob: float
    bocpd_threshold: float
    battery: BenchmarkRow

    @property
    def disagreement(self) -> DisagreementVerdict:
        """Klasyfikacja Disagreement po 3 filarach rdzeniowych (reuse DoD-4 classify)."""
        return classify(
            {
                "h1": self.bocpd_reject,  # BOCPD = rodzina temporalna H1 (zob. PILLARS)
                "mmd": self.battery.mmd_reject,
                "cooccurrence": self.battery.cooc_reject,
            }
        )

    @property
    def core_fraction(self) -> str:
        """Ulamek zgodnych filarow rdzeniowych ('0/3'..'3/3') do raportow."""
        return self.disagreement.fraction

    @property
    def flagged(self) -> bool:
        """Czy konwergencja filarow rdzeniowych >=2/3 (Disagreement, NIE naiwny OR)."""
        return self.disagreement.n_agree >= 2

    @property
    def verdict(self) -> str:
        return "FLAG" if self.flagged else "clear"


def run_multimulti_audit(
    *,
    window: int = _DEFAULT_WINDOW,
    n_perm: int = 499,
    alpha: float = 0.05,
    seed_csv: Path | None = None,
) -> MultiMultiAuditRow:
    """Audyt negative-control Multi Multi na oknie ostatnich `window` losowan.

    Wczytuje realny strumien MM (`load_generic_seed_csv`, pool_size=80), tnie do `window`
    ostatnich losowan i liczy: BOCPD(field="main") + pelny battery (`run_battery` reuse).
    Wszystkie detektory wyprowadzaja pool/k z rekordow (kroki 1–5). Oczekiwany: clear
    (Disagreement; samotny filar 1/3 = clear, NIE finding).

    `seed_csv`: nadpisanie sciezki (testy/inne zrodla); None → `data/seed/multimulti_history.csv`.
    """
    path = seed_csv if seed_csv is not None else _MM_SEED_PATH
    draws = load_generic_seed_csv(path, pool_size=_MM_POOL_SIZE)
    # BOCPD jest sekwencyjny, a "okno = ostatnie N" zaklada porzadek chronologiczny.
    # Realny MM seed ma 2 historyczne inwersje dat (2010) — sortujemy defensywnie, by
    # okno i detekcja change-pointow byly niezalezne od porzadku w pliku zrodlowym.
    draws.sort(key=lambda d: d.draw_date)
    recent = draws[-window:] if 0 < window < len(draws) else draws

    bocpd = run_bocpd(recent, field="main")
    battery = run_battery("Multi Multi", "real", recent, alpha=alpha, n_perm=n_perm)

    return MultiMultiAuditRow(
        source="Multi Multi (20/80)",
        n=len(recent),
        window=window,
        bocpd_reject=bocpd.reject_h0,
        bocpd_max_prob=float(bocpd.statistic),
        bocpd_threshold=float(bocpd.metadata["reject_threshold"]),
        battery=battery,
    )
