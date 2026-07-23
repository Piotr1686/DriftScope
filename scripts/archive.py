"""SHA-256 manifest generator for reproducibility (DoD-6).

Generates `artifacts/artifacts_manifest.json` with SHA-256 of the data files — the committed
seed CSV (Tier-1 anchor) plus any `artifacts/*.parquet`. Files are sorted by relative POSIX
path → the manifest is DETERMINISTIC: the same content yields a bit-identical JSON regardless
of filesystem ordering.

DoD-6 ("cold-machine re-run = bit-identical SHA-256 CSV"): the seed CSV hash is the anchor —
two machines reading the same committed file must compute the same SHA-256. The functions are
pure and testable (`tests/test_reproducibility.py`).

Usage:
    python scripts/archive.py
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB — streaming hashing (without loading the whole file into RAM)

# File patterns included in the manifest (relative to the repo root). Pattern order is
# irrelevant — the final manifest is sorted by key.
_PATTERNS: tuple[str, ...] = (
    "data/seed/*.csv",
    "artifacts/*.parquet",
    "artifacts/**/*.parquet",
)


def sha256_file(path: Path) -> str:
    """SHA-256 (hex) of a file, streamed. Deterministic for the given byte content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: Path) -> list[Path]:
    """Data files for the manifest (unique, sorted by relative POSIX path)."""
    seen: set[Path] = set()
    for pattern in _PATTERNS:
        for p in root.glob(pattern):
            if p.is_file():
                seen.add(p)
    return sorted(seen, key=lambda p: p.relative_to(root).as_posix())


def build_manifest(paths: Iterable[Path], root: Path) -> dict[str, str]:
    """Map {relpath POSIX: sha256}, sorted by key (determinism)."""
    entries = {p.relative_to(root).as_posix(): sha256_file(p) for p in paths}
    return dict(sorted(entries.items()))


def write_manifest(root: Path, output: Path | None = None) -> dict[str, object]:
    """Build the manifest for `root` and write JSON (sort_keys → bit-identical output)."""
    manifest = build_manifest(collect_files(root), root)
    payload: dict[str, object] = {"version": 1, "files": manifest}
    out = output or root / "artifacts" / "artifacts_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = write_manifest(root)
    files = payload["files"]
    assert isinstance(files, dict)
    print(f"Manifest: {len(files)} files (root={root})")
    for rel, digest in files.items():
        print(f"  {digest[:12]}…  {rel}")


if __name__ == "__main__":
    main()
