"""SHA-256 manifest generator dla git-lfs artifacts — stub (W1).

Generuje artifacts_manifest.json z hash'ami posortowanych plikow Parquet.
Determinizm: ORDER BY (test, regime, seed) przed hashowaniem CSV eksportu.
"""
