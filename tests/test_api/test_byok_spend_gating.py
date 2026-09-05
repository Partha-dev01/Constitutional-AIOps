"""
BYOK spend-surface gating regression (BYOK Phase B).

Locks the decision that every LLM-spend surface a *regular* tenant could reach
either routes to the caller's own bring-your-own endpoint (chat / analyze) or is
admin-only (operator tools) — so a regular user can never silently spend the
owner key. See project_byok_multitenant_spec.md (Phase B).

  * chat /analyze  -> per-user routing: a regular user with no endpoint gets a
    clear 400; admin / self-host keeps the shared global agent (503 only when
    that agent is genuinely down).
  * benchmark /run + /evaluate-endpoint, metrics /benchmark + /validate/
    determinism, graph /generate-episodes -> operator tools that exercise the
    box's configured (owner) endpoint via the shared runner/router, so they are
    admin-only (require_admin). topology/prompts generate were already admin-only
    (SEC-004) and are covered by their own suites.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from src.auth.deps import require_admin, synthetic_admin, User


def _find_route(router, path: str, method: str = "POST") -> APIRoute:
    for route in router.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"route {method} {path} not found on router")


def _dependency_calls(route: APIRoute) -> set:
    return {dep.call for dep in route.dependant.dependencies}


class TestAdminGatedSpendSurfaces:
    """Each operator spend surface must carry the require_admin dependency."""

    def test_benchmark_run_is_admin_only(self):
        from src.api.routes.benchmark import router

        assert require_admin in _dependency_calls(_find_route(router, "/run"))

    def test_benchmark_evaluate_endpoint_is_admin_only(self):
        from src.api.routes.benchmark import router

        assert require_admin in _dependency_calls(_find_route(router, "/evaluate-endpoint"))

    def test_metrics_benchmark_is_admin_only(self):
        from src.api.routes.metrics import router

        assert require_admin in _dependency_calls(_find_route(router, "/benchmark"))

    def test_metrics_validate_determinism_is_admin_only(self):
        from src.api.routes.metrics import router

        assert require_admin in _dependency_calls(_find_route(router, "/validate/determinism"))

    def test_graph_generate_episodes_is_admin_only(self):
        from src.api.routes.graph import router

        assert require_admin in _dependency_calls(_find_route(router, "/generate-episodes"))


class TestChatAnalyzePerUserRouting:
    """chat /analyze routes RCA/planning to the caller's own endpoint (BYOK #3)."""

    @pytest.fixture
    def db_env(self, tmp_path, monkeypatch):
        from src.auth import crypto, store

        monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-analyze")
        crypto.reset_cache()
        store.init_db()
        record = store.create_user("tenant-analyze", "a-long-enough-password", role="user")
        yield record
        crypto.reset_cache()

    @pytest.mark.asyncio
    async def test_regular_user_without_endpoint_gets_400(self, db_env):
        from src.api.routes.chat import analyze
        from src.api.schemas.chat import AnalysisRequest

        user = User(id=db_env.id, username="tenant-analyze", role="user")
        # A global agent exists on app.state, but a regular tenant must NOT reach
        # it: with no endpoint of their own they get a 400, not the owner key.
        request = SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(reasoning_agent=object()))
        )
        with pytest.raises(HTTPException) as exc:
            await analyze(request, AnalysisRequest(mode="rca", data={}), user=user)
        assert exc.value.status_code == 400
        assert "endpoint" in str(exc.value.detail).lower()

    @pytest.mark.asyncio
    async def test_admin_without_global_agent_gets_503_not_400(self, db_env):
        from src.api.routes.chat import analyze
        from src.api.schemas.chat import AnalysisRequest

        # Admin / self-host still uses the shared global agent; when it is truly
        # unavailable that is a 503 (infra), never the regular-user 400.
        request = SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(reasoning_agent=None))
        )
        with pytest.raises(HTTPException) as exc:
            await analyze(
                request, AnalysisRequest(mode="rca", data={}), user=synthetic_admin()
            )
        assert exc.value.status_code == 503
