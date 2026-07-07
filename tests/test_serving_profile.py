"""
Tests for Phase 1 of the Mode 2 plan (mode plumbing / swap rails):

1. ``resolve_serving_profile()`` resolution matrix (unset / "" / "1" / "2" /
   garbage; MODE2_* overrides and fallbacks; single_engine derivation).
2. **Mode 1 default equivalence** — the primary Phase 1 acceptance criterion:
   a default-constructed ``ModelRouter`` (AIOPS_MODE unset) has today's exact
   URLs, model names, payload shape, and late-binding config reads.
3. ``GET /api/v1/health/serving`` response shape in Mode 1 and Mode 2, with
   probe degradation to nulls (never a 500).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.model_router import ModelRouter
from src.agents.serving_profile import ServingProfile, resolve_serving_profile

# Every env var the resolver reads; cleaned before each test so results are
# hermetic regardless of the developer's shell / .env.
_RESOLVER_ENV_VARS = [
    "AIOPS_MODE",
    "FAST_AGENT_URL",
    "REASONING_AGENT_URL",
    "FAST_AGENT_MODEL",
    "REASONING_AGENT_MODEL",
    "MODE2_FAST_AGENT_URL",
    "MODE2_REASONING_AGENT_URL",
    "MODE2_FAST_AGENT_MODEL",
    "MODE2_REASONING_AGENT_MODEL",
]


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all resolver-relevant env vars; return monkeypatch for setenv."""
    for var in _RESOLVER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def _mock_response() -> MagicMock:
    """Sync MagicMock standing in for an httpx.Response (json() -> dict)."""
    resp = MagicMock()
    resp.json = MagicMock(return_value={"choices": [{"message": {"content": "test"}}]})
    resp.raise_for_status = MagicMock(return_value=None)
    return resp


# =============================================================================
# 1. resolve_serving_profile() matrix
# =============================================================================


class TestResolveServingProfile:
    """Resolution matrix for AIOPS_MODE and the MODE2_* overrides."""

    def _assert_mode1_flags(self, profile: ServingProfile) -> None:
        assert profile.mode == 1
        assert profile.single_engine is False
        assert profile.supports_streaming is False
        assert profile.supports_native_tools is False
        assert profile.supports_guided_json is False
        assert profile.supports_priority is False

    def test_unset_resolves_to_mode1_with_todays_defaults(self, clean_env):
        profile = resolve_serving_profile()
        self._assert_mode1_flags(profile)
        assert profile.fast_url == "http://localhost:8000/v1"
        assert profile.reasoning_url == "http://localhost:8001/v1"
        assert profile.fast_model == "qwen3-4b"
        assert profile.reasoning_model == "qwen3-14b"

    def test_empty_resolves_to_mode1(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "")
        self._assert_mode1_flags(resolve_serving_profile())

    def test_explicit_1_resolves_to_mode1(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "1")
        self._assert_mode1_flags(resolve_serving_profile())

    @pytest.mark.parametrize("garbage", ["0", "3", "two", "mode2", "  ", "1.0", "2x"])
    def test_garbage_resolves_to_mode1(self, clean_env, garbage):
        """Fail safe: an operator typo lands on the frozen Mode 1 artifact."""
        clean_env.setenv("AIOPS_MODE", garbage)
        self._assert_mode1_flags(resolve_serving_profile())

    def test_mode1_defaults_stay_in_lockstep_with_llmconfig(self, clean_env):
        """serving_profile duplicates LLMConfig's env defaults (it must not
        import src.config); this pins the two files together."""
        from src.config import LLMConfig

        cfg = LLMConfig()  # default_factories read the cleaned env
        profile = resolve_serving_profile()
        assert profile.fast_url == cfg.fast_agent_url
        assert profile.reasoning_url == cfg.reasoning_agent_url
        assert profile.fast_model == cfg.fast_agent_model
        assert profile.reasoning_model == cfg.reasoning_agent_model

    def test_mode1_respects_existing_agent_env(self, clean_env):
        clean_env.setenv("FAST_AGENT_URL", "http://envhost:9000/v1")
        clean_env.setenv("REASONING_AGENT_URL", "http://envhost:9001/v1")
        clean_env.setenv("FAST_AGENT_MODEL", "qwen3:4b")
        clean_env.setenv("REASONING_AGENT_MODEL", "qwen3:14b")

        profile = resolve_serving_profile()
        self._assert_mode1_flags(profile)
        assert profile.fast_url == "http://envhost:9000/v1"
        assert profile.reasoning_url == "http://envhost:9001/v1"
        assert profile.fast_model == "qwen3:4b"
        assert profile.reasoning_model == "qwen3:14b"

    def test_mode2_turns_flags_on_and_falls_back_to_mode1_values(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "2")

        profile = resolve_serving_profile()
        assert profile.mode == 2
        assert profile.supports_streaming is True
        assert profile.supports_native_tools is True
        assert profile.supports_guided_json is True
        assert profile.supports_priority is True
        # No MODE2_* overrides => Mode 1 values carry over.
        assert profile.fast_url == "http://localhost:8000/v1"
        assert profile.reasoning_url == "http://localhost:8001/v1"
        assert profile.fast_model == "qwen3-4b"
        assert profile.reasoning_model == "qwen3-14b"
        # Distinct URLs => not single-engine.
        assert profile.single_engine is False

    def test_mode2_overrides_and_single_engine_derivation(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("MODE2_FAST_AGENT_URL", "http://llm-mode2:8001/v1")
        clean_env.setenv("MODE2_REASONING_AGENT_URL", "http://llm-mode2:8001/v1")
        clean_env.setenv("MODE2_FAST_AGENT_MODEL", "qwen3-14b")
        clean_env.setenv("MODE2_REASONING_AGENT_MODEL", "qwen3-14b")

        profile = resolve_serving_profile()
        assert profile.mode == 2
        assert profile.fast_url == "http://llm-mode2:8001/v1"
        assert profile.reasoning_url == "http://llm-mode2:8001/v1"
        assert profile.fast_model == "qwen3-14b"
        assert profile.reasoning_model == "qwen3-14b"
        # fast_url == reasoning_url => single engine.
        assert profile.single_engine is True

    def test_mode2_partial_override_falls_back_per_field(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("REASONING_AGENT_URL", "http://mode1-reasoning:8001/v1")
        clean_env.setenv("MODE2_FAST_AGENT_URL", "http://llm-mode2:8001/v1")

        profile = resolve_serving_profile()
        assert profile.fast_url == "http://llm-mode2:8001/v1"
        assert profile.reasoning_url == "http://mode1-reasoning:8001/v1"
        assert profile.single_engine is False

    def test_mode2_empty_override_falls_back(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("MODE2_FAST_AGENT_URL", "")
        clean_env.setenv("MODE2_FAST_AGENT_MODEL", "   ")

        profile = resolve_serving_profile()
        assert profile.fast_url == "http://localhost:8000/v1"
        assert profile.fast_model == "qwen3-4b"

    def test_mode_value_is_whitespace_tolerant(self, clean_env):
        clean_env.setenv("AIOPS_MODE", " 2 ")
        assert resolve_serving_profile().mode == 2


# =============================================================================
# 2. Mode 1 default equivalence for ModelRouter (primary acceptance criterion)
# =============================================================================


class TestModelRouterMode1Equivalence:
    """With AIOPS_MODE unset, ModelRouter() behaves EXACTLY as today."""

    def test_default_router_uses_config_urls_not_profile(self, clean_env):
        """Mode 1 keeps the legacy fallback chain: explicit arg -> src.config.
        Monkeypatching config.llm (NOT env) must still steer the router,
        proving the profile did not hijack URL resolution."""
        import src.config as _cfg_module

        clean_env.setattr(
            _cfg_module.config.llm, "fast_agent_url", "http://legacy-fast:1234/v1"
        )
        clean_env.setattr(
            _cfg_module.config.llm, "reasoning_agent_url", "http://legacy-reasoning:5678/v1"
        )

        router = ModelRouter()
        assert router.fast_agent_url == "http://legacy-fast:1234/v1"
        assert router.reasoning_agent_url == "http://legacy-reasoning:5678/v1"

    def test_default_router_profile_is_mode1(self, clean_env):
        router = ModelRouter()
        assert router.profile.mode == 1
        assert router.profile.single_engine is False
        assert router.profile.supports_streaming is False
        assert router.profile.supports_native_tools is False
        assert router.profile.supports_guided_json is False
        assert router.profile.supports_priority is False

    def test_explicit_url_args_still_win(self, clean_env):
        router = ModelRouter(
            fast_agent_url="http://custom:9001/v1",
            reasoning_agent_url="http://custom:9002/v1",
        )
        assert router.fast_agent_url == "http://custom:9001/v1"
        assert router.reasoning_agent_url == "http://custom:9002/v1"

    @pytest.mark.asyncio
    async def test_mode1_model_name_is_late_bound_from_config(self, clean_env):
        """Legacy contract: the served model name is read from src.config at
        CALL time, so a config monkeypatch AFTER construction still applies
        (exactly like the pre-existing test_model_router.py suppression tests)."""
        import src.config as _cfg_module

        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        clean_env.setattr(_cfg_module.config.llm, "fast_agent_model", "qwen3:4b-late")
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("test prompt")

        payload = router._fast_client.post.call_args.kwargs["json"]
        assert payload["model"] == "qwen3:4b-late"
        # Colon-bearing (Ollama-style) name => no suppression kwarg, as today.
        assert "chat_template_kwargs" not in payload

    @pytest.mark.asyncio
    async def test_mode1_fast_payload_is_byte_identical_to_legacy(self, clean_env):
        """Full-payload equality with today's exact request shape."""
        import src.config as _cfg_module

        clean_env.setattr(_cfg_module.config.llm, "fast_agent_model", "qwen3-4b")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("hello", max_tokens=64)

        payload = router._fast_client.post.call_args.kwargs["json"]
        assert payload == {
            "model": "qwen3-4b",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 64,
            "temperature": 0.0,
            "seed": hash("hello") % (2**32),
            "chat_template_kwargs": {"enable_thinking": False},
        }

    @pytest.mark.asyncio
    async def test_mode1_reasoning_payload_is_byte_identical_to_legacy(self, clean_env):
        import src.config as _cfg_module

        clean_env.setattr(_cfg_module.config.llm, "reasoning_agent_model", "qwen3-14b")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.reasoning_completion("why did it fail", system_prompt="sys")

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert payload == {
            "model": "qwen3-14b",
            "messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "why did it fail"},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
            "seed": hash("why did it fail") % (2**32),
            "chat_template_kwargs": {"enable_thinking": False},
        }

    @pytest.mark.asyncio
    async def test_mode1_chat_payload_keeps_no_seed(self, clean_env):
        import src.config as _cfg_module

        clean_env.setattr(_cfg_module.config.llm, "reasoning_agent_model", "qwen3-14b")
        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.chat_completion("hi there")

        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert "seed" not in payload  # chat is intentionally non-deterministic
        assert payload["temperature"] == 0.5
        assert payload["model"] == "qwen3-14b"
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}


# =============================================================================
# 2b. Mode 2 / injected-profile behavior of ModelRouter
# =============================================================================


class TestModelRouterMode2:
    """AIOPS_MODE=2 (or an injected profile) makes the profile authoritative."""

    def test_mode2_env_router_uses_profile_urls(self, clean_env):
        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("MODE2_FAST_AGENT_URL", "http://llm-mode2:8001/v1")
        clean_env.setenv("MODE2_REASONING_AGENT_URL", "http://llm-mode2:8001/v1")

        router = ModelRouter()
        assert router.profile.mode == 2
        assert router.profile.single_engine is True
        assert router.fast_agent_url == "http://llm-mode2:8001/v1"
        assert router.reasoning_agent_url == "http://llm-mode2:8001/v1"

    @pytest.mark.asyncio
    async def test_mode2_payload_uses_profile_model_not_config(self, clean_env):
        """In Mode 2 the served model name comes from the profile, even if
        src.config says otherwise — the overlay env is the single source."""
        import src.config as _cfg_module

        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("MODE2_FAST_AGENT_MODEL", "qwen3-14b")
        clean_env.setattr(_cfg_module.config.llm, "fast_agent_model", "stale-config-model")

        router = ModelRouter(
            fast_agent_url="http://test:8000/v1",
            reasoning_agent_url="http://test:8001/v1",
        )
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("annotate this")

        payload = router._fast_client.post.call_args.kwargs["json"]
        assert payload["model"] == "qwen3-14b"
        # Colon-free Mode 2 served name keeps the thinking suppression.
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}

    @pytest.mark.asyncio
    async def test_injected_profile_is_authoritative(self, clean_env):
        profile = ServingProfile(
            mode=2,
            single_engine=True,
            supports_streaming=True,
            supports_native_tools=True,
            supports_guided_json=True,
            supports_priority=True,
            fast_model="injected-model",
            reasoning_model="injected-model",
            fast_url="http://injected:8001/v1",
            reasoning_url="http://injected:8001/v1",
        )

        router = ModelRouter(profile=profile)
        assert router.fast_agent_url == "http://injected:8001/v1"
        assert router.reasoning_agent_url == "http://injected:8001/v1"

        router._reasoning_client.post = AsyncMock(return_value=_mock_response())
        await router.reasoning_completion("test")
        payload = router._reasoning_client.post.call_args.kwargs["json"]
        assert payload["model"] == "injected-model"


# =============================================================================
# 2c. Priority scheduling field (Phase 2)
# =============================================================================


def _priority_profile() -> ServingProfile:
    return ServingProfile(
        mode=2,
        single_engine=True,
        supports_streaming=True,
        supports_native_tools=True,
        supports_guided_json=True,
        supports_priority=True,
        fast_model="qwen3-14b",
        reasoning_model="qwen3-14b",
        fast_url="http://llm-mode2:8001/v1",
        reasoning_url="http://llm-mode2:8001/v1",
    )


class TestModelRouterPriority:
    """`priority` is injected ONLY when profile.supports_priority (Mode 2);
    the byte-identical Mode 1 payload tests above already prove absence in
    Mode 1 — the explicit checks here document the contract."""

    @pytest.mark.asyncio
    async def test_mode2_default_priorities_per_method(self, clean_env):
        from src.agents.model_router import (
            PRIORITY_BACKGROUND,
            PRIORITY_CHAT,
            PRIORITY_RCA,
        )

        router = ModelRouter(profile=_priority_profile())
        router._fast_client.post = AsyncMock(return_value=_mock_response())
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("annotate")
        assert (
            router._fast_client.post.call_args.kwargs["json"]["priority"]
            == PRIORITY_BACKGROUND
        )

        await router.reasoning_completion("rca")
        assert (
            router._reasoning_client.post.call_args.kwargs["json"]["priority"]
            == PRIORITY_RCA
        )

        await router.chat_completion("hi")
        assert (
            router._reasoning_client.post.call_args.kwargs["json"]["priority"]
            == PRIORITY_CHAT
        )

    @pytest.mark.asyncio
    async def test_caller_kwarg_overrides_default_priority(self, clean_env):
        router = ModelRouter(profile=_priority_profile())
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("urgent annotation", priority=0)
        assert router._fast_client.post.call_args.kwargs["json"]["priority"] == 0

    @pytest.mark.asyncio
    async def test_mode1_payloads_have_no_priority_field(self, clean_env):
        router = ModelRouter()
        assert router.profile.supports_priority is False
        router._fast_client.post = AsyncMock(return_value=_mock_response())
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("annotate")
        assert "priority" not in router._fast_client.post.call_args.kwargs["json"]

        await router.reasoning_completion("rca")
        assert "priority" not in router._reasoning_client.post.call_args.kwargs["json"]

        await router.chat_completion("hi")
        assert "priority" not in router._reasoning_client.post.call_args.kwargs["json"]


# =============================================================================
# 3. GET /api/v1/health/serving
# =============================================================================


class TestServingHealthRoute:
    """Route shape + probe degradation (never 500s)."""

    @pytest.mark.asyncio
    async def test_mode1_shape_with_healthy_probes(self, clean_env):
        from src.api.routes.health import serving_health

        mock_router = MagicMock()
        mock_router.profile = resolve_serving_profile()  # Mode 1
        mock_router.health_check = AsyncMock(
            return_value={"fast_agent": True, "reasoning_agent": True}
        )
        mock_request = MagicMock()
        mock_request.app.state.model_router = mock_router

        body = await serving_health(mock_request)

        assert body["mode"] == 1
        assert body["single_engine"] is False
        assert body["features"] == {
            "streaming": False,
            "native_tools": False,
            "guided_json": False,
            "priority": False,
        }
        engine = body["engine"]
        assert engine["fast_url"] == "http://localhost:8000/v1"
        assert engine["reasoning_url"] == "http://localhost:8001/v1"
        assert engine["fast_model"] == "qwen3-4b"
        assert engine["reasoning_model"] == "qwen3-14b"
        assert engine["fast_agent_healthy"] is True
        assert engine["reasoning_agent_healthy"] is True
        assert engine["fast_agent_latency_ms"] is not None
        assert engine["reasoning_agent_latency_ms"] is not None

    @pytest.mark.asyncio
    async def test_unhealthy_engine_reports_false_not_500(self, clean_env):
        from src.api.routes.health import serving_health

        mock_router = MagicMock()
        mock_router.profile = resolve_serving_profile()
        mock_router.health_check = AsyncMock(
            return_value={"fast_agent": False, "reasoning_agent": False}
        )
        mock_request = MagicMock()
        mock_request.app.state.model_router = mock_router

        body = await serving_health(mock_request)

        assert body["engine"]["fast_agent_healthy"] is False
        assert body["engine"]["reasoning_agent_healthy"] is False

    @pytest.mark.asyncio
    async def test_missing_router_degrades_probes_to_null(self, clean_env):
        """No ModelRouter on app.state: mode/features still resolve (fresh env
        read); probe fields are null; no exception."""
        from src.api.routes.health import serving_health

        mock_request = MagicMock()
        mock_request.app.state = SimpleNamespace()  # no model_router attribute

        body = await serving_health(mock_request)

        assert body["mode"] == 1
        assert body["engine"]["fast_agent_healthy"] is None
        assert body["engine"]["reasoning_agent_healthy"] is None
        assert body["engine"]["fast_agent_latency_ms"] is None
        assert body["engine"]["reasoning_agent_latency_ms"] is None

    @pytest.mark.asyncio
    async def test_probe_exception_degrades_to_null(self, clean_env):
        """A raising health_check must degrade the probe fields to null (the
        helper reports an error), never bubble into a 500."""
        from src.api.routes.health import serving_health

        mock_router = MagicMock()
        mock_router.profile = resolve_serving_profile()
        mock_router.health_check = AsyncMock(side_effect=RuntimeError("probe boom"))
        mock_request = MagicMock()
        mock_request.app.state.model_router = mock_router

        body = await serving_health(mock_request)  # must not raise

        assert body["mode"] == 1
        assert body["engine"]["fast_agent_healthy"] is None
        assert body["engine"]["reasoning_agent_healthy"] is None

    @pytest.mark.asyncio
    async def test_mode2_shape(self, clean_env):
        from src.api.routes.health import serving_health

        clean_env.setenv("AIOPS_MODE", "2")
        clean_env.setenv("MODE2_FAST_AGENT_URL", "http://llm-mode2:8001/v1")
        clean_env.setenv("MODE2_REASONING_AGENT_URL", "http://llm-mode2:8001/v1")
        clean_env.setenv("MODE2_FAST_AGENT_MODEL", "qwen3-14b")
        clean_env.setenv("MODE2_REASONING_AGENT_MODEL", "qwen3-14b")

        mock_request = MagicMock()
        mock_request.app.state = SimpleNamespace()  # fresh resolve path

        body = await serving_health(mock_request)

        assert body["mode"] == 2
        assert body["single_engine"] is True
        assert body["features"] == {
            "streaming": True,
            "native_tools": True,
            "guided_json": True,
            "priority": True,
        }
        assert body["engine"]["fast_url"] == "http://llm-mode2:8001/v1"
        assert body["engine"]["reasoning_url"] == "http://llm-mode2:8001/v1"

    @pytest.mark.asyncio
    async def test_live_router_profile_wins_over_env(self, clean_env):
        """The endpoint reports what the app is ACTUALLY serving with (the
        router's startup-resolved profile), not a fresh env read."""
        from src.api.routes.health import serving_health

        startup_profile = resolve_serving_profile()  # Mode 1 snapshot
        clean_env.setenv("AIOPS_MODE", "2")  # env changed after startup

        mock_router = MagicMock()
        mock_router.profile = startup_profile
        mock_router.health_check = AsyncMock(
            return_value={"fast_agent": True, "reasoning_agent": True}
        )
        mock_request = MagicMock()
        mock_request.app.state.model_router = mock_router

        body = await serving_health(mock_request)

        assert body["mode"] == 1  # live profile, not the mutated env


# =============================================================================
# 4. ServingConfig (src/config.py) — additive section
# =============================================================================


class TestServingConfig:
    """ServingConfig mirrors the canonical resolver's mode parse."""

    def test_default_mode_is_1(self, clean_env):
        from src.config import ServingConfig

        assert ServingConfig().mode == 1

    def test_mode2_env(self, clean_env):
        from src.config import ServingConfig

        clean_env.setenv("AIOPS_MODE", "2")
        assert ServingConfig().mode == 2

    def test_garbage_env_is_mode1(self, clean_env):
        from src.config import ServingConfig

        clean_env.setenv("AIOPS_MODE", "banana")
        assert ServingConfig().mode == 1

    def test_resolve_profile_delegates_to_canonical_resolver(self, clean_env):
        from src.config import ServingConfig

        clean_env.setenv("AIOPS_MODE", "2")
        section = ServingConfig()
        profile = section.resolve_profile()
        assert isinstance(profile, ServingProfile)
        assert profile.mode == 2

    def test_global_config_has_serving_section(self):
        from src.config import config

        assert hasattr(config, "serving")
        assert config.serving.mode in (1, 2)
