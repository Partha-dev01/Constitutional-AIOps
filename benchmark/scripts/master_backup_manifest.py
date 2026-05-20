"""Generate pre-zip manifest of every file under benchmark/ with SHA-256.

Output: benchmark/final/MASTER_BACKUP_MANIFEST_2026-05-20.json

Run from repo root.
"""
import os
import hashlib
import json
from pathlib import Path


def main():
    root = Path("benchmark")
    files = []
    total_size = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(".").as_posix()
        sz = p.stat().st_size
        total_size += sz
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        files.append({"path": rel, "size": sz, "sha256": h.hexdigest()})
    manifest = {
        "generated_at": "2026-05-20",
        "total_files": len(files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / 1e6, 2),
        "files": files,
    }
    print(f"Files: {len(files)}, Total size: {total_size:,} bytes ({total_size/1e6:.2f} MB)")
    out_path = Path("benchmark/final/MASTER_BACKUP_MANIFEST_2026-05-20.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written: {out_path.as_posix()}")


if __name__ == "__main__":
    main()
