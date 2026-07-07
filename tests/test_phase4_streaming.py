"""
Tests for Phase 4 of the Mode 2 plan (streaming, offline part):

1. ``ModelRouter.reasoning_completion_stream`` — SSE parsing, delta events,
   TTFT + token accounting into the latency history, thinking-leak promotion,
   payload shape (stream flags, thinking suppression, Mode 2 priority).
2. ``POST /chat/stream`` — event sequence (meta -> tool_result* -> delta* ->
   done), the done event carrying the full ChatResponse contract persisted
   identically to the blocking endpoint, Mode 1 single-delta fallback, and
   mid-stream failures surfacing as an `error` event.

The live half (SSE through Caddy + real vLLM chunking) is a GPU-session gate.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.model_router import ModelRouter
from src.agents.reasoning_agent import CHAT_SYSTEM_PROMPT
from src.api.routes import chat as chat_module
from src.api.routes.chat import chat_stream
from src.api.schemas.chat import ChatRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(**state) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def _agent_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.confidence = 0.5
    resp.metadata = {"mode": "chat", "model_used": "qwen3-14b", "tokens_used": 42}
    return resp


class _FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeStreamCM:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc):
        return False


def _sse_chunk(**delta) -> str:
    return "data: " + json.dumps({"choices": [{"delta": delta}]})


async def _collect_events(streaming_response) -> list[tuple[str, dict]]:
    """Parse the SSE frames a StreamingResponse yields into (event, data)."""
    raw = ""
    async for chunk in streaming_response.body_iterator:
        raw += chunk
    events: list[tuple[str, dict]] = []
    for frame in raw.split("\n\n"):
        if not frame.strip():
            continue
        name, data = "", {}
        for line in frame.splitlines():
            if line.startswith("event:"):
                name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
        events.append((name, data))
    return events


@pytest.fixture(autouse=True)
def _reset_chat_module_state(monkeypatch):
    chat_module._conversations.clear()
    chat_module._runtime_ctx_cache["value"] = None
    chat_module._runtime_ctx_cache["expires_at"] = 0.0
    monkeypatch.delenv("CHAT_AGENTIC_TOOL_LOOP", raising=False)
    monkeypatch.delenv("AIOPS_MODE", raising=False)
    yield
    chat_module._runtime_ctx_cache["value"] = None
    chat_module._runtime_ctx_cache["expires_at"] = 0.0


_RESOLVER_ENV_VARS = [
    "AIOPS_MODE",
    "FAST_AGENT_URL",
    "REASONING_AGENT_URL",
    "FAST_AGENT_MODEL",
    "REASONING_AGENT_MODEL",
    "MODE2_FAST_AGENT_URL",
    "MODE2_REASONING_AGENT_URL",
    "MODE2_FAST_AGENT_MODEL",
    "MODE2_REASONING_AGENT_MODEL",
]


@pytest.fixture
def clean_env(monkeypatch):
    for var in _RESOLVER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


# ---------------------------------------------------------------------------
# 1. ModelRouter.reasoning_completion_stream
# ---------------------------------------------------------------------------


class TestRouterStreaming:
    @pytest.mark.asyncio
    async def test_stream_yields_deltas_then_done_and_records_metrics(self, clean_env):
        router = ModelRouter()
        lines = [
            _sse_chunk(content="Hello"),
            "",  # keep-alive blank line
            _sse_chunk(content=" world"),
            "data: "
            + json.dumps(
                {"choices": [], "usage": {"completion_tokens": 2, "prompt_tokens": 10}}
            ),
            "data: [DONE]",
        ]
        router._reasoning_client.stream = MagicMock(
            return_value=_FakeStreamCM(_FakeStreamResponse(lines))
        )

        events = [e async for e in router.reasoning_completion_stream("hi")]

        deltas = [e for e in events if e["type"] == "delta"]
        assert [d["text"] for d in deltas] == ["Hello", " world"]
        done = events[-1]
        assert done["type"] == "done"
        assert done["content"] == "Hello world"
        assert done["usage"]["completion_tokens"] == 2
        assert done["ttft_ms"] is not None
        assert done["latency_ms"] >= 0

        # Metrics stay truthful: one reasoning record with TTFT + tokens.
        record = router._latency_history[-1]
        assert record.agent == "reasoning"
        assert record.tokens_generated == 2
        assert record.ttft_ms is not None
        assert record.success is True

    @pytest.mark.asyncio
    async def test_stream_payload_shape(self, clean_env):
        import src.config as _cfg_module

        # Pin the production-style colon-free served name (the local dev
        # default is Ollama's "qwen3:14b", which correctly skips suppression);
        # the router reads the model name late-bound at call time.
        clean_env.setattr(
            _cfg_module.config.llm, "reasoning_agent_model", "qwen3-14b"
        )
        router = ModelRouter()
        router._reasoning_client.stream = MagicMock(
            return_value=_FakeStreamCM(_FakeStreamResponse(["data: [DONE]"]))
        )

        async for _ in router.reasoning_completion_stream("hi", system_prompt="SYS"):
            pass

        payload = router._reasoning_client.stream.call_args.kwargs["json"]
        assert payload["stream"] is True
        assert payload["stream_options"] == {"include_usage": True}
        assert payload["messages"][0] == {"role": "system", "content": "SYS"}
        # Colon-free Mode 1 default model keeps thinking suppression.
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        # Mode 1: no priority field.
        assert "priority" not in payload

    @pytest.mark.asyncio
    async def test_stream_mode2_priority_chat(self, clean_env):
        from src.agents.serving_profile import ServingProfile

        profile = ServingProfile(
            mode=2,
            single_engine=True,
            supports_streaming=True,
            supports_native_tools=True,
            supports_guided_json=True,
            supports_priority=True,
            fast_model="qwen3-14b",
            reasoning_model="qwen3-14b",
            fast_url="http://llm-mode2:8001/v1",
            reasoning_url="http://llm-mode2:8001/v1",
        )
        router = ModelRouter(profile=profile)
        router._reasoning_client.stream = MagicMock(
            return_value=_FakeStreamCM(_FakeStreamResponse(["data: [DONE]"]))
        )

        async for _ in router.reasoning_completion_stream("hi"):
            pass

        payload = router._reasoning_client.stream.call_args.kwargs["json"]
        assert payload["priority"] == 0  # PRIORITY_CHAT

    @pytest.mark.asyncio
    async def test_thinking_leak_promoted_to_content(self, clean_env):
        router = ModelRouter()
        lines = [
            _sse_chunk(reasoning_content="thinking aloud"),
            "data: [DONE]",
        ]
        router._reasoning_client.stream = MagicMock(
            return_value=_FakeStreamCM(_FakeStreamResponse(lines))
        )

        events = [e async for e in router.reasoning_completion_stream("hi")]

        done = events[-1]
        assert done["content"] == "thinking aloud"
        assert done["reasoning"] == "thinking aloud"
        # The promotion arrives as a (single) delta so clients still render it.
        deltas = [e for e in events if e["type"] == "delta"]
        assert [d["text"] for d in deltas] == ["thinking aloud"]


# ---------------------------------------------------------------------------
# 2. POST /chat/stream endpoint
# ---------------------------------------------------------------------------


def _mode2_router_state(stream_events):
    captured: dict = {}

    async def fake_stream(**kwargs):
        captured.update(kwargs)
        for event in stream_events:
            yield event

    router = SimpleNamespace(
        profile=SimpleNamespace(mode=2),
        reasoning_completion_stream=fake_stream,
        _reasoning_model_name=lambda: "qwen3-14b",
    )
    return router, captured


class TestChatStreamEndpoint:
    @pytest.mark.asyncio
    async def test_mode2_event_sequence_and_done_contract(self):
        agent = MagicMock()
        agent.get_system_prompt = MagicMock(return_value=CHAT_SYSTEM_PROMPT)
        agent.chat = AsyncMock()  # must NOT be used on the streaming path

        model_router, captured = _mode2_router_state(
            [
                {"type": "delta", "text": "Nextcloud "},
                {"type": "delta", "text": "is healthy."},
                {
                    "type": "done",
                    "content": "Nextcloud is healthy.",
                    "reasoning": "",
                    "usage": {"completion_tokens": 5},
                    "ttft_ms": 12.3,
                    "latency_ms": 100.0,
                },
            ]
        )
        request = _make_request(reasoning_agent=agent, model_router=model_router)
        chat_request = ChatRequest(message="is nextcloud healthy?")

        with patch.object(
            chat_module,
            "_build_runtime_context",
            new=AsyncMock(return_value="live-ctx"),
        ):
            streaming_response = await chat_stream(request, chat_request)
            events = await _collect_events(streaming_response)

        names = [name for name, _ in events]
        assert names[0] == "meta"
        assert names[-1] == "done"
        assert names.count("delta") == 2

        meta = events[0][1]
        assert meta["streaming"] is True and meta["mode"] == 2

        done = events[-1][1]
        assert done["message"]["content"] == "Nextcloud is healthy."
        assert done["metadata"]["timings"]["ttft_ms"] == 12.3
        assert done["metadata"]["tokens_used"] == 5
        assert done["metadata"]["model_used"] == "qwen3-14b"
        assert "tool_calls" in done["metadata"]

        # Stream used the Mode 2 stable-prefix assembly, not the .chat path.
        assert agent.chat.await_count == 0
        assert "live-ctx" in captured["prompt"]
        assert "live-ctx" not in captured["system_prompt"]

        # Persistence identical to the blocking endpoint: assistant message
        # stored on the conversation with the per-turn metadata.
        conv = chat_module._conversations[done["conversation_id"]]
        assert conv.messages[-1].content == "Nextcloud is healthy."
        assert conv.messages[-1].metadata["metadata"]["timings"]["ttft_ms"] == 12.3

    @pytest.mark.asyncio
    async def test_mode1_fallback_single_delta(self):
        agent = MagicMock()
        agent.chat = AsyncMock(return_value=_agent_response("All services are fine."))

        request = _make_request(reasoning_agent=agent)  # no model_router => Mode 1
        chat_request = ChatRequest(message="status of nextcloud?")

        with patch.object(
            chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")
        ):
            streaming_response = await chat_stream(request, chat_request)
            events = await _collect_events(streaming_response)

        names = [name for name, _ in events]
        assert names[0] == "meta"
        assert events[0][1]["streaming"] is False
        assert names.count("delta") == 1
        done = events[-1][1]
        assert done["message"]["content"] == "All services are fine."
        assert done["metadata"]["timings"]["ttft_ms"] is None
        assert agent.chat.await_count == 1

    @pytest.mark.asyncio
    async def test_midstream_failure_emits_error_event(self):
        agent = MagicMock()
        agent.chat = AsyncMock(side_effect=RuntimeError("engine exploded"))

        request = _make_request(reasoning_agent=agent)
        chat_request = ChatRequest(message="status of nextcloud?")

        with patch.object(
            chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")
        ):
            streaming_response = await chat_stream(request, chat_request)
            events = await _collect_events(streaming_response)

        assert events[-1][0] == "error"
        assert "engine exploded" in events[-1][1]["detail"]
