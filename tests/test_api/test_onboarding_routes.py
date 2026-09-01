"""Route tests for the onboarding wizard backend (P1).

Follows the suite's established pattern: direct route-fn calls with
``SimpleNamespace`` mock requests (never import ``src.main`` — langgraph is not
installed in CI). Covers the two generators (template + llm-with-fallback), the
onboarding state round-trip, and the monitoring live-probe.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

import src.api.routes.prompts as prompts_mod
import src.api.routes.settings as settings_mod
import src.api.routes.topology as topology_mod
from src.topology.schema import validate_topology_schema


def _request(model_router=None):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(model_router=model_router))
    )


def _router_returning(content: str):
    router = MagicMock()
    router.reasoning_completion = AsyncMock(
        return_value={"choices": [{"message": {"content": content}}]}
    )
    return router


def _failing_router():
    router = MagicMock()
    router.reasoning_completion = AsyncMock(side_effect=RuntimeError("endpoint down"))
    return router


_WIZARD_SERVICES = [
    {"name": "Caddy", "role": "gateway", "dependsOn": ["Backend"]},
    {"name": "Backend", "role": "backend", "dependsOn": ["Postgres"]},
    {"name": "Postgres", "role": "datastore"},
]


# ── topology /generate ─────────────────────────────────────────────────────

async def test_topology_generate_template():
    body = topology_mod.GenerateFromServicesRequest(
        services=_WIZARD_SERVICES, mode="template"
    )
    resp = await topology_mod.generate_topology_from_services(_request(), body)
    assert resp.preview is True
    schema = validate_topology_schema({"nodes": resp.nodes, "edges": resp.edges})
    assert {n.id for n in schema.nodes} == {"caddy", "backend", "postgres"}
    assert ("caddy", "backend") in {(e.source, e.target) for e in schema.edges}


async def test_topology_generate_no_services_is_422():
    body = topology_mod.GenerateFromServicesRequest(services=[], mode="template")
    with pytest.raises(HTTPException) as exc:
        await topology_mod.generate_topology_from_services(_request(), body)
    assert exc.value.status_code == 422


async def test_topology_generate_llm_uses_model_output():
    llm_schema = json.dumps(
        {
            "nodes": [
                {"id": "gw", "label": "GW", "kind": "gateway", "tier": 0},
                {"id": "api", "label": "API", "kind": "backend", "tier": 1},
            ],
            "edges": [
                {"source": "gw", "target": "api", "relationship": "DEPENDS_ON", "kind": "static"}
            ],
        }
    )
    body = topology_mod.GenerateFromServicesRequest(
        services=_WIZARD_SERVICES, mode="llm"
    )
    resp = await topology_mod.generate_topology_from_services(
        _request(_router_returning(llm_schema)), body
    )
    assert {n["id"] for n in resp.nodes} == {"gw", "api"}
    assert "AI-assisted" in resp.note


async def test_topology_generate_llm_falls_back_to_template():
    body = topology_mod.GenerateFromServicesRequest(
        services=_WIZARD_SERVICES, mode="llm"
    )
    resp = await topology_mod.generate_topology_from_services(
        _request(_failing_router()), body
    )
    # Fell back to the deterministic template (the real services), not empty.
    assert {n["id"] for n in resp.nodes} == {"caddy", "backend", "postgres"}
    assert "unavailable" in resp.note.lower()


async def test_topology_generate_llm_no_router_uses_template():
    body = topology_mod.GenerateFromServicesRequest(
        services=_WIZARD_SERVICES, mode="llm"
    )
    resp = await topology_mod.generate_topology_from_services(_request(None), body)
    assert {n["id"] for n in resp.nodes} == {"caddy", "backend", "postgres"}
    assert "no llm endpoint" in resp.note.lower()


# ── prompts /generate ──────────────────────────────────────────────────────

async def test_prompts_generate_template():
    topo = topology_mod.build_topology_from_services(_WIZARD_SERVICES)
    body = prompts_mod.GeneratePromptRequest(
        services=_WIZARD_SERVICES, topology=topo, mode="template"
    )
    resp = await prompts_mod.generate_base_prompt(_request(), body)
    assert len(resp.prompt) >= 10
    assert "Caddy" in resp.prompt


async def test_prompts_generate_llm_uses_model_output():
    body = prompts_mod.GeneratePromptRequest(
        services=_WIZARD_SERVICES, topology={}, mode="llm"
    )
    text = "You are the operations assistant for the Acme platform. Help operators diagnose incidents."
    resp = await prompts_mod.generate_base_prompt(_request(_router_returning(text)), body)
    assert resp.prompt == text
    assert "AI-assisted" in resp.note


async def test_prompts_generate_llm_strips_think_and_falls_back_on_empty():
    body = prompts_mod.GeneratePromptRequest(
        services=_WIZARD_SERVICES, topology={}, mode="llm"
    )
    # Model returns only a think block → nothing usable → template fallback.
    resp = await prompts_mod.generate_base_prompt(
        _request(_router_returning("<think>hmm</think>")), body
    )
    assert "AIOps operations assistant" in resp.prompt  # the template


async def test_prompts_generate_llm_failure_falls_back():
    body = prompts_mod.GeneratePromptRequest(
        services=_WIZARD_SERVICES, topology={}, mode="llm"
    )
    resp = await prompts_mod.generate_base_prompt(_request(_failing_router()), body)
    assert len(resp.prompt) >= 10
    assert "unavailable" in resp.note.lower()


# ── settings /onboarding ───────────────────────────────────────────────────

async def test_onboarding_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    # Fresh instance → defaults.
    fresh = await settings_mod.get_onboarding()
    assert fresh.completed is False and fresh.skipped is False and fresh.step == 0
    # Persist progress, then read it back.
    saved = await settings_mod.put_onboarding(
        settings_mod.OnboardingState(completed=True, step=7)
    )
    assert saved.completed is True and saved.step == 7
    again = await settings_mod.get_onboarding()
    assert again.completed is True and again.step == 7


async def test_onboarding_put_forbidden_for_non_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    viewer = settings_mod.User(id="real-1", username="viewer", role="viewer")
    with pytest.raises(HTTPException) as exc:
        await settings_mod.put_onboarding(
            settings_mod.OnboardingState(completed=True), user=viewer
        )
    assert exc.value.status_code == 403


# ── settings /monitoring/test ──────────────────────────────────────────────

async def test_monitoring_test_no_urls_returns_all_none():
    resp = await settings_mod.test_monitoring(settings_mod.MonitoringTestRequest())
    assert resp.loki is None and resp.prometheus is None and resp.tempo is None


async def test_monitoring_test_unreachable_is_not_ok():
    # 127.0.0.1:1 refuses immediately — offline + deterministic.
    resp = await settings_mod.test_monitoring(
        settings_mod.MonitoringTestRequest(lokiUrl="http://127.0.0.1:1")
    )
    assert resp.loki is not None
    assert resp.loki.ok is False
    assert resp.prometheus is None
