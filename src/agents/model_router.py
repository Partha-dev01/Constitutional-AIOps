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

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import httpx

import src.config as _cfg_module
from src.agents.serving_profile import ServingProfile, resolve_serving_profile

logger = logging.getLogger(__name__)

# vLLM V1 priority scheduling (Mode 2 plan, Phase 2): lower value = scheduled
# first, so interactive chat preempts RCA, which preempts background
# annotation. The field is injected ONLY when the resolved profile advertises
# priority support (Mode 2) — Mode 1 request payloads stay byte-identical,
# and the payload-equality tests in tests/test_serving_profile.py pin that.
PRIORITY_CHAT = 0
PRIORITY_RCA = 1
PRIORITY_BACKGROUND = 2


def _guided_json_response_format(schema: dict[str, Any]) -> dict[str, Any]:
    """OpenAI-compatible structured-outputs body for vLLM (Phase 5).

    vLLM's ``auto`` structured-outputs backend compiles this with xgrammar;
    kept in one helper so the exact wire format has a single owner (it gets
    validated live against v0.24 in the Phase 5 gate).
    """
    return {
        "type": "json_schema",
        "json_schema": {"name": "aiops_structured_output", "schema": schema},
    }


@dataclass
class LatencyRecord:
    """Record of a single LLM request latency."""
    agent: str  # "fast" or "reasoning"
    latency_ms: float
    timestamp: str
    prompt_hash: int
    tokens_generated: int = 0
    success: bool = True
    # Time-to-first-token for streamed requests (Phase 4); None on the
    # blocking paths, so existing records/exports are unchanged.
    ttft_ms: Optional[float] = None


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
        profile: Optional[ServingProfile] = None,
    ):
        """
        Initialize the model router.

        Args:
            fast_agent_url: URL for fast agent (default from config)
            reasoning_agent_url: URL for reasoning agent (default from config)
            profile: Optional pre-resolved ServingProfile (Mode 2 plan,
                Phase 1). When None (the default) the profile is resolved
                from the environment; in Mode 1 that resolution changes
                NOTHING — URLs and model names keep coming from src.config
                exactly as before (including late-bound model-name reads at
                call time). An explicitly injected profile — or a resolved
                Mode 2 — is authoritative for URLs and model names instead.
        """
        # Serving profile (Mode 2 plan, Phase 1). `_profile_authoritative`
        # gates every profile-driven branch so the default Mode 1 path stays
        # byte-identical to the pre-Mode-2 router.
        self.profile: ServingProfile = profile if profile is not None else resolve_serving_profile()
        self._profile_authoritative: bool = profile is not None or self.profile.mode != 1

        if self._profile_authoritative:
            self.fast_agent_url = fast_agent_url or self.profile.fast_url
            self.reasoning_agent_url = reasoning_agent_url or self.profile.reasoning_url
        else:
            # Mode 1 default: unchanged legacy behavior (config fallback).
            self.fast_agent_url = fast_agent_url or _cfg_module.config.llm.fast_agent_url
            self.reasoning_agent_url = reasoning_agent_url or _cfg_module.config.llm.reasoning_agent_url

        # Create separate HTTP clients for each endpoint. When a BYO endpoint
        # requires auth, FAST_AGENT_API_KEY / REASONING_AGENT_API_KEY (or a shared
        # LLM_API_KEY) become an "Authorization: Bearer <key>" default header on
        # that client, applied to every request (chat/completions, models list,
        # streaming). An empty key sends no header, so an unauthenticated local
        # endpoint behaves exactly as before. Keys come from config (not the
        # serving profile) — consistent with the timeouts read just below.
        self._fast_client = httpx.AsyncClient(
            base_url=self.fast_agent_url,
            timeout=_cfg_module.config.llm.fast_agent_timeout,
            headers=self._auth_headers(_cfg_module.config.llm.fast_agent_api_key),
        )
        self._reasoning_client = httpx.AsyncClient(
            base_url=self.reasoning_agent_url,
            timeout=_cfg_module.config.llm.reasoning_agent_timeout,
            headers=self._auth_headers(_cfg_module.config.llm.reasoning_agent_api_key),
        )

        # Latency tracking for benchmarking
        self._latency_history: list[LatencyRecord] = []
        self._max_history_size = 10000  # Keep last 10K records

        logger.info(f"ModelRouter initialized")
        logger.info(f"  Fast Agent: {self.fast_agent_url}")
        logger.info(f"  Reasoning Agent: {self.reasoning_agent_url}")
        logger.info(f"  Determinism: temperature=0.0, seed=hash(prompt)")
        if self._profile_authoritative:
            # Only logged off the legacy path so Mode 1 startup logs are unchanged.
            logger.info(
                "  Serving profile: mode=%d single_engine=%s fast_model=%s reasoning_model=%s",
                self.profile.mode,
                self.profile.single_engine,
                self.profile.fast_model,
                self.profile.reasoning_model,
            )

    @staticmethod
    def _auth_headers(api_key: str) -> dict[str, str]:
        """Bearer-auth header for a secured BYO endpoint (empty key -> no header)."""
        key = (api_key or "").strip()
        return {"Authorization": f"Bearer {key}"} if key else {}

    def _fast_model_name(self) -> str:
        """Served model name for fast-agent requests.

        Mode 1 default keeps the legacy contract: read src.config at CALL time
        (late binding — tests monkeypatch config.llm after construction).
        Only an authoritative profile (explicitly injected, or resolved
        Mode 2) supplies the name itself.
        """
        if self._profile_authoritative:
            return self.profile.fast_model
        return _cfg_module.config.llm.fast_agent_model

    def _reasoning_model_name(self) -> str:
        """Served model name for reasoning-agent requests (see _fast_model_name)."""
        if self._profile_authoritative:
            return self.profile.reasoning_model
        return _cfg_module.config.llm.reasoning_agent_model

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

                # Audit-log: preserve the original reasoning ALWAYS (Phase 4.0a, 2026-05-12)
                # Ollama 0.23.2 emits chain-of-thought in `reasoning` regardless of
                # enable_thinking=False. We capture it for trace reproducibility / RG3.
                if reasoning:
                    msg["_original_reasoning"] = reasoning

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
        guided_schema: Optional[dict[str, Any]] = None,  # Phase 5: Mode 2 only
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

        model_name = self._fast_model_name()
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,  # For deterministic outputs
            **kwargs,
        }
        # vLLM + Qwen3 has thinking ON by default when --reasoning-parser qwen3 is set.
        # Annotation (4B) must NOT think — Ollama's qwen3:4b-instruct suppresses it via
        # instruct tuning; vLLM AWQ does not. Detect vLLM by model name (no colon).
        if ":" not in model_name:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        # Fast-agent calls are background annotation by default; callers may
        # pass priority=... in kwargs to override (setdefault respects it).
        if self.profile.supports_priority:
            payload.setdefault("priority", PRIORITY_BACKGROUND)
        # Phase 5: schema-constrained decode. Explicit kwarg (never **kwargs)
        # + profile gate => Mode 1 payloads stay byte-identical even when a
        # caller always passes its schema.
        if guided_schema is not None and self.profile.supports_guided_json:
            payload["response_format"] = _guided_json_response_format(guided_schema)

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
        guided_schema: Optional[dict[str, Any]] = None,  # Phase 5: Mode 2 only
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

        model_name = self._reasoning_model_name()
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,  # For deterministic outputs
            **kwargs,
        }
        # vLLM + Qwen3 has thinking ON by default when --reasoning-parser qwen3 is
        # set, so the 14B leaks chain-of-thought into chat/RCA answers (which
        # _fix_thinking_response then promotes into the visible content). Mirror
        # fast_completion: suppress thinking for the production colon-free vLLM
        # model UNLESS this call explicitly asked for extended thinking. Ollama's
        # instruct tuning (colon in the model name) handles suppression itself, so
        # only the no-colon vLLM path needs the kwarg.
        if not enable_thinking and ":" not in model_name:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        # Direct reasoning calls are RCA/planning work: above background
        # annotation, below interactive chat. Caller kwargs win (setdefault).
        if self.profile.supports_priority:
            payload.setdefault("priority", PRIORITY_RCA)
        # Phase 5: schema-constrained decode (see fast_completion).
        if guided_schema is not None and self.profile.supports_guided_json:
            payload["response_format"] = _guided_json_response_format(guided_schema)

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

        model_name = self._reasoning_model_name()
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            # No seed parameter - intentionally non-deterministic
            **kwargs,
        }
        # Same vLLM thinking-suppression contract as reasoning_completion: the
        # colon-free production model leaks CoT unless we disable thinking, and
        # this method has no system prompt so a leak would be entirely raw CoT.
        if not enable_thinking and ":" not in model_name:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        # Interactive chat gets the highest scheduling priority (lowest value).
        if self.profile.supports_priority:
            payload.setdefault("priority", PRIORITY_CHAT)

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

    async def reasoning_completion_stream(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,  # chat semantics: natural, non-deterministic
        enable_thinking: bool = False,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a reasoning-agent completion token by token (Phase 4).

        Async generator yielding event dicts:
          {"type": "delta", "text": str}          — one per content token chunk
          {"type": "done", "content": str,        — full assembled answer
           "reasoning": str,                      — captured CoT (audit; "" when none)
           "usage": dict | None,                  — from stream_options.include_usage
           "ttft_ms": float | None,               — first-token latency
           "latency_ms": float}                   — full-stream latency

        Latency/token accounting lands in the same in-memory history the
        blocking paths use (agent="reasoning"), with ``ttft_ms`` populated, so
        GET /api/v1/metrics stays truthful for streamed traffic. Mirrors
        chat_completion's semantics: no seed, thinking suppressed for the
        colon-free vLLM served names unless explicitly enabled, and (Mode 2)
        interactive-chat priority.
        """
        if enable_thinking:
            prompt = f"/think\n{prompt}"

        prompt_hash = hash(prompt) % (2**32)

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model_name = self._reasoning_model_name()
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
            **kwargs,
        }
        if not enable_thinking and ":" not in model_name:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        if self.profile.supports_priority:
            payload.setdefault("priority", PRIORITY_CHAT)

        start_time = time.perf_counter()
        success = True
        tokens_generated = 0
        ttft_ms: Optional[float] = None
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        usage: Optional[dict[str, Any]] = None

        try:
            async with self._reasoning_client.stream(
                "POST", "chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        logger.debug("Skipping unparseable SSE chunk: %.120s", data)
                        continue
                    if isinstance(chunk.get("usage"), dict):
                        usage = chunk["usage"]
                    for choice in chunk.get("choices", []):
                        delta = choice.get("delta") or {}
                        text = delta.get("content") or ""
                        reasoning = delta.get("reasoning_content") or delta.get("reasoning") or ""
                        if reasoning:
                            reasoning_parts.append(reasoning)
                        if text:
                            if ttft_ms is None:
                                ttft_ms = (time.perf_counter() - start_time) * 1000
                            content_parts.append(text)
                            yield {"type": "delta", "text": text}

            content = "".join(content_parts)
            reasoning_text = "".join(reasoning_parts)
            if not content and reasoning_text:
                # Same promotion contract as _fix_thinking_response: a thinking
                # leak with empty content becomes the visible answer.
                content = reasoning_text
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - start_time) * 1000
                yield {"type": "delta", "text": content}

            if isinstance(usage, dict):
                tokens_generated = usage.get("completion_tokens", 0) or 0

            latency_ms = (time.perf_counter() - start_time) * 1000
            yield {
                "type": "done",
                "content": content,
                "reasoning": reasoning_text,
                "usage": usage,
                "ttft_ms": round(ttft_ms, 2) if ttft_ms is not None else None,
                "latency_ms": round(latency_ms, 2),
            }

        except httpx.HTTPError as e:
            success = False
            logger.error(f"Streaming reasoning request failed: {e}")
            raise

        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._record_latency(
                agent="reasoning",
                latency_ms=latency_ms,
                prompt_hash=prompt_hash,
                tokens_generated=tokens_generated,
                success=success,
                ttft_ms=ttft_ms,
            )

    async def health_check(self) -> dict[str, bool]:
        """
        Check health of both LLM endpoints.

        Returns:
            Dictionary with health status for each agent
        """
        health = {"fast_agent": False, "reasoning_agent": False}

        # base_url ends in /v1/, and httpx appends relative paths, so the
        # relative "models" resolves to {base}/v1/models — the OpenAI-style model
        # list that BOTH vLLM and Ollama return 200 for when ready. (The old
        # "../" root probe only worked for Ollama; vLLM returns 404 at "/".)
        try:
            response = await self._fast_client.get("models")
            health["fast_agent"] = response.status_code == 200
        except httpx.HTTPError:
            pass

        try:
            response = await self._reasoning_client.get("models")
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
        ttft_ms: Optional[float] = None,
    ) -> None:
        """Record a latency measurement."""
        record = LatencyRecord(
            agent=agent,
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow().isoformat(),
            prompt_hash=prompt_hash,
            tokens_generated=tokens_generated,
            success=success,
            ttft_ms=round(ttft_ms, 2) if ttft_ms is not None else None,
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


__all__ = [
    "ModelRouter",
    "ModelManager",
    "LatencyRecord",
    "MetricsSnapshot",
    "PRIORITY_CHAT",
    "PRIORITY_RCA",
    "PRIORITY_BACKGROUND",
]
