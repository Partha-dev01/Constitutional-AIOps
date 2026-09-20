"""Gate 0: every version surface must agree with the single source src/version.py."""

import json
from pathlib import Path

import src
from src.version import __version__ as VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_single_source_is_canonical() -> None:
    assert VERSION == "1.1.0"


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


def test_openapi_snapshot_version_matches() -> None:
    """The committed API snapshot is served to SDK consumers and Swagger.

    It is `app.version` fed from the single source, so a bump that misses it
    publishes a schema claiming the previous release.
    """
    schema = json.loads((REPO_ROOT / "openapi" / "openapi.json").read_text(encoding="utf-8"))
    assert schema["info"]["version"] == VERSION


def test_docs_site_nav_version_matches() -> None:
    """The docs site's nav advertises the release to every public reader.

    This surface had no gate and sat at v1.0.0 for the whole v1.1.0 release,
    because nothing tied it to src/version.py.
    """
    config = (REPO_ROOT / "docs-site" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    assert f"text: 'v{VERSION}'" in config


def test_frontend_whats_new_version_matches() -> None:
    """A returning browser is told what changed by comparing against APP_VERSION."""
    source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "tour" / "whatsNew.ts"
    ).read_text(encoding="utf-8")
    assert f"export const APP_VERSION = '{VERSION}'" in source
