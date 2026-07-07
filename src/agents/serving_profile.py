"""
Constitutional AIOps - Serving Profile (Mode 1 / Mode 2 plumbing)

Phase 1 of the Mode 2 plan: a single, canonical description of *which serving
stack the backend is talking to* and *which engine features it may use*.

Modes
-----
- **Mode 1** (default; the frozen research-paper artifact): dual vLLM engines
  (fast agent + reasoning agent on separate ports). Selected whenever
  ``AIOPS_MODE`` is unset, empty, ``"1"``, or unrecognized — so a bare deploy
  is byte-identical to today. All feature flags are ``False``; nothing in the
  request path changes.
- **Mode 2** (``AIOPS_MODE=2``; applied via ``docker/docker-compose.mode2.yml``):
  the modernized serving stack. Feature flags turn ON so later phases
  (streaming, native tool calls, guided JSON, priority scheduling) can gate
  their code paths on this profile instead of sniffing env vars ad hoc.
  Phase 1 itself only *reports* these flags (``GET /api/v1/health/serving``);
  no request-path behavior is wired to them yet.

Design constraints
------------------
- This module is intentionally **pure stdlib** (no ``src.config`` import) so it
  can be imported from ``src/config.py`` and ``src/agents/model_router.py``
  without any circular-import risk.
- ``resolve_serving_profile()`` reads the environment **at call time** (not at
  import time), so tests can monkeypatch env vars and the ``ModelRouter``
  constructor always sees the current environment.
- Mode 2 served-model names must stay **colon-free** (e.g. ``qwen3-14b``):
  ``ModelRouter`` uses the ``":" not in model`` heuristic to decide whether to
  inject ``chat_template_kwargs={"enable_thinking": False}`` for vLLM.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mode 1 fallback defaults.
#
# These MUST stay in lockstep with LLMConfig in src/config.py (same env vars,
# same defaults). They are duplicated here — rather than imported — because
# this module must not import src.config (see "Design constraints" above);
# tests/test_serving_profile.py asserts the two stay equal.
# ---------------------------------------------------------------------------
_MODE1_FAST_URL_DEFAULT = "http://localhost:8000/v1"
_MODE1_REASONING_URL_DEFAULT = "http://localhost:8001/v1"
_MODE1_FAST_MODEL_DEFAULT = "qwen3-4b"
_MODE1_REASONING_MODEL_DEFAULT = "qwen3-14b"


@dataclass(frozen=True)
class ServingProfile:
    """Immutable snapshot of the resolved serving mode + engine capabilities.

    Fields
    ------
    mode:
        Resolved serving mode: ``1`` (frozen Mode 1 dual-engine artifact) or
        ``2`` (modernized stack from the mode2 compose overlay). Anything the
        operator sets that is not exactly ``"2"`` resolves to ``1``.
    single_engine:
        ``True`` when one engine serves BOTH agent roles (fast_url ==
        reasoning_url). In Phase 1's Mode 2 skeleton this is True (llm-mode2
        clones the 14B and serves both roles); in Mode 1 it is always False
        (two dedicated engines). Later phases use this to skip duplicate
        health probes and to know both roles share one scheduler.
    supports_streaming:
        Engine + harness may use SSE token streaming (wired in Phase 4).
        Always False in Mode 1 so the blocking-POST path is untouched.
    supports_native_tools:
        Engine runs with ``--enable-auto-tool-choice --tool-call-parser hermes``
        so the native tool-call path in src/agents/tool_calling.py may be
        enabled (wired in Phase 5). False in Mode 1 (app-layer JSON loop).
    supports_guided_json:
        Engine accepts schema-constrained (xgrammar) structured output for
        annotation/RCA (wired in Phase 5). False in Mode 1.
    supports_priority:
        Engine runs with ``--scheduling-policy priority`` so requests may carry
        a ``priority`` field (chat > RCA > background annotation; wired in
        Phase 2). False in Mode 1 (FCFS per engine).
    fast_model:
        Served model name the fast-agent (annotation/classification) requests
        use. Mode 1: ``FAST_AGENT_MODEL`` (default ``qwen3-4b``). Mode 2:
        ``MODE2_FAST_AGENT_MODEL``, falling back to the Mode 1 value.
    reasoning_model:
        Served model name for reasoning-agent (RCA/chat) requests. Mode 1:
        ``REASONING_AGENT_MODEL`` (default ``qwen3-14b``). Mode 2:
        ``MODE2_REASONING_AGENT_MODEL``, falling back to the Mode 1 value.
    fast_url:
        OpenAI-compatible base URL for fast-agent requests. Mode 1:
        ``FAST_AGENT_URL`` (default ``http://localhost:8000/v1``). Mode 2:
        ``MODE2_FAST_AGENT_URL``, falling back to the Mode 1 value.
    reasoning_url:
        OpenAI-compatible base URL for reasoning-agent requests. Mode 1:
        ``REASONING_AGENT_URL`` (default ``http://localhost:8001/v1``).
        Mode 2: ``MODE2_REASONING_AGENT_URL``, falling back to the Mode 1
        value.
    """

    mode: int
    single_engine: bool
    supports_streaming: bool
    supports_native_tools: bool
    supports_guided_json: bool
    supports_priority: bool
    fast_model: str
    reasoning_model: str
    fast_url: str
    reasoning_url: str


def _env(name: str, fallback: str) -> str:
    """Read an env var, treating unset / empty / whitespace-only as absent."""
    value = (os.getenv(name) or "").strip()
    return value if value else fallback


def resolve_serving_profile() -> ServingProfile:
    """Resolve the :class:`ServingProfile` from the current environment.

    Resolution rules (Phase 1 contract):

    - ``AIOPS_MODE`` defaults to ``"1"``. Unset, empty, or any unrecognized
      value resolves to **Mode 1** with every feature flag ``False`` and the
      existing ``FAST_AGENT_URL`` / ``REASONING_AGENT_URL`` /
      ``FAST_AGENT_MODEL`` / ``REASONING_AGENT_MODEL`` values — i.e. a bare
      deploy behaves exactly as today. (Same default-off convention as
      ``CHAT_AGENTIC_TOOL_LOOP`` in the production compose file.)
    - ``AIOPS_MODE=2`` resolves to **Mode 2**: all feature flags ``True``,
      with ``MODE2_FAST_AGENT_URL`` / ``MODE2_REASONING_AGENT_URL`` /
      ``MODE2_FAST_AGENT_MODEL`` / ``MODE2_REASONING_AGENT_MODEL`` overrides
      falling back to the Mode 1 values when unset/empty, and
      ``single_engine`` derived from ``fast_url == reasoning_url``.

    Reads env at call time; safe to call repeatedly (cheap, no I/O).
    """
    raw_mode = (os.getenv("AIOPS_MODE") or "").strip()

    # Mode 1 base values — same env vars and defaults as LLMConfig.
    fast_url = _env("FAST_AGENT_URL", _MODE1_FAST_URL_DEFAULT)
    reasoning_url = _env("REASONING_AGENT_URL", _MODE1_REASONING_URL_DEFAULT)
    fast_model = _env("FAST_AGENT_MODEL", _MODE1_FAST_MODEL_DEFAULT)
    reasoning_model = _env("REASONING_AGENT_MODEL", _MODE1_REASONING_MODEL_DEFAULT)

    if raw_mode == "2":
        # Mode 2: MODE2_* overrides fall back to the Mode 1 values so the
        # compose overlay only has to set what actually differs.
        fast_url = _env("MODE2_FAST_AGENT_URL", fast_url)
        reasoning_url = _env("MODE2_REASONING_AGENT_URL", reasoning_url)
        fast_model = _env("MODE2_FAST_AGENT_MODEL", fast_model)
        reasoning_model = _env("MODE2_REASONING_AGENT_MODEL", reasoning_model)
        return ServingProfile(
            mode=2,
            single_engine=(fast_url == reasoning_url),
            supports_streaming=True,
            supports_native_tools=True,
            supports_guided_json=True,
            supports_priority=True,
            fast_model=fast_model,
            reasoning_model=reasoning_model,
            fast_url=fast_url,
            reasoning_url=reasoning_url,
        )

    if raw_mode not in ("", "1"):
        # Fail SAFE, loudly: an operator typo must never silently change the
        # serving stack — it lands on the frozen Mode 1 artifact.
        logger.warning(
            "AIOPS_MODE=%r is not a recognized mode (expected '1' or '2'); "
            "falling back to Mode 1.",
            raw_mode,
        )

    return ServingProfile(
        mode=1,
        single_engine=False,
        supports_streaming=False,
        supports_native_tools=False,
        supports_guided_json=False,
        supports_priority=False,
        fast_model=fast_model,
        reasoning_model=reasoning_model,
        fast_url=fast_url,
        reasoning_url=reasoning_url,
    )


__all__ = ["ServingProfile", "resolve_serving_profile"]
