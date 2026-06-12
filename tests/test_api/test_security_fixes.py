"""
Regression tests for the session-12 security/correctness fixes.

Covers:
  S1  — action tools (restart/scale) refused via /tools/call unless explicitly
        enabled AND constitutionally authorized
  S2  — get_dependencies depth coerced/clamped (Cypher-injection guard)
  S6  — generate-episodes no longer wipes the graph by default
  S7  — demo routes gated off in production; container whitelist enforced
  S9  — in-memory conversation store evicts beyond its cap
  S10 — logql_escape strips selector-breaking characters
  F2  — _extract_actions collects keyword-less bullets under a
        recommendations-style header

NOTE: per CI constraints these tests import route modules directly and never
import src.main (langgraph is absent from the minimal CI install).
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# S1 — action-tool constitutional gate
# ---------------------------------------------------------------------------

class TestActionToolGate:
    def _tool_call(self, name="restart_service", params=None):
        from src.api.routes.tools import ToolCallRequest

        return ToolCallRequest(tool_name=name, parameters=params or {"service_name": "nextcloud"})

    def test_disabled_by_default(self, monkeypatch):
        from src.api.routes.tools import _action_tool_gate

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        error = _action_tool_gate(request, self._tool_call())
        assert error is not None
        assert "disabled" in error

    def test_enabled_but_no_validator_refuses(self, monkeypatch):
        from src.api.routes.tools import _action_tool_gate

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        request = MagicMock()
        request.app.state = MagicMock(spec=[])  # no validator attribute
        error = _action_tool_gate(request, self._tool_call())
        assert error is not None
        assert "validator" in error.lower()

    def test_enabled_validator_refuses_without_automatic_authorization(self, monkeypatch):
        from src.api.routes.tools import _action_tool_gate

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        report = MagicMock()
        report.can_proceed = True
        report.requires_approval = True  # APPROVAL_REQUIRED band
        report.authorization_level.value = "approval"
        report.explanation = "needs human approval"

        validator = MagicMock()
        validator.validate.return_value = report

        request = MagicMock()
        request.app.state = MagicMock(spec=["validator"])
        request.app.state.validator = validator

        error = _action_tool_gate(request, self._tool_call())
        assert error is not None
        assert "refused" in error.lower()
        validator.validate.assert_called_once()

    def test_enabled_validator_allows_automatic(self, monkeypatch):
        from src.api.routes.tools import _action_tool_gate

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        report = MagicMock()
        report.can_proceed = True
        report.requires_approval = False
        validator = MagicMock()
        validator.validate.return_value = report

        request = MagicMock()
        request.app.state = MagicMock(spec=["validator"])
        request.app.state.validator = validator

        assert _action_tool_gate(request, self._tool_call()) is None

    @pytest.mark.asyncio
    async def test_call_tool_endpoint_refuses_restart_by_default(self, monkeypatch):
        """End-to-end through the dispatcher: a restart call must come back
        success=False with the disabled error and never reach subprocess."""
        from src.api.routes.tools import call_tool

        monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
        request = MagicMock()
        request.app.state = MagicMock(spec=[])

        response = await call_tool(request, self._tool_call("restart_service"))
        assert response.success is False
        assert "disabled" in (response.error or "")

        response = await call_tool(request, self._tool_call(
            "scale_service", {"service_name": "nextcloud", "target_replicas": 2}
        ))
        assert response.success is False
        assert "disabled" in (response.error or "")


# ---------------------------------------------------------------------------
# S2 — depth clamp in get_dependencies (REST tools path)
# ---------------------------------------------------------------------------

class TestDependencyDepthClamp:
    @pytest.mark.asyncio
    async def test_malicious_depth_is_clamped_not_interpolated(self):
        from src.api.routes.tools import _execute_get_dependencies

        captured_queries: list[str] = []

        class FakeResult:
            async def data(self):
                return []

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def run(self, query, **params):
                captured_queries.append(query)
                return FakeResult()

        client = MagicMock()
        client.session = lambda: FakeSession()

        injection = '1]->() DETACH DELETE n //'
        response = await _execute_get_dependencies(
            client,
            {"service_name": "backend", "depth": injection},
            0.0,
        )
        # Injection string is not a valid int → falls back to default depth 2.
        assert response.success is True
        assert all("DETACH DELETE" not in q for q in captured_queries)
        assert all("*1..2" in q for q in captured_queries)

    @pytest.mark.asyncio
    async def test_depth_clamped_to_max_5(self):
        from src.api.routes.tools import _execute_get_dependencies

        captured_queries: list[str] = []

        class FakeResult:
            async def data(self):
                return []

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def run(self, query, **params):
                captured_queries.append(query)
                return FakeResult()

        client = MagicMock()
        client.session = lambda: FakeSession()

        await _execute_get_dependencies(client, {"service_name": "backend", "depth": 99}, 0.0)
        assert all("*1..5" in q for q in captured_queries)


# ---------------------------------------------------------------------------
# S6 — generate-episodes default no longer destructive
# ---------------------------------------------------------------------------

class TestGenerateEpisodesDefault:
    def test_clear_existing_defaults_false(self):
        from src.api.routes.graph import GenerateEpisodesRequest

        assert GenerateEpisodesRequest().clear_existing is False


# ---------------------------------------------------------------------------
# S7 — demo gating
# ---------------------------------------------------------------------------

class TestDemoGate:
    def test_blocked_in_production_by_default(self, monkeypatch):
        from fastapi import HTTPException

        from src.api.routes.demo import _ensure_demo_allowed

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("AIOPS_ENABLE_DEMO", raising=False)
        with pytest.raises(HTTPException) as exc:
            _ensure_demo_allowed()
        assert exc.value.status_code == 403

    def test_allowed_in_production_when_enabled(self, monkeypatch):
        from src.api.routes.demo import _ensure_demo_allowed

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("AIOPS_ENABLE_DEMO", "true")
        _ensure_demo_allowed()  # must not raise

    def test_allowed_outside_production(self, monkeypatch):
        from src.api.routes.demo import _ensure_demo_allowed

        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.delenv("AIOPS_ENABLE_DEMO", raising=False)
        _ensure_demo_allowed()  # must not raise

    def test_container_whitelist(self, monkeypatch):
        from src.api.routes.demo import _allowed_demo_containers

        monkeypatch.delenv("AIOPS_DEMO_CONTAINER_WHITELIST", raising=False)
        assert _allowed_demo_containers() == {"nextcloud"}

        monkeypatch.setenv("AIOPS_DEMO_CONTAINER_WHITELIST", "alpha, beta")
        assert _allowed_demo_containers() == {"nextcloud", "alpha", "beta"}


# ---------------------------------------------------------------------------
# S9 — conversation eviction
# ---------------------------------------------------------------------------

class TestConversationEviction:
    def test_evicts_least_recently_updated(self, monkeypatch):
        import src.api.routes.chat as chat_module
        from src.api.schemas.chat import ConversationHistory

        monkeypatch.setattr(chat_module, "_MAX_CONVERSATIONS", 3)
        monkeypatch.setattr(chat_module, "_conversations", {})

        base = datetime.utcnow()
        for i in range(5):
            conv = ConversationHistory(
                conversation_id=f"conv-{i}",
                created_at=base,
                updated_at=base + timedelta(minutes=i),
                messages=[],
                context=None,
            )
            chat_module._conversations[conv.conversation_id] = conv

        chat_module._evict_stale_conversations()

        assert len(chat_module._conversations) == 3
        # The two OLDEST (conv-0, conv-1) were evicted.
        assert set(chat_module._conversations) == {"conv-2", "conv-3", "conv-4"}


# ---------------------------------------------------------------------------
# S10 — LogQL escaping
# ---------------------------------------------------------------------------

class TestLogqlEscape:
    def test_strips_selector_breakout_characters(self):
        from src.telemetry.collector import logql_escape

        assert logql_escape('nextcloud"} |= "x') == "nextcloud  x"
        assert logql_escape("svc{label=~'.*'}") == "svclabel."
        assert logql_escape("back\\slash") == "backslash"
        # The dangerous breakout characters are always gone.
        for ch in '"{}|=~\\*$':
            assert ch not in logql_escape(f"abc{ch}def")

    def test_preserves_normal_service_names(self):
        from src.telemetry.collector import logql_escape

        for name in ("nextcloud", "aiops-backend", "otel-collector", "ns/svc_1", "node:9100"):
            assert logql_escape(name) == name

    def test_handles_empty_and_none(self):
        from src.telemetry.collector import logql_escape

        assert logql_escape("") == ""
        assert logql_escape(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# F2 — _extract_actions section-bullet collection
# ---------------------------------------------------------------------------

class TestExtractActions:
    def test_collects_keywordless_bullets_under_recommendations_header(self):
        from src.api.routes.chat import _extract_actions

        content = (
            "The database is saturated.\n"
            "\n"
            "**Recommendations:**\n"
            "- Restart the nextcloud container\n"
            "- Increase the DB connection pool to 50\n"
            "\n"
            "Let me know if the errors persist."
        )
        actions = _extract_actions(content)
        assert actions is not None
        assert "Restart the nextcloud container" in actions
        assert "Increase the DB connection pool to 50" in actions
        # The header itself and trailing prose are not actions.
        assert all("recommendation" not in a.lower() for a in actions)
        assert all("errors persist" not in a for a in actions)

    def test_keyword_lines_still_collected(self):
        from src.api.routes.chat import _extract_actions

        content = "You should restart the loki container to clear the WAL."
        actions = _extract_actions(content)
        assert actions == ["You should restart the loki container to clear the WAL."]

    def test_bare_header_yields_nothing(self):
        from src.api.routes.chat import _extract_actions

        assert _extract_actions("**Recommendations:**") is None

    def test_no_duplicates(self):
        from src.api.routes.chat import _extract_actions

        content = (
            "Recommendations:\n"
            "- You should restart the nextcloud container\n"
            "- You should restart the nextcloud container\n"
        )
        actions = _extract_actions(content)
        assert actions == ["You should restart the nextcloud container"]
