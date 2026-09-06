#!/usr/bin/env python3
"""Dump the FastAPI OpenAPI schema to a committed snapshot (Track 3-A).

Why this exists
---------------
The SDK clients (``sdk/python``, ``sdk/typescript``) and the API-reference docs
generate from an OpenAPI document. Generating them against a *live* instance is
fragile: it needs the app running, and in production ``openapi_url`` is gated
off (``AIOPS_ENABLE_DOCS``). Committing a snapshot lets SDKs and docs regenerate
offline in CI, and makes API-surface changes show up as a reviewable diff.

What it writes
--------------
``openapi/openapi.json`` at the repo root -- pretty-printed with sorted keys so
the diff is stable and readable across regenerations.

Guarantees checked
------------------
* Every ``operationId`` is unique (the readable "<tag>-<function>" ids from
  ``src/main.py``). Duplicates would silently collide in generated clients, so
  this fails loudly instead.

Usage
-----
    python scripts/dump_openapi.py            # write the snapshot
    python scripts/dump_openapi.py --check    # verify it is up to date (CI)

``--check`` exits non-zero if the on-disk snapshot differs from the freshly
generated schema, so a workflow can gate on ``python scripts/dump_openapi.py
--check`` the same way ``git diff --exit-code`` gates generated code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Import the assembled app. This pulls in every router so the schema is complete.
# ENVIRONMENT stays whatever the caller set; app.openapi() builds the schema even
# when the openapi_url HTTP route is gated off in production.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.main import app  # noqa: E402

OUT_PATH = REPO_ROOT / "openapi" / "openapi.json"


def build_schema() -> dict:
    schema = app.openapi()
    _assert_unique_operation_ids(schema)
    return schema


def _assert_unique_operation_ids(schema: dict) -> None:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for path, path_item in schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            op_id = operation.get("operationId")
            if not op_id:
                continue
            where = f"{method.upper()} {path}"
            if op_id in seen:
                duplicates.append(f"  {op_id!r}: {seen[op_id]}  &  {where}")
            else:
                seen[op_id] = where
    if duplicates:
        print("Duplicate operationId(s) found:", file=sys.stderr)
        print("\n".join(duplicates), file=sys.stderr)
        raise SystemExit(
            "OpenAPI operationIds must be unique for the SDK generators. "
            "Give the colliding routes explicit operation_id= values."
        )


def _serialize(schema: dict) -> str:
    # sort_keys for a stable diff; trailing newline so the file is POSIX-clean.
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    check_only = "--check" in argv[1:]
    text = _serialize(build_schema())

    if check_only:
        if not OUT_PATH.exists():
            print(f"{OUT_PATH} is missing; run: python scripts/dump_openapi.py", file=sys.stderr)
            return 1
        current = OUT_PATH.read_text(encoding="utf-8")
        if current != text:
            print(
                f"{OUT_PATH} is out of date; run: python scripts/dump_openapi.py",
                file=sys.stderr,
            )
            return 1
        print(f"{OUT_PATH} is up to date ({len(json.loads(text)['paths'])} paths).")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # newline="" so the LF in `text` is written verbatim on every platform
    # (Windows would otherwise translate to CRLF and drift against Linux CI).
    OUT_PATH.write_text(text, encoding="utf-8", newline="")
    schema = json.loads(text)
    n_paths = len(schema.get("paths", {}))
    n_ops = sum(
        1
        for p in schema.get("paths", {}).values()
        for m, op in p.items()
        if isinstance(op, dict) and op.get("operationId")
    )
    print(f"Wrote {OUT_PATH.relative_to(REPO_ROOT)}: {n_paths} paths, {n_ops} operations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
