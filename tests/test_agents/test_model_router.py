"""
Tests for ModelRouter - dual-endpoint routing.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.model_router import ModelRouter


class TestModelRouter:
    """Test suite for ModelRouter."""

    def test_init_default_urls(self):
        """Test ModelRouter initializes with default URLs."""
        router = ModelRouter()
        assert "8081" in router.fast_agent_url
        assert "8082" in router.reasoning_agent_url

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
        """Test fast_completion uses port 8081."""
        router = ModelRouter()
        
        with patch.object(router._fast_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "test"}}]
            }
            mock_post.return_value.raise_for_status = lambda: None
            
            await router.fast_completion("test prompt")
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/chat/completions" in str(call_args)

    @pytest.mark.asyncio
    async def test_reasoning_completion_calls_correct_endpoint(self):
        """Test reasoning_completion uses port 8082."""
        router = ModelRouter()
        
        with patch.object(router._reasoning_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "test"}}]
            }
            mock_post.return_value.raise_for_status = lambda: None
            
            await router.reasoning_completion("test prompt")
            
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_reasoning_completion_with_thinking_mode(self):
        """Test reasoning_completion adds /think prefix when enabled."""
        router = ModelRouter()
        
        with patch.object(router._reasoning_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "test"}}]
            }
            mock_post.return_value.raise_for_status = lambda: None
            
            await router.reasoning_completion("test prompt", enable_thinking=True)
            
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert "/think" in payload["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_health_check_returns_status(self):
        """Test health_check returns status for both agents."""
        router = ModelRouter()
        
        with patch.object(router._fast_client, 'get', new_callable=AsyncMock) as mock_fast:
            with patch.object(router._reasoning_client, 'get', new_callable=AsyncMock) as mock_reasoning:
                mock_fast.return_value.status_code = 200
                mock_reasoning.return_value.status_code = 200
                
                health = await router.health_check()
                
                assert "fast_agent" in health
                assert "reasoning_agent" in health
