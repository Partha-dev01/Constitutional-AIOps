#!/usr/bin/env python3
"""Fail if the two hand-written SDK clients have drifted apart.

Why this exists
---------------
``sdk-drift`` already holds each *generated* core to ``openapi/openapi.json``.
Nothing held the two *hand-written* ergonomic clients to each other, and the
Python client has a unit-test suite while the TypeScript one has none. So when
the v1.1.0 security work updated ``approve_action``'s Python docstring and
signature, the TypeScript twin kept requiring ``approvedBy`` and documented
nothing, and every gate stayed green. A human reading both files caught it.

This compares the public surface of the two clients: method names (normalised
across the naming conventions), the error hierarchy, and the vocabulary
constants both mirror from the server. Constants are compared **by value**, so a
new insight kind or refusal code landing in one client and not the other fails
here rather than reaching users.

It does not compare documentation prose, which no gate can judge. It narrows the
gap to the part a machine can check.

Usage:  python sdk/scripts/check_parity.py <surface.python.json> <surface.typescript.json>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

# Methods that exist in one client on purpose. Each entry has to say why, so the
# list stays a record of decisions rather than a place to bury new drift.
INTENTIONAL_ASYMMETRY: Dict[str, str] = {
    "close": (
        "Python only. urllib holds no persistent connection, so close() is a no-op that "
        "exists to support the `with AIOpsClient(...)` idiom. fetch has no equivalent to "
        "release, so the TypeScript client offers nothing to mirror."
    ),
}

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake(name: str) -> str:
    """`callTool` -> `call_tool`. Leaves an already-snake_case name alone."""
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2

    python = load(sys.argv[1])
    typescript = load(sys.argv[2])
    problems: List[str] = []

    # ── methods ───────────────────────────────────────────────────────────────
    # Normalise both sides to snake_case, but keep the native spelling so the
    # report names the symbol the reader has to go and add.
    py_native = {to_snake(name): name for name in python["methods"]}
    ts_native = {to_snake(name): name for name in typescript["methods"]}

    missing_in_ts = sorted(set(py_native) - set(ts_native))
    missing_in_py = sorted(set(ts_native) - set(py_native))

    for key in missing_in_ts:
        if key in INTENTIONAL_ASYMMETRY:
            continue
        problems.append(
            f"method `{py_native[key]}` exists in Python but not in TypeScript "
            f"(expected `{to_camel(key)}`)"
        )
    for key in missing_in_py:
        if key in INTENTIONAL_ASYMMETRY:
            continue
        problems.append(
            f"method `{ts_native[key]}` exists in TypeScript but not in Python "
            f"(expected `{key}`)"
        )

    # ── error hierarchy ───────────────────────────────────────────────────────
    py_errors, ts_errors = set(python["errors"]), set(typescript["errors"])
    for name in sorted(py_errors - ts_errors):
        problems.append(f"error class `{name}` exists in Python but not in TypeScript")
    for name in sorted(ts_errors - py_errors):
        problems.append(f"error class `{name}` exists in TypeScript but not in Python")

    # ── server vocabulary, compared by value ──────────────────────────────────
    for key in sorted(set(python["constants"]) | set(typescript["constants"])):
        py_value = python["constants"].get(key)
        ts_value = typescript["constants"].get(key)
        if py_value is None:
            problems.append(f"constant `{key}` is missing from the Python client")
            continue
        if ts_value is None:
            problems.append(f"constant `{key}` is missing from the TypeScript client")
            continue
        if list(py_value) != list(ts_value):
            problems.append(
                f"constant `{key}` differs:\n"
                f"      python:     {py_value}\n"
                f"      typescript: {ts_value}"
            )

    # ── report ────────────────────────────────────────────────────────────────
    if problems:
        print("SDK parity check FAILED\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nThe two clients are published as one version and documented as the same "
            "surface, so a change to one is a change to both. If a difference is "
            "deliberate, add it to INTENTIONAL_ASYMMETRY in this file with the reason.",
            file=sys.stderr,
        )
        return 1

    print(
        f"SDK parity OK: {len(py_native)} Python methods vs {len(ts_native)} TypeScript, "
        f"{len(py_errors)} error classes, {len(python['constants'])} shared constants"
    )
    for key, reason in INTENTIONAL_ASYMMETRY.items():
        print(f"  allowed asymmetry `{key}`: {reason.split('.')[0]}.")
    return 0


def to_camel(snake: str) -> str:
    head, *rest = snake.split("_")
    return head + "".join(part.title() for part in rest)


if __name__ == "__main__":
    raise SystemExit(main())
