"""SHA-256 manifest generator dla reprodukowalnosci (DoD-6).

Generuje `artifacts/artifacts_manifest.json` z SHA-256 plikow danych — committed seed CSV
(Tier-1 kotwica) + ewentualne `artifacts/*.parquet` / `*.sqlite`. Pliki sortowane po
sciezce wzglednej (POSIX) → manifest jest DETERMINISTYCZNY: ta sama zawartosc daje
bit-identyczny JSON niezaleznie od kolejnosci systemu plikow.

DoD-6 ("cold-machine re-run = bit-identical SHA-256 CSV"): hash seed CSV jest kotwica —
dwie maszyny czytajace ten sam committed plik musza policzyc ten sam SHA-256. Funkcje
sa czyste i testowalne (`tests/test_reproducibility.py`).

Uruchomienie:
    python scripts/archive.py
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB — strumieniowe hashowanie (bez ladowania calego pliku do RAM)

# Wzorce plikow wchodzacych do manifestu (wzgledem root repo). Kolejnosc patternow
# nieistotna — finalny manifest sortowany po kluczu.
_PATTERNS: tuple[str, ...] = (
    "data/seed/*.csv",
    "artifacts/*.parquet",
    "artifacts/**/*.parquet",
    "artifacts/*.sqlite",
)


def sha256_file(path: Path) -> str:
    """SHA-256 (hex) pliku, strumieniowo. Deterministyczny dla danej zawartosci bajtow."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: Path) -> list[Path]:
    """Pliki danych do manifestu (unikalne, posortowane po sciezce wzglednej POSIX)."""
    seen: set[Path] = set()
    for pattern in _PATTERNS:
        for p in root.glob(pattern):
            if p.is_file():
                seen.add(p)
    return sorted(seen, key=lambda p: p.relative_to(root).as_posix())


def build_manifest(paths: Iterable[Path], root: Path) -> dict[str, str]:
    """Mapa {relpath POSIX: sha256}, posortowana po kluczu (determinizm)."""
    entries = {p.relative_to(root).as_posix(): sha256_file(p) for p in paths}
    return dict(sorted(entries.items()))


def write_manifest(root: Path, output: Path | None = None) -> dict[str, object]:
    """Buduje manifest dla `root` i zapisuje JSON (sort_keys → bit-identyczny output)."""
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
    print(f"Manifest: {len(files)} plikow (root={root})")
    for rel, digest in files.items():
        print(f"  {digest[:12]}…  {rel}")


if __name__ == "__main__":
    main()
