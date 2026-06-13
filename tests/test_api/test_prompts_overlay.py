"""
Session-14 W4 — system-prompt overlay chain.

Pins the behaviour that was broken before W4: a UI prompt edit must reach the
live agent, fail loudly when it can't, persist across restarts, and be rejected
when it drops a required placeholder. No `src.main` import (langgraph-free CI).
"""

import importlib

import pytest
from unittest.mock import MagicMock

from src.agents.fast_annotator import FastAnnotator, FAST_ANNOTATOR_SYSTEM_PROMPT
from src.agents.reasoning_agent import ReasoningAgent, CHAT_SYSTEM_PROMPT


# ── agent overlay methods ────────────────────────────────────────────────────

def test_reasoning_override_applies_and_resets():
    agent = ReasoningAgent()
    assert agent.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT

    new = "Custom chat prompt with {runtime_context} kept."
    agent.set_system_prompt("reasoning_chat", new)
    assert agent.get_system_prompt("chat") == new
    # Other modes are untouched.
    assert agent.get_system_prompt("rca") != new

    agent.reset_prompts("reasoning_chat")
    assert agent.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT


def test_reasoning_chat_override_requires_runtime_context_placeholder():
    agent = ReasoningAgent()
    with pytest.raises(ValueError, match="runtime_context"):
        agent.set_system_prompt("reasoning_chat", "No placeholder here at all.")
    # The rejected edit did not take effect.
    assert agent.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT


def test_reasoning_rejects_unknown_and_empty():
    agent = ReasoningAgent()
    with pytest.raises(ValueError, match="Unknown"):
        agent.set_system_prompt("nope", "x" * 20)
    with pytest.raises(ValueError, match="empty"):
        agent.set_system_prompt("reasoning_rca", "   ")


def test_reasoning_reset_all_clears_every_override():
    agent = ReasoningAgent()
    agent.set_system_prompt("reasoning_rca", "RCA override text long enough.")
    agent.set_system_prompt("reasoning_chat", "Chat {runtime_context} override.")
    agent.reset_prompts()
    assert agent.get_system_prompt("rca") != "RCA override text long enough."
    assert agent.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT


def test_fast_override_applies_and_rejects_unknown():
    agent = FastAnnotator()
    assert agent.get_system_prompt() == FAST_ANNOTATOR_SYSTEM_PROMPT
    agent.set_system_prompt("fast_annotator", "New fast annotation prompt body.")
    assert agent.get_system_prompt() == "New fast annotation prompt body."
    with pytest.raises(ValueError, match="fast_classifier|Unknown"):
        agent.set_system_prompt("fast_classifier", "x" * 20)
    agent.reset_prompts()
    assert agent.get_system_prompt() == FAST_ANNOTATOR_SYSTEM_PROMPT


# ── persistence + startup re-application ─────────────────────────────────────

@pytest.fixture
def prompts_mod(tmp_path, monkeypatch):
    """Reload the prompts module with AIOPS_DATA_DIR pointed at a temp dir."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    import src.api.routes.prompts as mod
    mod = importlib.reload(mod)
    mod._custom_prompts.clear()
    return mod


def _request_with_agents(fast=None, reasoning=None):
    req = MagicMock()
    req.app.state.fast_annotator = fast
    req.app.state.reasoning_agent = reasoning
    return req


def test_persist_and_apply_round_trip(prompts_mod, tmp_path):
    body = "Restored chat prompt with {runtime_context} placeholder."
    prompts_mod._save_persisted({"reasoning_chat": body})
    assert (tmp_path / "prompts.json").exists()
    assert prompts_mod._load_persisted() == {"reasoning_chat": body}

    agent = ReasoningAgent()
    app = MagicMock()
    app.state.reasoning_agent = agent
    app.state.fast_annotator = FastAnnotator()
    applied = prompts_mod.apply_persisted_prompts(app)
    assert applied == ["reasoning_chat"]
    assert agent.get_system_prompt("chat") == body


def test_apply_skips_bad_override(prompts_mod):
    # A persisted chat override missing the placeholder must be skipped, not crash.
    prompts_mod._save_persisted({"reasoning_chat": "missing placeholder"})
    app = MagicMock()
    app.state.reasoning_agent = ReasoningAgent()
    app.state.fast_annotator = FastAnnotator()
    assert prompts_mod.apply_persisted_prompts(app) == []


# ── loud PUT route ───────────────────────────────────────────────────────────

async def test_put_applies_persists_and_returns(prompts_mod, tmp_path):
    reasoning = ReasoningAgent()
    req = _request_with_agents(reasoning=reasoning, fast=FastAnnotator())
    body = prompts_mod.PromptUpdate(
        prompt="Updated chat with {runtime_context} retained for grounding."
    )
    result = await prompts_mod.update_prompt(req, "reasoning_chat", body)
    assert result.prompt == body.prompt
    assert reasoning.get_system_prompt("chat") == body.prompt          # applied
    assert prompts_mod._load_persisted()["reasoning_chat"] == body.prompt  # persisted


async def test_put_bad_placeholder_is_422_and_not_persisted(prompts_mod):
    from fastapi import HTTPException

    reasoning = ReasoningAgent()
    req = _request_with_agents(reasoning=reasoning)
    body = prompts_mod.PromptUpdate(prompt="No placeholder, should be rejected.")
    with pytest.raises(HTTPException) as exc:
        await prompts_mod.update_prompt(req, "reasoning_chat", body)
    assert exc.value.status_code == 422
    assert prompts_mod._load_persisted() == {}            # nothing half-written
    assert reasoning.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT


async def test_put_missing_agent_is_503(prompts_mod):
    from fastapi import HTTPException

    req = _request_with_agents(reasoning=None)  # agent not initialised
    body = prompts_mod.PromptUpdate(prompt="Chat {runtime_context} body here.")
    with pytest.raises(HTTPException) as exc:
        await prompts_mod.update_prompt(req, "reasoning_chat", body)
    assert exc.value.status_code == 503
    assert prompts_mod._load_persisted() == {}


async def test_reset_clears_persisted_file(prompts_mod):
    reasoning = ReasoningAgent()
    req = _request_with_agents(reasoning=reasoning, fast=FastAnnotator())
    await prompts_mod.update_prompt(
        req,
        "reasoning_chat",
        prompts_mod.PromptUpdate(prompt="Chat {runtime_context} override body."),
    )
    assert prompts_mod._load_persisted() != {}
    await prompts_mod.reset_prompts(req)
    assert prompts_mod._load_persisted() == {}
    assert reasoning.get_system_prompt("chat") == CHAT_SYSTEM_PROMPT
