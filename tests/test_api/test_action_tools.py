"""Session-14 W5 — gated action tools (restart_service / scale_service) end-to-end.

Covers the full REST contract for action-class tools:
  - gate OFF (default)  → structured refusal (error_code="action_tools_disabled"),
    zero behavior beyond the refusal; subprocess never reached
  - gate ON + validator pass → docker execution (mocked) with the
    constitutional verdict attached to the response metadata
  - gate ON + requires_approval → NO execution; verdict payload returned with
    error_code="approval_required"
  - container whitelist enforcement (default nextcloud +
    AIOPS_ACTION_CONTAINER_WHITELIST extension)
  - scale replica clamp to [0, 5]
  - tool listing exposes per-tool enabled/gated_by metadata (REST fallback,
    REST mcp_server path, and MCPActionServer.list_tools directly)
  - programmatic execute_tool_call path is gated identically
  - every action attempt produces an audit log line

NOTE: per CI constraints these tests import route modules directly and never
import src.main (langgraph is absent from the minimal CI install).
"""

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tool_call(name="restart_service", params=None):
    from src.api.routes.tools import ToolCallRequest

    return ToolCallRequest(
        tool_name=name,
        parameters=params if params is not None else {"service_name": "nextcloud", "reason": "test"},
    )


def _report(can_proceed=True, requires_approval=False, authorization="automatic",
            explanation="ok", tier2_passed=True, violations=None, warnings=None):
    """Mock ValidationReport with every attribute the verdict serializer reads."""
    report = MagicMock()
    report.can_proceed = can_proceed
    report.requires_approval = requires_approval
    report.authorization_level = MagicMock()
    report.authorization_level.value = authorization
    report.overall_result = MagicMock()
    report.overall_result.value = "passed" if can_proceed and not violations else "warning"
    report.confidence = 0.95
    report.tier1_passed = True
    report.tier2_passed = tier2_passed
    report.tier3_passed = True
    report.violations = violations or []
    report.warnings = warnings or []
    report.explanation = explanation
    return report


def _request_with_validator(report):
    validator = MagicMock()
    validator.validate.return_value = report
    request = MagicMock()
    request.app.state = MagicMock(spec=["validator"])
    request.app.state.validator = validator
    return request


class _FakeRun:
    """Records subprocess.run invocations and returns a canned result."""

    def __init__(self, returncode=0, stderr=""):
        self.calls = []
        self.returncode = returncode
        self.stderr = stderr

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)
        result = MagicMock()
        result.returncode = self.returncode
        result.stdout = ""
        result.stderr = self.stderr
        return result


@pytest.fixture()
def fake_run(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr("subprocess.run", fake)
    return fake


@pytest.fixture(autouse=True)
def _mock_audit(monkeypatch):
    """Keep unit tests from writing real audit files; capture the calls."""
    audit = MagicMock()
    monkeypatch.setattr("src.api.routes.tools.get_audit_logger", lambda: audit)
    return audit


# ---------------------------------------------------------------------------
# Gate OFF (production default) — structured refusal
# ---------------------------------------------------------------------------

class TestGateOffRefusal:
    @pytest.mark.asyncio
    async def test_structured_refusal_shape(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        response = await call_tool(request, _tool_call("restart_service"))
        assert response.success is False
        assert response.data is None
        assert response.error_code == "action_tools_disabled"
        assert "AIOPS_ENABLE_ACTION_TOOLS" in (response.error or "")
        assert response.metadata.get("gated_by") == "AIOPS_ENABLE_ACTION_TOOLS"
        # No validation ran, so no verdict — and absolutely no docker call.
        assert "constitutional" not in response.metadata
        assert fake_run.calls == []

    @pytest.mark.asyncio
    async def test_falsy_env_values_stay_disabled(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        for value in ("0", "false", "no", ""):
            monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", value)
            request = MagicMock()
            request.app.state = MagicMock(spec=[])
            response = await call_tool(request, _tool_call("scale_service", {
                "service_name": "nextcloud", "target_replicas": 2, "reason": "test",
            }))
            assert response.success is False
            assert response.error_code == "action_tools_disabled"
        assert fake_run.calls == []

    @pytest.mark.asyncio
    async def test_audit_line_written_on_refusal(self, monkeypatch, fake_run, _mock_audit):
        from src.api.routes.tools import call_tool

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        await call_tool(request, _tool_call("restart_service"))
        _mock_audit.log_tool_invocation.assert_called_once()
        kwargs = _mock_audit.log_tool_invocation.call_args.kwargs
        assert kwargs["tool_name"] == "restart_service"
        assert kwargs["context"]["outcome"] == "refused"
        assert kwargs["context"]["error_code"] == "action_tools_disabled"


# ---------------------------------------------------------------------------
# Gate ON + validator pass — executes through mocked docker
# ---------------------------------------------------------------------------

class TestValidatedExecution:
    @pytest.mark.asyncio
    async def test_restart_executes_with_verdict_attached(self, monkeypatch, fake_run, _mock_audit):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.delenv("AIOPS_ACTION_CONTAINER_WHITELIST", raising=False)
        request = _request_with_validator(_report(can_proceed=True, requires_approval=False))

        response = await call_tool(request, _tool_call("restart_service"))
        assert response.success is True
        assert response.error_code is None
        assert fake_run.calls == [["docker", "restart", "nextcloud"]]
        assert response.data["container"] == "nextcloud"
        assert response.data["status"] == "completed"
        # Verdict is part of the payload on success too.
        verdict = response.metadata["constitutional"]
        assert verdict["can_proceed"] is True
        assert verdict["requires_approval"] is False
        assert verdict["authorization_level"] == "automatic"
        assert verdict["principles"] == {
            "tier1_safety_passed": True,
            "tier2_operational_passed": True,
            "tier3_learning_passed": True,
        }
        # Audit line for the executed attempt.
        kwargs = _mock_audit.log_tool_invocation.call_args.kwargs
        assert kwargs["context"]["outcome"] == "executed"

    @pytest.mark.asyncio
    async def test_docker_failure_is_structured(self, monkeypatch):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        fake = _FakeRun(returncode=1, stderr="No such container")
        monkeypatch.setattr("subprocess.run", fake)
        request = _request_with_validator(_report())

        response = await call_tool(request, _tool_call("restart_service"))
        assert response.success is False
        assert response.error_code == "execution_failed"
        assert "No such container" in (response.error or "")
        # Verdict still attached on execution failure.
        assert response.metadata["constitutional"]["can_proceed"] is True


# ---------------------------------------------------------------------------
# Gate ON + requires_approval — verdict surfaced, NOTHING executed
# ---------------------------------------------------------------------------

class TestApprovalRequired:
    @pytest.mark.asyncio
    async def test_no_execution_and_verdict_payload(self, monkeypatch, fake_run, _mock_audit):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        violation = MagicMock()
        violation.principle = MagicMock()
        violation.principle.id = "P2.2"
        violation.principle.name = "Evidence-Based"
        violation.severity = "high"
        violation.reason = "No telemetry evidence provided"
        report = _report(
            can_proceed=True, requires_approval=True, authorization="approval",
            explanation="Tier 2 (Operational) violation - requires human approval",
            tier2_passed=False, violations=[violation],
        )
        request = _request_with_validator(report)

        response = await call_tool(request, _tool_call("restart_service"))
        assert response.success is False
        assert response.error_code == "approval_required"
        assert fake_run.calls == []  # never executed
        verdict = response.metadata["constitutional"]
        assert verdict["requires_approval"] is True
        assert verdict["principles"]["tier2_operational_passed"] is False
        assert verdict["violations"] == [{
            "principle_id": "P2.2",
            "principle_name": "Evidence-Based",
            "severity": "high",
            "reason": "No telemetry evidence provided",
        }]
        assert "approval" in verdict["explanation"].lower()
        kwargs = _mock_audit.log_tool_invocation.call_args.kwargs
        assert kwargs["context"]["outcome"] == "refused"
        assert kwargs["context"]["error_code"] == "approval_required"

    @pytest.mark.asyncio
    async def test_blocked_verdict_is_validation_blocked(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        report = _report(
            can_proceed=False, requires_approval=False, authorization="alert",
            explanation="Validation passed - alert (low confidence - alert only)",
        )
        request = _request_with_validator(report)

        response = await call_tool(request, _tool_call("restart_service"))
        assert response.success is False
        assert response.error_code == "validation_blocked"
        assert response.metadata["constitutional"]["can_proceed"] is False
        assert fake_run.calls == []


# ---------------------------------------------------------------------------
# Container whitelist
# ---------------------------------------------------------------------------

class TestContainerWhitelist:
    @pytest.mark.asyncio
    async def test_non_whitelisted_container_refused_before_validation(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.delenv("AIOPS_ACTION_CONTAINER_WHITELIST", raising=False)
        request = _request_with_validator(_report())

        response = await call_tool(request, _tool_call(
            "restart_service", {"service_name": "etcd", "reason": "test"},
        ))
        assert response.success is False
        assert response.error_code == "container_not_whitelisted"
        assert fake_run.calls == []
        # Whitelist is checked before the validator even runs.
        request.app.state.validator.validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_env_whitelist_extension_allows_container(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.setenv("AIOPS_ACTION_CONTAINER_WHITELIST", "alpha, beta")
        request = _request_with_validator(_report())

        response = await call_tool(request, _tool_call(
            "restart_service", {"service_name": "alpha", "reason": "test"},
        ))
        assert response.success is True
        assert fake_run.calls == [["docker", "restart", "alpha"]]

    def test_resolver_rejects_flag_like_and_empty_names(self, monkeypatch):
        from src.api.routes.tools import _resolve_action_container

        monkeypatch.setenv("AIOPS_ACTION_CONTAINER_WHITELIST", "--privileged,-x")
        # Even whitelisted, flag-like names never resolve (defense in depth).
        assert _resolve_action_container("--privileged") is None
        assert _resolve_action_container("-x") is None
        assert _resolve_action_container("") is None
        assert _resolve_action_container(None) is None
        assert _resolve_action_container(123) is None

    def test_resolver_accepts_aiops_prefixed_whitelist_entry(self, monkeypatch):
        from src.api.routes.tools import _resolve_action_container

        monkeypatch.setenv("AIOPS_ACTION_CONTAINER_WHITELIST", "aiops-backend")
        assert _resolve_action_container("backend") == "aiops-backend"
        assert _resolve_action_container("aiops-backend") == "aiops-backend"


# ---------------------------------------------------------------------------
# Replica clamp
# ---------------------------------------------------------------------------

class TestReplicaClamp:
    def _scale(self, replicas):
        return _tool_call("scale_service", {
            "service_name": "nextcloud", "target_replicas": replicas, "reason": "test",
        })

    @pytest.mark.asyncio
    async def test_high_count_clamped_to_max(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request = _request_with_validator(_report())

        response = await call_tool(request, self._scale(50))
        assert response.success is True
        assert fake_run.calls == [["docker", "compose", "up", "-d", "--scale", "nextcloud=5"]]
        assert response.data["target_replicas"] == 5
        assert response.data["requested_replicas"] == 50
        assert response.data["clamped"] is True

    @pytest.mark.asyncio
    async def test_negative_count_clamped_to_min(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request = _request_with_validator(_report())

        response = await call_tool(request, self._scale(-3))
        assert response.success is True
        assert fake_run.calls == [["docker", "compose", "up", "-d", "--scale", "nextcloud=0"]]
        assert response.data["target_replicas"] == 0
        assert response.data["clamped"] is True

    @pytest.mark.asyncio
    async def test_in_range_count_not_clamped(self, monkeypatch, fake_run):
        from src.api.routes.tools import call_tool

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request = _request_with_validator(_report())

        response = await call_tool(request, self._scale(2))
        assert response.success is True
        assert fake_run.calls == [["docker", "compose", "up", "-d", "--scale", "nextcloud=2"]]
        assert response.data["clamped"] is False

    @pytest.mark.asyncio
    async def test_non_integer_count_refused(self, monkeypatch, fake_run):
        from src.api.routes.tools import _execute_scale_service

        # Direct executor call — the pydantic request model would reject the
        # type at the API boundary, but the executor must hold on its own.
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        response = await _execute_scale_service(
            {"service_name": "nextcloud", "target_replicas": "ten", "reason": "t"}, 0.0,
        )
        assert response.success is False
        assert response.error_code == "invalid_parameters"
        assert fake_run.calls == []


# ---------------------------------------------------------------------------
# Tool listing exposes gating metadata
# ---------------------------------------------------------------------------

class TestListingGatingMetadata:
    def _by_name(self, listing):
        return {t.name: t for t in listing.tools}

    @pytest.mark.asyncio
    async def test_rest_fallback_listing_disabled_by_default(self, monkeypatch):
        from src.api.routes.tools import list_tools

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])  # no mcp_server → fallback list

        tools = self._by_name(await list_tools(request))
        for name in ("restart_service", "scale_service"):
            assert tools[name].enabled is False
            assert tools[name].gated_by == "AIOPS_ENABLE_ACTION_TOOLS"
        for name in ("find_similar", "get_dependencies", "analyze_logs",
                     "query_recent_logs", "query_metric", "list_containers",
                     "analyze_time_series_anomaly"):
            assert tools[name].enabled is True
            assert tools[name].gated_by is None

    @pytest.mark.asyncio
    async def test_rest_fallback_listing_enabled_with_env(self, monkeypatch):
        from src.api.routes.tools import list_tools

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        tools = self._by_name(await list_tools(request))
        for name in ("restart_service", "scale_service"):
            assert tools[name].enabled is True
            assert tools[name].gated_by == "AIOPS_ENABLE_ACTION_TOOLS"

    @pytest.mark.asyncio
    async def test_rest_mcp_server_listing_carries_gating(self, monkeypatch):
        from src.api.routes.tools import list_tools
        from src.mcp.server import MCPActionServer

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=["mcp_server"])
        request.app.state.mcp_server = MCPActionServer()

        tools = self._by_name(await list_tools(request))
        assert tools["restart_service"].enabled is False
        assert tools["restart_service"].gated_by == "AIOPS_ENABLE_ACTION_TOOLS"
        assert tools["find_similar"].enabled is True

    def test_mcp_server_list_tools_metadata(self, monkeypatch):
        from src.mcp.server import MCPActionServer

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        server = MCPActionServer()
        tools = {t["name"]: t for t in server.list_tools()}
        assert tools["restart_service"]["enabled"] is False
        assert tools["scale_service"]["enabled"] is False
        assert tools["restart_service"]["gated_by"] == "AIOPS_ENABLE_ACTION_TOOLS"
        assert tools["list_containers"]["enabled"] is True
        assert tools["list_containers"]["gated_by"] is None

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        tools = {t["name"]: t for t in server.list_tools()}
        assert tools["restart_service"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_tool_endpoint_carries_gating(self, monkeypatch):
        from src.api.routes.tools import get_tool

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        tool = await get_tool(request, "scale_service")
        assert tool.enabled is False
        assert tool.gated_by == "AIOPS_ENABLE_ACTION_TOOLS"

        tool = await get_tool(request, "find_similar")
        assert tool.enabled is True


# ---------------------------------------------------------------------------
# D-item5: gate populates constitutional context (active_incident / action_scope)
# ---------------------------------------------------------------------------

class TestGateContextPopulation:
    def _capturing_validator_request(self):
        """Real-ish request whose validator captures the context it was given."""
        captured = {}
        validator = MagicMock()
        validator.validate.side_effect = lambda **kw: captured.update(kw) or _report()
        request = MagicMock()
        request.app.state = MagicMock(spec=["validator"])
        request.app.state.validator = validator
        return request, captured

    @pytest.mark.asyncio
    async def test_incident_remediate_source_sets_active_incident(self, monkeypatch, fake_run):
        from src.api.routes.tools import ToolCallRequest, _action_tool_gate

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request, captured = self._capturing_validator_request()
        tool_call = ToolCallRequest(
            tool_name="restart_service",
            parameters={"service_name": "nextcloud", "reason": "t", "confidence": 0.9},
            context={"source": "incident_remediate", "human_approved": True},
        )

        _action_tool_gate(request, tool_call)

        ctx = captured["context"]
        # Wired so P1.2/P2.1 actually evaluate on the live remediation path.
        assert ctx["active_incident"] is True
        assert ctx["action_scope"] == "single"
        # Caller context still flows through.
        assert ctx["human_approved"] is True

    @pytest.mark.asyncio
    async def test_rest_ui_call_does_not_assert_active_incident(self, monkeypatch, fake_run):
        from src.api.routes.tools import ToolCallRequest, _action_tool_gate

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request, captured = self._capturing_validator_request()
        tool_call = ToolCallRequest(
            tool_name="restart_service",
            parameters={"service_name": "nextcloud", "reason": "t", "confidence": 0.9},
        )

        _action_tool_gate(request, tool_call)

        ctx = captured["context"]
        # A bare UI call is not an incident-remediation flow.
        assert ctx.get("active_incident") is not True


# ---------------------------------------------------------------------------
# Programmatic + MCP-server execution paths share the gate
# ---------------------------------------------------------------------------

class TestOtherDispatchPaths:
    @pytest.mark.asyncio
    async def test_execute_tool_call_is_gated(self, monkeypatch, fake_run):
        """The programmatic path (chat.py) must not bypass the gate."""
        from src.api.routes.tools import execute_tool_call

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        result = await execute_tool_call(
            request, "restart_service", {"service_name": "nextcloud", "reason": "t"},
        )
        assert result["success"] is False
        assert result["error_code"] == "action_tools_disabled"
        assert fake_run.calls == []

    @pytest.mark.asyncio
    async def test_mcp_server_execute_tool_is_gated(self, monkeypatch):
        from src.mcp.server import MCPActionServer

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        server = MCPActionServer()
        result = await server.execute_tool(
            "restart_service", {"service_name": "nextcloud", "reason": "t"},
        )
        assert result.success is False
        assert result.metadata.get("error_code") == "action_tools_disabled"
