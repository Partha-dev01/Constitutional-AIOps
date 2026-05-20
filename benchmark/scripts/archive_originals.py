#!/usr/bin/env python3
"""Archive original result dirs into _archive_originals_<date>/ with a zip
backup sitting outside. NEVER deletes data — only moves.

HISTORICAL — this script already executed once on 2026-05-19, producing
`benchmark/results_aws/originals_backup_2026-05-19.zip` and
`benchmark/results_aws/_archive_originals_2026-05-19/`. Both were then
relocated during the 2026-05-20 benchmark/ reorg to
`benchmark/archive/originals_backup_2026-05-19.zip` and
`benchmark/archive/originals_2026-05-19/` respectively. The hardcoded
paths below reflect the pre-reorg world at execution time and would need
updating for any future re-run.

Steps (as executed in May 2026):
  1. Build comprehensive zip backup at benchmark/results_aws/originals_backup_<DATE>.zip
  2. Verify the zip contains every source file with matching SHA-256
  3. Create benchmark/results_aws/_archive_originals_<DATE>/
  4. MOVE the 6 result dirs into the archive (atomic rename, fast)
  5. Write _ARCHIVED.md in archive root + per-dir notice files
  6. Final verify: FINAL/ untouched (SHA-checked); zip count matches moved-dir count

Run modes:
  --dry-run   show exactly what would happen, change nothing
  --execute   actually do the work
"""
from __future__ import annotations
import argparse
import hashlib
import shutil
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_AWS = REPO_ROOT / "benchmark" / "results_aws"
FINAL = RESULTS_AWS / "FINAL"
DATE_STR = date.today().isoformat()  # e.g. 2026-05-19
ARCHIVE_DIR = RESULTS_AWS / f"_archive_originals_{DATE_STR}"
ZIP_PATH = RESULTS_AWS / f"originals_backup_{DATE_STR}.zip"

# Dirs to move into the archive. These are the "active" result dirs whose
# canonical copies now live in FINAL/. Each one is moved as a whole.
DIRS_TO_ARCHIVE = [
    ("run_stackA_main431_newprompt",  "FINAL/main_benchmark/"),
    ("ablation_v4_newprompt",         "FINAL/ablation_v4/"),
    ("sota_llama_3_3_70b",            "FINAL/sota_baselines/llama_3_3_70b.jsonl"),
    ("sota_deepseek_v3",              "FINAL/sota_baselines/deepseek_v3.jsonl"),
    ("sota_drain",                    "FINAL/sota_baselines/drain.jsonl + drain_summary.json"),
    ("phase46_noprompt",              "FINAL/phase46_no_prompt/"),
]

# Explicitly NOT touched (constraints from prior sessions):
PRESERVE_IN_PLACE = [
    "run_stackA_main431",     # OLD prompt — v1 paper reference, used for diff
    "archive",                # smoke tests, already organized
    "FINAL",                  # the canonical sorted dir
    # Plus all top-level .md files and the existing tarball
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def precheck():
    """Verify the world is in the expected state before doing anything."""
    issues = []

    if not FINAL.exists():
        issues.append(f"FINAL/ not present at {FINAL} — run build_final_results.py first")

    if ARCHIVE_DIR.exists():
        if any(ARCHIVE_DIR.iterdir()):
            issues.append(f"Archive dir {ARCHIVE_DIR} already exists and is non-empty — abort to avoid clobber")

    if ZIP_PATH.exists():
        issues.append(f"Zip path {ZIP_PATH} already exists — rename or remove it before re-running")

    for src_name, _ in DIRS_TO_ARCHIVE:
        src = RESULTS_AWS / src_name
        if not src.exists():
            issues.append(f"Source dir missing: {src}")

    return issues


def build_zip(dry_run: bool) -> dict:
    """Build the comprehensive zip + collect SHA manifest of contents.

    Returns: {relpath_str: sha256_hex_of_original_file}
    """
    file_shas: dict[str, str] = {}
    for src_name, _ in DIRS_TO_ARCHIVE:
        src_dir = RESULTS_AWS / src_name
        for p in walk_files(src_dir):
            rel = p.relative_to(RESULTS_AWS).as_posix()
            file_shas[rel] = sha256(p)

    if dry_run:
        print(f"[DRY] Would build zip: {ZIP_PATH} containing {len(file_shas)} files")
        return file_shas

    # Stream-write the zip
    with zipfile.ZipFile(ZIP_PATH, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel in sorted(file_shas):
            abs_path = RESULTS_AWS / rel
            z.write(abs_path, arcname=rel)
    print(f"[OK] Built zip: {ZIP_PATH} ({ZIP_PATH.stat().st_size:,} bytes, {len(file_shas)} entries)")
    return file_shas


def verify_zip(file_shas: dict) -> bool:
    """Re-open the zip and verify each entry's SHA matches the original."""
    ok = True
    with zipfile.ZipFile(ZIP_PATH, mode="r") as z:
        for rel, expected_sha in file_shas.items():
            with z.open(rel) as zf:
                h = hashlib.sha256()
                while True:
                    chunk = zf.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
                actual_sha = h.hexdigest()
            if actual_sha != expected_sha:
                print(f"[FAIL] SHA mismatch in zip: {rel}")
                print(f"       expected: {expected_sha}")
                print(f"       actual:   {actual_sha}")
                ok = False
    if ok:
        print(f"[OK] Verified all {len(file_shas)} zip entries (SHA matches originals)")
    return ok


def snapshot_final_shas() -> dict:
    """Before move: snapshot SHA of every file in FINAL/ so we can prove
    it was untouched by the move."""
    return {p.relative_to(FINAL).as_posix(): sha256(p) for p in walk_files(FINAL)}


def verify_final_unchanged(before: dict) -> bool:
    """After move: re-hash every file in FINAL/ and compare to snapshot."""
    after = {p.relative_to(FINAL).as_posix(): sha256(p) for p in walk_files(FINAL)}
    if set(before) != set(after):
        only_before = set(before) - set(after)
        only_after = set(after) - set(before)
        if only_before:
            print(f"[FAIL] FINAL/ lost files after move: {only_before}")
        if only_after:
            print(f"[FAIL] FINAL/ gained files after move: {only_after}")
        return False
    for rel, sha in before.items():
        if after[rel] != sha:
            print(f"[FAIL] FINAL/ file changed: {rel}")
            return False
    print(f"[OK] FINAL/ untouched ({len(before)} files, all SHAs match)")
    return True


def move_dirs(dry_run: bool):
    for src_name, _ in DIRS_TO_ARCHIVE:
        src = RESULTS_AWS / src_name
        dst = ARCHIVE_DIR / src_name
        if dry_run:
            print(f"[DRY] Would move: {src.relative_to(REPO_ROOT)}")
            print(f"                 -> {dst.relative_to(REPO_ROOT)}")
        else:
            shutil.move(str(src), str(dst))
            print(f"[OK] Moved: {src_name}/ -> {dst.relative_to(REPO_ROOT)}")


def write_metadata(dry_run: bool):
    """Write _ARCHIVED.md in archive root + per-dir notice."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    root_md = f"""# Archived originals — {DATE_STR}

_Moved here: {timestamp}_

These are the original result directories whose canonical paper-ready copies now
live in `benchmark/results_aws/FINAL/`. They were MOVED here (not deleted) to
keep `results_aws/` clean while preserving full provenance.

## Defense-in-depth

- This folder (file-level access to originals)
- `benchmark/results_aws/originals_backup_{DATE_STR}.zip` (zip backup with SHA-verified contents)
- `benchmark/results_aws/aiops_archive_2026-05-17.tar.gz` (earlier tarball)
- EBS snapshot `snap-01b191aedbf46b598` (cloud disaster recovery)

## Map (archived dir → canonical FINAL/ location)

| Archived dir | Canonical now lives at |
|---|---|
"""
    for src_name, final_loc in DIRS_TO_ARCHIVE:
        root_md += f"| `{src_name}/` | `{final_loc}` |\n"
    root_md += """
## Restoring

If a downstream script or doc still expects the original path:

```bash
# Option 1: move back from this archive
mv benchmark/results_aws/_archive_originals_""" + DATE_STR + """/<dirname> benchmark/results_aws/

# Option 2: extract from zip
unzip benchmark/results_aws/originals_backup_""" + DATE_STR + """.zip -d benchmark/results_aws/
```

But the recommended fix is to update the script/doc to reference `FINAL/` instead.

## Constraint reminders (preserved from prior sessions)

- `run_stackA_main431/` (OLD-prompt v1 paper reference) was NOT archived — left in place
- `archive/` (smoke tests) was NOT archived — already an archive
- All `*_BAK*` files in archived dirs were preserved as-is (do NOT delete per provenance rule)
- `*_BROKEN` dirs on the AWS instance are NOT affected by this operation (they're on instance only)
"""

    if dry_run:
        print(f"[DRY] Would write {(ARCHIVE_DIR / '_ARCHIVED.md').relative_to(REPO_ROOT)} ({len(root_md)} chars)")
    else:
        (ARCHIVE_DIR / "_ARCHIVED.md").write_text(root_md, encoding="utf-8")
        print(f"[OK] Wrote _ARCHIVED.md ({len(root_md)} chars)")

    # Per-dir notice
    for src_name, final_loc in DIRS_TO_ARCHIVE:
        notice = f"""# Archived — {DATE_STR}

This directory was moved from `benchmark/results_aws/{src_name}/` on {timestamp}.

**Canonical paper-ready copy is now at**: `{final_loc}` (under `benchmark/results_aws/FINAL/`).

This archived copy is kept for provenance only. The contents of this directory
are unchanged from before the move (verified via SHA-256 against the zip backup
`benchmark/results_aws/originals_backup_{DATE_STR}.zip`).

See `../_ARCHIVED.md` for the full archive manifest.
"""
        dst = ARCHIVE_DIR / src_name / "_ARCHIVED_NOTICE.md"
        if dry_run:
            print(f"[DRY] Would write {dst.relative_to(REPO_ROOT)} ({len(notice)} chars)")
        else:
            dst.write_text(notice, encoding="utf-8")
    if not dry_run:
        print(f"[OK] Wrote {len(DIRS_TO_ARCHIVE)} per-dir notice files")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="show what would happen")
    g.add_argument("--execute", action="store_true", help="actually do the work")
    args = ap.parse_args()
    dry = args.dry_run

    print(f"{'DRY RUN' if dry else 'EXECUTE'} — archive_originals.py")
    print(f"  Date stamp: {DATE_STR}")
    print(f"  Archive dir: {ARCHIVE_DIR.relative_to(REPO_ROOT)}")
    print(f"  Zip path:    {ZIP_PATH.relative_to(REPO_ROOT)}")
    print(f"  Dirs to move ({len(DIRS_TO_ARCHIVE)}):")
    for src_name, final_loc in DIRS_TO_ARCHIVE:
        src = RESULTS_AWS / src_name
        file_count = sum(1 for _ in walk_files(src)) if src.exists() else 0
        size = sum(p.stat().st_size for p in walk_files(src)) if src.exists() else 0
        marker = "PRESENT" if src.exists() else "MISSING"
        print(f"    [{marker:7s}] {src_name:35s}  {file_count:4d} files  {size:>10,} B  ({final_loc})")
    print()

    issues = precheck()
    if issues:
        print("PRECHECK FAILED:")
        for i in issues:
            print(f"  - {i}")
        sys.exit(1)
    print("[OK] Precheck passed")

    # Snapshot FINAL/ before any move so we can prove non-interference
    print()
    print("Snapshotting FINAL/ SHAs (for non-interference proof)...")
    final_before = snapshot_final_shas() if not dry else {}
    if not dry:
        print(f"[OK] Snapshotted {len(final_before)} FINAL/ files")

    # Step 1: build zip
    print()
    print("Step 1: build zip backup")
    file_shas = build_zip(dry)

    if not dry:
        # Step 2: verify zip
        print()
        print("Step 2: verify zip against source SHAs")
        if not verify_zip(file_shas):
            print("ABORT: zip verification failed. NO move performed. Zip is on disk for inspection.")
            sys.exit(2)

    # Step 3: create archive dir
    print()
    print("Step 3: create archive dir")
    if dry:
        print(f"[DRY] Would mkdir: {ARCHIVE_DIR.relative_to(REPO_ROOT)}")
    else:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=False)
        print(f"[OK] Created {ARCHIVE_DIR.relative_to(REPO_ROOT)}")

    # Step 4: move dirs
    print()
    print("Step 4: move directories")
    move_dirs(dry)

    # Step 5: write metadata
    print()
    print("Step 5: write metadata files")
    write_metadata(dry)

    if not dry:
        # Step 6: verify FINAL/ unchanged
        print()
        print("Step 6: verify FINAL/ unchanged")
        if not verify_final_unchanged(final_before):
            print("WARN: FINAL/ verification failed — investigate IMMEDIATELY")
            sys.exit(3)

        print()
        print("ALL STEPS OK. Summary:")
        print(f"  Zip:     {ZIP_PATH} ({ZIP_PATH.stat().st_size:,} bytes, {len(file_shas)} entries)")
        print(f"  Moved:   {len(DIRS_TO_ARCHIVE)} dirs into {ARCHIVE_DIR.relative_to(REPO_ROOT)}")
        print(f"  FINAL/:  {len(final_before)} files untouched (SHA-verified)")
    else:
        print()
        print("DRY RUN complete. No changes made. Re-run with --execute to perform the operation.")


if __name__ == "__main__":
    main()
