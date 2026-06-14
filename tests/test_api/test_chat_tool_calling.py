"""Constitutional AIOps - Agentic chat tool-calling tests.

Pins the PROPER tool-calling behaviour for the chat path:

  * deterministic routing: a NAMED tool ALWAYS runs (the core bug — "use the
    get_dependencies tool" used to only narrate intent), and clearly-IMPLIED
    keyword+service tools run too;
  * missing required params surface as a STRUCTURED ``needs_param`` record, not
    silent prose;
  * the ordered ``metadata.tool_calls`` contract is populated for every run, with
    the exact ``{id,name,arguments,status,result,error,duration_ms}`` shape;
  * results route to the REAL tools.py executors (here mocked at
    ``execute_tool_call``) and carry the live structured JSON;
  * back-compat ``metadata.tools`` (similar/dependencies/logs) still populated;
  * action tools are exposed to the agent only behind AIOPS_ENABLE_ACTION_TOOLS,
    and even then flow through the constitutional gate (never auto-forced);
  * the model-driven agentic loop (app-layer JSON protocol) executes a tool the
    MODEL itself requests and grounds the final answer — no live LLM required.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.tool_calling import (
    detect_named_tools,
    missing_required,
    plan_forced_tool_calls,
    run_tool_calling_loop,
)
from src.api.routes import chat as chat_module
from src.api.routes.chat import chat
from src.api.schemas.chat import ChatRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**state) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def _agent_response(content: str, *, model="qwen3-14b", tokens=42) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.confidence = 0.5
    resp.metadata = {"mode": "chat", "model_used": model, "tokens_used": tokens}
    return resp


_DEPS_RESULT = {
    "success": True,
    "data": {
        "service": "nextcloud",
        "dependencies": {"upstream": ["loki", "prometheus"], "downstream": ["neo4j"]},
        "depth": 2,
    },
}


# ---------------------------------------------------------------------------
# Routing unit tests
# ---------------------------------------------------------------------------

def test_detect_named_tools_matches_underscore_and_spaced() -> None:
    assert detect_named_tools("Use the get_dependencies tool now") == ["get_dependencies"]
    assert detect_named_tools("please get dependencies for x") == ["get_dependencies"]
    assert detect_named_tools("run find_similar and analyze_logs") == ["find_similar", "analyze_logs"]
    assert detect_named_tools("just chat, no tools") == []


def test_named_tool_without_service_is_planned_and_needs_param() -> None:
    """The exact bug: a named tool with no service token MUST still run/route."""
    plan = plan_forced_tool_calls("Use the get_dependencies tool to find all dependencies", None)
    names = [spec.name for spec, _ in plan]
    assert names == ["get_dependencies"]
    spec, args = plan[0]
    # No service was resolvable -> required param missing -> needs_param downstream.
    assert missing_required(spec, args) == ["service_name"]


def test_keyword_routing_requires_service_for_service_tools() -> None:
    # Dependency keyword but no service -> not planned (can't run without service).
    assert plan_forced_tool_calls("show me the dependencies", None) == []
    # With a service it is planned.
    plan = plan_forced_tool_calls("show me the dependencies", "nextcloud")
    assert [s.name for s, _ in plan] == ["get_dependencies"]


def test_list_containers_routes_without_service() -> None:
    plan = plan_forced_tool_calls("list the containers please", None)
    assert [s.name for s, _ in plan] == ["list_containers"]


def test_action_tools_gated_by_env(monkeypatch) -> None:
    monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)
    assert plan_forced_tool_calls("restart_service nextcloud", "nextcloud") == []
    monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
    plan = plan_forced_tool_calls("please restart_service nextcloud", "nextcloud")
    assert [s.name for s, _ in plan] == ["restart_service"]


# ---------------------------------------------------------------------------
# Loop: deterministic routing + needs_param via the real loop function
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_runs_named_tool_and_records_needs_param() -> None:
    """A named tool with a missing param yields a structured needs_param record."""
    async def executor(name, args):
        return _DEPS_RESULT  # would succeed if it had been called with a service

    async def completion(system, messages, tools):
        return {"choices": [{"message": {"content": '{"final_answer": "done"}'}}]}

    result = await run_tool_calling_loop(
        message="Use the get_dependencies tool to find all dependencies",
        system_prompt="SYS {runtime_context}".replace("{runtime_context}", "ctx"),
        conversation_history=[],
        service=None,
        completion=completion,
        executor=executor,
    )
    assert len(result.tool_calls) == 1
    rec = result.tool_calls[0]
    assert rec.name == "get_dependencies"
    assert rec.status == "needs_param"
    assert rec.result == {"status": "needs_param", "missing": ["service_name"]}
    assert result.final_answer == "done"


@pytest.mark.asyncio
async def test_loop_executes_named_tool_with_service() -> None:
    captured = {}

    async def executor(name, args):
        captured["name"] = name
        captured["args"] = args
        return _DEPS_RESULT

    async def completion(system, messages, tools):
        # The model is given the tool result in the transcript; it answers.
        return {"choices": [{"message": {"content": '{"final_answer": "deps found"}'}}]}

    result = await run_tool_calling_loop(
        message="Use the get_dependencies tool",
        system_prompt="ctx",
        conversation_history=[],
        service="nextcloud",
        completion=completion,
        executor=executor,
    )
    assert captured == {"name": "get_dependencies", "args": {"service_name": "nextcloud"}}
    rec = result.tool_calls[0]
    assert rec.status == "ok"
    assert rec.result["data"]["dependencies"]["upstream"] == ["loki", "prometheus"]
    assert isinstance(rec.duration_ms, float)


# ---------------------------------------------------------------------------
# Loop: MODEL-driven tool call (real agentic, app-layer JSON protocol)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_model_requests_tool_then_answers() -> None:
    """The MODEL emits a JSON tool_call; the loop executes it and the model answers."""
    calls = []

    async def executor(name, args):
        calls.append((name, args))
        return {"success": True, "data": {"containers": [{"name": "nextcloud", "status": "running"}], "total": 1}}

    responses = [
        # Step 1: model asks to call list_containers.
        {"choices": [{"message": {"content": '{"tool_call": {"name": "list_containers", "arguments": {}}}'}}]},
        # Step 2: model gives final answer using the result.
        {"choices": [{"message": {"content": '{"final_answer": "1 container running: nextcloud."}'}}]},
    ]

    async def completion(system, messages, tools):
        return responses.pop(0)

    # No deterministic forced calls (message names/implies nothing).
    result = await run_tool_calling_loop(
        message="what is going on",
        system_prompt="ctx",
        conversation_history=[],
        service=None,
        completion=completion,
        executor=executor,
        forced_calls=[],
    )
    assert calls == [("list_containers", {})]
    assert [r.name for r in result.tool_calls] == ["list_containers"]
    assert result.tool_calls[0].status == "ok"
    assert result.final_answer == "1 container running: nextcloud."


@pytest.mark.asyncio
async def test_loop_caps_iterations() -> None:
    """A model that never answers is bounded by max_iterations (+ 1 final ask)."""
    completion_calls = {"n": 0}

    async def executor(name, args):
        return {"success": True, "data": {}}

    async def completion(system, messages, tools):
        completion_calls["n"] += 1
        # Always request another tool — never answers on its own.
        return {"choices": [{"message": {"content": '{"tool_call": {"name": "list_containers", "arguments": {}}}'}}]}

    result = await run_tool_calling_loop(
        message="loop forever",
        system_prompt="ctx",
        conversation_history=[],
        service=None,
        completion=completion,
        executor=executor,
        forced_calls=[],
        max_iterations=2,
    )
    # 2 loop rounds + 1 forced final-answer completion.
    assert completion_calls["n"] == 3
    assert result.iterations == 2
    # The forced tool ran twice (once per round).
    assert len(result.tool_calls) == 2


# ---------------------------------------------------------------------------
# Native vLLM tool-calling path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_native_tool_calls_executed(monkeypatch) -> None:
    monkeypatch.setenv("AIOPS_NATIVE_TOOL_CALLING", "true")
    calls = []

    async def executor(name, args):
        calls.append((name, args))
        return {"success": True, "data": _DEPS_RESULT["data"]}

    responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "tc-1",
                                "function": {
                                    "name": "get_dependencies",
                                    "arguments": '{"service_name": "nextcloud"}',
                                },
                            }
                        ],
                    }
                }
            ]
        },
        {"choices": [{"message": {"content": "Here are the dependencies."}}]},
    ]

    async def completion(system, messages, tools):
        # Native path passes tool defs.
        assert tools is not None
        return responses.pop(0)

    result = await run_tool_calling_loop(
        message="dependencies of nextcloud",
        system_prompt="ctx",
        conversation_history=[],
        service=None,
        completion=completion,
        executor=executor,
        forced_calls=[],
    )
    assert calls == [("get_dependencies", {"service_name": "nextcloud"})]
    assert result.native is True
    assert result.final_answer == "Here are the dependencies."


# ---------------------------------------------------------------------------
# End-to-end chat() route: tool_calls contract + named-tool execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_named_tool_runs_and_populates_tool_calls() -> None:
    """End-to-end: 'use the get_dependencies tool for nextcloud' actually runs it."""
    chat_module._conversations.clear()

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response("Nextcloud depends on loki and neo4j."))
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="Use the get_dependencies tool for nextcloud")

    async def fake_exec(req, tool_name, parameters):
        assert tool_name == "get_dependencies"
        assert parameters == {"service_name": "nextcloud"}
        return _DEPS_RESULT

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=fake_exec):
        response = await chat(request, chat_request)

    tool_calls = response.metadata["tool_calls"]
    assert len(tool_calls) == 1
    tc = tool_calls[0]
    assert tc["name"] == "get_dependencies"
    assert tc["arguments"] == {"service_name": "nextcloud"}
    assert tc["status"] == "ok"
    assert tc["result"]["data"]["dependencies"]["upstream"] == ["loki", "prometheus"]
    assert tc["error"] is None
    assert isinstance(tc["duration_ms"], (int, float))
    assert set(tc.keys()) == {"id", "name", "arguments", "status", "result", "error", "duration_ms"}
    # Back-compat tools object still populated.
    assert response.metadata["tools"]["dependencies"]["upstream"] == ["loki", "prometheus"]


@pytest.mark.asyncio
async def test_chat_named_tool_missing_param_returns_needs_param() -> None:
    """A named tool with no resolvable service -> structured needs_param, no narration."""
    chat_module._conversations.clear()

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(
        return_value=_agent_response("Which service should I analyze dependencies for?")
    )
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    # No known service token in the message.
    chat_request = ChatRequest(message="Use the get_dependencies tool to find all dependencies")

    exec_mock = AsyncMock()  # must NOT be called for a missing-param tool
    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=exec_mock):
        response = await chat(request, chat_request)

    tool_calls = response.metadata["tool_calls"]
    assert len(tool_calls) == 1
    tc = tool_calls[0]
    assert tc["name"] == "get_dependencies"
    assert tc["status"] == "needs_param"
    assert tc["result"] == {"status": "needs_param", "missing": ["service_name"]}
    assert "service_name" in (tc["error"] or "")
    # The real executor was never invoked (no point running with a missing param).
    exec_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_chat_no_tools_yields_empty_tool_calls_list() -> None:
    """A plain chat with no tool route still has a (empty) tool_calls list."""
    chat_module._conversations.clear()

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response("Hello, how can I help?"))
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="hello there")

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")):
        response = await chat(request, chat_request)

    assert response.metadata["tool_calls"] == []


@pytest.mark.asyncio
async def test_chat_action_tool_missing_reason_is_needs_param(monkeypatch) -> None:
    """A destructive action named without its required 'reason' MUST NOT execute.

    It surfaces a structured needs_param record instead — no silent restart.
    """
    chat_module._conversations.clear()
    monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response("Why should I restart it?"))
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="please restart_service nextcloud now")

    exec_mock = AsyncMock()
    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=exec_mock):
        response = await chat(request, chat_request)

    tc = response.metadata["tool_calls"][0]
    assert tc["name"] == "restart_service"
    assert tc["status"] == "needs_param"
    assert "reason" in tc["result"]["missing"]
    # The destructive executor was NEVER reached without a reason.
    exec_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_chat_action_tool_runs_through_gate_via_model_loop(monkeypatch) -> None:
    """With the agentic loop on, a MODEL-supplied action call hits the gated executor."""
    chat_module._conversations.clear()
    monkeypatch.setenv("AIOPS_ENABLE_ACTION_TOOLS", "true")
    monkeypatch.setenv("CHAT_AGENTIC_TOOL_LOOP", "true")

    # Model router emits a JSON tool_call (with a reason) then a final answer.
    responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"tool_call": {"name": "restart_service", "arguments": '
                            '{"service_name": "nextcloud", "reason": "memory leak"}}}'
                        )
                    }
                }
            ]
        },
        {"choices": [{"message": {"content": '{"final_answer": "Restart requested."}'}}]},
    ]

    model_router = MagicMock()
    model_router.reasoning_completion = AsyncMock(side_effect=responses)

    reasoning_agent = MagicMock()
    reasoning_agent.model_router = model_router
    reasoning_agent.chat = AsyncMock(return_value=_agent_response("Restart requested."))
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="restart nextcloud, it is leaking memory")

    captured = {}

    async def fake_exec(req, tool_name, parameters, context=None):
        captured["tool_name"] = tool_name
        captured["context"] = context
        captured["parameters"] = parameters
        return {
            "success": False,
            "data": None,
            "error": "approval required",
            "error_code": "approval_required",
            "metadata": {"constitutional": {"requires_approval": True}},
        }

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=fake_exec):
        response = await chat(request, chat_request)

    # The model-chosen action reached the gated executor with action context.
    assert captured["tool_name"] == "restart_service"
    assert captured["parameters"]["reason"] == "memory leak"
    assert captured["context"]["source"] == "chat_agent"
    names = [tc["name"] for tc in response.metadata["tool_calls"]]
    assert "restart_service" in names
    rec = next(tc for tc in response.metadata["tool_calls"] if tc["name"] == "restart_service")
    # Gate refused automatic execution -> recorded as error, never silently run.
    assert rec["status"] == "error"


@pytest.mark.asyncio
async def test_chat_action_tool_not_exposed_when_disabled(monkeypatch) -> None:
    chat_module._conversations.clear()
    monkeypatch.delenv("AIOPS_ENABLE_ACTION_TOOLS", raising=False)

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response("I can't auto-restart."))
    reasoning_agent.get_system_prompt = MagicMock(return_value="SYS {runtime_context}")

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="please restart_service nextcloud now")

    exec_mock = AsyncMock()
    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=exec_mock):
        response = await chat(request, chat_request)

    # Action tool disabled -> not routed, executor never called for it.
    assert response.metadata["tool_calls"] == []
    exec_mock.assert_not_awaited()
