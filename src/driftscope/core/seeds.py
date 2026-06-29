"""Seed management — deterministic, independent per-worker RNG streams."""
from __future__ import annotations

from numpy.random import SeedSequence


def make_worker_seeds(base_seed: int, n_workers: int) -> list[SeedSequence]:
    """Creates n_workers independent SeedSequences from base_seed.

    Guarantees no correlation between RNG streams for joblib workers.
    Usage in a worker: rng = np.random.default_rng(seed_seq)
    """
    root = SeedSequence(base_seed)
    return root.spawn(n_workers)
