"""Shuffle test core — stub (W1/W6).

Wzorzec (PoC verified 2026-05-17):
  @njit(cache=True) kontroluje wewnetrzny loop permutacji.
  joblib.Parallel nad konfiguracjami (test, regime, kernel_config, seed_offset).
  NIE nad pojedynczymi permutacjami.

Output: Parquet shards per worker w artifacts/permutations/{test}/{regime}/.
"""
