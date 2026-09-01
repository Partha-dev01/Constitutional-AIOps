"""ReasoningAgent.record_activity — the public hook the chat route uses so
tool-loop chat turns (which bypass process()) still show in the Agents feed."""

from unittest.mock import MagicMock

from src.agents.reasoning_agent import ReasoningAgent


def _agent():
    return ReasoningAgent(model_router=MagicMock())


def test_record_activity_appends_entry():
    agent = _agent()
    agent.record_activity("chat", "hello", "world", latency_ms=12.5)
    assert len(agent.activity_log) == 1
    entry = agent.activity_log[0]
    assert entry["type"] == "chat"
    assert entry["input"] == "hello"
    assert entry["output"] == "world"
    assert entry["status"] == "success"
    assert entry["latency_ms"] == 12.5


def test_record_activity_never_raises_on_bad_input():
    agent = _agent()
    # None input/output must not raise (best-effort logging).
    agent.record_activity("chat", None, None)  # type: ignore[arg-type]
    assert len(agent.activity_log) == 1
