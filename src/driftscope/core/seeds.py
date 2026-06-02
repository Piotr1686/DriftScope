"""Seed management — deterministyczne, niezależne strumienie RNG per worker."""
from __future__ import annotations

from numpy.random import SeedSequence


def make_worker_seeds(base_seed: int, n_workers: int) -> list[SeedSequence]:
    """Tworzy n_workers niezależnych SeedSequence z base_seed.

    Gwarantuje brak korelacji między strumieniami RNG dla joblib workers.
    Użycie w workerze: rng = np.random.default_rng(seed_seq)
    """
    root = SeedSequence(base_seed)
    return root.spawn(n_workers)
