"""Gate 0: every version surface must agree with the single source src/version.py."""

import json
from pathlib import Path

import src
from src.version import __version__ as VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_single_source_is_canonical() -> None:
    assert VERSION == "0.7.0"


def test_package_dunder_matches() -> None:
    assert src.__version__ == VERSION


def test_validation_constants_matches() -> None:
    from src.validation import constants

    assert constants.__version__ == VERSION


def test_frontend_package_version_matches() -> None:
    pkg = json.loads((REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == VERSION


def test_pyproject_declares_dynamic_version() -> None:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # version is sourced from src/version.py, not hardcoded in [project]
    assert 'dynamic = ["version"]' in text
    assert 'attr = "src.version.__version__"' in text
