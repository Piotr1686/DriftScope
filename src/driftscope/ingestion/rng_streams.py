"""PRNG adapters → EuroJackpot draw stream (reusability benchmark, wow Option α).

Each PRNG provides a raw uint64 stream; we map it DETERMINISTICALLY onto 5-of-50 draws
(+2-of-K euron) in `DrawRecord` format, to run them through EXACTLY the same detector
battery as the EuroJackpot audit (`pipeline.run_audit`).

Strategic goal: turn the audit's honest-null into PROOF of the instrument's SENSITIVITY —
the framework should fire on a PRNG with an injected defect (`favor=`) and stay silent on a
crypto-PRNG (ChaCha20) and on real EuroJackpot. This cashes the reusability claim stated in
CLAUDE.md (NIST RNG / cryptographic PRNG) as a demonstrated artifact.

Architectural note: the PRNG is NOT wrapped in `np.random.Generator` — Xorshift64 and
ChaCha20 are not numpy BitGenerators, and wrapping MT19937 would hide the fact that these are
different implementations. Each generator is its own `BitStream`; the 5-of-50 sampling does
unbiased rejection (no modulo bias) on raw bits. This makes the PRNG a LITERAL source of
draws, not an intermediary.

A pure ingestion module: it only knows `DrawRecord` + stdlib/cryptography, not the detectors.
"""
from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from datetime import date, timedelta

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from driftscope.core.types import DrawRecord

_U64 = 1 << 64
_MAIN_POOL = 50
_MAIN_DRAW = 5
_EURON_DRAW = 2
_ANCHOR = date(2015, 1, 2)  # Friday — synthetic dates (the RNG stream does not model real data)


# ---------------------------------------------------------------------------
# BitStream — abstract uint64 source
# ---------------------------------------------------------------------------

class BitStream(ABC):
    """A single PRNG as a uint64 stream + unbiased sampling without replacement."""

    #: human-readable generator name (benchmark column)
    name: str = "abstract"

    @abstractmethod
    def next_u64(self) -> int:
        """The next 64 pseudo-random bits (0 <= x < 2^64)."""

    def randbelow(self, n: int) -> int:
        """Unbiased integer in [0, n) — rejection sampling (no modulo bias).

        Rejects the top incomplete block [limit, 2^64) so that the modulo remainder is
        uniform. For n=50 and 64-bit the rejection probability is negligible (~3e-17), but
        we keep it honest: zero bias introduced by the adapter.
        """
        if n <= 0:
            raise ValueError(f"n must be > 0, got {n}")
        limit = _U64 - (_U64 % n)
        while True:
            x = self.next_u64()
            if x < limit:
                return x % n

    def sample_distinct(self, k: int, n: int) -> list[int]:
        """k distinct numbers 1..n (ascending) — partial Fisher-Yates on the BitStream."""
        pool = list(range(1, n + 1))
        for i in range(k):
            j = i + self.randbelow(n - i)
            pool[i], pool[j] = pool[j], pool[i]
        return sorted(pool[:k])


# ---------------------------------------------------------------------------
# Concrete generators
# ---------------------------------------------------------------------------

class MT19937Stream(BitStream):
    """Mersenne Twister (the stdlib `random.Random` IS MT19937). Statistically good,
    NOT cryptographic (state recoverable from 624 outputs) — expected clear on our
    frequency/co-occurrence tests (MT defects lie beyond this battery's reach)."""

    name = "MT19937"

    def __init__(self, seed: int) -> None:
        self._r = random.Random(seed)

    def next_u64(self) -> int:
        return self._r.getrandbits(64)


class Xorshift64Stream(BitStream):
    """Xorshift64 (Marsaglia 2003) — fast, lightweight, NOT cryptographic. Passes
    simple frequency tests, fails advanced ones (TestU01). Here a control: whether our
    battery (chi²/MMD/cooc on 5-of-50 margins) lets it through like MT19937."""

    name = "Xorshift64"

    def __init__(self, seed: int) -> None:
        # State must be non-zero (xorshift from 0 gets stuck at 0).
        self._s = (seed & (_U64 - 1)) or 0x9E3779B97F4A7C15

    def next_u64(self) -> int:
        x = self._s
        x ^= (x << 13) & (_U64 - 1)
        x ^= x >> 7
        x ^= (x << 17) & (_U64 - 1)
        self._s = x & (_U64 - 1)
        return self._s


class ChaCha20Stream(BitStream):
    """ChaCha20 keystream (cryptographic PRNG). The keystream = encrypting zeros with a key
    derived from the seed (SHA-256). A representative of crypto quality: expected clear,
    indistinguishable from uniform under every battery test (specificity showcase)."""

    name = "ChaCha20"

    def __init__(self, seed: int) -> None:
        key = hashlib.sha256(seed.to_bytes(8, "little", signed=False)).digest()  # 32 B
        nonce = b"\x00" * 16  # 128-bit nonce; deterministic per seed
        self._enc = Cipher(algorithms.ChaCha20(key, nonce), mode=None).encryptor()
        self._buf = b""

    def next_u64(self) -> int:
        while len(self._buf) < 8:
            # update(zeros) returns the raw keystream (XOR with zeros = keystream).
            self._buf += self._enc.update(b"\x00" * 64)
        chunk, self._buf = self._buf[:8], self._buf[8:]
        return int.from_bytes(chunk, "little")


class AESCtrDrbgStream(BitStream):
    """AES-256 in CTR mode as a DRBG (deterministic random bit generator, skeleton of
    NIST SP 800-90A CTR_DRBG). The keystream = encrypting zeros with a key from the seed
    (SHA-256, 32 B = AES-256), the counter starting at zero. A second representative of
    crypto quality alongside ChaCha20 — expected clear, indistinguishable from uniform (a
    specificity showcase on a different primitive: a block cipher in CTR vs the ChaCha stream)."""

    name = "AES-CTR-DRBG"

    def __init__(self, seed: int) -> None:
        key = hashlib.sha256(seed.to_bytes(8, "little", signed=False)).digest()  # 32 B
        nonce = b"\x00" * 16  # 128-bit initial counter block; deterministic per seed
        self._enc = Cipher(algorithms.AES(key), modes.CTR(nonce)).encryptor()
        self._buf = b""

    def next_u64(self) -> int:
        while len(self._buf) < 8:
            # update(zeros) in CTR returns the raw keystream (XOR with zeros = keystream).
            self._buf += self._enc.update(b"\x00" * 64)
        chunk, self._buf = self._buf[:8], self._buf[8:]
        return int.from_bytes(chunk, "little")


#: Registry name → factory(seed) for the benchmark. All "good" (defect-free).
STREAM_FACTORIES: dict[str, type[BitStream]] = {
    "MT19937": MT19937Stream,
    "Xorshift64": Xorshift64Stream,
    "ChaCha20": ChaCha20Stream,
    "AES-CTR-DRBG": AESCtrDrbgStream,
}


# ---------------------------------------------------------------------------
# Stream → draws mapping
# ---------------------------------------------------------------------------

def draws_from_stream(
    stream: BitStream,
    n_draws: int,
    *,
    euron_pool: int = 12,
    favor: tuple[int, float] | None = None,
    period: int | None = None,
) -> list[DrawRecord]:
    """Maps `n_draws` draws 5-of-50 (+2-of-`euron_pool`) from `stream`.

    Synthetic dates (weekly from an anchor) — the RNG stream models the generative process,
    not the calendar. Chronological order (needed for BOCPD).

    Two MUTUALLY EXCLUSIVE defects (positive sensitivity control; supply at most one):

    `favor=(number, prob)` — MARGINAL bias: in each draw, with probability `prob`, force
    the presence of `number` in the main pool (replacing the largest slot if `number` is not
    yet present). Over-represents `number` → detectable by Family B (binomial), chi² and MMD.
    The defect coin comes from THE SAME stream (determinism).

    `period=p` — SHORT PERIOD (period-truncation): the generator behaves like a PRNG with a
    period of `p` draws — the first `p` draws form a cycle that REPEATS up to `n_draws`. The
    frequencies are then FROZEN at the cycle's values and do not average out with n → at
    n ≫ p the deviations grow ~(n/p)× above binomial noise → OVER-DISPERSION of counts,
    detectable by Family B (effective sample = `p`, not `n`) and MMD (windows ~identical vs
    uniform). A different mechanism than `favor` (the whole distribution frozen, not one number).

    `None`/`None` = pure uniform (good RNG).

    Args:
        stream: the PRNG source (the only source of randomness).
        n_draws: the number of draws (> 0).
        euron_pool: the upper bound of the euron pool (1..K); default 12 (R3).
        favor: optional marginal defect (number 1-50, probability 0..1).
        period: optional period-truncation defect (cycle length > 0).

    Returns:
        A list of `n_draws` `DrawRecord` records in chronological order.

    Raises:
        ValueError: when `n_draws` <= 0, `favor` out of range, `period` <= 0,
            or when BOTH `favor` and `period` are supplied.
    """
    if n_draws <= 0:
        raise ValueError(f"n_draws must be > 0, got {n_draws}")
    if favor is not None and period is not None:
        raise ValueError("favor and period are mutually exclusive defects — supply at most one")
    if period is not None and period <= 0:
        raise ValueError(f"period must be > 0, got {period}")
    if favor is not None:
        fav_num, fav_prob = favor
        if not 1 <= fav_num <= _MAIN_POOL:
            raise ValueError(f"favor number {fav_num} out of 1-{_MAIN_POOL}")
        if not 0.0 <= fav_prob <= 1.0:
            raise ValueError(f"favor prob {fav_prob} out of 0..1")

    # Number of UNIQUE draws from the stream: under period-truncation we generate only the
    # `period` cycle (then repeated); without a defect = full `n_draws` (period=None →
    # n_unique=n_draws → i % n_unique == i → identical behaviour to no cycle).
    n_unique = n_draws if period is None else min(period, n_draws)

    cycle: list[tuple[list[int], list[int]]] = []
    for _ in range(n_unique):
        main = stream.sample_distinct(_MAIN_DRAW, _MAIN_POOL)
        if favor is not None:
            fav_num, fav_prob = favor
            coin = stream.next_u64() / _U64
            if coin < fav_prob and fav_num not in main:
                main[-1] = fav_num  # replace the largest slot with the favoured number
                main.sort()
        euron = stream.sample_distinct(_EURON_DRAW, euron_pool)
        cycle.append((main, euron))

    records: list[DrawRecord] = []
    for i in range(n_draws):
        main, euron = cycle[i % n_unique]  # cyclic repetition under period-truncation
        records.append(
            DrawRecord(
                draw_date=_ANCHOR + timedelta(weeks=i),
                main_1=main[0],
                main_2=main[1],
                main_3=main[2],
                main_4=main[3],
                main_5=main[4],
                euron_1=euron[0],
                euron_2=euron[1],
            )
        )
    return records
