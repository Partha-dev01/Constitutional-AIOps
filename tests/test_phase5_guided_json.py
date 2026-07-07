"""
Tests for Phase 5 of the Mode 2 plan (structured decoding, offline part):

1. ``guided_schema`` on ModelRouter completions is applied ONLY when the
   serving profile supports guided JSON (Mode 2) — Mode 1 payloads stay
   byte-identical even when callers always pass their schema.
2. FastAnnotator always passes the annotation schema; ReasoningAgent passes
   the RCA schema for RCA mode only (chat/planning stay free-form).
3. Schema sanity: the schemas mirror the JSON contracts the system prompts
   demand (field names + enums), with no $ref indirection.

The live half of Phase 5 (xgrammar behavior on vLLM v0.24, hermes tool
parser) is a GPU-session gate, not covered here.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.model_router import ModelRouter
from src.agents.schemas import ANNOTATION_JSON_SCHEMA, RCA_JSON_SCHEMA
from src.agents.serving_profile import ServingProfile

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
    for var in _RESOLVER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def _mock_response() -> MagicMock:
    resp = MagicMock()
    resp.json = MagicMock(return_value={"choices": [{"message": {"content": "{}"}}]})
    resp.raise_for_status = MagicMock(return_value=None)
    return resp


def _mode2_profile() -> ServingProfile:
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


# ---------------------------------------------------------------------------
# 1. Router gating
# ---------------------------------------------------------------------------


class TestGuidedSchemaGating:
    @pytest.mark.asyncio
    async def test_mode1_never_sends_response_format(self, clean_env):
        router = ModelRouter()
        router._fast_client.post = AsyncMock(return_value=_mock_response())
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("annotate", guided_schema=ANNOTATION_JSON_SCHEMA)
        assert "response_format" not in router._fast_client.post.call_args.kwargs["json"]

        await router.reasoning_completion("rca", guided_schema=RCA_JSON_SCHEMA)
        assert (
            "response_format"
            not in router._reasoning_client.post.call_args.kwargs["json"]
        )

    @pytest.mark.asyncio
    async def test_mode2_sends_json_schema_response_format(self, clean_env):
        router = ModelRouter(profile=_mode2_profile())
        router._fast_client.post = AsyncMock(return_value=_mock_response())
        router._reasoning_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("annotate", guided_schema=ANNOTATION_JSON_SCHEMA)
        rf = router._fast_client.post.call_args.kwargs["json"]["response_format"]
        assert rf["type"] == "json_schema"
        assert rf["json_schema"]["schema"] is ANNOTATION_JSON_SCHEMA

        await router.reasoning_completion("rca", guided_schema=RCA_JSON_SCHEMA)
        rf = router._reasoning_client.post.call_args.kwargs["json"]["response_format"]
        assert rf["json_schema"]["schema"] is RCA_JSON_SCHEMA

    @pytest.mark.asyncio
    async def test_mode2_without_schema_sends_nothing(self, clean_env):
        router = ModelRouter(profile=_mode2_profile())
        router._fast_client.post = AsyncMock(return_value=_mock_response())

        await router.fast_completion("free-form request")
        assert "response_format" not in router._fast_client.post.call_args.kwargs["json"]


# ---------------------------------------------------------------------------
# 2. Caller wiring
# ---------------------------------------------------------------------------


class TestCallerWiring:
    @pytest.mark.asyncio
    async def test_fast_annotator_passes_annotation_schema(self):
        from src.agents.fast_annotator import FastAnnotator

        router = MagicMock()
        router.fast_completion = AsyncMock(
            return_value={
                "choices": [{"message": {"content": '{"severity": "info"}'}}]
            }
        )
        annotator = FastAnnotator(model_router=router)

        await annotator.process({"telemetry_type": "log", "content": "hello"})

        assert (
            router.fast_completion.call_args.kwargs["guided_schema"]
            is ANNOTATION_JSON_SCHEMA
        )

    @pytest.mark.asyncio
    async def test_reasoning_agent_schema_per_mode(self):
        from src.agents.reasoning_agent import ReasoningAgent

        router = MagicMock()
        router.reasoning_completion = AsyncMock(
            return_value={
                "choices": [{"message": {"content": '{"root_cause": "x", "confidence": 0.8}'}}]
            }
        )
        agent = ReasoningAgent(model_router=router)

        await agent.process({"mode": "rca", "query": "why?", "context": ""})
        assert (
            router.reasoning_completion.call_args.kwargs["guided_schema"]
            is RCA_JSON_SCHEMA
        )

        await agent.process({"mode": "chat", "query": "hi", "context": ""})
        assert router.reasoning_completion.call_args.kwargs["guided_schema"] is None


# ---------------------------------------------------------------------------
# 3. Schema sanity
# ---------------------------------------------------------------------------


class TestSchemaShape:
    def test_annotation_schema_mirrors_prompt_contract(self):
        props = ANNOTATION_JSON_SCHEMA["properties"]
        assert set(ANNOTATION_JSON_SCHEMA["required"]) == {
            "anomaly_detected",
            "severity",
            "category",
            "confidence",
            "summary",
            "needs_reasoning",
            "key_indicators",
            "triplets",
        }
        assert props["severity"]["enum"] == ["critical", "warning", "info"]
        assert props["category"]["enum"] == [
            "performance",
            "error",
            "security",
            "resource",
        ]
        triplet = props["triplets"]["items"]
        assert triplet["required"] == ["subject", "relation", "object"]

    def test_rca_schema_mirrors_prompt_contract(self):
        props = RCA_JSON_SCHEMA["properties"]
        assert "root_cause" in RCA_JSON_SCHEMA["required"]
        assert "confidence" in RCA_JSON_SCHEMA["required"]
        assert props["impact"]["properties"]["severity"]["enum"] == [
            "critical",
            "high",
            "medium",
            "low",
        ]
        step = props["remediation_steps"]["items"]
        assert step["required"] == ["action", "risk"]

    def test_schemas_have_no_ref_indirection(self):
        import json

        for schema in (ANNOTATION_JSON_SCHEMA, RCA_JSON_SCHEMA):
            text = json.dumps(schema)
            assert "$ref" not in text and "$defs" not in text
