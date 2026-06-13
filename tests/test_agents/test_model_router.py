"""
Tests for ModelRouter - dual-endpoint routing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.model_router import ModelRouter


def _mock_response() -> MagicMock:
    """A sync MagicMock standing in for an httpx.Response (json() returns a dict)."""
    resp = MagicMock()
    resp.json = MagicMock(return_value={"choices": [{"message": {"content": "test"}}]})
    resp.raise_for_status = MagicMock(return_value=None)
    return resp


class TestModelRouter:
    """Test suite for ModelRouter."""

    def test_init_uses_config_urls(self, monkeypatch):
        """ModelRouter falls back to the configured vLLM endpoints (Gate 1: ports 8000/8001)."""
        import src.config as _cfg_module

        monkeypatch.setattr(_cfg_module.config.llm, "fast_agent_url", "http://localhost:8000/v1")
        monkeypatch.setattr(_cfg_module.config.llm, "reasoning_agent_url", "http://localhost:8001/v1")

        router = ModelRouter()
        assert router.fast_agent_url == "http://localhost:8000/v1"
        assert router.reasoning_agent_url == "http://localhost:8001/v1"
        assert "8000" in router.fast_agent_url
        assert "8001" in router.reasoning_agent_url

    def test_init_custom_urls(self):
        """Test ModelRouter accepts custom URLs."""
        router = ModelRouter(
            fast_agent_url="http://custom:9001/v1",
            reasoning_agent_url="http://custom:9002/v1",
        )
        assert router.fast_agent_url == "http://custom:9001/v1"
        assert router.reasoning_agent_url == "http://custom:9002/v1"

    @pytest.mark.asyncio
    async def test_fast_completion_calls_correct_endpoint(self):
        """fast_completion POSTs to chat/completions on the fast client."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("test prompt")

        router._fast_client.post.assert_awaited_once()
        assert "chat/completions" in str(router._fast_client.post.call_args)

    @pytest.mark.asyncio
    async def test_reasoning_completion_calls_correct_endpoint(self):
        """reasoning_completion POSTs to chat/completions on the reasoning client."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("test prompt")

        router._reasoning_client.post.assert_awaited_once()
        assert "chat/completions" in str(router._reasoning_client.post.call_args)

    @pytest.mark.asyncio
    async def test_reasoning_completion_with_thinking_mode(self):
        """enable_thinking=True prepends the /think directive to the user prompt."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("test prompt", enable_thinking=True)

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        user_msg = payload["messages"][-1]["content"]
        assert "/think" in user_msg

    @pytest.mark.asyncio
    async def test_reasoning_completion_suppresses_thinking_on_vllm(self, monkeypatch):
        """D-item1 (T4): the reasoning path mirrors fast_completion and injects
        chat_template_kwargs={"enable_thinking": False} for the colon-free
        production vLLM model, so the 14B does not leak chain-of-thought into
        chat/RCA answers. Default enable_thinking is False."""
        import src.config as _cfg_module

        monkeypatch.setattr(_cfg_module.config.llm, "reasoning_agent_model", "qwen3-14b")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("test prompt")

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert payload.get("chat_template_kwargs") == {"enable_thinking": False}

    @pytest.mark.asyncio
    async def test_reasoning_completion_keeps_thinking_when_requested(self, monkeypatch):
        """When enable_thinking=True the suppression kwarg is NOT injected (the
        caller explicitly opted into extended thinking)."""
        import src.config as _cfg_module

        monkeypatch.setattr(_cfg_module.config.llm, "reasoning_agent_model", "qwen3-14b")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("test prompt", enable_thinking=True)

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert "chat_template_kwargs" not in payload

    @pytest.mark.asyncio
    async def test_reasoning_completion_no_suppression_on_ollama(self, monkeypatch):
        """A colon-bearing (Ollama local-dev) model name handles suppression via
        instruct tuning, so the kwarg is not injected."""
        import src.config as _cfg_module

        monkeypatch.setattr(
            _cfg_module.config.llm, "reasoning_agent_model", "qwen3:14b-instruct"
        )
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("test prompt")

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert "chat_template_kwargs" not in payload

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self):
        """Test health_check returns status for both agents."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )

        with patch.object(router._fast_client, 'get', new_callable=AsyncMock) as mock_fast:
            with patch.object(router._reasoning_client, 'get', new_callable=AsyncMock) as mock_reasoning:
                mock_fast.return_value.status_code = 200
                mock_reasoning.return_value.status_code = 200

                health = await router.health_check()

                assert "fast_agent" in health
                assert "reasoning_agent" in health
