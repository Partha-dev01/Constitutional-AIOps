"""Gate 1: Stack-B vLLM defaults are colon-free + secrets fail-fast in production."""

import pytest

from src.config import LLMConfig, _require_password


def test_default_models_are_colon_free_for_vllm(monkeypatch: pytest.MonkeyPatch) -> None:
    # Exercise the dataclass DEFAULTS (clear any value the loaded .env injected).
    monkeypatch.delenv("FAST_AGENT_MODEL", raising=False)
    monkeypatch.delenv("REASONING_AGENT_MODEL", raising=False)
    llm = LLMConfig()
    # colon-free served-model-name triggers ModelRouter's enable_thinking=false path
    assert llm.fast_agent_model == "qwen3-4b"
    assert llm.reasoning_agent_model == "qwen3-14b"
    assert ":" not in llm.fast_agent_model
    assert ":" not in llm.reasoning_agent_model


def test_default_urls_point_at_vllm_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FAST_AGENT_URL", raising=False)
    monkeypatch.delenv("REASONING_AGENT_URL", raising=False)
    llm = LLMConfig()
    assert llm.fast_agent_url.endswith(":8000/v1")
    assert llm.reasoning_agent_url.endswith(":8001/v1")


def test_require_password_fails_fast_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        _require_password("NEO4J_PASSWORD", "devpassword")


def test_require_password_uses_env_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("NEO4J_PASSWORD", "s3cret")
    assert _require_password("NEO4J_PASSWORD", "devpassword") == "s3cret"


def test_require_password_dev_default_outside_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    assert _require_password("NEO4J_PASSWORD", "devpassword") == "devpassword"
