"""Constitutional AIOps - Lane B remediation tests.

Covers the 3 remediation modes (diagnose / approve / auto) on the chat path and
the approve-to-run decision endpoint.

Mirrors the established direct-call test style (no ``src.main`` import, no
FastAPI DI): build a fake Request with SimpleNamespace, patch
``execute_tool_call`` and ``get_remediation_settings`` on the chat module, and
call route functions / helpers directly.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.routes import chat as chat_module
from src.api.routes.chat import (
    _auto_exec_rate_ok,
    _build_proposed_action,
    _detect_remediation_action,
    _maybe_propose_remediation,
    _record_auto_exec,
    chat,
    decide_action,
)
from src.api.schemas.chat import ChatRequest, DecisionRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**state) -> SimpleNamespace:
    """Fake FastAPI Request whose app.state only carries the given attrs."""
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def _agent_response(content: str, *, model="qwen3-14b", tokens=42) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.confidence = 0.5
    resp.metadata = {"mode": "chat", "model_used": model, "tokens_used": tokens}
    return resp


def _make_log(message: str, level: str) -> MagicMock:
    log = MagicMock()
    log.timestamp = datetime(2026, 1, 1, 12, 0, 0)
    log.level = level
    log.message = message
    log.service = "nextcloud"
    return log


def _make_metric(name: str, value: float) -> MagicMock:
    m = MagicMock()
    m.timestamp = datetime(2026, 1, 1, 12, 0, 0)
    m.name = name
    m.value = value
    return m


# RCA reply that clearly proposes restarting a whitelisted container.
_RCA_RESTART_DB = (
    "Root cause: the nextcloud-db connection pool is exhausted.\n"
    "Recommendations:\n"
    "- Restart the nextcloud-db container to clear the stuck pool.\n"
)


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset module-level caches between tests."""
    chat_module._conversations.clear()
    chat_module._pending_actions.clear()
    chat_module._auto_exec_times.clear()
    yield
    chat_module._conversations.clear()
    chat_module._pending_actions.clear()
    chat_module._auto_exec_times.clear()


def _remediation(mode="diagnose", **over):
    base = {
        "mode": mode,
        "autoConfidenceThreshold": 90,
        "requireEvidenceForAuto": True,
        "demoTargetUrl": "",
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Detection + builder (unit)
# ---------------------------------------------------------------------------

class TestDetection:
    def test_detects_restart_of_whitelisted_container(self):
        detected = _detect_remediation_action(
            _RCA_RESTART_DB, ["Restart the nextcloud-db container"], "nextcloud"
        )
        assert detected is not None
        assert detected["service_name"] == "nextcloud-db"
        assert "restart" in detected["reason"].lower()

    def test_detects_from_suggested_actions_only(self):
        detected = _detect_remediation_action(
            "Some prose with no action.", ["Please restart nextcloud now"], None
        )
        assert detected is not None
        assert detected["service_name"] == "nextcloud"

    def test_ignores_non_whitelisted_container(self):
        detected = _detect_remediation_action(
            "Restart the neo4j container to fix it.", None, "neo4j"
        )
        assert detected is None

    def test_no_restart_no_action(self):
        detected = _detect_remediation_action(
            "Increase the connection pool size in config.", ["Scale up workers"], "nextcloud"
        )
        assert detected is None

    def test_builder_shape_and_target_routing(self):
        action = _build_proposed_action(
            {"service_name": "nextcloud-db", "reason": "restart it"},
            mode="approve",
            status_value="proposed",
        )
        assert action["tool_name"] == "restart_service"
        assert action["parameters"] == {"service_name": "nextcloud-db", "reason": "restart it"}
        assert action["target"] == "t3"          # db -> t3
        assert action["mode"] == "approve"
        assert action["status"] == "proposed"
        assert action["verdict"] is None and action["execution_result"] is None
        assert action["id"].startswith("act-")

        local = _build_proposed_action(
            {"service_name": "nextcloud", "reason": "r"}, mode="auto", status_value="proposed"
        )
        assert local["target"] == "local"        # non-db -> local


# ---------------------------------------------------------------------------
# Rate limiter (unit)
# ---------------------------------------------------------------------------

def test_auto_exec_rate_limit():
    chat_module._auto_exec_times.clear()
    assert _auto_exec_rate_ok() is True
    for _ in range(chat_module._AUTO_EXEC_MAX):
        assert _auto_exec_rate_ok() is True
        _record_auto_exec()
    # Budget now exhausted.
    assert _auto_exec_rate_ok() is False


# ---------------------------------------------------------------------------
# _maybe_propose_remediation behaviour per mode (unit-ish)
# ---------------------------------------------------------------------------

class TestMaybeProposeRemediation:
    @pytest.mark.asyncio
    async def test_diagnose_returns_none_no_cache(self):
        out = await _maybe_propose_remediation(
            _make_request(),
            mode="diagnose",
            content=_RCA_RESTART_DB,
            suggested_actions=["Restart the nextcloud-db container"],
            service="nextcloud",
            confidence=0.95,
            has_tool_data=True,
            remediation_settings=_remediation("diagnose"),
            owner="admin",
            conversation_id="conv-1",
        )
        assert out is None
        assert chat_module._pending_actions == {}

    @pytest.mark.asyncio
    async def test_approve_caches_but_does_not_execute(self):
        called = {"n": 0}

        async def fake_exec(*a, **k):
            called["n"] += 1
            return {"success": True}

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="approve",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.95,
                has_tool_data=True,
                remediation_settings=_remediation("approve"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out is not None
        assert out["status"] == "proposed"
        assert called["n"] == 0                       # nothing executed
        assert out["id"] in chat_module._pending_actions
        entry = chat_module._pending_actions[out["id"]]
        assert entry["owner"] == "admin"
        assert entry["tool_name"] == "restart_service"

    @pytest.mark.asyncio
    async def test_auto_executes_when_interlocks_pass(self):
        async def fake_exec(request, tool_name, parameters):
            assert tool_name == "restart_service"
            return {
                "success": True,
                "data": {"service": "nextcloud-db", "action": "restart", "status": "completed"},
                "metadata": {"constitutional": {"can_proceed": True}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.95,           # >= 0.90 threshold
                has_tool_data=True,        # evidence present
                remediation_settings=_remediation("auto"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "auto_executed"
        assert out["execution_result"]["status"] == "completed"
        assert out["verdict"] == {"can_proceed": True}
        # Executed -> not left pending.
        assert out["id"] not in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_degrades_to_proposed_below_confidence(self):
        async def fake_exec(*a, **k):
            raise AssertionError("must not execute below threshold")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.80,           # < 0.90 -> interlock fails
                has_tool_data=True,
                remediation_settings=_remediation("auto"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "proposed"
        assert out["id"] in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_degrades_when_evidence_required_but_absent(self):
        async def fake_exec(*a, **k):
            raise AssertionError("must not execute without evidence")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=False,       # no evidence + requireEvidenceForAuto True
                remediation_settings=_remediation("auto", requireEvidenceForAuto=True),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "proposed"

    @pytest.mark.asyncio
    async def test_auto_executes_without_evidence_when_not_required(self):
        async def fake_exec(request, tool_name, parameters):
            return {"success": True, "data": {"status": "completed"}}

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=False,
                remediation_settings=_remediation("auto", requireEvidenceForAuto=False),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "auto_executed"

    @pytest.mark.asyncio
    async def test_auto_degrades_when_gate_requires_approval(self):
        """The constitutional gate may return approval_required -> never forced."""
        async def fake_exec(request, tool_name, parameters):
            return {
                "success": False,
                "error_code": "approval_required",
                "error": "needs a human",
                "metadata": {"constitutional": {"requires_approval": True}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=_remediation("auto"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "proposed"             # degraded, not executed
        assert out["verdict"] == {"requires_approval": True}
        assert out["id"] in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_blocked_when_kill_switch_disabled(self):
        """Disabled action tools (kill-switch) surface as blocked, cached for retry."""
        async def fake_exec(request, tool_name, parameters):
            return {
                "success": False,
                "error_code": "action_tools_disabled",
                "error": "disabled",
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=_remediation("auto"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "blocked"
        assert out["execution_result"]["error_code"] == "action_tools_disabled"
        assert out["id"] in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_degrades_when_rate_limited(self):
        # Exhaust the per-minute budget first.
        for _ in range(chat_module._AUTO_EXEC_MAX):
            _record_auto_exec()

        async def fake_exec(*a, **k):
            raise AssertionError("must not execute when rate-limited")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=_remediation("auto"),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "proposed"


# ---------------------------------------------------------------------------
# End-to-end chat() integration per mode
# ---------------------------------------------------------------------------

class TestChatModes:
    @pytest.mark.asyncio
    async def test_diagnose_attaches_no_proposed_action(self):
        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=_agent_response(_RCA_RESTART_DB))
        request = _make_request(reasoning_agent=reasoning_agent)
        chat_request = ChatRequest(message="what is wrong with nextcloud?")

        with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
             patch.object(chat_module, "get_remediation_settings", return_value=_remediation("diagnose")):
            response = await chat(request, chat_request)

        assert response.proposed_action is None
        assert chat_module._pending_actions == {}

    @pytest.mark.asyncio
    async def test_approve_attaches_proposed_action(self):
        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=_agent_response(_RCA_RESTART_DB))
        request = _make_request(reasoning_agent=reasoning_agent)
        chat_request = ChatRequest(message="diagnose nextcloud and recommend a fix")

        async def fake_exec(*a, **k):
            raise AssertionError("approve mode must not execute in chat()")

        with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
             patch.object(chat_module, "get_remediation_settings", return_value=_remediation("approve")), \
             patch.object(chat_module, "execute_tool_call", new=fake_exec):
            response = await chat(request, chat_request)

        pa = response.proposed_action
        assert pa is not None
        assert pa["status"] == "proposed"
        assert pa["tool_name"] == "restart_service"
        assert pa["parameters"]["service_name"] == "nextcloud-db"
        assert pa["id"] in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_executes_with_telemetry_evidence(self):
        collector = MagicMock()
        collector.query_logs = AsyncMock(return_value=[_make_log("pool exhausted", "ERROR")])
        collector.query_metrics = AsyncMock(return_value=[_make_metric("db_conns", 99.0)])

        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=_agent_response(_RCA_RESTART_DB))
        request = _make_request(reasoning_agent=reasoning_agent, telemetry_collector=collector)
        chat_request = ChatRequest(message="analyze nextcloud error logs and fix it")

        async def fake_exec(request, tool_name, parameters):
            # The read-only analyze_logs tool also routes here; only assert on restart.
            if tool_name == "restart_service":
                return {"success": True, "data": {"status": "completed"}}
            return {"success": True, "data": {"summary": {"total_logs": 1, "error_count": 1}}}

        with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
             patch.object(chat_module, "get_remediation_settings",
                          return_value=_remediation("auto", autoConfidenceThreshold=70)), \
             patch.object(chat_module, "execute_tool_call", new=fake_exec):
            response = await chat(request, chat_request)

        pa = response.proposed_action
        assert pa is not None
        assert pa["status"] == "auto_executed"
        assert pa["execution_result"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_remediation_failure_never_breaks_chat(self):
        """If get_remediation_settings raises, chat() still returns a response."""
        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=_agent_response("Nextcloud is healthy."))
        request = _make_request(reasoning_agent=reasoning_agent)
        chat_request = ChatRequest(message="is nextcloud healthy?")

        def boom():
            raise RuntimeError("settings unavailable")

        with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
             patch.object(chat_module, "get_remediation_settings", side_effect=boom):
            response = await chat(request, chat_request)

        assert response.proposed_action is None
        assert response.message.content == "Nextcloud is healthy."


# ---------------------------------------------------------------------------
# Decision endpoint
# ---------------------------------------------------------------------------

class TestDecisionEndpoint:
    def _seed_pending(self, owner="admin", service="nextcloud-db"):
        action = _build_proposed_action(
            {"service_name": service, "reason": "restart it"},
            mode="approve",
            status_value="proposed",
        )
        chat_module._pending_actions[action["id"]] = {
            "tool_name": action["tool_name"],
            "parameters": action["parameters"],
            "owner": owner,
            "conversation_id": "conv-1",
            "created_at": __import__("time").time(),
            "proposed_action": action,
        }
        return action["id"]

    @pytest.mark.asyncio
    async def test_reject_does_not_execute(self):
        aid = self._seed_pending()

        async def fake_exec(*a, **k):
            raise AssertionError("rejection must not execute")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            resp = await decide_action(_make_request(), aid, DecisionRequest(approved=False))

        assert resp.action_id == aid
        assert resp.status == "rejected"
        assert resp.success is False
        assert aid not in chat_module._pending_actions      # consumed

    @pytest.mark.asyncio
    async def test_approve_executes_and_maps_success(self):
        aid = self._seed_pending()

        async def fake_exec(request, tool_name, parameters):
            assert tool_name == "restart_service"
            assert parameters["service_name"] == "nextcloud-db"
            return {
                "success": True,
                "data": {"service": "nextcloud-db", "action": "restart", "status": "completed"},
                "metadata": {"constitutional": {"can_proceed": True}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            resp = await decide_action(_make_request(), aid, DecisionRequest(approved=True))

        assert resp.status == "executed"
        assert resp.success is True
        assert resp.error_code is None
        assert resp.verdict == {"can_proceed": True}
        assert resp.result["status"] == "completed"
        assert aid not in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_approve_maps_gate_refusal(self):
        aid = self._seed_pending()

        async def fake_exec(request, tool_name, parameters):
            return {
                "success": False,
                "error_code": "approval_required",
                "error": "needs a human",
                "metadata": {"constitutional": {"requires_approval": True}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            resp = await decide_action(_make_request(), aid, DecisionRequest(approved=True))

        assert resp.status == "refused"
        assert resp.success is False
        assert resp.error_code == "approval_required"
        assert resp.verdict == {"requires_approval": True}

    @pytest.mark.asyncio
    async def test_unknown_or_expired_action_404(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as ei:
            await decide_action(_make_request(), "act-doesnotexist", DecisionRequest(approved=True))
        assert ei.value.status_code == 404

    @pytest.mark.asyncio
    async def test_other_user_cannot_decide(self):
        """An action owned by someone else is 404 (not 403) to its non-owner."""
        from fastapi import HTTPException

        from src.auth.deps import User
        aid = self._seed_pending(owner="alice")
        bob = User(id="bob-id", username="bob", role="user")
        with pytest.raises(HTTPException) as ei:
            await decide_action(_make_request(), aid, DecisionRequest(approved=True), user=bob)
        assert ei.value.status_code == 404
        # Still pending (untouched).
        assert aid in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_execute_exception_maps_to_refused(self):
        aid = self._seed_pending()

        async def fake_exec(*a, **k):
            raise RuntimeError("docker daemon down")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            resp = await decide_action(_make_request(), aid, DecisionRequest(approved=True))

        assert resp.status == "refused"
        assert resp.success is False
        assert resp.error_code == "execution_failed"
