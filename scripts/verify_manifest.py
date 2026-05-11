#!/usr/bin/env python3
"""scripts/verify_manifest.py — recompute hashes and check against a manifest.

Exits 0 if every file in the manifest is present and matches its recorded
SHA-256; exits non-zero with a diff if anything has drifted.

Usage:
    python scripts/verify_manifest.py [manifest_path]

If manifest_path is omitted, defaults to benchmark/data/manifest.json.

Designed to be added to CI as a required check before benchmark runs, so
a 62-bogus-cases-style silent drift surfaces immediately.

Non-destructive: read-only.
"""

from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        manifest_path = Path(argv[1])
    else:
        manifest_path = REPO_ROOT / "benchmark" / "data" / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text())

    errors: list[str] = []
    checked = 0

    for section in ("sources", "scripts", "outputs"):
        for rec in manifest.get(section, []):
            if rec.get("missing"):
                # Already-missing entries are warnings, not errors
                print(f"WARN missing: {rec['path']}")
                continue
            rel = rec.get("path")
            expected = rec.get("sha256")
            if not rel or not expected:
                continue
            p = REPO_ROOT / rel
            if not p.exists():
                errors.append(f"{section}: {rel} — MISSING ON DISK")
                continue
            actual = sha256_file(p)
            checked += 1
            if actual != expected:
                errors.append(
                    f"{section}: {rel}\n"
                    f"    expected: {expected}\n"
                    f"    actual:   {actual}"
                )

    if errors:
        print(f"VERIFY FAILED: {len(errors)} mismatches out of {checked + len(errors)} checked", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"VERIFY OK: {checked} files match manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
