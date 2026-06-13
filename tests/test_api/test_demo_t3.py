"""Tests for the t3-backed demo path: src.remediation.t3_client + the demo.py
routes + the remediation executor routing.

Per CI constraints these import route/module functions directly and NEVER import
src.main (langgraph is absent from the minimal CI install). httpx is mocked at
the AsyncClient boundary; t3_client is monkeypatched when exercising the routes.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.remediation import t3_client
from src.remediation.executor import resolve_remediation_target

# ---------------------------------------------------------------------------
# Fake httpx plumbing
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code=200, json_body=None, text="", raise_json=False):
        self.status_code = status_code
        self._json = json_body if json_body is not None else {}
        self.text = text
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("not json")
        return self._json


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient; records requests, returns a canned resp."""

    last_instance = None

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get("timeout")
        self.calls = []
        self.response = _FakeResponse()
        self.raise_exc = None
        _FakeAsyncClient.last_instance = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def request(self, method, url, headers=None, json=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "json": json})
        if self.raise_exc is not None:
            raise self.raise_exc
        return self.response


@pytest.fixture()
def fake_httpx(monkeypatch):
    """Patch httpx.AsyncClient in the t3_client module + configure target/token."""
    holder = {"response": _FakeResponse(), "raise_exc": None}

    def _factory(*args, **kwargs):
        client = _FakeAsyncClient(*args, **kwargs)
        client.response = holder["response"]
        client.raise_exc = holder["raise_exc"]
        return client

    monkeypatch.setattr(t3_client.httpx, "AsyncClient", _factory)
    # Resolve base url from env (no persisted settings); set a token.
    monkeypatch.setattr(
        "src.api.routes.settings._load_persisted", lambda: {}, raising=True,
    )
    monkeypatch.setenv("DEMO_TARGET_URL", "http://t3.example:8889")
    monkeypatch.setenv("DEMO_AGENT_TOKEN", "tok-123")
    return holder


# ---------------------------------------------------------------------------
# resolve_remediation_target
# ---------------------------------------------------------------------------

class TestResolveRemediationTarget:
    def test_default_only_db_is_remote(self, monkeypatch):
        monkeypatch.delenv("DEMO_REMOTE_CONTAINERS", raising=False)
        assert resolve_remediation_target("nextcloud-db") == "t3"
        # nextcloud stays LOCAL by default (keeps action-tool tests green).
        assert resolve_remediation_target("nextcloud") == "local"
        assert resolve_remediation_target("anything") == "local"

    def test_env_override_sets_remote_set(self, monkeypatch):
        monkeypatch.setenv("DEMO_REMOTE_CONTAINERS", "nextcloud, foo")
        assert resolve_remediation_target("nextcloud") == "t3"
        assert resolve_remediation_target("foo") == "t3"
        assert resolve_remediation_target("nextcloud-db") == "local"

    def test_blank_and_nonstr_are_local(self, monkeypatch):
        monkeypatch.delenv("DEMO_REMOTE_CONTAINERS", raising=False)
        assert resolve_remediation_target("") == "local"
        assert resolve_remediation_target("   ") == "local"
        assert resolve_remediation_target(None) == "local"  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# t3_client
# ---------------------------------------------------------------------------

class TestT3Client:
    @pytest.mark.asyncio
    async def test_chaos_start_success_merges_success_true(self, fake_httpx):
        fake_httpx["response"] = _FakeResponse(
            200, {"scenario": "db_down", "action": "start", "detail": "ok"},
        )
        result = await t3_client.chaos_start("db_down")
        assert result["success"] is True
        assert result["scenario"] == "db_down"
        assert result["detail"] == "ok"
        call = _FakeAsyncClient.last_instance.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "http://t3.example:8889/chaos/db_down/start"
        assert call["headers"]["Authorization"] == "Bearer tok-123"

    @pytest.mark.asyncio
    async def test_chaos_heal_hits_heal_path(self, fake_httpx):
        fake_httpx["response"] = _FakeResponse(200, {"detail": "healed"})
        result = await t3_client.chaos_heal("cpu_stress")
        assert result["success"] is True
        call = _FakeAsyncClient.last_instance.calls[0]
        assert call["url"].endswith("/chaos/cpu_stress/heal")

    @pytest.mark.asyncio
    async def test_status_success(self, fake_httpx):
        fake_httpx["response"] = _FakeResponse(
            200, {"scenarios": {"db_down": {"active": True}}, "containers": {}},
        )
        result = await t3_client.t3_status()
        assert result["success"] is True
        assert result["scenarios"]["db_down"]["active"] is True
        call = _FakeAsyncClient.last_instance.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/status")

    @pytest.mark.asyncio
    async def test_restart_remote_sends_container_body(self, fake_httpx):
        fake_httpx["response"] = _FakeResponse(
            200, {"container": "nextcloud-db", "action": "restart"},
        )
        result = await t3_client.restart_remote("nextcloud-db")
        assert result["success"] is True
        call = _FakeAsyncClient.last_instance.calls[0]
        assert call["url"].endswith("/remediate/restart")
        assert call["json"] == {"container": "nextcloud-db"}

    @pytest.mark.asyncio
    async def test_non_2xx_returns_failure(self, fake_httpx):
        fake_httpx["response"] = _FakeResponse(500, {}, text="boom")
        result = await t3_client.chaos_start("db_down")
        assert result["success"] is False
        assert "500" in result["error"]

    @pytest.mark.asyncio
    async def test_transport_error_returns_failure(self, fake_httpx):
        fake_httpx["raise_exc"] = RuntimeError("conn refused")
        result = await t3_client.t3_status()
        assert result["success"] is False
        assert "conn refused" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_base_url_fails_closed(self, monkeypatch):
        monkeypatch.setattr(
            "src.api.routes.settings._load_persisted", lambda: {}, raising=True,
        )
        monkeypatch.delenv("DEMO_TARGET_URL", raising=False)
        result = await t3_client.chaos_start("db_down")
        assert result["success"] is False
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_persisted_url_takes_priority_over_env(self, monkeypatch):
        monkeypatch.setattr(
            "src.api.routes.settings._load_persisted",
            lambda: {"remediation": {"demoTargetUrl": "http://persisted:9/"}},
            raising=True,
        )
        monkeypatch.setenv("DEMO_TARGET_URL", "http://env-fallback:8889")
        monkeypatch.setenv("DEMO_AGENT_TOKEN", "tok")

        captured = {}

        def _factory(*args, **kwargs):
            client = _FakeAsyncClient(*args, **kwargs)
            client.response = _FakeResponse(200, {"ok": True})
            captured["client"] = client
            return client

        monkeypatch.setattr(t3_client.httpx, "AsyncClient", _factory)
        await t3_client.t3_status()
        # Trailing slash stripped, persisted wins.
        assert captured["client"].calls[0]["url"] == "http://persisted:9/status"

    @pytest.mark.asyncio
    async def test_missing_token_sends_no_auth_header(self, fake_httpx, monkeypatch):
        monkeypatch.delenv("DEMO_AGENT_TOKEN", raising=False)
        fake_httpx["response"] = _FakeResponse(200, {"ok": True})
        await t3_client.t3_status()
        assert "Authorization" not in _FakeAsyncClient.last_instance.calls[0]["headers"]


# ---------------------------------------------------------------------------
# demo.py routes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _demo_allowed(monkeypatch):
    """Keep the demo gate open (non-production) for route tests."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "local")


class TestDemoScenariosRoute:
    @pytest.mark.asyncio
    async def test_lists_all_five_scenarios(self):
        from src.api.routes.demo import list_scenarios

        resp = await list_scenarios()
        ids = {s.id for s in resp.scenarios}
        assert ids == {"db_down", "cpu_stress", "mem_stress", "bad_config_5xx", "disk_fill"}
        for s in resp.scenarios:
            assert s.label and s.description


class TestDemoStatusRoute:
    @pytest.mark.asyncio
    async def test_status_proxies_t3_when_reachable(self, monkeypatch):
        import src.api.routes.demo as demo

        monkeypatch.setattr(
            demo.t3_client, "t3_status",
            AsyncMock(return_value={
                "success": True,
                "scenarios": {"db_down": {"active": True}},
                "containers": {"nextcloud": {"running": True}},
            }),
        )
        monkeypatch.setattr(demo, "_resolved_target_url", lambda: "http://t3:8889")
        out = await demo.get_demo_status()
        assert out["reachable"] is True
        assert out["target_url"] == "http://t3:8889"
        assert out["scenarios"]["db_down"]["active"] is True
        assert out["containers"]["nextcloud"]["running"] is True

    @pytest.mark.asyncio
    async def test_status_unreachable_returns_empty_maps(self, monkeypatch):
        import src.api.routes.demo as demo

        monkeypatch.setattr(
            demo.t3_client, "t3_status",
            AsyncMock(return_value={"success": False, "error": "down"}),
        )
        monkeypatch.setattr(demo, "_resolved_target_url", lambda: "")
        out = await demo.get_demo_status()
        assert out["reachable"] is False
        assert out["scenarios"] == {}
        assert out["containers"] == {}


class TestDemoChaosRoutes:
    @pytest.mark.asyncio
    async def test_start_unknown_scenario_404(self, monkeypatch):
        from fastapi import HTTPException

        import src.api.routes.demo as demo

        with pytest.raises(HTTPException) as exc:
            await demo.start_chaos("nope", MagicMock())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_start_success_fires_rca_and_updates_state(self, monkeypatch):
        import src.api.routes.demo as demo

        # Reset shared state.
        demo._demo_state.update({"active": False, "started_at": None, "anomalies_triggered": 0})

        monkeypatch.setattr(
            demo.t3_client, "chaos_start",
            AsyncMock(return_value={"success": True, "detail": "started"}),
        )
        logged = {}
        async def _fake_log(request, scenarios):
            logged["scenarios"] = scenarios
        monkeypatch.setattr(demo, "_log_demo_incidents", _fake_log)

        resp = await demo.start_chaos("db_down", MagicMock())
        assert resp.scenario == "db_down"
        assert resp.action == "start"
        assert resp.success is True
        assert resp.detail == "started"
        # RCA path was invoked, state advanced.
        assert logged["scenarios"] == ["db_down"]
        assert demo._demo_state["active"] is True
        assert demo._demo_state["anomalies_triggered"] == 1

    @pytest.mark.asyncio
    async def test_start_failure_does_not_fire_rca(self, monkeypatch):
        import src.api.routes.demo as demo

        demo._demo_state.update({"active": False, "started_at": None, "anomalies_triggered": 0})
        monkeypatch.setattr(
            demo.t3_client, "chaos_start",
            AsyncMock(return_value={"success": False, "error": "agent down"}),
        )
        called = {"n": 0}
        async def _fake_log(request, scenarios):
            called["n"] += 1
        monkeypatch.setattr(demo, "_log_demo_incidents", _fake_log)

        resp = await demo.start_chaos("cpu_stress", MagicMock())
        assert resp.success is False
        assert resp.detail == "agent down"
        assert called["n"] == 0
        assert demo._demo_state["active"] is False

    @pytest.mark.asyncio
    async def test_heal_unknown_scenario_404(self):
        from fastapi import HTTPException

        import src.api.routes.demo as demo

        with pytest.raises(HTTPException) as exc:
            await demo.heal_chaos("nope", MagicMock())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_heal_success_shape(self, monkeypatch):
        import src.api.routes.demo as demo

        monkeypatch.setattr(
            demo.t3_client, "chaos_heal",
            AsyncMock(return_value={"success": True, "detail": "healed"}),
        )
        resp = await demo.heal_chaos("db_down", MagicMock())
        assert resp.action == "heal"
        assert resp.success is True
        assert resp.detail == "healed"


class TestDemoTargetRoute:
    @pytest.mark.asyncio
    async def test_put_target_persists_via_settings_helpers(self, monkeypatch):
        import src.api.routes.demo as demo

        store = {}
        monkeypatch.setattr("src.api.routes.settings._load_persisted", lambda: dict(store))
        def _save(data):
            store.clear()
            store.update(data)
        monkeypatch.setattr("src.api.routes.settings._save_persisted", _save)

        resp = await demo.set_target(demo.TargetUpdateRequest(url="http://t3:8889/"))
        assert resp.target_url == "http://t3:8889/"
        assert store["remediation"]["demoTargetUrl"] == "http://t3:8889/"

    @pytest.mark.asyncio
    async def test_put_target_merges_existing_remediation(self, monkeypatch):
        import src.api.routes.demo as demo

        store = {"remediation": {"mode": "approve"}, "other": 1}
        monkeypatch.setattr("src.api.routes.settings._load_persisted", lambda: {
            "remediation": dict(store["remediation"]), "other": store["other"],
        })
        saved = {}
        monkeypatch.setattr("src.api.routes.settings._save_persisted", lambda d: saved.update(d))

        await demo.set_target(demo.TargetUpdateRequest(url="http://new:1"))
        # Existing keys preserved; new key merged in.
        assert saved["remediation"]["mode"] == "approve"
        assert saved["remediation"]["demoTargetUrl"] == "http://new:1"
        assert saved["other"] == 1


# ---------------------------------------------------------------------------
# tools.py remote-restart dispatch
# ---------------------------------------------------------------------------

class TestToolsRemoteRestartDispatch:
    @pytest.mark.asyncio
    async def test_db_restart_routes_to_t3(self, monkeypatch):
        from src.api.routes import tools

        monkeypatch.setenv("DEMO_REMOTE_CONTAINERS", "nextcloud-db")
        # Local docker must never be touched on the remote path.
        fake_run = MagicMock(side_effect=AssertionError("local docker called"))
        monkeypatch.setattr("subprocess.run", fake_run)
        monkeypatch.setattr(
            "src.remediation.t3_client.restart_remote",
            AsyncMock(return_value={"success": True, "container": "nextcloud-db"}),
        )

        resp = await tools._execute_restart_service(
            {"service_name": "nextcloud-db", "reason": "t"}, 0.0,
        )
        assert resp.success is True
        assert resp.data["container"] == "nextcloud-db"
        assert resp.metadata["source"] == "t3"

    @pytest.mark.asyncio
    async def test_t3_failure_is_structured(self, monkeypatch):
        from src.api.routes import tools

        monkeypatch.setenv("DEMO_REMOTE_CONTAINERS", "nextcloud-db")
        monkeypatch.setattr(
            "src.remediation.t3_client.restart_remote",
            AsyncMock(return_value={"success": False, "error": "agent down"}),
        )
        resp = await tools._execute_restart_service(
            {"service_name": "nextcloud-db", "reason": "t"}, 0.0,
        )
        assert resp.success is False
        assert resp.error_code == "execution_failed"
        assert "agent down" in resp.error

    @pytest.mark.asyncio
    async def test_local_container_still_uses_local_docker(self, monkeypatch):
        from src.api.routes import tools

        monkeypatch.setenv("DEMO_REMOTE_CONTAINERS", "nextcloud-db")
        calls = []
        def _run(cmd, **kwargs):
            calls.append(cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result
        monkeypatch.setattr("subprocess.run", _run)
        # restart_remote must NOT be called for a local container.
        monkeypatch.setattr(
            "src.remediation.t3_client.restart_remote",
            AsyncMock(side_effect=AssertionError("t3 called for local container")),
        )

        resp = await tools._execute_restart_service(
            {"service_name": "nextcloud", "reason": "t"}, 0.0,
        )
        assert resp.success is True
        assert calls == [["docker", "restart", "nextcloud"]]
        assert resp.metadata["source"] == "docker"
