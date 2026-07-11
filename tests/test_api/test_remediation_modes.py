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
    # The cap now comes from the persisted constitutional.maxActionsPerMinute
    # setting (W2.2), falling back to the env/default — use the resolved value.
    chat_module._auto_exec_times.clear()
    cap = chat_module._auto_exec_max_per_min()
    assert _auto_exec_rate_ok() is True
    for _ in range(cap):
        assert _auto_exec_rate_ok() is True
        _record_auto_exec()
    # Budget now exhausted.
    assert _auto_exec_rate_ok() is False
    chat_module._auto_exec_times.clear()


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
        async def fake_exec(request, tool_name, parameters, context=None):
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
        async def fake_exec(request, tool_name, parameters, context=None):
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
        assert len(chat_module._auto_exec_times) == 1  # execution consumed budget

    @pytest.mark.asyncio
    async def test_auto_degrades_when_gate_requires_approval(self):
        """The constitutional gate may return approval_required -> never forced."""
        async def fake_exec(request, tool_name, parameters, context=None):
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
    async def test_gate_refusal_does_not_consume_rate_budget(self):
        """Only real executions count against the per-minute cap — a gate
        refusal that degrades to proposed must leave the budget untouched."""
        async def fake_exec(request, tool_name, parameters, context=None):
            return {
                "success": False,
                "error_code": "approval_required",
                "error": "needs a human",
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
        assert out["status"] == "proposed"
        assert len(chat_module._auto_exec_times) == 0
        assert _auto_exec_rate_ok() is True

    @pytest.mark.asyncio
    async def test_auto_blocked_when_kill_switch_disabled(self):
        """Disabled action tools (kill-switch) surface as blocked, cached for retry."""
        async def fake_exec(request, tool_name, parameters, context=None):
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

        captured: dict = {}

        async def fake_exec(request, tool_name, parameters, context=None):
            # The read-only analyze_logs tool also routes here; only assert on restart.
            if tool_name == "restart_service":
                captured["parameters"] = parameters
                captured["context"] = context
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
        # The gate received the forwarded confidence + telemetry evidence.
        assert "confidence" in captured["parameters"]
        assert captured["context"]["telemetry_evidence"] is True

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
    def _seed_pending(self, owner="admin", service="nextcloud-db", confidence=0.82):
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
            # The real evidence-based chat confidence cached with the proposal;
            # decide_action carries this through to the gate (D5: no longer
            # synthesized to the auto threshold).
            "confidence": confidence,
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

        async def fake_exec(request, tool_name, parameters, context=None):
            assert tool_name == "restart_service"
            assert parameters["service_name"] == "nextcloud-db"
            # D5: human approval no longer synthesizes a 0.90 confidence. The REAL
            # evidence-based confidence cached with the proposal (0.82 here) is
            # carried through; human_approved=True is the matrix authorization, so
            # the gate still authorizes even below the auto threshold.
            assert parameters.get("confidence") == 0.82
            assert context is not None
            assert context.get("telemetry_evidence") is True
            assert context.get("human_approved") is True
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

        async def fake_exec(request, tool_name, parameters, context=None):
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


# ---------------------------------------------------------------------------
# Agent-initiated action queue (consent-before-execution)
# ---------------------------------------------------------------------------

class TestQueueActionProposal:
    """_queue_action_proposal: an agent action-tool call queues a consent
    proposal instead of executing — or refuses with an honest error_code."""

    def test_kill_switch_off_refuses(self, monkeypatch):
        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        queue: list = []
        out = chat_module._queue_action_proposal(
            "restart_service", {"service_name": "nextcloud", "reason": "r"}, queue
        )
        assert out["success"] is False
        assert out["error_code"] == "action_tools_disabled"
        assert queue == []

    def test_diagnose_mode_refuses(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("diagnose")
        ):
            out = chat_module._queue_action_proposal(
                "restart_service", {"service_name": "nextcloud", "reason": "r"}, queue
            )
        assert out["success"] is False
        assert out["error_code"] == "remediation_disabled"
        assert queue == []

    def test_approve_mode_queues_without_executing(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("approve")
        ):
            out = chat_module._queue_action_proposal(
                "restart_service",
                {"service_name": "nextcloud", "reason": "stuck workers"},
                queue,
            )
        assert out["success"] is True
        assert out["data"]["status"] == "queued_for_approval"
        assert len(queue) == 1
        proposed = queue[0]
        assert proposed["status"] == "proposed"
        assert proposed["mode"] == "approve"
        assert proposed["tool_name"] == "restart_service"
        assert proposed["parameters"]["service_name"] == "nextcloud"
        assert out["data"]["action_id"] == proposed["id"]
        # Queueing must not touch the pending cache — _finalize_proposal owns that.
        assert chat_module._pending_actions == {}

    def test_non_whitelisted_target_refused(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.delenv("AIOPS_ACTION_CONTAINER_WHITELIST", raising=False)
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("approve")
        ):
            out = chat_module._queue_action_proposal(
                "restart_service", {"service_name": "neo4j", "reason": "r"}, queue
            )
        assert out["success"] is False
        assert out["error_code"] == "container_not_whitelisted"
        assert queue == []

    def test_env_whitelist_extension_allows_target(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.setenv("AIOPS_ACTION_CONTAINER_WHITELIST", "nextcloud-db")
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("approve")
        ):
            out = chat_module._queue_action_proposal(
                "restart_service", {"service_name": "nextcloud-db", "reason": "r"}, queue
            )
        assert out["success"] is True
        assert queue[0]["target"] == "t3"

    def test_second_action_same_turn_refused(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("approve")
        ):
            first = chat_module._queue_action_proposal(
                "restart_service", {"service_name": "nextcloud", "reason": "r"}, queue
            )
            second = chat_module._queue_action_proposal(
                "scale_service",
                {"service_name": "nextcloud", "target_replicas": 2, "reason": "r"},
                queue,
            )
        assert first["success"] is True
        assert second["success"] is False
        assert second["error_code"] == "action_already_queued"
        assert len(queue) == 1

    def test_scale_service_proposal_shape(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        queue: list = []
        with patch.object(
            chat_module, "get_remediation_settings", return_value=_remediation("auto")
        ):
            out = chat_module._queue_action_proposal(
                "scale_service",
                {"service_name": "nextcloud", "target_replicas": 9, "reason": "load"},
                queue,
            )
        assert out["success"] is True
        proposed = queue[0]
        assert proposed["tool_name"] == "scale_service"
        assert proposed["mode"] == "auto"
        # Display clamp mirrors tools.py's authoritative 0-5 clamp.
        assert proposed["parameters"]["target_replicas"] == 5
        assert "Scale nextcloud to 5 replicas" == proposed["title"]


class TestFinalizeProposalAllowlist:
    """auto mode is scoped per tool by remediation.autoToolAllowlist."""

    @pytest.mark.asyncio
    async def test_auto_not_allowlisted_degrades_to_proposed(self):
        async def fake_exec(*a, **k):
            raise AssertionError("non-allowlisted tool must not auto-execute")

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=_remediation("auto", autoToolAllowlist=[]),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "proposed"
        assert out["id"] in chat_module._pending_actions

    @pytest.mark.asyncio
    async def test_auto_allowlisted_executes(self):
        async def fake_exec(request, tool_name, parameters, context=None):
            return {"success": True, "data": {"status": "completed"}}

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=_remediation(
                    "auto", autoToolAllowlist=["restart_service"]
                ),
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "auto_executed"

    @pytest.mark.asyncio
    async def test_missing_allowlist_key_keeps_legacy_behaviour(self):
        """Settings dicts without the key (legacy persisted files) stay permissive."""
        async def fake_exec(request, tool_name, parameters, context=None):
            return {"success": True, "data": {"status": "completed"}}

        settings = _remediation("auto")
        assert "autoToolAllowlist" not in settings
        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            out = await _maybe_propose_remediation(
                _make_request(),
                mode="auto",
                content=_RCA_RESTART_DB,
                suggested_actions=["Restart the nextcloud-db container"],
                service="nextcloud",
                confidence=0.99,
                has_tool_data=True,
                remediation_settings=settings,
                owner="admin",
                conversation_id="conv-1",
            )
        assert out["status"] == "auto_executed"


class TestQueuedActionInFinalize:
    """_finalize_chat_turn: a queued agent action IS the turn's proposal."""

    def _make_conversation(self):
        from src.api.schemas.chat import ConversationHistory

        conv = ConversationHistory(
            conversation_id="conv-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[],
            context=None,
            owner="admin",
        )
        chat_module._conversations["conv-1"] = conv
        return conv

    @pytest.mark.asyncio
    async def test_queued_action_wins_over_text_detection(self):
        from src.auth.deps import User

        conv = self._make_conversation()
        queued = [
            _build_proposed_action(
                {"service_name": "nextcloud", "reason": "agent-initiated restart"},
                mode="approve",
                status_value="proposed",
            )
        ]
        with patch.object(
            chat_module, "get_remediation_settings",
            return_value=_remediation("approve"),
        ), patch.object(
            chat_module, "_find_related_incidents", new=AsyncMock(return_value=[])
        ):
            resp = await chat_module._finalize_chat_turn(
                _make_request(),
                user_message_text="restart nextcloud",
                conversation=conv,
                conversation_id="conv-1",
                user=User(id="u1", username="admin", role="admin"),
                service="nextcloud",
                # This content would text-detect a nextcloud-db restart if the
                # queued proposal did not take precedence.
                content=_RCA_RESTART_DB,
                confidence=0.9,
                metadata={},
                tool_struct={},
                has_tool_data=True,
                queued_actions=queued,
            )
        assert resp.proposed_action is not None
        assert resp.proposed_action["id"] == queued[0]["id"]
        assert resp.proposed_action["parameters"]["service_name"] == "nextcloud"
        assert resp.proposed_action["id"] in chat_module._pending_actions
        # Persisted on the assistant turn for reload replay.
        assert conv.messages[-1].metadata["proposed_action"]["id"] == queued[0]["id"]

    @pytest.mark.asyncio
    async def test_no_queue_falls_back_to_text_detection(self):
        from src.auth.deps import User

        conv = self._make_conversation()
        with patch.object(
            chat_module, "get_remediation_settings",
            return_value=_remediation("approve"),
        ), patch.object(
            chat_module, "_find_related_incidents", new=AsyncMock(return_value=[])
        ):
            resp = await chat_module._finalize_chat_turn(
                _make_request(),
                user_message_text="what is wrong with nextcloud?",
                conversation=conv,
                conversation_id="conv-1",
                user=User(id="u1", username="admin", role="admin"),
                service="nextcloud",
                content=_RCA_RESTART_DB,
                confidence=0.9,
                metadata={},
                tool_struct={},
                has_tool_data=True,
                queued_actions=[],
            )
        assert resp.proposed_action is not None
        assert resp.proposed_action["parameters"]["service_name"] == "nextcloud-db"


class TestDecisionWriteBack:
    """decide_action writes the outcome back onto the persisted conversation."""

    def _seed(self, *, status_ok=True):
        from src.api.schemas.chat import ChatMessage, ChatRole, ConversationHistory

        action = _build_proposed_action(
            {"service_name": "nextcloud-db", "reason": "restart it"},
            mode="approve",
            status_value="proposed",
        )
        conv = ConversationHistory(
            conversation_id="conv-1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[
                ChatMessage(
                    role=ChatRole.ASSISTANT,
                    content="I found the fault; approve the restart below.",
                    timestamp=datetime.utcnow(),
                    metadata={"confidence": 0.82, "proposed_action": action},
                )
            ],
            context=None,
            owner="admin",
        )
        chat_module._conversations["conv-1"] = conv
        chat_module._pending_actions[action["id"]] = {
            "tool_name": action["tool_name"],
            "parameters": action["parameters"],
            "owner": "admin",
            "conversation_id": "conv-1",
            "created_at": __import__("time").time(),
            "proposed_action": action,
            "confidence": 0.82,
        }
        return action["id"], conv

    @pytest.mark.asyncio
    async def test_reject_marks_conversation_rejected(self):
        aid, conv = self._seed()
        await decide_action(_make_request(), aid, DecisionRequest(approved=False))
        assert conv.messages[0].metadata["proposed_action"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_approve_success_marks_conversation_executed(self):
        aid, conv = self._seed()

        async def fake_exec(request, tool_name, parameters, context=None):
            return {
                "success": True,
                "data": {"status": "completed"},
                "metadata": {"constitutional": {"can_proceed": True}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            await decide_action(_make_request(), aid, DecisionRequest(approved=True))
        stored = conv.messages[0].metadata["proposed_action"]
        assert stored["status"] == "executed"
        assert stored["execution_result"] == {"status": "completed"}
        assert stored["verdict"] == {"can_proceed": True}

    @pytest.mark.asyncio
    async def test_gate_refusal_marks_conversation_refused(self):
        aid, conv = self._seed()

        async def fake_exec(request, tool_name, parameters, context=None):
            return {
                "success": False,
                "error_code": "validation_blocked",
                "error": "tier-1",
                "metadata": {"constitutional": {"can_proceed": False}},
            }

        with patch.object(chat_module, "execute_tool_call", new=fake_exec):
            await decide_action(_make_request(), aid, DecisionRequest(approved=True))
        assert conv.messages[0].metadata["proposed_action"]["status"] == "refused"

    @pytest.mark.asyncio
    async def test_missing_conversation_is_harmless(self):
        """Decision still succeeds when the conversation was evicted/deleted."""
        aid, _ = self._seed()
        chat_module._conversations.clear()
        resp = await decide_action(_make_request(), aid, DecisionRequest(approved=False))
        assert resp.status == "rejected"


class TestScaleProposalBuilder:
    def test_scale_shape_title_and_clamp(self):
        action = _build_proposed_action(
            {"service_name": "nextcloud", "reason": "load spike", "target_replicas": 3},
            mode="approve",
            status_value="proposed",
            tool_name="scale_service",
        )
        assert action["tool_name"] == "scale_service"
        assert action["parameters"]["target_replicas"] == 3
        assert action["title"] == "Scale nextcloud to 3 replicas"

        one = _build_proposed_action(
            {"service_name": "nextcloud", "reason": "r", "target_replicas": 1},
            mode="approve",
            status_value="proposed",
            tool_name="scale_service",
        )
        assert one["title"] == "Scale nextcloud to 1 replica"

        # Garbage replica counts fall back to a safe display default.
        bad = _build_proposed_action(
            {"service_name": "nextcloud", "reason": "r", "target_replicas": "lots"},
            mode="approve",
            status_value="proposed",
            tool_name="scale_service",
        )
        assert bad["parameters"]["target_replicas"] == 1
