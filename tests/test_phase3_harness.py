"""
Tests for Phase 3 of the Mode 2 plan (harness optimization):

1. ``assemble_mode2_chat_prompt`` — the SYSTEM prompt is byte-stable across
   turns (volatile content moves to the user-message tail), block ordering is
   [history -> volatile -> directive -> query], and the in-scope directive
   is the pre-call replacement for the Mode 1 refusal-guard retry.
2. Runtime-context TTL cache — Mode 1 rebuilds per turn (baseline behavior
   unchanged); Mode 2 reuses within the TTL and rebuilds after expiry.
3. Parallel read-tool execution — Mode 2 runs planned READ tools
   concurrently with a per-tool timeout while preserving the planned order;
   Mode 1 stays strictly sequential.
4. Mode 2 chat route — ONE reasoning call per turn: stable-prefix
   prompt_override goes to ReasoningAgent.process, and a residual refusal
   falls back to deterministic synthesis (never a second model call).

Every Mode 2 behavior here is gated on the serving mode; the Mode 1
assertions pin that the default path is unchanged.
"""

import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.prompt_layout import (
    HISTORY_HEADER,
    STATIC_RUNTIME_NOTE,
    VOLATILE_HEADER,
    assemble_mode2_chat_prompt,
    build_in_scope_directive,
)
from src.agents.reasoning_agent import CHAT_SYSTEM_PROMPT
from src.api.routes import chat as chat_module
from src.api.routes.chat import _execute_chat_tools, chat
from src.api.schemas.chat import ChatRequest


# ---------------------------------------------------------------------------
# Helpers (same idioms as tests/test_api/test_chat_tools_metadata.py)
# ---------------------------------------------------------------------------


def _make_request(**state) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def _mode2_request(**state) -> SimpleNamespace:
    """Request whose app.state carries a Mode 2 router profile."""
    state.setdefault(
        "model_router", SimpleNamespace(profile=SimpleNamespace(mode=2))
    )
    return _make_request(**state)


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


@pytest.fixture(autouse=True)
def _reset_chat_module_state(monkeypatch):
    """Isolate the module-level runtime-context cache + conversation store,
    and make sure the agentic loop / mode env don't leak between tests."""
    chat_module._conversations.clear()
    chat_module._runtime_ctx_cache["value"] = None
    chat_module._runtime_ctx_cache["expires_at"] = 0.0
    monkeypatch.delenv("CHAT_AGENTIC_TOOL_LOOP", raising=False)
    monkeypatch.delenv("AIOPS_MODE", raising=False)
    yield
    chat_module._runtime_ctx_cache["value"] = None
    chat_module._runtime_ctx_cache["expires_at"] = 0.0


# ---------------------------------------------------------------------------
# 1. Stable-prefix prompt assembly
# ---------------------------------------------------------------------------


class TestPromptAssembly:
    def test_system_prompt_is_stable_across_turns(self):
        a = assemble_mode2_chat_prompt(
            base_system=CHAT_SYSTEM_PROMPT,
            message="turn one",
            volatile_blocks=["## Containers\nnextcloud: RUNNING"],
        )
        b = assemble_mode2_chat_prompt(
            base_system=CHAT_SYSTEM_PROMPT,
            message="turn two",
            history=[{"role": "user", "content": "turn one"}],
            volatile_blocks=["## Containers\nnextcloud: EXITED"],
        )
        # The whole point: identical system prompt regardless of live state.
        assert a.system_prompt == b.system_prompt
        assert STATIC_RUNTIME_NOTE in a.system_prompt
        assert "{runtime_context}" not in a.system_prompt
        # Live content never leaks into the system prompt.
        assert "RUNNING" not in a.system_prompt
        assert "EXITED" not in b.system_prompt

    def test_user_prompt_block_ordering(self):
        assembled = assemble_mode2_chat_prompt(
            base_system=CHAT_SYSTEM_PROMPT,
            message="what changed?",
            history=[
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi, how can I help?"},
            ],
            volatile_blocks=["## Telemetry\ncpu 90%", "## Containers\nok"],
            in_scope_directive=build_in_scope_directive("nextcloud"),
        )
        up = assembled.user_prompt
        i_hist = up.index(HISTORY_HEADER)
        i_vol = up.index(VOLATILE_HEADER)
        i_dir = up.index("## IMPORTANT")
        i_query = up.index("User Query: what changed?")
        assert i_hist < i_vol < i_dir < i_query
        # Volatile blocks keep their given precedence order.
        assert up.index("## Telemetry") < up.index("## Containers")
        # History lines rendered role-prefixed, oldest first.
        assert up.index("user: hello") < up.index("assistant: hi, how can I help?")

    def test_empty_history_and_volatile_are_omitted(self):
        assembled = assemble_mode2_chat_prompt(
            base_system=CHAT_SYSTEM_PROMPT,
            message="hi",
            history=[],
            volatile_blocks=["", None] if False else ["", ""],
        )
        assert HISTORY_HEADER not in assembled.user_prompt
        assert VOLATILE_HEADER not in assembled.user_prompt
        assert assembled.user_prompt == "User Query: hi"

    def test_directive_wording(self):
        assert "'nextcloud'" in build_in_scope_directive("nextcloud")
        assert "'this system'" in build_in_scope_directive(None)
        assert "Do NOT decline" in build_in_scope_directive("loki")


# ---------------------------------------------------------------------------
# 2. Runtime-context TTL cache
# ---------------------------------------------------------------------------


class TestRuntimeContextCache:
    @pytest.mark.asyncio
    async def test_mode1_rebuilds_every_call(self):
        request = _make_request()
        build = AsyncMock(side_effect=["ctx-1", "ctx-2"])
        with patch.object(chat_module, "_build_runtime_context", new=build):
            first = await chat_module._cached_runtime_context(request)
            second = await chat_module._cached_runtime_context(request)
        assert (first, second) == ("ctx-1", "ctx-2")
        assert build.await_count == 2

    @pytest.mark.asyncio
    async def test_mode2_reuses_within_ttl(self):
        request = _mode2_request()
        build = AsyncMock(side_effect=["ctx-1", "ctx-2"])
        with patch.object(chat_module, "_build_runtime_context", new=build):
            first = await chat_module._cached_runtime_context(request)
            second = await chat_module._cached_runtime_context(request)
        assert (first, second) == ("ctx-1", "ctx-1")
        assert build.await_count == 1

    @pytest.mark.asyncio
    async def test_mode2_rebuilds_after_expiry(self):
        request = _mode2_request()
        build = AsyncMock(side_effect=["ctx-1", "ctx-2"])
        with patch.object(chat_module, "_build_runtime_context", new=build):
            first = await chat_module._cached_runtime_context(request)
            chat_module._runtime_ctx_cache["expires_at"] = 0.0  # force expiry
            second = await chat_module._cached_runtime_context(request)
        assert (first, second) == ("ctx-1", "ctx-2")
        assert build.await_count == 2


# ---------------------------------------------------------------------------
# 3. Parallel read-tool execution
# ---------------------------------------------------------------------------

# Names a service + hits similar/dependency/log keywords => three READ tools.
_MULTI_TOOL_MESSAGE = (
    "show similar past incidents and dependencies and error logs for nextcloud"
)


def _concurrency_probe(state: dict):
    async def fake_exec(req, tool_name, parameters, context=None):
        state["active"] += 1
        state["max_active"] = max(state["max_active"], state["active"])
        await asyncio.sleep(0.05)
        state["active"] -= 1
        return {"success": True, "data": {"service": "nextcloud"}}

    return fake_exec


class TestParallelTools:
    @pytest.mark.asyncio
    async def test_mode2_runs_read_tools_concurrently_in_planned_order(self):
        from src.agents.tool_calling import plan_forced_tool_calls

        planned_names = [
            spec.name
            for spec, _ in plan_forced_tool_calls(_MULTI_TOOL_MESSAGE, "nextcloud")
        ]
        assert len(planned_names) >= 2  # sanity: this message plans several tools

        state = {"active": 0, "max_active": 0}
        request = _mode2_request()
        with patch.object(chat_module, "execute_tool_call", new=_concurrency_probe(state)):
            result = await _execute_chat_tools(
                request,
                MagicMock(),
                message=_MULTI_TOOL_MESSAGE,
                conversation_history=[],
                service="nextcloud",
                runtime_context="ctx",
                enable_thinking=False,
            )
        assert state["max_active"] >= 2  # actually overlapped
        assert [rec.name for rec in result.tool_calls] == planned_names
        assert all(rec.status == "ok" for rec in result.tool_calls)

    @pytest.mark.asyncio
    async def test_mode1_stays_sequential(self):
        state = {"active": 0, "max_active": 0}
        request = _make_request()
        with patch.object(chat_module, "execute_tool_call", new=_concurrency_probe(state)):
            result = await _execute_chat_tools(
                request,
                MagicMock(),
                message=_MULTI_TOOL_MESSAGE,
                conversation_history=[],
                service="nextcloud",
                runtime_context="ctx",
                enable_thinking=False,
            )
        assert state["max_active"] == 1
        assert len(result.tool_calls) >= 2

    @pytest.mark.asyncio
    async def test_mode2_tool_timeout_yields_error_record(self, monkeypatch):
        monkeypatch.setattr(chat_module, "_CHAT_TOOL_TIMEOUT_SECONDS", 0.05)

        async def hang(req, tool_name, parameters, context=None):
            await asyncio.sleep(5)
            return {"success": True, "data": {}}

        request = _mode2_request()
        with patch.object(chat_module, "execute_tool_call", new=hang):
            result = await _execute_chat_tools(
                request,
                MagicMock(),
                message=_MULTI_TOOL_MESSAGE,
                conversation_history=[],
                service="nextcloud",
                runtime_context="ctx",
                enable_thinking=False,
            )
        assert result.tool_calls, "planned tools must still produce records"
        for rec in result.tool_calls:
            assert rec.status == "error"
            assert "timed out" in (rec.error or "")


# ---------------------------------------------------------------------------
# 4. Mode 2 chat route: single-call turns + pre-call directive
# ---------------------------------------------------------------------------


def _mode2_reasoning_agent(content: str) -> MagicMock:
    agent = MagicMock()
    agent.get_system_prompt = MagicMock(return_value=CHAT_SYSTEM_PROMPT)
    agent.process = AsyncMock(return_value=_agent_response(content))
    agent.chat = AsyncMock()  # must never be awaited in Mode 2
    return agent


class TestMode2ChatRoute:
    @pytest.mark.asyncio
    async def test_single_call_with_stable_prefix_and_directive(self):
        agent = _mode2_reasoning_agent("Nextcloud is healthy; no recent errors.")
        request = _mode2_request(reasoning_agent=agent)
        chat_request = ChatRequest(message="is nextcloud healthy?")  # in-domain

        with patch.object(
            chat_module,
            "_build_runtime_context",
            new=AsyncMock(return_value="live-ctx-marker"),
        ):
            response = await chat(request, chat_request)

        assert response.message.content == "Nextcloud is healthy; no recent errors."
        # Exactly ONE model call, via process(); the Mode 1 .chat path unused.
        assert agent.process.await_count == 1
        assert agent.chat.await_count == 0

        call_input = agent.process.await_args.args[0]
        user_prompt, system_prompt = call_input["prompt_override"]
        # System prompt is the static head: placeholder swapped, no live data.
        assert STATIC_RUNTIME_NOTE in system_prompt
        assert "live-ctx-marker" not in system_prompt
        # Live data + pre-call directive live in the user-message tail.
        assert "live-ctx-marker" in user_prompt
        assert "IS in scope" in user_prompt
        assert user_prompt.rstrip().endswith("User Query: is nextcloud healthy?")
        # Timings contract still present.
        assert "timings" in response.metadata

    @pytest.mark.asyncio
    async def test_residual_refusal_synthesizes_without_second_call(self):
        refusal = "I can only help with infrastructure operations."
        agent = _mode2_reasoning_agent(refusal)

        collector = MagicMock()
        collector.query_logs = AsyncMock(return_value=[_make_log("boom", "ERROR")])
        collector.query_metrics = AsyncMock(
            return_value=[_make_metric("cpu_usage", 0.5)]
        )
        request = _mode2_request(reasoning_agent=agent, telemetry_collector=collector)
        chat_request = ChatRequest(message="what is happening with nextcloud?")

        with patch.object(
            chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")
        ):
            response = await chat(request, chat_request)

        # Synthesized from gathered data — not the refusal, and NO second call.
        assert "can only help with infrastructure" not in response.message.content.lower()
        assert "nextcloud" in response.message.content.lower()
        assert agent.process.await_count == 1
        assert agent.chat.await_count == 0

    @pytest.mark.asyncio
    async def test_off_domain_refusal_kept_in_mode2(self):
        refusal = "I can only help with infrastructure operations and incident response."
        agent = _mode2_reasoning_agent(refusal)
        request = _mode2_request(reasoning_agent=agent)
        chat_request = ChatRequest(message="What is the capital of France?")

        with patch.object(
            chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")
        ):
            response = await chat(request, chat_request)

        assert response.message.content == refusal
        assert response.confidence is None
        assert agent.process.await_count == 1
        # Off-domain => no in-scope directive in the prompt.
        user_prompt, _ = agent.process.await_args.args[0]["prompt_override"]
        assert "IS in scope" not in user_prompt
