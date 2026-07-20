"""Public randomness beacons → draw stream (Path B, reusability extension of wow Option alpha).

Extends the PRNG benchmark (`rng_streams.py`) with REAL public randomness beacons: drand
(League of Entropy, threshold BLS) and the NIST Randomness Beacon 2.0 (hardware entropy,
NIST IR 8213). Both publish a verifiable digest on a fixed cadence; we treat that digest
sequence as a `BitStream` and map it onto 5-of-50 draws through the SAME `draws_from_stream`
used for the PRNGs, then run the SAME battery.

What this DOES claim: a specificity showcase on real-world, externally-produced entropy.
ChaCha20/AES-CTR-DRBG are crypto-clean by construction (we generate them); drand and NIST are
crypto-clean by INDEPENDENT construction, published by third parties, with no seed we control.
A battery that stays silent here is being tested against entropy it did not manufacture.

What this does NOT claim: anything about MANIPULABILITY. Ethereum RANDAO is deliberately
ABSENT from this module. Two reasons, both load-bearing:
  1. Methodological — RANDAO's mix is an XOR of hashed BLS reveals. A proposer withholding a
     block picks one of 2^k candidates by a utility defined on DOWNSTREAM duty assignment, not
     on the bits. The marginal bit distribution stays uniform under the attack, so a uniformity
     battery on the mix tests the wrong hypothesis. The withholding trace lives in the
     POSITION-WITHIN-EPOCH of missed slots — audited separately (Path B3), not here.
  2. Practical — public beacon nodes prune state; `/eth/v1/beacon/states/{slot}/randao` 404s
     beyond ~100 slots, so a historical mix series is not retrievable without an archive node.

Architectural note: unlike a PRNG, a `BeaconStream` is FINITE and takes NO seed — the beacon
IS the entropy, and there is no state to re-derive. Reproducibility (DoD-6) therefore comes
from the committed CSV cache, not from `BASE_SEED`: the frozen digest file IS the artifact.
Exhaustion is a loud error, never a silent wrap-around, so a stream can never be reused as if
it carried more entropy than it does.

A pure ingestion module: it knows `BitStream` + stdlib/httpx, not the detectors.
"""
from __future__ import annotations

import csv
import ssl
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from driftscope.ingestion.rng_streams import BitStream

#: u64 draws per DrawRecord: sample_distinct(5, 50) + sample_distinct(2, euron_pool).
#: Rejection sampling can in principle consume more, but P(reject) ~ 3e-17 for n=50 and
#: ~2e-19 for n=12 — below any sample size we will ever fetch. Fetchers add headroom anyway.
_U64_PER_DRAW = 7
_BYTES_PER_U64 = 8

#: drand League of Entropy — default chained chain (30 s period, genesis 2020-07-22).
DRAND_API = "https://api.drand.sh"
DRAND_DEFAULT_CHAIN = "8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce"

#: NIST Randomness Beacon 2.0 — 512-bit pulses every 60 s. Chain 2 is the current chain.
NIST_API = "https://beacon.nist.gov/beacon/2.0"
NIST_DEFAULT_CHAIN = 2


class BeaconExhaustedError(RuntimeError):
    """A `BeaconStream` ran out of cached digest bytes.

    Raised instead of wrapping around: reusing the digest pool would silently repeat draws
    (a period-truncation defect indistinguishable from the one we INJECT as a positive
    control in `draws_from_stream(period=...)`). Fetch more rounds instead.
    """


@dataclass(frozen=True)
class BeaconPulse:
    """One published beacon value: chain index, UTC timestamp, hex digest."""

    index: int
    timestamp: str
    value_hex: str

    @property
    def value(self) -> bytes:
        return bytes.fromhex(self.value_hex)


def bytes_needed_for_draws(n_draws: int) -> int:
    """Digest bytes required to map `n_draws` draws (no headroom)."""
    return n_draws * _U64_PER_DRAW * _BYTES_PER_U64


# ---------------------------------------------------------------------------
# BeaconStream — finite uint64 source over published digests
# ---------------------------------------------------------------------------

class BeaconStream(BitStream):
    """A published beacon's digest sequence as a finite uint64 stream.

    Digests are concatenated in publication order and consumed little-endian in 8-byte
    chunks, inheriting `randbelow`/`sample_distinct` (unbiased rejection sampling) from
    `BitStream` unchanged — the adapter introduces no bias of its own, exactly as for the PRNGs.
    """

    def __init__(self, name: str, digests: Sequence[bytes]) -> None:
        if not digests:
            raise ValueError("digests must be non-empty")
        self.name = name
        self._buf = b"".join(digests)
        self._pos = 0

    @property
    def capacity_draws(self) -> int:
        """How many draws this stream can still supply (floor)."""
        return (len(self._buf) - self._pos) // (_U64_PER_DRAW * _BYTES_PER_U64)

    def next_u64(self) -> int:
        end = self._pos + _BYTES_PER_U64
        if end > len(self._buf):
            raise BeaconExhaustedError(
                f"{self.name}: consumed all {len(self._buf)} cached digest bytes "
                f"(~{len(self._buf) // (_U64_PER_DRAW * _BYTES_PER_U64)} draws). "
                "Fetch more rounds with scripts/fetch_beacons.py."
            )
        chunk = self._buf[self._pos:end]
        self._pos = end
        return int.from_bytes(chunk, "little")


# ---------------------------------------------------------------------------
# CSV cache — the committed, frozen artifact (DoD-6 substitute for a seed)
# ---------------------------------------------------------------------------

_CSV_FIELDS = ("index", "timestamp", "value_hex")


def write_beacon_csv(path: Path, pulses: Sequence[BeaconPulse]) -> None:
    """Writes pulses to the seed CSV cache (publication order preserved)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(_CSV_FIELDS)
        for p in pulses:
            writer.writerow([p.index, p.timestamp, p.value_hex])


def load_beacon_csv(path: Path, name: str) -> BeaconStream:
    """Loads a cached beacon CSV → `BeaconStream`.

    Verifies strictly increasing indices: a gap or reorder would break the "this is the
    published sequence" claim, and a duplicate would inject an artificial repeat.
    """
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"{path}: empty beacon cache")

    indices = [int(r["index"]) for r in rows]
    if any(b <= a for a, b in zip(indices, indices[1:])):
        raise ValueError(f"{path}: beacon indices must be strictly increasing")

    return BeaconStream(name, [bytes.fromhex(r["value_hex"]) for r in rows])


# ---------------------------------------------------------------------------
# Fetchers — live beacon APIs
# ---------------------------------------------------------------------------

def _client(timeout: float = 30.0) -> httpx.Client:
    """httpx client with an explicit default SSL context.

    `verify=ssl.create_default_context()` is deliberate: local TLS-inspecting AV (AVG) acts as
    a MITM and breaks httpx's bundled-CA verification. Using the OS trust store makes the
    fetchers work on the dev machine without disabling verification.
    """
    return httpx.Client(
        verify=ssl.create_default_context(),
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "DriftScope/0.1 (research audit framework)"},
    )


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=20))
def _get_json(client: httpx.Client, url: str) -> dict[str, Any]:
    r = client.get(url)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError(f"{url}: expected a JSON object, got {type(data).__name__}")
    return data


def fetch_drand_rounds(
    n_rounds: int,
    *,
    end_round: int | None = None,
    chain_hash: str = DRAND_DEFAULT_CHAIN,
) -> list[BeaconPulse]:
    """Fetches `n_rounds` consecutive drand rounds ending at `end_round` (default: latest).

    Each round yields a 32-byte `randomness` = SHA-256 of the threshold BLS signature over the
    previous signature and round number. Timestamps are derived from the chain's genesis and
    period rather than returned by the API.
    """
    if n_rounds <= 0:
        raise ValueError(f"n_rounds must be > 0, got {n_rounds}")

    with _client() as client:
        info = _get_json(client, f"{DRAND_API}/{chain_hash}/info")
        period, genesis = int(info["period"]), int(info["genesis_time"])
        if end_round is None:
            end_round = int(_get_json(client, f"{DRAND_API}/{chain_hash}/public/latest")["round"])

        start = end_round - n_rounds + 1
        if start < 1:
            raise ValueError(f"n_rounds={n_rounds} reaches before round 1 (end_round={end_round})")

        pulses: list[BeaconPulse] = []
        for rnd in range(start, end_round + 1):
            data = _get_json(client, f"{DRAND_API}/{chain_hash}/public/{rnd}")
            pulses.append(
                BeaconPulse(
                    index=int(data["round"]),
                    timestamp=_iso_utc(genesis + (int(data["round"]) - 1) * period),
                    value_hex=str(data["randomness"]),
                )
            )
    return pulses


def fetch_nist_pulses(
    n_pulses: int,
    *,
    end_index: int | None = None,
    chain_index: int = NIST_DEFAULT_CHAIN,
) -> list[BeaconPulse]:
    """Fetches `n_pulses` consecutive NIST Beacon 2.0 pulses ending at `end_index` (default: last).

    Each pulse yields a 512-bit `outputValue` (64 bytes) — twice drand's width, so roughly half
    as many requests are needed for the same byte budget.
    """
    if n_pulses <= 0:
        raise ValueError(f"n_pulses must be > 0, got {n_pulses}")

    with _client() as client:
        if end_index is None:
            end_index = int(_get_json(client, f"{NIST_API}/pulse/last")["pulse"]["pulseIndex"])

        start = end_index - n_pulses + 1
        if start < 1:
            raise ValueError(f"n_pulses={n_pulses} reaches before pulse 1 (end_index={end_index})")

        pulses: list[BeaconPulse] = []
        for idx in range(start, end_index + 1):
            data = _get_json(client, f"{NIST_API}/chain/{chain_index}/pulse/{idx}")["pulse"]
            pulses.append(
                BeaconPulse(
                    index=int(data["pulseIndex"]),
                    timestamp=str(data["timeStamp"]),
                    value_hex=str(data["outputValue"]).lower(),
                )
            )
    return pulses


def _iso_utc(unix_seconds: int) -> str:
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).isoformat()
