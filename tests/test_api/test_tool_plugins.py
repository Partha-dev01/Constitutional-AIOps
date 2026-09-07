"""Track 3-F Phase 3 — optional tool plugins (discovery + wiring + gate safety).

The plugin surface is DEFAULT-OFF and fail-closed. These tests prove:
  - discovery (src/tools/plugins.py): entry points load to PluginTool descriptors,
    a factory / list / bad entry point are all handled, invalid descriptors skipped
  - wiring (register_plugin_tools): read plugins join the dispatch table, action
    plugins join the action-executor map + route to the gated _handle_action,
    a name that shadows a built-in is refused, an action plugin without an
    executor is skipped
  - the lazy loader only runs when AIOPS_ENABLE_PLUGINS is set, at most once
  - SAFETY: a plugin action tool has no path to execution except the same
    constitutional gate the built-ins use — a non-container plugin action always
    requires human approval, and a destructive plugin verb is Tier-1 blocked by
    the REAL validator.

Per CI constraints these import route modules directly, never src.main.
"""

from unittest.mock import MagicMock

import pytest

from src.tools.plugins import PluginTool, discover_plugins, plugins_enabled
from src.tools.registry import ToolMeta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeEP:
    """A stand-in for an importlib.metadata EntryPoint."""

    def __init__(self, name, loader):
        self.name = name
        self._loader = loader

    def load(self):
        return self._loader()


def _eps_fn(*eps):
    """Build an entry_points_fn returning the given fake entry points."""
    def _fn(group):
        return list(eps)
    return _fn


def _read_meta(name="ext_probe"):
    return ToolMeta(
        name=name, category="query", description="", agent_description="",
        parameters={"type": "object", "properties": {}, "required": []},
    )


def _action_meta(name, action_type, target_kind="container", reversible=True):
    return ToolMeta(
        name=name, category="action", description="", agent_description="",
        parameters={"type": "object", "properties": {}, "required": []},
        requires_approval=True, risk_level="high",
        action_type=action_type, target_kind=target_kind, reversible=reversible,
    )


def _ok_response(data=None):
    from src.api.routes.tools import ToolCallResponse

    return ToolCallResponse(success=True, data=data or {"plugin": True}, execution_time_ms=0.0)


def _report(can_proceed=True, requires_approval=False, authorization="automatic", explanation="ok"):
    report = MagicMock()
    report.can_proceed = can_proceed
    report.requires_approval = requires_approval
    report.authorization_level = MagicMock()
    report.authorization_level.value = authorization
    report.overall_result = MagicMock()
    report.overall_result.value = "passed"
    report.confidence = 0.95
    report.tier1_passed = True
    report.tier2_passed = True
    report.tier3_passed = True
    report.violations = []
    report.warnings = []
    report.explanation = explanation
    return report


@pytest.fixture()
def restore_registries():
    """Snapshot + restore the live registries the plugin loader mutates."""
    from src.api.routes import tools as tools_mod
    from src.tools.registry import TOOLS_BY_NAME

    saved_tools = dict(TOOLS_BY_NAME)
    saved_handlers = dict(tools_mod._TOOL_HANDLERS)
    saved_execs = dict(tools_mod._ACTION_EXECUTORS)
    saved_loaded = tools_mod._PLUGINS_LOADED
    yield
    TOOLS_BY_NAME.clear(); TOOLS_BY_NAME.update(saved_tools)
    tools_mod._TOOL_HANDLERS.clear(); tools_mod._TOOL_HANDLERS.update(saved_handlers)
    tools_mod._ACTION_EXECUTORS.clear(); tools_mod._ACTION_EXECUTORS.update(saved_execs)
    tools_mod._PLUGINS_LOADED = saved_loaded


@pytest.fixture(autouse=True)
def _mock_audit(monkeypatch):
    audit = MagicMock()
    monkeypatch.setattr("src.api.routes.tools.get_audit_logger", lambda: audit)
    return audit


# ---------------------------------------------------------------------------
# Discovery (src/tools/plugins.py)
# ---------------------------------------------------------------------------

class TestPluginDiscovery:
    def test_plugins_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("AIOPS_ENABLE_PLUGINS", raising=False)
        assert plugins_enabled() is False
        monkeypatch.setenv("AIOPS_ENABLE_PLUGINS", "true")
        assert plugins_enabled() is True
        monkeypatch.setenv("AIOPS_ENABLE_PLUGINS", "0")
        assert plugins_enabled() is False

    def test_no_plugins_installed_yields_empty(self):
        # The real importlib path: this repo ships no entry points in the group.
        assert discover_plugins() == []

    def test_entry_point_returning_plugin_tool(self):
        pt = PluginTool(meta=_read_meta(), handler=lambda ctx, p, s: _ok_response())
        found = discover_plugins(entry_points_fn=_eps_fn(_FakeEP("probe", lambda: pt)))
        assert found == [pt]

    def test_entry_point_factory_and_list(self):
        pt1 = PluginTool(meta=_read_meta("a"), handler=lambda ctx, p, s: _ok_response())
        pt2 = PluginTool(meta=_read_meta("b"), handler=lambda ctx, p, s: _ok_response())
        # A factory returning a list is accepted and flattened.
        found = discover_plugins(entry_points_fn=_eps_fn(_FakeEP("multi", lambda: [pt1, pt2])))
        assert found == [pt1, pt2]

    def test_broken_entry_point_is_skipped(self):
        def _boom():
            raise RuntimeError("bad plugin")

        good = PluginTool(meta=_read_meta("good"), handler=lambda ctx, p, s: _ok_response())
        found = discover_plugins(
            entry_points_fn=_eps_fn(_FakeEP("boom", _boom), _FakeEP("good", lambda: good))
        )
        assert found == [good]

    def test_non_plugin_object_is_skipped(self):
        found = discover_plugins(entry_points_fn=_eps_fn(_FakeEP("junk", lambda: {"not": "a tool"})))
        assert found == []

    def test_invalid_descriptor_is_skipped(self):
        # An action descriptor with no executor is not well-formed.
        bad = PluginTool(meta=_action_meta("x", "restart"), executor=None)
        found = discover_plugins(entry_points_fn=_eps_fn(_FakeEP("bad", lambda: bad)))
        assert found == []

    def test_enumeration_error_returns_empty(self):
        def _raises(group):
            raise RuntimeError("enumeration failed")

        assert discover_plugins(entry_points_fn=_raises) == []


# ---------------------------------------------------------------------------
# Registration / wiring
# ---------------------------------------------------------------------------

class TestPluginRegistration:
    def test_read_plugin_joins_dispatch_table(self, monkeypatch, restore_registries):
        from src.api.routes import tools as tools_mod
        from src.tools.registry import TOOLS_BY_NAME

        handler = lambda ctx, p, s: _ok_response()  # noqa: E731
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(meta=_read_meta("ext_probe"), handler=handler)],
        )
        count = tools_mod.register_plugin_tools()
        assert count == 1
        assert "ext_probe" in TOOLS_BY_NAME
        assert tools_mod._TOOL_HANDLERS["ext_probe"] is handler
        assert tools_mod._resolve_handler("ext_probe") is handler

    def test_action_plugin_joins_executor_map_and_routes_to_gate(self, monkeypatch, restore_registries):
        from src.api.routes import tools as tools_mod
        from src.tools.registry import TOOLS_BY_NAME

        executor = lambda p, s: _ok_response()  # noqa: E731
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(
                meta=_action_meta("cloud_snap", "snapshot", target_kind="cloud_resource"),
                executor=executor,
            )],
        )
        tools_mod.register_plugin_tools()
        assert "cloud_snap" in TOOLS_BY_NAME
        assert tools_mod._ACTION_EXECUTORS["cloud_snap"] is executor
        # Action tools are NOT in the read table; they resolve by category.
        assert "cloud_snap" not in tools_mod._TOOL_HANDLERS
        assert tools_mod._resolve_handler("cloud_snap") is tools_mod._handle_action

    def test_plugin_cannot_shadow_builtin(self, monkeypatch, restore_registries):
        from src.api.routes import tools as tools_mod
        from src.tools.registry import TOOLS_BY_NAME

        original = TOOLS_BY_NAME["restart_service"]
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(
                meta=_action_meta("restart_service", "wipe"), executor=lambda p, s: _ok_response(),
            )],
        )
        count = tools_mod.register_plugin_tools()
        assert count == 0
        assert TOOLS_BY_NAME["restart_service"] is original

    def test_action_plugin_without_executor_skipped(self, monkeypatch, restore_registries):
        from src.api.routes import tools as tools_mod
        from src.tools.registry import TOOLS_BY_NAME

        # discover_plugins would normally drop this, but register is defensive too.
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(meta=_action_meta("no_exec", "snapshot"), executor=None)],
        )
        assert tools_mod.register_plugin_tools() == 0
        assert "no_exec" not in TOOLS_BY_NAME

    def test_ensure_loads_once_only_when_enabled(self, monkeypatch, restore_registries):
        from src.api.routes import tools as tools_mod

        calls = {"n": 0}

        def _fake_register():
            calls["n"] += 1
            return 0

        monkeypatch.setattr(tools_mod, "register_plugin_tools", _fake_register)
        monkeypatch.setattr(tools_mod, "_PLUGINS_LOADED", False)

        monkeypatch.delenv("AIOPS_ENABLE_PLUGINS", raising=False)
        tools_mod._ensure_plugins_loaded()
        assert calls["n"] == 0  # disabled: never registers

        monkeypatch.setattr(tools_mod, "_PLUGINS_LOADED", False)
        monkeypatch.setenv("AIOPS_ENABLE_PLUGINS", "true")
        tools_mod._ensure_plugins_loaded()
        tools_mod._ensure_plugins_loaded()
        assert calls["n"] == 1  # enabled: registers exactly once


# ---------------------------------------------------------------------------
# Safety — a plugin action tool cannot bypass the constitutional gate
# ---------------------------------------------------------------------------

class TestPluginSafety:
    def _request(self, validator):
        request = MagicMock()
        request.app.state = MagicMock(spec=["validator"])
        request.app.state.validator = validator
        return request

    @pytest.mark.asyncio
    async def test_noncontainer_plugin_action_forced_to_approval(self, monkeypatch, restore_registries):
        # Even with action tools enabled and an AUTOMATIC validator verdict, a
        # non-container plugin action is downgraded to approval_required and its
        # executor never runs (fail-closed target policy).
        from src.api.routes import tools as tools_mod

        ran = {"n": 0}

        def _executor(p, s):
            ran["n"] += 1
            return _ok_response()

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(
                meta=_action_meta("cloud_snap", "snapshot", target_kind="cloud_resource",
                                  reversible=True),
                executor=_executor,
            )],
        )
        tools_mod.register_plugin_tools()

        validator = MagicMock()
        validator.validate.return_value = _report()  # AUTOMATIC
        resp = await tools_mod.call_tool(
            self._request(validator),
            tools_mod.ToolCallRequest(
                tool_name="cloud_snap", parameters={"reason": "t", "confidence": 0.99},
            ),
        )
        assert resp.success is False
        assert resp.error_code == "approval_required"
        assert ran["n"] == 0

    @pytest.mark.asyncio
    async def test_destructive_plugin_verb_blocked_by_real_validator(self, monkeypatch, restore_registries):
        # A plugin whose verb is destructive is Tier-1 BLOCKED by the REAL
        # validator (P1.1), regardless of confidence or target_kind.
        from src.api.routes import tools as tools_mod
        from src.constitutional.validator import ConstitutionalValidator

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(
                meta=_action_meta("delete_backups", "delete_backups", target_kind="cloud_resource"),
                executor=lambda p, s: _ok_response(),
            )],
        )
        tools_mod.register_plugin_tools()

        resp = await tools_mod.call_tool(
            self._request(ConstitutionalValidator()),
            tools_mod.ToolCallRequest(
                tool_name="delete_backups", parameters={"reason": "t", "confidence": 0.99},
            ),
        )
        assert resp.success is False
        assert resp.error_code == "validation_blocked"
        assert resp.metadata["constitutional"]["principles"]["tier1_safety_passed"] is False

    @pytest.mark.asyncio
    async def test_container_plugin_action_executes_after_gate(self, monkeypatch, restore_registries):
        # A container-kind plugin action completes the loop: it passes the gate
        # (whitelisted container + AUTOMATIC verdict) and its executor runs —
        # proving the plugin execution path works end to end, still gated.
        from src.api.routes import tools as tools_mod

        seen = {}

        async def _executor(p, s):
            seen["params"] = p
            return _ok_response({"cycled": p.get("service_name")})

        monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
        monkeypatch.delenv("AIOPS_ACTION_CONTAINER_WHITELIST", raising=False)
        monkeypatch.setattr(
            "src.tools.plugins.discover_plugins",
            lambda: [PluginTool(
                meta=_action_meta("cycle_service", "restart", target_kind="container"),
                executor=_executor,
            )],
        )
        tools_mod.register_plugin_tools()

        validator = MagicMock()
        validator.validate.return_value = _report()  # AUTOMATIC
        resp = await tools_mod.call_tool(
            self._request(validator),
            tools_mod.ToolCallRequest(
                tool_name="cycle_service",
                parameters={"service_name": "nextcloud", "reason": "t", "confidence": 0.99},
            ),
        )
        assert resp.success is True
        assert resp.data == {"cycled": "nextcloud"}
        assert seen["params"]["service_name"] == "nextcloud"
        assert resp.metadata["constitutional"]["can_proceed"] is True
