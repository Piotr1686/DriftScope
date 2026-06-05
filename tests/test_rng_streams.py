"""Testy adapterow PRNG → strumien losowan (rng_streams.py, wow Opcja α).

Walidacja niezmiennikow generatora PRZED benchmarkiem reusability:
  - determinizm (DoD-6: ten sam seed → bit-identyczne losowania),
  - poprawnosc formatu DrawRecord (5-z-50 distinct sorted, 2-z-K euron),
  - unbiased sampling (randbelow rownomierny, good RNG ~ uniform marginesy),
  - WYKRYWALNOSC wstrzyknietego defektu (pozytywna kontrola czulosci frameworka).
"""
import numpy as np
import pytest

from driftscope.ingestion.rng_streams import (
    ChaCha20Stream,
    MT19937Stream,
    Xorshift64Stream,
    draws_from_stream,
)

_STREAMS = [MT19937Stream, Xorshift64Stream, ChaCha20Stream]


@pytest.mark.parametrize("cls", _STREAMS)
def test_determinism(cls: type) -> None:
    """Ten sam seed → identyczne losowania (DoD-6, reprodukowalnosc)."""
    a = draws_from_stream(cls(123), 100)
    b = draws_from_stream(cls(123), 100)
    assert a == b


@pytest.mark.parametrize("cls", _STREAMS)
def test_draw_format_valid(cls: type) -> None:
    """Kazde losowanie: 5 roznych liczb glownych 1-50 sorted + 2 euron 1-12 sorted."""
    draws = draws_from_stream(cls(7), 50)
    for d in draws:
        main = d.main_numbers
        euron = d.euronumbers
        assert len(set(main)) == 5 and all(1 <= x <= 50 for x in main)
        assert main == sorted(main)
        assert len(set(euron)) == 2 and all(1 <= x <= 12 for x in euron)
        assert euron == sorted(euron)
    # daty monotoniczne rosnaco (potrzebne dla BOCPD)
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)


@pytest.mark.parametrize("cls", _STREAMS)
def test_different_seeds_differ(cls: type) -> None:
    """Rozne seedy → rozne strumienie (brak zdegenerowanego stanu)."""
    assert draws_from_stream(cls(1), 50) != draws_from_stream(cls(2), 50)


def test_randbelow_unbiased() -> None:
    """randbelow(k) rownomierny: kazdy kubel w granicach +-15% przy duzej probie."""
    stream = MT19937Stream(42)
    k = 10
    n = 20_000
    counts = np.zeros(k, dtype=np.int64)
    for _ in range(n):
        counts[stream.randbelow(k)] += 1
    expected = n / k
    assert np.all(np.abs(counts - expected) < 0.15 * expected)


@pytest.mark.parametrize("cls", [MT19937Stream, ChaCha20Stream])
def test_good_rng_marginals_near_uniform(cls: type) -> None:
    """Good/crypto RNG: czestosc kazdej liczby glownej ~ 5/50 (zaden numer nie odstaje)."""
    draws = draws_from_stream(cls(99), 5000)
    counts = np.zeros(50, dtype=np.int64)
    for d in draws:
        for x in d.main_numbers:
            counts[x - 1] += 1
    expected = 5000 * 5 / 50  # 500 na numer
    # Tolerancja luzna (to nie test statystyczny, tylko sanity braku razacego biasu).
    assert np.all(np.abs(counts - expected) < 0.20 * expected)


def test_defect_detectable() -> None:
    """Wstrzykniety defekt favor=(7, p): numer 7 RAZACO nadreprezentowany vs good."""
    n = 3000
    good = draws_from_stream(MT19937Stream(5), n)
    bad = draws_from_stream(MT19937Stream(5), n, favor=(7, 0.3))
    freq_good = sum(7 in d.main_numbers for d in good)
    freq_bad = sum(7 in d.main_numbers for d in bad)
    assert freq_bad > 1.5 * freq_good  # defekt musi byc widoczny golym okiem


def test_invalid_args() -> None:
    """Walidacja: n_draws<=0 i favor poza zakresem → ValueError."""
    stream = MT19937Stream(1)
    with pytest.raises(ValueError):
        draws_from_stream(stream, 0)
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, favor=(99, 0.1))
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, favor=(7, 1.5))


def test_randbelow_rejects_nonpositive() -> None:
    """randbelow(n<=0) → ValueError (kontrakt unbiased sampling)."""
    with pytest.raises(ValueError):
        MT19937Stream(1).randbelow(0)
