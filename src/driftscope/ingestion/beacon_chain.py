"""Ethereum beacon chain slot occupancy → missed-slot record (Path B3).

Fetches, for a contiguous slot range, which slots carry a canonical block and which are
MISSED. That occupancy series is the observable behind the RANDAO withholding audit: a
proposer manipulating the RANDAO does it by NOT publishing, so the trace it leaves is a
missed slot, and the discriminating feature is that slot's POSITION WITHIN ITS EPOCH.

Why position-within-epoch is the right observable — and the mix is not: the epoch's final
RANDAO mix determines proposer duties two epochs later. Withholding only pays if the attacker
can PREDICT the resulting mix, which requires that no unpredictable contribution follows —
i.e. the attacker sits at the epoch's last slot, or owns a contiguous tail run. Manipulation
value therefore concentrates at position 31 and decays toward the front, while the mix's own
bit distribution stays uniform under the attack. See `ingestion/beacon_streams.py` for why the
mix is deliberately excluded from the uniformity battery.

Known benign confound: position 0 carries an ELEVATED miss rate unrelated to RANDAO — the
epoch transition (justification, finalization, reward and shuffling computation) lands on the
first slot, and slower nodes miss it. Position 0 is also the WORST possible withholding slot
(maximally far from the epoch end, 31 unpredictable contributions still to come), so the
benign and adversarial explanations point at opposite ends of the epoch. The audit reports
position 0 but excludes it from the null reference set; see `reporting/randao_audit.py`.

Correctness note: HTTP 404 means "no block at this slot" (a genuine miss) while a transport
error means "we do not know". These are never conflated — a network failure counts as a miss
nowhere, it is retried, and an unresolved slot aborts the scan rather than silently entering
the record as a miss. Fabricating misses would manufacture exactly the signal under test.
"""
from __future__ import annotations

import asyncio
import csv
import json
import ssl
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

#: Slots per epoch on the Ethereum beacon chain (phase 0 constant, unchanged since genesis).
SLOTS_PER_EPOCH = 32

#: Public consensus-layer REST endpoint. States are pruned here (the historical RANDAO mix is
#: NOT retrievable), but headers reach millions of slots back — which is all this audit needs.
DEFAULT_NODE = "https://ethereum-beacon-api.publicnode.com"

#: Conservative default: this is a free public service and a scan issues one request per slot.
DEFAULT_CONCURRENCY = 6

#: Sustained request rate. Measured empirically: bursts of a few hundred requests survive
#: >130 req/s, but a sustained scan is throttled to 429 within ~1400 requests at ~100 req/s,
#: while 25-44 req/s runs clean. The limiter targets the safe end and adapts downward on 429.
DEFAULT_RATE = 25.0

#: Slots per resumable chunk. Each completed chunk is checkpointed, so a throttle or a dropped
#: connection costs at most one chunk of re-work instead of the whole scan.
CHUNK_SLOTS = 1600


class SlotScanError(RuntimeError):
    """A slot could not be resolved to present-or-missed after retries.

    Raised rather than defaulting: an unresolved slot recorded as a miss would fabricate the
    very signal the audit tests for, and recorded as present would mask it.
    """


@dataclass(frozen=True)
class MissedSlot:
    """One slot with no canonical block."""

    slot: int
    epoch: int
    position: int


@dataclass(frozen=True)
class ScanMeta:
    """Provenance and denominators for a scan — without these the miss COUNTS are unreadable.

    `cursor` is the next unscanned slot: it equals `end_slot` for a complete scan and marks the
    resume point for a partial one. A partial scan is still a VALID sample (the range is
    contiguous and epoch-aligned), just a smaller one — `n_slots` always reports what was
    actually covered, never what was requested.
    """

    start_slot: int
    end_slot: int
    n_slots: int
    n_missed: int
    node: str
    fetched_at: str
    cursor: int = 0

    @property
    def complete(self) -> bool:
        return self.cursor >= self.end_slot


class RateLimiter:
    """Token-bucket limiter with AIMD congestion control (halve on 429, creep back on success).

    Multiplicative decrease alone is not enough for a long scan: a short burst of throttling
    would pin the rate at the floor for hours afterwards. Measured on this workload, four 429s
    took a 35 req/s scan down to 4 req/s and it never recovered, turning a ~45 minute job into
    a multi-hour one. Additive increase lets the scan climb back toward the target once the
    server stops complaining, so it tracks the sustainable rate instead of the worst rate ever
    observed — the same reason TCP uses AIMD rather than pure backoff.
    """

    #: successes required before nudging the rate back up
    RECOVERY_INTERVAL = 150
    #: fraction of the target rate added per recovery step
    RECOVERY_STEP = 0.10
    #: never drop below this — a stalled scan is worse than a slow one
    FLOOR = 2.0

    def __init__(self, rate: float) -> None:
        self.target = rate
        self.rate = rate
        self._next = 0.0
        self._ok_streak = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = asyncio.get_running_loop().time()
            self._next = max(now, self._next) + 1.0 / self.rate
            wait = self._next - now
        if wait > 0:
            await asyncio.sleep(wait)

    def throttled(self) -> None:
        """Server returned 429 — halve the rate and restart the recovery streak."""
        self.rate = max(self.FLOOR, self.rate / 2)
        self._ok_streak = 0

    def succeeded(self) -> None:
        """A clean response — after a long enough streak, creep back toward the target."""
        if self.rate >= self.target:
            return
        self._ok_streak += 1
        if self._ok_streak >= self.RECOVERY_INTERVAL:
            self._ok_streak = 0
            self.rate = min(self.target, self.rate + self.target * self.RECOVERY_STEP)


async def _slot_present(
    client: httpx.AsyncClient,
    node: str,
    slot: int,
    limiter: RateLimiter,
    *,
    attempts: int = 8,
) -> bool:
    """True if `slot` carries a canonical block, False if genuinely missed.

    404 (or a 200 with an empty payload) is authoritative for "missed". Anything else — a
    transport error, a 429, a 5xx — means "we do not know" and is retried. Exhausting retries
    raises rather than guessing: a rate-limit response recorded as a miss would fabricate
    exactly the withholding signature the audit is looking for.
    """
    last: str = "no attempt made"
    for attempt in range(attempts):
        await limiter.acquire()
        try:
            r = await client.get(f"{node}/eth/v1/beacon/headers?slot={slot}")
        except httpx.HTTPError as exc:  # transport failure — unknown, never a miss
            last = f"{type(exc).__name__}: {exc}"
        else:
            if r.status_code == 404:
                limiter.succeeded()
                return False
            if r.status_code == 200:
                try:
                    present = bool(r.json().get("data"))
                except ValueError as exc:
                    last = f"malformed JSON: {exc}"
                else:
                    limiter.succeeded()
                    return present
            elif r.status_code == 429:
                limiter.throttled()
                last = "HTTP 429 (rate limited)"
                retry_after = r.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    await asyncio.sleep(min(int(retry_after), 60))
                    continue
            else:
                last = f"HTTP {r.status_code}"
        await asyncio.sleep(min(2**attempt * 0.5, 30.0))
    raise SlotScanError(f"slot {slot} unresolved after {attempts} attempts ({last})")


async def scan_slot_range(
    start_slot: int,
    end_slot: int,
    *,
    node: str = DEFAULT_NODE,
    concurrency: int = DEFAULT_CONCURRENCY,
    rate: float = DEFAULT_RATE,
    checkpoint: Callable[[list[MissedSlot], ScanMeta], None] | None = None,
    resume_from: tuple[list[MissedSlot], ScanMeta] | None = None,
) -> tuple[list[MissedSlot], ScanMeta]:
    """Scans `[start_slot, end_slot)` and returns the missed slots plus scan metadata.

    Only MISSES are materialised: at a ~0.5% base rate the misses are a few hundred rows while
    the presences are hundreds of thousands, and `ScanMeta.n_slots` carries the denominator.

    Work proceeds in chunks of `CHUNK_SLOTS`, invoking `checkpoint` after each so an
    interrupted scan resumes from `ScanMeta.cursor` rather than starting over. Pass the loaded
    partial scan as `resume_from` to continue it.
    """
    if end_slot <= start_slot:
        raise ValueError(f"empty range: [{start_slot}, {end_slot})")

    missed: list[MissedSlot] = []
    cursor = start_slot
    if resume_from is not None:
        prior, prior_meta = resume_from
        if prior_meta.start_slot != start_slot or prior_meta.end_slot != end_slot:
            raise ValueError(
                f"resume range mismatch: checkpoint covers "
                f"[{prior_meta.start_slot}, {prior_meta.end_slot}), requested "
                f"[{start_slot}, {end_slot})"
            )
        missed, cursor = list(prior), max(start_slot, prior_meta.cursor)

    sem = asyncio.Semaphore(concurrency)
    limiter = RateLimiter(rate)
    total = end_slot - start_slot

    async with httpx.AsyncClient(
        verify=ssl.create_default_context(),
        timeout=30.0,
        limits=httpx.Limits(max_connections=concurrency),
        headers={"User-Agent": "DriftScope/0.1 (research audit framework)"},
    ) as client:

        async def one(slot: int) -> int | None:
            async with sem:
                present = await _slot_present(client, node, slot, limiter)
            return None if present else slot

        while cursor < end_slot:
            chunk_end = min(cursor + CHUNK_SLOTS, end_slot)
            results = await asyncio.gather(*(one(s) for s in range(cursor, chunk_end)))
            missed.extend(
                MissedSlot(slot=s, epoch=s // SLOTS_PER_EPOCH, position=s % SLOTS_PER_EPOCH)
                for s in sorted(x for x in results if x is not None)
            )
            cursor = chunk_end

            meta = _meta_for(start_slot, end_slot, cursor, missed, node)
            if checkpoint is not None:
                checkpoint(missed, meta)
            print(
                f"  ... {cursor - start_slot}/{total} slots, {len(missed)} missed "
                f"({limiter.rate:.0f} req/s)",
                flush=True,
            )

    return missed, _meta_for(start_slot, end_slot, cursor, missed, node)


def _meta_for(
    start_slot: int, end_slot: int, cursor: int, missed: list[MissedSlot], node: str
) -> ScanMeta:
    """Metadata for a scan covering `[start_slot, cursor)` within a target range."""
    return ScanMeta(
        start_slot=start_slot,
        end_slot=end_slot,
        n_slots=cursor - start_slot,
        n_missed=len(missed),
        node=node,
        fetched_at=datetime.now(tz=timezone.utc).isoformat(),
        cursor=cursor,
    )


def fetch_head_slot(node: str = DEFAULT_NODE) -> int:
    """Current head slot (synchronous — one call, used to anchor a scan range)."""
    with httpx.Client(
        verify=ssl.create_default_context(),
        timeout=30.0,
        headers={"User-Agent": "DriftScope/0.1 (research audit framework)"},
    ) as client:
        r = client.get(f"{node}/eth/v1/beacon/headers/head")
        r.raise_for_status()
        return int(r.json()["data"]["header"]["message"]["slot"])


# ---------------------------------------------------------------------------
# Persistence — missed slots (CSV) + scan denominators (JSON sidecar)
# ---------------------------------------------------------------------------

_CSV_FIELDS = ("slot", "epoch", "position")


def write_scan(csv_path: Path, meta_path: Path, missed: list[MissedSlot], meta: ScanMeta) -> None:
    """Writes the missed-slot record and its metadata sidecar."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(_CSV_FIELDS)
        for m in missed:
            w.writerow([m.slot, m.epoch, m.position])
    meta_path.write_text(json.dumps(asdict(meta), indent=2) + "\n", encoding="utf-8")


def load_scan(csv_path: Path, meta_path: Path) -> tuple[list[MissedSlot], ScanMeta]:
    """Loads a persisted scan, validating that the record is consistent with its metadata."""
    with csv_path.open(newline="", encoding="utf-8") as fh:
        missed = [
            MissedSlot(slot=int(r["slot"]), epoch=int(r["epoch"]), position=int(r["position"]))
            for r in csv.DictReader(fh)
        ]
    meta = ScanMeta(**json.loads(meta_path.read_text(encoding="utf-8")))

    if len(missed) != meta.n_missed:
        raise ValueError(f"{csv_path}: {len(missed)} rows but metadata claims {meta.n_missed}")
    for m in missed:
        if not meta.start_slot <= m.slot < meta.end_slot:
            raise ValueError(f"{csv_path}: slot {m.slot} outside scanned range")
        if m.epoch != m.slot // SLOTS_PER_EPOCH or m.position != m.slot % SLOTS_PER_EPOCH:
            raise ValueError(f"{csv_path}: slot {m.slot} has inconsistent epoch/position")
    return missed, meta
