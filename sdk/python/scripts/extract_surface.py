#!/usr/bin/env python3
"""Emit the Python SDK's public surface as JSON, for the cross-SDK parity gate.

Reads the hand-written ergonomic layer with ``ast`` rather than importing it, so
this runs with no dependencies and no side effects, and reports what the source
actually declares rather than what an import happens to expose.

The generated typed core is deliberately out of scope: ``sdk-drift`` already
holds that to ``openapi/openapi.json``. What had no gate at all was the
hand-written layer, which is how the TypeScript client fell a release behind the
Python one without anything going red.

Usage:  python scripts/extract_surface.py > surface.python.json
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PACKAGE = Path(__file__).resolve().parents[1] / "constitutional_aiops"

# Vocabulary constants that both clients mirror from the server. Compared by
# value, not just by name: a new insight kind landing in one client and not the
# other is exactly the drift this gate exists to catch.
TRACKED_CONSTANTS = (
    "INSIGHT_KINDS",
    "INSIGHT_TIERS",
    "INSIGHT_UNAVAILABLE_REASONS",
    "CONSTITUTIONAL_CODES",
)


def _module(name: str) -> ast.Module:
    path = PACKAGE / name
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _public_methods(module: ast.Module, class_name: str) -> List[str]:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return sorted(
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not item.name.startswith("_")
            )
    raise SystemExit(f"parity: class {class_name} not found in the Python client")


def _error_classes(module: ast.Module) -> List[str]:
    return sorted(node.name for node in module.body if isinstance(node, ast.ClassDef))


def _constants(*modules: ast.Module) -> Dict[str, Any]:
    found: Dict[str, Any] = {}
    for module in modules:
        for node in module.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in TRACKED_CONSTANTS:
                    try:
                        found[target.id] = list(ast.literal_eval(node.value))
                    except ValueError:
                        # A constant that is not a literal sequence is a change
                        # worth failing on rather than silently skipping.
                        raise SystemExit(
                            f"parity: {target.id} is not a literal sequence in the Python client"
                        )
    return found


def main() -> None:
    client = _module("client.py")
    errors = _module("errors.py")

    surface = {
        "language": "python",
        "methods": _public_methods(client, "AIOpsClient"),
        "errors": _error_classes(errors),
        "constants": {key: _constants(client, errors).get(key) for key in TRACKED_CONSTANTS},
    }
    json.dump(surface, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
