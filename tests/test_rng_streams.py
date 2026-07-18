"""PRNG adapter tests → draw stream (rng_streams.py, wow Option α).

Validates generator invariants BEFORE the reusability benchmark:
  - determinism (DoD-6: same seed → bit-identical draws),
  - DrawRecord format correctness (5-of-50 distinct sorted, 2-of-K euron),
  - unbiased sampling (randbelow uniform, good RNG ~ uniform margins),
  - DETECTABILITY of an injected defect (positive control for framework sensitivity).
"""
import numpy as np
import pytest

from driftscope.ingestion.rng_streams import (
    AESCtrDrbgStream,
    ChaCha20Stream,
    MT19937Stream,
    Xorshift64Stream,
    draws_from_stream,
)

_STREAMS = [MT19937Stream, Xorshift64Stream, ChaCha20Stream, AESCtrDrbgStream]


@pytest.mark.parametrize("cls", _STREAMS)
def test_determinism(cls: type) -> None:
    """Same seed → identical draws (DoD-6, reproducibility)."""
    a = draws_from_stream(cls(123), 100)
    b = draws_from_stream(cls(123), 100)
    assert a == b


@pytest.mark.parametrize("cls", _STREAMS)
def test_draw_format_valid(cls: type) -> None:
    """Each draw: 5 distinct main numbers 1-50 sorted + 2 euron 1-12 sorted."""
    draws = draws_from_stream(cls(7), 50)
    for d in draws:
        main = d.main_numbers
        euron = d.euronumbers
        assert len(set(main)) == 5 and all(1 <= x <= 50 for x in main)
        assert main == sorted(main)
        assert len(set(euron)) == 2 and all(1 <= x <= 12 for x in euron)
        assert euron == sorted(euron)
    # dates monotonically increasing (needed for BOCPD)
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates)


@pytest.mark.parametrize("cls", _STREAMS)
def test_different_seeds_differ(cls: type) -> None:
    """Different seeds → different streams (no degenerate state)."""
    assert draws_from_stream(cls(1), 50) != draws_from_stream(cls(2), 50)


def test_randbelow_unbiased() -> None:
    """randbelow(k) uniform: each bucket within +-15% at a large sample."""
    stream = MT19937Stream(42)
    k = 10
    n = 20_000
    counts = np.zeros(k, dtype=np.int64)
    for _ in range(n):
        counts[stream.randbelow(k)] += 1
    expected = n / k
    assert np.all(np.abs(counts - expected) < 0.15 * expected)


@pytest.mark.parametrize("cls", [MT19937Stream, ChaCha20Stream, AESCtrDrbgStream])
def test_good_rng_marginals_near_uniform(cls: type) -> None:
    """Good/crypto RNG: each main number's frequency ~ 5/50 (no number stands out)."""
    draws = draws_from_stream(cls(99), 5000)
    counts = np.zeros(50, dtype=np.int64)
    for d in draws:
        for x in d.main_numbers:
            counts[x - 1] += 1
    expected = 5000 * 5 / 50  # 500 per number
    # Loose tolerance (this is not a statistical test, just a sanity check for gross bias).
    assert np.all(np.abs(counts - expected) < 0.20 * expected)


def test_defect_detectable() -> None:
    """Injected defect favor=(7, p): number 7 GROSSLY over-represented vs good."""
    n = 3000
    good = draws_from_stream(MT19937Stream(5), n)
    bad = draws_from_stream(MT19937Stream(5), n, favor=(7, 0.3))
    freq_good = sum(7 in d.main_numbers for d in good)
    freq_bad = sum(7 in d.main_numbers for d in bad)
    assert freq_bad > 1.5 * freq_good  # the defect must be visible to the naked eye


def test_period_truncation_repeats() -> None:
    """Defect period=p: draws repeat with period p (frozen cycle)."""
    p = 20
    draws = draws_from_stream(MT19937Stream(11), 100, period=p)
    for i in range(p, 100):
        # numbers (main+euron) identical every p; dates stay monotonic (re-stamp).
        assert draws[i].main_numbers == draws[i % p].main_numbers
        assert draws[i].euronumbers == draws[i % p].euronumbers
    dates = [d.draw_date for d in draws]
    assert dates == sorted(dates) and len(set(dates)) == 100  # dates still unique


def test_period_truncation_overdispersion() -> None:
    """Short period → FROZEN frequencies → count spread >> good RNG (over-dispersion).

    A different mechanism than favor: the whole distribution is frozen, not one number.
    The battery catches this via Family B (effective sample = period, not n)."""
    n, p = 1500, 50

    def _counts(draws: list) -> np.ndarray:
        c = np.zeros(50, dtype=np.int64)
        for d in draws:
            for x in d.main_numbers:
                c[x - 1] += 1
        return c

    good = _counts(draws_from_stream(MT19937Stream(5), n))
    truncated = _counts(draws_from_stream(MT19937Stream(5), n, period=p))
    # both have the same sum (n*5), but the cycle freezes deviations -> larger count variance
    assert truncated.sum() == good.sum() == n * 5
    assert truncated.var() > 3.0 * good.var()


def test_period_and_favor_mutually_exclusive() -> None:
    """favor + period simultaneously → ValueError (mutually exclusive defects)."""
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, favor=(7, 0.2), period=10)


def test_invalid_args() -> None:
    """Validation: n_draws<=0, favor out of range, period<=0 → ValueError."""
    stream = MT19937Stream(1)
    with pytest.raises(ValueError):
        draws_from_stream(stream, 0)
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, favor=(99, 0.1))
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, favor=(7, 1.5))
    with pytest.raises(ValueError):
        draws_from_stream(MT19937Stream(1), 10, period=0)


def test_randbelow_rejects_nonpositive() -> None:
    """randbelow(n<=0) → ValueError (unbiased sampling contract)."""
    with pytest.raises(ValueError):
        MT19937Stream(1).randbelow(0)
