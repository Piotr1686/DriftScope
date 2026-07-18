"""Global fixtures and pytest configuration for DriftScope."""
import numpy as np
import pytest


@pytest.fixture(scope="session")
def base_seed() -> int:
    """Global deterministic seed (BASE_SEED=42)."""
    return 42


@pytest.fixture(scope="session")
def rng(base_seed: int) -> np.random.Generator:
    """Session-scoped RNG from SeedSequence — guarantees non-correlated streams."""
    return np.random.default_rng(np.random.SeedSequence(base_seed))


# Default tolerances for stochastic tests (see PROJECT_BRIEF.md §3)
STOCHASTIC_REL: float = 0.05
STOCHASTIC_ABS: float = 1e-3
