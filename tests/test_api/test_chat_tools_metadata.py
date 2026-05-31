"""Constitutional AIOps - Chat tool-metadata / refusal-guard tests.

Covers the backend chat-path bug fixes:
  * B1 - get_dependencies nested-key read (data["dependencies"]["upstream"/...]).
  * B2 - analyze_logs nested-key read (data["summary"], data["top_errors"]).
  * B3 - structured tool results surfaced in ChatResponse.metadata["tools"].
  * C1 - related_incidents sourced from the find_similar tool when it ran.
  * A1 - evidence-based confidence (helper + end-to-end).
  * D1 - deterministic over-refusal guard for in-domain queries.
  * A3/C6 - model_used / tokens_used populated in chat metadata.

The tool-result dicts are mocked with the REAL nested shape that
``tools.py`` produces, so these tests pin the key-reading contract that the
bugs violated.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.routes import chat as chat_module
from src.api.routes.chat import (
    _compute_chat_confidence,
    _invoke_mcp_tools_for_query,
    _looks_like_refusal,
    _related_from_similar,
    chat,
)
from src.api.schemas.chat import ChatRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**state) -> SimpleNamespace:
    """Build a fake FastAPI Request whose app.state only has the given attrs.

    Using SimpleNamespace (not MagicMock) means getattr(state, "x", None)
    returns None for unset attributes, matching production behaviour.
    """
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


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


def _agent_response(content: str, *, model="qwen3-14b", tokens=42) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.confidence = 0.5
    resp.metadata = {"mode": "chat", "model_used": model, "tokens_used": tokens}
    return resp


# Nested-shape tool dicts matching tools.py exactly.
_DEPS_RESULT = {
    "success": True,
    "data": {
        "service": "nextcloud",
        "dependencies": {
            "upstream": ["loki", "prometheus"],
            "downstream": ["neo4j"],
        },
        "depth": 2,
    },
}

_LOGS_RESULT = {
    "success": True,
    "data": {
        "service": "nextcloud",
        "time_range_minutes": 15,
        "summary": {"total_logs": 120, "error_count": 7, "warning_count": 13},
        "top_errors": [
            {"pattern": "Connection refused to db:5432", "count": 5},
            {"pattern": "Timeout waiting for response", "count": 2},
        ],
        "sample_errors": [],
    },
}

_SIMILAR_RESULT = {
    "success": True,
    "data": {
        "similar_incidents": [
            {
                "incident_id": "INC-2025-001",
                "episode_id": "ep-1",
                "title": "Nextcloud DB pool exhaustion",
                "similarity_score": 0.82,
                "root_cause": "pool misconfig",
                "severity": "high",
            }
        ],
        "total_found": 1,
    },
}


# ---------------------------------------------------------------------------
# B1 / B2 - nested key reads in _invoke_mcp_tools_for_query
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_b1_dependencies_nested_key_read() -> None:
    """get_dependencies upstream/downstream are read from data['dependencies']."""
    async def fake_exec(request, tool_name, parameters):
        assert tool_name == "get_dependencies"
        return _DEPS_RESULT

    with patch.object(chat_module, "execute_tool_call", new=fake_exec):
        context, struct = await _invoke_mcp_tools_for_query(
            _make_request(), "show the dependencies of nextcloud", "nextcloud"
        )

    # Real deps must appear in the LLM context string (not "No dependencies").
    assert "loki" in context and "prometheus" in context and "neo4j" in context
    assert "No dependencies found" not in context
    # Structured form for the UI contract.
    assert struct["dependencies"]["upstream"] == ["loki", "prometheus"]
    assert struct["dependencies"]["downstream"] == ["neo4j"]


@pytest.mark.asyncio
async def test_b2_analyze_logs_nested_key_read() -> None:
    """analyze_logs counts come from data['summary'] / data['top_errors']."""
    async def fake_exec(request, tool_name, parameters):
        assert tool_name == "analyze_logs"
        return _LOGS_RESULT

    with patch.object(chat_module, "execute_tool_call", new=fake_exec):
        context, struct = await _invoke_mcp_tools_for_query(
            _make_request(), "analyze the error logs for nextcloud", "nextcloud"
        )

    # Must surface REAL counts, not the old hardcoded "Total logs: 0".
    assert "Total logs: 120" in context
    assert "Error count: 7" in context
    assert "Total logs: 0" not in context
    assert "Connection refused to db:5432" in context
    # Structured form.
    assert struct["logs"]["total_logs"] == 120
    assert struct["logs"]["error_count"] == 7
    assert struct["logs"]["warning_count"] == 13
    assert struct["logs"]["top_errors"][0]["pattern"] == "Connection refused to db:5432"
    assert struct["logs"]["top_errors"][0]["count"] == 5


# ---------------------------------------------------------------------------
# Confidence + refusal helpers (unit)
# ---------------------------------------------------------------------------

def test_compute_confidence_evidence_based() -> None:
    # No evidence -> floor 0.5
    assert _compute_chat_confidence(None, {}) == 0.5
    # Telemetry only -> +0.2
    tele = {"log_count": 5, "error_count": 1, "metrics": [{"name": "cpu", "value": 1.0}]}
    assert _compute_chat_confidence(tele, {}) == pytest.approx(0.7)
    # Telemetry + a tool -> +0.2 +0.15, clamped to 0.85
    tools = {"dependencies": {"upstream": ["loki"], "downstream": []}}
    assert _compute_chat_confidence(tele, tools) == pytest.approx(0.85)
    # Tool only -> +0.15
    assert _compute_chat_confidence(None, tools) == pytest.approx(0.65)


def test_looks_like_refusal() -> None:
    refusal = (
        "I'm the Constitutional AIOps Reasoning Agent and I can only help with "
        "infrastructure operations."
    )
    assert _looks_like_refusal(refusal) is True
    # A long, substantive answer that merely mentions infrastructure is NOT a refusal.
    answer = "Here is the analysis. " * 40 + "infrastructure"
    assert _looks_like_refusal(answer) is False
    assert _looks_like_refusal("") is False
    assert _looks_like_refusal("Nextcloud is healthy with 0 errors.") is False


def test_related_from_similar() -> None:
    assert _related_from_similar({}) is None
    struct = {
        "similar": {
            "count": 1,
            "incidents": [{"id": "INC-1", "summary": "DB pool exhaustion", "score": 0.82}],
        }
    }
    related = _related_from_similar(struct)
    assert related == ["DB pool exhaustion (similarity: 0.82)"]


# ---------------------------------------------------------------------------
# End-to-end chat() route behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_metadata_tools_populated_when_tools_return_data() -> None:
    """B3/C1/A3: metadata.tools is populated and related_incidents come from find_similar."""
    chat_module._conversations.clear()

    # Telemetry collector returns real logs + metrics for nextcloud.
    collector = MagicMock()
    collector.query_logs = AsyncMock(return_value=[
        _make_log("Connection refused", "ERROR"),
        _make_log("Health ok", "INFO"),
    ])
    collector.query_metrics = AsyncMock(return_value=[_make_metric("cpu_usage", 0.9)])

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(
        return_value=_agent_response("Nextcloud shows recent errors; here is the analysis.")
    )

    request = _make_request(
        reasoning_agent=reasoning_agent,
        telemetry_collector=collector,
    )

    # The query triggers similar + dependencies + logs tools and names a service.
    chat_request = ChatRequest(
        message="show similar past incidents and dependencies and error logs for nextcloud",
    )

    async def fake_exec(req, tool_name, parameters):
        return {
            "find_similar": _SIMILAR_RESULT,
            "get_dependencies": _DEPS_RESULT,
            "analyze_logs": _LOGS_RESULT,
        }[tool_name]

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")), \
         patch.object(chat_module, "execute_tool_call", new=fake_exec):
        response = await chat(request, chat_request)

    tools = response.metadata["tools"]
    # telemetry tool
    assert tools["telemetry"]["service"] == "nextcloud"
    assert tools["telemetry"]["log_count"] == 2
    assert tools["telemetry"]["error_count"] == 1
    assert tools["telemetry"]["metrics"] == [{"name": "cpu_usage", "value": 0.9}]
    assert len(tools["telemetry"]["sample_logs"]) >= 1
    # similar tool
    assert tools["similar"]["count"] == 1
    assert tools["similar"]["incidents"][0]["id"] == "INC-2025-001"
    assert tools["similar"]["incidents"][0]["score"] == pytest.approx(0.82)
    # dependencies tool
    assert tools["dependencies"]["upstream"] == ["loki", "prometheus"]
    assert tools["dependencies"]["downstream"] == ["neo4j"]
    # logs tool
    assert tools["logs"]["total_logs"] == 120
    assert tools["logs"]["error_count"] == 7

    # A3/C6: model + tokens present.
    assert response.metadata["model_used"] == "qwen3-14b"
    assert response.metadata["tokens_used"] == 42

    # C1: related_incidents come from the find_similar tool, not the fallback store.
    assert response.related_incidents == ["Nextcloud DB pool exhaustion (similarity: 0.82)"]

    # A1: evidence-based confidence (telemetry + tools) -> 0.85.
    assert response.confidence == pytest.approx(0.85)


@pytest.mark.asyncio
async def test_chat_in_domain_query_does_not_return_canned_refusal() -> None:
    """D1: an in-domain query that the model refuses is re-issued; the refusal is dropped."""
    chat_module._conversations.clear()

    refusal_text = (
        "I'm the Constitutional AIOps Reasoning Agent and I can only help with "
        "infrastructure operations, observability, and incident response."
    )
    good_text = "Nextcloud is currently healthy; recent logs show no errors."

    reasoning_agent = MagicMock()
    # First call refuses, retry (with forceful directive) answers properly.
    reasoning_agent.chat = AsyncMock(side_effect=[
        _agent_response(refusal_text),
        _agent_response(good_text),
    ])

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="is nextcloud healthy?")  # names a known service

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")):
        response = await chat(request, chat_request)

    # The canned refusal must NOT be what the user sees.
    assert response.message.content == good_text
    assert "can only help with infrastructure" not in response.message.content.lower()
    # chat() must have re-issued exactly once.
    assert reasoning_agent.chat.await_count == 2
    # Confidence is a real (non-None) evidence-based float because service is in-domain.
    assert response.confidence >= 0.5


@pytest.mark.asyncio
async def test_chat_in_domain_persistent_refusal_synthesizes_answer() -> None:
    """D1: if the model refuses even after re-issue, synthesize from gathered data."""
    chat_module._conversations.clear()

    refusal_text = "I can only help with infrastructure operations."

    collector = MagicMock()
    collector.query_logs = AsyncMock(return_value=[_make_log("boom", "ERROR")])
    collector.query_metrics = AsyncMock(return_value=[_make_metric("cpu_usage", 0.5)])

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response(refusal_text))

    request = _make_request(reasoning_agent=reasoning_agent, telemetry_collector=collector)
    chat_request = ChatRequest(message="what is happening with nextcloud?")

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")):
        response = await chat(request, chat_request)

    # Persistent refusal -> synthesized answer drawn from telemetry, not the refusal.
    assert "can only help with infrastructure" not in response.message.content.lower()
    assert "nextcloud" in response.message.content.lower()
    assert reasoning_agent.chat.await_count == 2  # original + one re-issue


@pytest.mark.asyncio
async def test_chat_off_domain_refusal_kept_and_confidence_null() -> None:
    """D1/A1: a genuinely off-domain refusal is preserved; confidence is None (gauge hidden)."""
    chat_module._conversations.clear()

    refusal_text = "I can only help with infrastructure operations and incident response."

    reasoning_agent = MagicMock()
    reasoning_agent.chat = AsyncMock(return_value=_agent_response(refusal_text))

    request = _make_request(reasoning_agent=reasoning_agent)
    chat_request = ChatRequest(message="What is the capital of France?")  # no known service

    with patch.object(chat_module, "_build_runtime_context", new=AsyncMock(return_value="ctx")):
        response = await chat(request, chat_request)

    # Off-domain: refusal kept, no re-issue, confidence is None so the UI hides the gauge.
    assert response.message.content == refusal_text
    assert reasoning_agent.chat.await_count == 1
    assert response.confidence is None
    # No tools ran -> no tools key.
    assert "tools" not in response.metadata
