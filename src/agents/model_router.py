"""
Constitutional AIOps - Model Router

Simple dual-endpoint router for simultaneous model loading architecture.
Both models (Qwen3-4B and Qwen3-14B) are always loaded on separate ports.

NO hot-swap logic needed - direct port-based routing.

Architecture:
- Fast Agent: Qwen3-4B Q4_K_M @ port 8081 (TTL: -1, never unload)
- Reasoning Agent: Qwen3-14B Q4_K_M @ port 8082 (TTL: -1, never unload)

Determinism:
- temperature=0.0 for greedy decoding (reproducible outputs)
- seed=hash(prompt) for deterministic sampling
- Latency tracking for benchmarking
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class LatencyRecord:
    """Record of a single LLM request latency."""
    agent: str  # "fast" or "reasoning"
    latency_ms: float
    timestamp: str
    prompt_hash: int
    tokens_generated: int = 0
    success: bool = True


@dataclass
class MetricsSnapshot:
    """Snapshot of router metrics for export."""
    timestamp: str
    fast_agent: dict
    reasoning_agent: dict
    total_requests: int
    success_rate: float


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

        # Latency tracking for benchmarking
        self._latency_history: list[LatencyRecord] = []
        self._max_history_size = 10000  # Keep last 10K records

        logger.info(f"ModelRouter initialized")
        logger.info(f"  Fast Agent: {self.fast_agent_url}")
        logger.info(f"  Reasoning Agent: {self.reasoning_agent_url}")
        logger.info(f"  Determinism: temperature=0.0, seed=hash(prompt)")
    
    @staticmethod
    def _fix_thinking_response(result: dict[str, Any]) -> dict[str, Any]:
        """
        Fix Qwen3 thinking mode response for OpenAI-compatible endpoint.

        Problem: Ollama's /v1/chat/completions puts Qwen3's thinking output
        in message.reasoning and leaves message.content empty. The native
        /api/chat endpoint handles think:false correctly, but /v1/ does not.

        Fix: When content is empty but reasoning has data, move reasoning
        to content so downstream agents can parse it normally.

        See: https://github.com/ollama/ollama/issues/12917
        """
        try:
            for choice in result.get("choices", []):
                msg = choice.get("message", {})
                content = msg.get("content", "")
                reasoning = msg.get("reasoning", "")

                if not content and reasoning:
                    # Content is empty, reasoning has the actual output
                    # Move reasoning to content for downstream parsing
                    msg["content"] = reasoning
                    msg["_thinking_mode_fixed"] = True
                    logger.debug(
                        "Fixed Qwen3 thinking mode: moved %d chars from reasoning to content",
                        len(reasoning),
                    )
        except (KeyError, TypeError):
            pass  # Malformed response, let downstream handle it

        return result

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
        temperature: float = 0.0,  # Changed from 0.1 for determinism
        seed: Optional[int] = None,  # Fixed seed for reproducibility
        system_prompt: Optional[str] = None,  # System prompt for context
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get completion from fast agent (Qwen3-4B).

        Best for:
        - Telemetry annotation
        - Alert classification
        - Confidence scoring
        - Quick decisions

        Determinism:
        - temperature=0.0 (greedy decoding) ensures same output for same input
        - seed=hash(prompt) ensures reproducible sampling if temperature > 0

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 for determinism)
            seed: Random seed for reproducibility (default: hash of prompt)
            system_prompt: Optional system prompt for context
            **kwargs: Additional parameters for the API

        Returns:
            API response dictionary with added _latency_ms field
        """
        # Generate deterministic seed from prompt hash
        prompt_hash = hash(prompt) % (2**32)
        if seed is None:
            seed = prompt_hash

        # Build messages list with optional system prompt
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.llm.fast_agent_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,  # For deterministic outputs
            **kwargs,
        }

        start_time = time.perf_counter()
        success = True
        tokens_generated = 0

        try:
            response = await self._fast_client.post("chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()

            # Fix Qwen3 thinking mode: content empty, reasoning has data
            result = self._fix_thinking_response(result)

            # Extract token count if available
            if "usage" in result:
                tokens_generated = result["usage"].get("completion_tokens", 0)

            # Add latency to response
            latency_ms = (time.perf_counter() - start_time) * 1000
            result["_latency_ms"] = round(latency_ms, 2)
            result["_seed"] = seed

            return result

        except httpx.HTTPError as e:
            success = False
            logger.error(f"Fast agent request failed: {e}")
            raise

        finally:
            # Record latency regardless of success/failure
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._record_latency(
                agent="fast",
                latency_ms=latency_ms,
                prompt_hash=prompt_hash,
                tokens_generated=tokens_generated,
                success=success,
            )

    async def reasoning_completion(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,  # Changed from 0.3 for determinism
        seed: Optional[int] = None,  # Fixed seed for reproducibility
        enable_thinking: bool = False,
        system_prompt: Optional[str] = None,  # System prompt for context
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get completion from reasoning agent (Qwen3-14B).

        Best for:
        - Root cause analysis
        - Remediation planning
        - Human chat interaction
        - Complex multi-step reasoning

        Determinism:
        - temperature=0.0 (greedy decoding) ensures same output for same input
        - seed=hash(prompt) ensures reproducible sampling if temperature > 0

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 for determinism)
            seed: Random seed for reproducibility (default: hash of prompt)
            enable_thinking: Enable extended thinking mode
            system_prompt: Optional system prompt for context
            **kwargs: Additional parameters for the API

        Returns:
            API response dictionary with added _latency_ms field
        """
        # Optionally enable thinking mode
        if enable_thinking:
            prompt = f"/think\n{prompt}"

        # Generate deterministic seed from prompt hash
        prompt_hash = hash(prompt) % (2**32)
        if seed is None:
            seed = prompt_hash

        # Build messages list with optional system prompt
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.llm.reasoning_agent_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,  # For deterministic outputs
            **kwargs,
        }

        start_time = time.perf_counter()
        success = True
        tokens_generated = 0

        try:
            response = await self._reasoning_client.post("chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()

            # Fix Qwen3 thinking mode: content empty, reasoning has data
            result = self._fix_thinking_response(result)

            # Extract token count if available
            if "usage" in result:
                tokens_generated = result["usage"].get("completion_tokens", 0)

            # Add latency to response
            latency_ms = (time.perf_counter() - start_time) * 1000
            result["_latency_ms"] = round(latency_ms, 2)
            result["_seed"] = seed

            return result

        except httpx.HTTPError as e:
            success = False
            logger.error(f"Reasoning agent request failed: {e}")
            raise

        finally:
            # Record latency regardless of success/failure
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._record_latency(
                agent="reasoning",
                latency_ms=latency_ms,
                prompt_hash=prompt_hash,
                tokens_generated=tokens_generated,
                success=success,
            )
    
    async def chat_completion(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,  # Non-deterministic for natural conversation
        enable_thinking: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get chat completion from reasoning agent (Qwen3-14B).

        Unlike reasoning_completion, this is intentionally NON-deterministic
        for natural, varied conversation. No fixed seed is used.

        Best for:
        - Human chat interaction
        - Conversational responses
        - Natural language Q&A

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.5 for varied but coherent responses)
            enable_thinking: Enable extended thinking mode
            **kwargs: Additional parameters for the API

        Returns:
            API response dictionary with added _latency_ms field
        """
        # Optionally enable thinking mode
        if enable_thinking:
            prompt = f"/think\n{prompt}"

        # NO seed for natural variation in chat
        prompt_hash = hash(prompt) % (2**32)

        payload = {
            "model": config.llm.reasoning_agent_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            # No seed parameter - intentionally non-deterministic
            **kwargs,
        }

        start_time = time.perf_counter()
        success = True
        tokens_generated = 0

        try:
            response = await self._reasoning_client.post("chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()

            # Fix Qwen3 thinking mode: content empty, reasoning has data
            result = self._fix_thinking_response(result)

            # Extract token count if available
            if "usage" in result:
                tokens_generated = result["usage"].get("completion_tokens", 0)

            # Add latency to response
            latency_ms = (time.perf_counter() - start_time) * 1000
            result["_latency_ms"] = round(latency_ms, 2)
            result["_mode"] = "chat"  # Mark as chat mode

            return result

        except httpx.HTTPError as e:
            success = False
            logger.error(f"Chat completion request failed: {e}")
            raise

        finally:
            # Record latency regardless of success/failure
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._record_latency(
                agent="reasoning",
                latency_ms=latency_ms,
                prompt_hash=prompt_hash,
                tokens_generated=tokens_generated,
                success=success,
            )

    async def health_check(self) -> dict[str, bool]:
        """
        Check health of both LLM endpoints.

        Returns:
            Dictionary with health status for each agent
        """
        health = {"fast_agent": False, "reasoning_agent": False}

        try:
            # Ollama doesn't have /health, use root endpoint or /api/tags
            response = await self._fast_client.get("../")
            health["fast_agent"] = response.status_code == 200
        except httpx.HTTPError:
            pass

        try:
            response = await self._reasoning_client.get("../")
            health["reasoning_agent"] = response.status_code == 200
        except httpx.HTTPError:
            pass

        return health

    # =========================================================================
    # Metrics and Latency Tracking
    # =========================================================================

    def _record_latency(
        self,
        agent: str,
        latency_ms: float,
        prompt_hash: int,
        tokens_generated: int = 0,
        success: bool = True,
    ) -> None:
        """Record a latency measurement."""
        record = LatencyRecord(
            agent=agent,
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow().isoformat(),
            prompt_hash=prompt_hash,
            tokens_generated=tokens_generated,
            success=success,
        )
        self._latency_history.append(record)

        # Trim history if it exceeds max size
        if len(self._latency_history) > self._max_history_size:
            self._latency_history = self._latency_history[-self._max_history_size:]

    def get_latency_stats(self, agent: Optional[str] = None) -> dict[str, Any]:
        """
        Get latency statistics for benchmarking.

        Args:
            agent: Optional filter by agent ("fast" or "reasoning")

        Returns:
            Dictionary with latency statistics
        """
        if agent:
            records = [r for r in self._latency_history if r.agent == agent]
        else:
            records = self._latency_history

        if not records:
            return {
                "count": 0,
                "avg_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "p50_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "success_rate": 0,
            }

        latencies = [r.latency_ms for r in records]
        successful = [r for r in records if r.success]
        sorted_latencies = sorted(latencies)

        def percentile(data: list, p: float) -> float:
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            return data[f] + (k - f) * (data[c] - data[f]) if c != f else data[f]

        return {
            "count": len(records),
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "p50_ms": round(percentile(sorted_latencies, 50), 2),
            "p95_ms": round(percentile(sorted_latencies, 95), 2),
            "p99_ms": round(percentile(sorted_latencies, 99), 2),
            "success_rate": round(len(successful) / len(records) * 100, 2),
            "total_tokens": sum(r.tokens_generated for r in records),
        }

    def get_metrics_snapshot(self) -> MetricsSnapshot:
        """
        Get a complete metrics snapshot for export.

        Returns:
            MetricsSnapshot with all current metrics
        """
        fast_stats = self.get_latency_stats("fast")
        reasoning_stats = self.get_latency_stats("reasoning")
        all_records = self._latency_history
        successful = [r for r in all_records if r.success]

        return MetricsSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            fast_agent=fast_stats,
            reasoning_agent=reasoning_stats,
            total_requests=len(all_records),
            success_rate=round(len(successful) / len(all_records) * 100, 2) if all_records else 100.0,
        )

    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format.

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Metrics as string in specified format
        """
        import json

        snapshot = self.get_metrics_snapshot()

        if format == "json":
            return json.dumps({
                "timestamp": snapshot.timestamp,
                "fast_agent": snapshot.fast_agent,
                "reasoning_agent": snapshot.reasoning_agent,
                "total_requests": snapshot.total_requests,
                "success_rate": snapshot.success_rate,
                "determinism": {
                    "temperature": 0.0,
                    "seed_method": "hash(prompt) % 2^32",
                },
            }, indent=2)

        elif format == "csv":
            lines = [
                "metric,fast_agent,reasoning_agent",
                f"count,{snapshot.fast_agent['count']},{snapshot.reasoning_agent['count']}",
                f"avg_ms,{snapshot.fast_agent['avg_ms']},{snapshot.reasoning_agent['avg_ms']}",
                f"min_ms,{snapshot.fast_agent['min_ms']},{snapshot.reasoning_agent['min_ms']}",
                f"max_ms,{snapshot.fast_agent['max_ms']},{snapshot.reasoning_agent['max_ms']}",
                f"p50_ms,{snapshot.fast_agent['p50_ms']},{snapshot.reasoning_agent['p50_ms']}",
                f"p95_ms,{snapshot.fast_agent['p95_ms']},{snapshot.reasoning_agent['p95_ms']}",
                f"p99_ms,{snapshot.fast_agent['p99_ms']},{snapshot.reasoning_agent['p99_ms']}",
                f"success_rate,{snapshot.fast_agent['success_rate']},{snapshot.reasoning_agent['success_rate']}",
            ]
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_latency_history(self, limit: int = 100) -> list[dict]:
        """
        Get recent latency records for detailed analysis.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of latency records as dictionaries
        """
        recent = self._latency_history[-limit:]
        return [
            {
                "agent": r.agent,
                "latency_ms": r.latency_ms,
                "timestamp": r.timestamp,
                "tokens_generated": r.tokens_generated,
                "success": r.success,
            }
            for r in recent
        ]

    def clear_metrics(self) -> None:
        """Clear all latency history."""
        self._latency_history.clear()
        logger.info("Metrics history cleared")


# Backward compatibility alias
ModelManager = ModelRouter


__all__ = ["ModelRouter", "ModelManager", "LatencyRecord", "MetricsSnapshot"]
