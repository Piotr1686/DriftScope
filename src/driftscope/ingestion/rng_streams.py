"""Adaptery PRNG → strumien losowan EuroJackpot (benchmark reusability, wow Opcja α).

Kazdy generator PRNG dostarcza surowy strumien uint64; mapujemy go DETERMINISTYCZNIE
na losowania 5-z-50 (+2-z-K euron) w formacie `DrawRecord`, by przepuscic je przez
DOKLADNIE ten sam battery detektorow co audyt EuroJackpot (`pipeline.run_audit`).

Cel strategiczny: zamienic honest-null audytu w dowod CZULOSCI przyrzadu — framework
ma sie zapalac na PRNG z wstrzyknietym defektem (`favor=`), a milczec na krypto-PRNG
(ChaCha20) i na realnym EuroJackpot. To inkasuje deklarowany w CLAUDE.md claim
reusability (NIST RNG / cryptographic PRNG) jako zademonstrowany artefakt.

Uwaga architektoniczna: PRNG NIE jest opakowany w `np.random.Generator` — Xorshift64
i ChaCha20 nie sa numpy BitGeneratorami, a opakowanie MT19937 ukrywaloby fakt, ze to
rozne implementacje. Kazdy generator to wlasny `BitStream`; sampling 5-z-50 robi
unbiased rejection (bez modulo-bias) na surowych bitach. To czyni PRNG DOSLOWNYM
zrodlem losowan, nie posrednikiem.

Czysty modul ingestion: zna tylko `DrawRecord` + stdlib/cryptography. Nie zna detektorow.
"""
from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from datetime import date, timedelta

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms

from driftscope.core.types import DrawRecord

_U64 = 1 << 64
_MAIN_POOL = 50
_MAIN_DRAW = 5
_EURON_DRAW = 2
_ANCHOR = date(2015, 1, 2)  # piatek — daty syntetyczne (RNG stream nie modeluje real-data)


# ---------------------------------------------------------------------------
# BitStream — abstrakcyjne zrodlo uint64
# ---------------------------------------------------------------------------

class BitStream(ABC):
    """Pojedynczy PRNG jako strumien uint64 + unbiased sampling bez zwracania."""

    #: czytelna nazwa generatora (kolumna benchmarku)
    name: str = "abstract"

    @abstractmethod
    def next_u64(self) -> int:
        """Kolejne 64 bity pseudolosowe (0 <= x < 2^64)."""

    def randbelow(self, n: int) -> int:
        """Unbiased liczba calkowita w [0, n) — rejection sampling (bez modulo-bias).

        Odrzuca gorny niepelny blok [limit, 2^64), by reszta modulo byla rownomierna.
        Dla n=50 i 64-bit prawdopodobienstwo odrzucenia jest pomijalne (~3e-17), ale
        utrzymujemy uczciwosc: zero bias wprowadzonego przez adapter.
        """
        if n <= 0:
            raise ValueError(f"n musi byc > 0, otrzymano {n}")
        limit = _U64 - (_U64 % n)
        while True:
            x = self.next_u64()
            if x < limit:
                return x % n

    def sample_distinct(self, k: int, n: int) -> list[int]:
        """k roznych liczb 1..n (rosnaco) — partial Fisher-Yates na BitStream."""
        pool = list(range(1, n + 1))
        for i in range(k):
            j = i + self.randbelow(n - i)
            pool[i], pool[j] = pool[j], pool[i]
        return sorted(pool[:k])


# ---------------------------------------------------------------------------
# Konkretne generatory
# ---------------------------------------------------------------------------

class MT19937Stream(BitStream):
    """Mersenne Twister (stdlib `random.Random` JEST MT19937). Statystycznie dobry,
    NIE kryptograficzny (stan odtwarzalny z 624 wyjsc) — oczekiwany clear na naszych
    testach czestosci/wspolwystapien (defekty MT leza poza zasiegiem tego batterny)."""

    name = "MT19937"

    def __init__(self, seed: int) -> None:
        self._r = random.Random(seed)

    def next_u64(self) -> int:
        return self._r.getrandbits(64)


class Xorshift64Stream(BitStream):
    """Xorshift64 (Marsaglia 2003) — szybki, lekki, NIE kryptograficzny. Przechodzi
    proste testy czestosci, oblewa zaawansowane (TestU01). Tu kontrola: czy nasz
    battery (chi²/MMD/cooc na marginesach 5-z-50) go przepusci jak MT19937."""

    name = "Xorshift64"

    def __init__(self, seed: int) -> None:
        # Stan musi byc niezerowy (xorshift z 0 utknie w 0).
        self._s = (seed & (_U64 - 1)) or 0x9E3779B97F4A7C15

    def next_u64(self) -> int:
        x = self._s
        x ^= (x << 13) & (_U64 - 1)
        x ^= x >> 7
        x ^= (x << 17) & (_U64 - 1)
        self._s = x & (_U64 - 1)
        return self._s


class ChaCha20Stream(BitStream):
    """ChaCha20 keystream (cryptographic PRNG). Keystream = szyfrowanie zer kluczem
    wyprowadzonym z seeda (SHA-256). Reprezentant krypto-jakosci: oczekiwany clear,
    nieodroznialny od uniform pod kazdym testem batterny (specificity showcase)."""

    name = "ChaCha20"

    def __init__(self, seed: int) -> None:
        key = hashlib.sha256(seed.to_bytes(8, "little", signed=False)).digest()  # 32 B
        nonce = b"\x00" * 16  # 128-bit nonce; deterministyczny per seed
        self._enc = Cipher(algorithms.ChaCha20(key, nonce), mode=None).encryptor()
        self._buf = b""

    def next_u64(self) -> int:
        while len(self._buf) < 8:
            # update(zeros) zwraca czysty keystream (XOR z zerami = keystream).
            self._buf += self._enc.update(b"\x00" * 64)
        chunk, self._buf = self._buf[:8], self._buf[8:]
        return int.from_bytes(chunk, "little")


#: Rejestr nazwa → fabryka(seed) dla benchmarku. Wszystkie "dobre" (bez defektu).
STREAM_FACTORIES: dict[str, type[BitStream]] = {
    "MT19937": MT19937Stream,
    "Xorshift64": Xorshift64Stream,
    "ChaCha20": ChaCha20Stream,
}


# ---------------------------------------------------------------------------
# Mapowanie strumienia → losowania
# ---------------------------------------------------------------------------

def draws_from_stream(
    stream: BitStream,
    n_draws: int,
    *,
    euron_pool: int = 12,
    favor: tuple[int, float] | None = None,
) -> list[DrawRecord]:
    """Mapuje `n_draws` losowan 5-z-50 (+2-z-`euron_pool`) z `stream`.

    Daty syntetyczne (tygodniowe od kotwicy) — RNG stream modeluje proces generatywny,
    nie kalendarz. Kolejnosc chronologiczna (potrzebna dla BOCPD).

    `favor=(number, prob)` — WSTRZYKNIETY DEFEKT (pozytywna kontrola czulosci): w kazdym
    losowaniu z prawdopodobienstwem `prob` wymusza obecnosc `number` w puli glownej
    (podmieniajac najwiekszy slot, jesli `number` jeszcze nieobecny). Nadreprezentuje
    `number` → wykrywalne przez Family B (binomial), chi² i MMD. Coin defektu pochodzi
    z TEGO SAMEGO strumienia (determinizm). `None` = czysty uniform (good RNG).

    Args:
        stream: zrodlo PRNG (jedyne zrodlo losowosci).
        n_draws: liczba losowan (> 0).
        euron_pool: gorna granica puli euron (1..K); domyslnie 12 (R3).
        favor: opcjonalny defekt (numer 1-50, prawdopodobienstwo 0..1).

    Returns:
        Lista `n_draws` rekordow `DrawRecord` w porzadku chronologicznym.

    Raises:
        ValueError: gdy `n_draws` <= 0 lub `favor` poza zakresem.
    """
    if n_draws <= 0:
        raise ValueError(f"n_draws musi byc > 0, otrzymano {n_draws}")
    if favor is not None:
        fav_num, fav_prob = favor
        if not 1 <= fav_num <= _MAIN_POOL:
            raise ValueError(f"favor number {fav_num} poza 1-{_MAIN_POOL}")
        if not 0.0 <= fav_prob <= 1.0:
            raise ValueError(f"favor prob {fav_prob} poza 0..1")

    records: list[DrawRecord] = []
    for i in range(n_draws):
        main = stream.sample_distinct(_MAIN_DRAW, _MAIN_POOL)
        if favor is not None:
            fav_num, fav_prob = favor
            coin = stream.next_u64() / _U64
            if coin < fav_prob and fav_num not in main:
                main[-1] = fav_num  # podmien najwiekszy slot na faworyzowany
                main.sort()
        euron = stream.sample_distinct(_EURON_DRAW, euron_pool)
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
