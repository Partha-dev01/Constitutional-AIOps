"""
tests/test_app_boot.py — App-boot / import smoke test (P0 #6 guard)

Guards against the regression where src/main.py and src/orchestration/* are
unimportable in CI because runtime deps (langgraph, python-multipart) are
absent from pyproject [project] dependencies.

The full lifespan (Neo4j connect, LLM health checks, background processor)
is NOT started — FastAPI does not execute the lifespan until .startup() or a
TestClient context-manager is entered. We only:
  1. Verify that `from src.main import app` succeeds (import-time check).
  2. Verify that `from src.orchestration.graph import build_incident_graph`
     succeeds (the langgraph import is at module top-level there).
  3. Assert the expected API routers are registered on the app (static
     inspection — no HTTP request needed, no live backend required).
  4. Assert the app title/version are non-empty strings (basic sanity on the
     FastAPI object).

If langgraph or python-multipart are missing from the install, step 1 or 2
will raise ImportError and this file fails at collection — exactly the signal
we want.
"""

import importlib


def test_main_module_importable():
    """src.main must be importable without raising ImportError."""
    mod = importlib.import_module("src.main")
    assert mod is not None, "src.main could not be imported"


def test_orchestration_graph_importable():
    """
    src.orchestration.graph imports langgraph at the top level
    (``from langgraph.graph import END, START, StateGraph``).
    This test fails at collection if langgraph is not installed.
    """
    mod = importlib.import_module("src.orchestration.graph")
    assert hasattr(mod, "build_incident_graph"), (
        "build_incident_graph not found in src.orchestration.graph"
    )


def test_app_object_is_fastapi():
    """The `app` object exported from src.main must be a FastAPI instance."""
    from fastapi import FastAPI
    from src.main import app

    assert isinstance(app, FastAPI), f"Expected FastAPI, got {type(app)}"


def test_app_has_expected_routers():
    """
    All API routers must be registered on the app.

    We inspect `app.routes` for path prefixes rather than importing router
    objects directly so this test stays decoupled from router internals.
    Expected prefixes (from app.include_router calls in src/main.py):
      /api/v1/health, /api/v1/auth, /api/v1/chat, /api/v1/incidents,
      /api/v1/actions, /api/v1/tools, /api/v1/agents, /api/v1/telemetry,
      /api/v1/graph, /api/v1/prompts, /api/v1/infrastructure, /api/v1/demo,
      /api/v1/metrics, /api/v1/benchmark, /api/v1/settings
    """
    from src.main import app

    registered_paths = {route.path for route in app.routes if hasattr(route, "path")}
    # FastAPI >= 0.139 (starlette 1.x) no longer flattens include_router()
    # targets into app.routes — each becomes an opaque _IncludedRouter entry
    # with no .path. The OpenAPI schema is the version-stable public view of
    # every registered HTTP route, so union it in (websocket routes are still
    # covered by the app.routes pass above).
    registered_paths |= set(app.openapi().get("paths", {}))

    # Build a set of route prefixes present in the registered paths
    expected_prefixes = [
        "/api/v1",       # health, root endpoint, and all sub-paths
        "/api/v1/auth",
        "/api/v1/chat",
        "/api/v1/incidents",
        "/api/v1/actions",
        "/api/v1/tools",
        "/api/v1/agents",
        "/api/v1/telemetry",
        "/api/v1/graph",
        "/api/v1/prompts",
        "/api/v1/infrastructure",
        "/api/v1/demo",
        "/api/v1/metrics",
        "/api/v1/benchmark",
        "/api/v1/settings",
    ]

    for prefix in expected_prefixes:
        matched = any(path.startswith(prefix) for path in registered_paths)
        assert matched, (
            f"No route with prefix '{prefix}' found in app.routes. "
            f"Registered paths: {sorted(registered_paths)}"
        )


def test_app_metadata():
    """FastAPI app title and version must be non-empty."""
    from src.main import app

    assert app.title, "app.title is empty"
    assert app.version, "app.version is empty"
    assert "AIOps" in app.title or "aiops" in app.title.lower(), (
        f"Unexpected app title: {app.title!r}"
    )
