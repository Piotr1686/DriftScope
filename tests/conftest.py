"""Globalne fixtures i konfiguracja pytest dla DriftScope."""
import pytest
import numpy as np


@pytest.fixture(scope="session")
def base_seed() -> int:
    """Globalny seed deterministyczny (BASE_SEED=42)."""
    return 42


@pytest.fixture(scope="session")
def rng(base_seed: int) -> np.random.Generator:
    """Sesyjny RNG z SeedSequence — gwarancja non-correlated streams."""
    return np.random.default_rng(np.random.SeedSequence(base_seed))


# Domyslne tolerancje dla testow stochastycznych (zob. PROJECT_BRIEF.md §3)
STOCHASTIC_REL: float = 0.05
STOCHASTIC_ABS: float = 1e-3
