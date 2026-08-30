"""
Tests for ModelRouter - dual-endpoint routing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.model_router import ModelRouter
from src.config import LLMConfig


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

    @pytest.mark.asyncio
    async def test_health_check_falls_back_to_chat_completions(self):
        """When /models is unavailable (e.g. Bedrock 404s on it), health falls
        back to a minimal chat/completions probe (5c BYO robustness)."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        with patch.object(router._fast_client, "get", new_callable=AsyncMock) as gf, \
             patch.object(router._reasoning_client, "get", new_callable=AsyncMock) as gr, \
             patch.object(router._fast_client, "post", new_callable=AsyncMock) as pf, \
             patch.object(router._reasoning_client, "post", new_callable=AsyncMock) as pr:
            gf.return_value.status_code = 404
            gr.return_value.status_code = 404
            pf.return_value.status_code = 200
            pr.return_value.status_code = 200
            health = await router.health_check()
            assert health["fast_agent"] is True
            assert health["reasoning_agent"] is True

    def test_ensure_trailing_slash(self):
        assert ModelRouter._ensure_trailing_slash("http://h/openai/v1") == "http://h/openai/v1/"
        assert ModelRouter._ensure_trailing_slash("http://h/openai/v1/") == "http://h/openai/v1/"

    def test_client_base_url_is_slash_terminated(self):
        """The HTTP client base_url is normalized even when the configured URL
        omits the trailing slash; the raw configured value is left untouched."""
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        assert str(router._fast_client.base_url).endswith("/")
        assert str(router._reasoning_client.base_url).endswith("/")
        assert router.fast_agent_url == "http://test:8000/v1"


class TestModelRouterBYOAuth:
    """BYO-endpoint bearer auth (5c WS1). Empty key => no header (unchanged)."""

    def test_auth_headers_empty_key_yields_no_header(self):
        assert ModelRouter._auth_headers("") == {}
        assert ModelRouter._auth_headers("   ") == {}
        assert ModelRouter._auth_headers(None) == {}

    def test_auth_headers_with_key_yields_bearer(self):
        assert ModelRouter._auth_headers("sk-abc") == {"Authorization": "Bearer sk-abc"}

    def test_no_api_key_sends_no_authorization_header(self, monkeypatch):
        """Default (empty) keys => neither client carries an Authorization header,
        so an unauthenticated local endpoint is byte-identical to before."""
        import src.config as _cfg_module

        monkeypatch.setattr(_cfg_module.config.llm, "fast_agent_api_key", "")
        monkeypatch.setattr(_cfg_module.config.llm, "reasoning_agent_api_key", "")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        assert "authorization" not in router._fast_client.headers
        assert "authorization" not in router._reasoning_client.headers

    def test_api_key_sets_per_client_bearer_header(self, monkeypatch):
        """A configured key becomes an Authorization: Bearer default header on the
        matching client (applied to every request that client makes)."""
        import src.config as _cfg_module

        monkeypatch.setattr(_cfg_module.config.llm, "fast_agent_api_key", "fast-secret")
        monkeypatch.setattr(
            _cfg_module.config.llm, "reasoning_agent_api_key", "reason-secret"
        )
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        assert router._fast_client.headers["authorization"] == "Bearer fast-secret"
        assert router._reasoning_client.headers["authorization"] == "Bearer reason-secret"


class TestLLMConfigApiKeyResolution:
    """FAST_/REASONING_AGENT_API_KEY with a shared LLM_API_KEY fallback (5c WS1)."""

    def test_absent_env_means_empty(self, monkeypatch):
        for var in ("FAST_AGENT_API_KEY", "REASONING_AGENT_API_KEY", "LLM_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        llm = LLMConfig()
        assert llm.fast_agent_api_key == ""
        assert llm.reasoning_agent_api_key == ""

    def test_shared_llm_api_key_covers_both_agents(self, monkeypatch):
        monkeypatch.delenv("FAST_AGENT_API_KEY", raising=False)
        monkeypatch.delenv("REASONING_AGENT_API_KEY", raising=False)
        monkeypatch.setenv("LLM_API_KEY", "shared-secret")
        llm = LLMConfig()
        assert llm.fast_agent_api_key == "shared-secret"
        assert llm.reasoning_agent_api_key == "shared-secret"

    def test_per_agent_key_overrides_shared(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "shared")
        monkeypatch.setenv("FAST_AGENT_API_KEY", "fast-only")
        monkeypatch.delenv("REASONING_AGENT_API_KEY", raising=False)
        llm = LLMConfig()
        assert llm.fast_agent_api_key == "fast-only"
        assert llm.reasoning_agent_api_key == "shared"
