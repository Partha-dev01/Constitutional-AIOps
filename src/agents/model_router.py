"""
Constitutional AIOps - Model Router

Simple dual-endpoint router for simultaneous model loading architecture.
Both models (Qwen3-4B and Qwen3-14B) are always loaded on separate ports.

NO hot-swap logic needed - direct port-based routing.

Architecture:
- Fast Agent: Qwen3-4B Q4_K_M @ port 8081 (TTL: -1, never unload)
- Reasoning Agent: Qwen3-14B Q4_K_M @ port 8082 (TTL: -1, never unload)
"""

import logging
from typing import Any, Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Routes requests to the appropriate LLM endpoint.
    
    Both models run simultaneously on 24GB VRAM:
    - Fast Agent (4B): High-throughput annotation, classification
    - Reasoning Agent (14B): Complex RCA, remediation planning, chat
    
    No swap latency, no timeout management - just direct routing.
    """
    
    def __init__(
        self,
        fast_agent_url: Optional[str] = None,
        reasoning_agent_url: Optional[str] = None,
    ):
        """
        Initialize the model router.
        
        Args:
            fast_agent_url: URL for fast agent (default from config)
            reasoning_agent_url: URL for reasoning agent (default from config)
        """
        self.fast_agent_url = fast_agent_url or config.llm.fast_agent_url
        self.reasoning_agent_url = reasoning_agent_url or config.llm.reasoning_agent_url
        
        # Create separate HTTP clients for each endpoint
        self._fast_client = httpx.AsyncClient(
            base_url=self.fast_agent_url,
            timeout=config.llm.fast_agent_timeout,
        )
        self._reasoning_client = httpx.AsyncClient(
            base_url=self.reasoning_agent_url,
            timeout=config.llm.reasoning_agent_timeout,
        )
        
        logger.info(f"ModelRouter initialized")
        logger.info(f"  Fast Agent: {self.fast_agent_url}")
        logger.info(f"  Reasoning Agent: {self.reasoning_agent_url}")
    
    async def close(self):
        """Close HTTP clients."""
        await self._fast_client.aclose()
        await self._reasoning_client.aclose()
    
    def get_fast_client(self) -> httpx.AsyncClient:
        """Get HTTP client for fast agent."""
        return self._fast_client
    
    def get_reasoning_client(self) -> httpx.AsyncClient:
        """Get HTTP client for reasoning agent."""
        return self._reasoning_client
    
    async def fast_completion(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.1,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get completion from fast agent (Qwen3-4B).
        
        Best for:
        - Telemetry annotation
        - Alert classification
        - Confidence scoring
        - Quick decisions
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (low for consistency)
            **kwargs: Additional parameters for the API
            
        Returns:
            API response dictionary
        """
        payload = {
            "model": config.llm.fast_agent_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        
        try:
            response = await self._fast_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Fast agent request failed: {e}")
            raise
    
    async def reasoning_completion(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        enable_thinking: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get completion from reasoning agent (Qwen3-14B).
        
        Best for:
        - Root cause analysis
        - Remediation planning
        - Human chat interaction
        - Complex multi-step reasoning
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            enable_thinking: Enable extended thinking mode
            **kwargs: Additional parameters for the API
            
        Returns:
            API response dictionary
        """
        # Optionally enable thinking mode
        if enable_thinking:
            prompt = f"/think\n{prompt}"
        
        payload = {
            "model": config.llm.reasoning_agent_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        
        try:
            response = await self._reasoning_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Reasoning agent request failed: {e}")
            raise
    
    async def health_check(self) -> dict[str, bool]:
        """
        Check health of both LLM endpoints.
        
        Returns:
            Dictionary with health status for each agent
        """
        health = {"fast_agent": False, "reasoning_agent": False}
        
        try:
            response = await self._fast_client.get("/health")
            health["fast_agent"] = response.status_code == 200
        except httpx.HTTPError:
            pass
        
        try:
            response = await self._reasoning_client.get("/health")
            health["reasoning_agent"] = response.status_code == 200
        except httpx.HTTPError:
            pass
        
        return health


# Backward compatibility alias
ModelManager = ModelRouter


__all__ = ["ModelRouter", "ModelManager"]
