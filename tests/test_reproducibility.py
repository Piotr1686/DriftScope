"""Testy reprodukowalnosci (DoD-6).

DoD-6: "cold-machine re-run = bit-identical SHA-256 CSV". Trzy filary:
  1. **Seed management** — `make_worker_seeds` deterministyczny (ten sam base_seed →
     identyczne strumienie RNG).
  2. **Pure-function reseed** — detektory sa CZYSTYMI FUNKCJAMI `draws`: powtorne
     wywolanie daje bit-identyczny wynik, a kolejnosc wywolan (globalny stan RNG
     numba/numpy) NIE wplywa na wynik (seed z zawartosci draws, nie ze stanu).
  3. **Manifest SHA-256** — `scripts/archive.py` liczy deterministyczny hash committed
     seed CSV (Tier-1 kotwica) niezaleznie od liczby wywolan.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from driftscope.core.seeds import make_worker_seeds
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.methodology.cooccurrence import cooccurrence_detector
from driftscope.methodology.permutation import serial_overlap_detector
from driftscope.methodology.recurrence import recurrence_detector

_ROOT = Path(__file__).resolve().parents[1]
_SEED_CSV = _ROOT / "data" / "seed" / "eurojackpot_history.csv"


def _load_archive():
    """Importuje scripts/archive.py (poza pakietem) przez importlib."""
    path = _ROOT / "scripts" / "archive.py"
    spec = importlib.util.spec_from_file_location("archive", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _draws(n: int = 60, seed: int = 7):
    rng = np.random.default_rng(seed)
    return generate_uniform_draws(n, "R3", rng)


# --- 1. Seed management -----------------------------------------------------

def test_make_worker_seeds_deterministic() -> None:
    """Ten sam base_seed → identyczne SeedSequence (stan RNG bit-identyczny)."""
    s1 = make_worker_seeds(42, 5)
    s2 = make_worker_seeds(42, 5)
    assert len(s1) == len(s2) == 5
    for a, b in zip(s1, s2):
        assert np.array_equal(a.generate_state(8), b.generate_state(8))


def test_make_worker_seeds_streams_independent() -> None:
    """Rozne workery → rozne strumienie (brak korelacji = nie identyczne stany)."""
    seeds = make_worker_seeds(42, 4)
    states = [tuple(s.generate_state(4).tolist()) for s in seeds]
    assert len(set(states)) == 4  # wszystkie rozne


# --- 2. Pure-function reseed (DoD-6 rdzen) ----------------------------------

@pytest.mark.parametrize(
    "factory",
    [
        lambda: serial_overlap_detector(n_perm=49),
        lambda: recurrence_detector(n_perm=49),
        lambda: cooccurrence_detector(n_perm=49),
    ],
    ids=["serial_overlap", "recurrence", "cooccurrence"],
)
def test_detector_repeat_is_bit_identical(factory) -> None:
    """Powtorne wywolanie tego samego detektora na tych samych draws → identyczny wynik."""
    draws = _draws()
    det = factory()
    r1 = det(draws)
    r2 = det(draws)
    assert r1.statistic == r2.statistic
    assert r1.p_value == r2.p_value
    assert r1.reject_h0 == r2.reject_h0


def test_detector_call_order_independence() -> None:
    """Pure-function reseed: wynik detektora A nie zalezy od tego, czy miedzy jego
    wywolaniami zadzialal detektor B (ktory ustawia globalny stan np.random)."""
    draws = _draws()
    det_a = serial_overlap_detector(n_perm=49)
    det_b = cooccurrence_detector(n_perm=49)  # mutuje globalny stan numba/numpy

    r_a1 = det_a(draws)
    _ = det_b(draws)            # "skazenie" globalnego RNG miedzy wywolaniami A
    r_a2 = det_a(draws)

    assert r_a1.statistic == r_a2.statistic
    assert r_a1.p_value == r_a2.p_value


def test_detector_seed_depends_on_content() -> None:
    """Rozna zawartosc draws → (z duzym prawdopodobienstwem) rozny seed → rozny null.

    Sanity: detektor NIE zwraca sta+lej niezaleznie od danych."""
    det = serial_overlap_detector(n_perm=99)
    r_seed7 = det(_draws(seed=7))
    r_seed8 = det(_draws(seed=8))
    # Statystyki obserwowane musza sie roznic dla roznych danych (nie zdegenerowane).
    assert r_seed7.statistic != r_seed8.statistic


# --- 3. Manifest SHA-256 ----------------------------------------------------

@pytest.mark.skipif(not _SEED_CSV.exists(), reason="Seed CSV niedostępny")
def test_seed_csv_hash_deterministic() -> None:
    """SHA-256 committed seed CSV jest stabilny miedzy wywolaniami (DoD-6 kotwica)."""
    archive = _load_archive()
    h1 = archive.sha256_file(_SEED_CSV)
    h2 = archive.sha256_file(_SEED_CSV)
    assert h1 == h2
    assert len(h1) == 64 and all(c in "0123456789abcdef" for c in h1)


def test_build_manifest_deterministic_and_sorted() -> None:
    """build_manifest dwa razy → identyczny, posortowany po kluczu."""
    archive = _load_archive()
    files = archive.collect_files(_ROOT)
    m1 = archive.build_manifest(files, _ROOT)
    m2 = archive.build_manifest(files, _ROOT)
    assert m1 == m2
    assert list(m1) == sorted(m1)  # klucze posortowane
    assert all(len(h) == 64 for h in m1.values())


def test_write_manifest_byte_identical(tmp_path) -> None:
    """write_manifest do tego samego wejscia → bit-identyczny JSON (sort_keys)."""
    archive = _load_archive()
    out1 = tmp_path / "m1.json"
    out2 = tmp_path / "m2.json"
    archive.write_manifest(_ROOT, output=out1)
    archive.write_manifest(_ROOT, output=out2)
    assert out1.read_bytes() == out2.read_bytes()
