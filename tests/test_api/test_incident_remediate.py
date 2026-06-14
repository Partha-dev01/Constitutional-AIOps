"""/incidents/{id}/remediate + /dismiss.

Demo incidents heal via the t3 agent (``t3_client.chaos_heal``); real incidents
restart the affected service through the gated ``execute_tool_call`` (so the
constitutional gate + Tier-1 safety + kill-switch still apply). Dismiss archives
the incident (status -> closed). Route functions are called directly (no
``src.main`` import) per the test gate.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _fast_demo_pacing(monkeypatch):
    """Shrink the staged-demo pacing + verification poll so tests run instantly.

    The live demo paces stages with multi-second sleeps and polls t3_status up to
    5x; tests don't need real wall-clock pacing.
    """
    import src.api.routes.incidents as inc

    monkeypatch.setattr(inc, "_DEMO_STAGE_DELAY_VALIDATE", 0.0, raising=True)
    monkeypatch.setattr(inc, "_DEMO_STAGE_DELAY_EXECUTE", 0.0, raising=True)
    monkeypatch.setattr(inc, "_DEMO_STAGE_DELAY_VERIFY", 0.0, raising=True)
    monkeypatch.setattr(inc, "_DEMO_VERIFY_RETRIES", 2, raising=True)
    monkeypatch.setattr(inc, "_DEMO_VERIFY_INTERVAL", 0.0, raising=True)


def _healed_status(scenario="cpu_stress", container="nextcloud"):
    """A t3_status payload confirming the scenario is inactive + container up."""
    return {
        "success": True,
        "scenarios": {scenario: {"active": False}},
        "containers": {container: {"running": True}},
    }


def _seed(
    *,
    demo: bool,
    scenario: str | None = None,
    service: str = "nextcloud",
    analyzed: bool = False,
    status=None,
):
    from src.api.routes.incidents import _incidents
    from src.api.schemas.incident import (
        Incident,
        IncidentCategory,
        IncidentSeverity,
        IncidentStatus,
        RCAResult,
        ServiceInfo,
    )

    _incidents.clear()
    now = datetime.utcnow()
    inc = Incident(
        id="INC-2026-9001",
        title="test incident",
        severity=IncidentSeverity.HIGH,
        category=IncidentCategory.PERFORMANCE,
        affected_services=[ServiceInfo(name=service)],
        tags=(["demo", "auto-generated", scenario] if demo and scenario else []),
        source=("demo-mode" if demo else "manual"),
        status=status or IncidentStatus.PENDING_APPROVAL,
        rca=(
            RCAResult(root_cause="rc", causal_chain=["a"], confidence=0.9)
            if analyzed
            else None
        ),
        created_at=now,
        updated_at=now,
        detected_at=now,
    )
    _incidents[inc.id] = inc
    return inc


def _validator_request(*, can_proceed=True):
    """A request whose validator returns a report with the given can_proceed and
    whose validate() captures the context it received."""
    captured = {}

    report = MagicMock()
    report.can_proceed = can_proceed
    report.requires_approval = False
    report.authorization_level = MagicMock(value="automatic")
    report.overall_result = MagicMock(value="passed" if can_proceed else "violated")
    report.confidence = 0.9
    report.tier1_passed = can_proceed
    report.tier2_passed = True
    report.tier3_passed = True
    report.violations = []
    report.warnings = []
    report.explanation = "ok" if can_proceed else "Tier 1 (Safety) violation - action BLOCKED"

    validator = MagicMock()
    validator.confidence_threshold_auto = 0.9
    validator.confidence_threshold_approval = 0.7
    validator.validate.side_effect = lambda **kw: captured.update(kw) or report
    req = MagicMock()
    req.app.state.validator = validator
    return req, captured, validator


@pytest.mark.asyncio
async def test_remediate_demo_incident_heals_via_t3() -> None:
    """W4-B: demo remediate goes REMEDIATING -> (gate) -> heal -> verify ->
    RESOLVED. The heal only resolves AFTER t3_status confirms recovery."""
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress")
    req, _captured, _validator = _validator_request(can_proceed=True)
    with patch(
        "src.remediation.t3_client.chaos_heal",
        new=AsyncMock(return_value={"success": True, "detail": "healed"}),
    ) as heal, patch(
        "src.remediation.t3_client.t3_status",
        new=AsyncMock(return_value=_healed_status("cpu_stress")),
    ) as status:
        out = await remediate_incident(req, inc.id)

    heal.assert_awaited_once_with("cpu_stress")
    status.assert_awaited()  # verification ran
    assert out["success"] is True
    assert out["method"] == "demo_heal"
    assert out["status"] == "resolved"
    assert inc.status == IncidentStatus.RESOLVED
    assert inc.resolved_at is not None


@pytest.mark.asyncio
async def test_remediate_demo_not_resolved_when_verification_fails() -> None:
    """W4-B: if the heal call succeeds but t3_status never confirms recovery, the
    incident is NOT falsely resolved — it stays actionable with a clear detail."""
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress")
    req, _captured, _validator = _validator_request(can_proceed=True)
    # Scenario still active across every poll -> verification fails.
    still_broken = {
        "success": True,
        "scenarios": {"cpu_stress": {"active": True}},
        "containers": {"nextcloud": {"running": True}},
    }
    with patch(
        "src.remediation.t3_client.chaos_heal",
        new=AsyncMock(return_value={"success": True, "detail": "heal sent"}),
    ) as heal, patch(
        "src.remediation.t3_client.t3_status",
        new=AsyncMock(return_value=still_broken),
    ):
        out = await remediate_incident(req, inc.id)

    heal.assert_awaited_once()
    assert out["success"] is False
    assert out["error_code"] == "verification_failed"
    # Never falsely resolved.
    assert inc.status == IncidentStatus.PENDING_APPROVAL
    assert inc.resolved_at is None


@pytest.mark.asyncio
async def test_demo_heal_goes_through_constitutional_gate() -> None:
    """D-item5: the demo heal is validated + audited (no silent bypass) and the
    real verdict is surfaced to the UI instead of None."""
    from src.api.routes.incidents import remediate_incident

    inc = _seed(demo=True, scenario="cpu_stress", analyzed=True)
    req, captured, validator = _validator_request(can_proceed=True)
    with patch(
        "src.remediation.t3_client.chaos_heal",
        new=AsyncMock(return_value={"success": True, "detail": "healed"}),
    ), patch(
        "src.remediation.t3_client.t3_status",
        new=AsyncMock(return_value=_healed_status("cpu_stress")),
    ):
        out = await remediate_incident(req, inc.id)

    # The validator actually ran for the heal action.
    validator.validate.assert_called_once()
    assert captured["context"]["active_incident"] is True
    assert captured["context"]["human_approved"] is True
    # W4-B: the gate now receives the REAL RCA confidence (0.9 from _seed),
    # not the hard-coded auto threshold.
    assert captured["confidence"] == 0.9
    # A real verdict is surfaced (not None as before).
    assert out["verdict"] is not None
    assert out["verdict"]["can_proceed"] is True


@pytest.mark.asyncio
async def test_demo_heal_blocked_by_validator_does_not_heal() -> None:
    """If constitutional validation refuses the heal, chaos_heal is NOT called and
    the incident stays actionable."""
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress")
    req, _captured, _validator = _validator_request(can_proceed=False)
    heal = AsyncMock(return_value={"success": True})
    with patch("src.remediation.t3_client.chaos_heal", new=heal):
        out = await remediate_incident(req, inc.id)

    heal.assert_not_awaited()
    assert out["success"] is False
    assert out["error_code"] == "validation_blocked"
    assert inc.status == IncidentStatus.PENDING_APPROVAL


@pytest.mark.asyncio
async def test_remediate_real_incident_uses_gated_executor() -> None:
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=False, service="nextcloud", analyzed=True)
    req = MagicMock()
    req.app.state.validator.confidence_threshold_auto = 0.9
    fake = AsyncMock(
        return_value={
            "success": True,
            "metadata": {"constitutional": {"can_proceed": True}},
        }
    )
    with patch("src.api.routes.tools.execute_tool_call", new=fake):
        out = await remediate_incident(req, inc.id)

    fake.assert_awaited_once()
    _, kwargs = fake.call_args
    assert kwargs["tool_name"] == "restart_service"
    assert kwargs["parameters"]["service_name"] == "nextcloud"
    assert kwargs["parameters"]["confidence"] == 0.9
    assert kwargs["context"]["human_approved"] is True
    # Evidence is asserted only because this incident has an RCA (analyzed=True).
    assert kwargs["context"]["telemetry_evidence"] is True
    assert out["success"] is True
    assert out["method"] == "restart_service"
    assert out["verdict"] == {"can_proceed": True}
    assert inc.status == IncidentStatus.RESOLVED


@pytest.mark.asyncio
async def test_remediate_declined_keeps_incident_actionable() -> None:
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=False, service="nextcloud")
    req = MagicMock()
    req.app.state.validator.confidence_threshold_auto = 0.9
    fake = AsyncMock(
        return_value={
            "success": False,
            "error_code": "validation_blocked",
            "metadata": {"constitutional": {"can_proceed": False}},
        }
    )
    with patch("src.api.routes.tools.execute_tool_call", new=fake):
        out = await remediate_incident(req, inc.id)

    assert out["success"] is False
    assert out["status"] == "refused"
    assert out["error_code"] == "validation_blocked"
    # Declined remediation must leave the incident actionable, not resolved.
    assert inc.status == IncidentStatus.PENDING_APPROVAL


@pytest.mark.asyncio
async def test_remediate_unknown_incident_raises_404() -> None:
    from fastapi import HTTPException

    from src.api.routes.incidents import _incidents, remediate_incident

    _incidents.clear()
    with pytest.raises(HTTPException) as exc_info:
        await remediate_incident(MagicMock(), "does-not-exist")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_dismiss_archives_incident() -> None:
    from src.api.routes.incidents import dismiss_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="db_down")
    out = await dismiss_incident(inc.id)
    assert out.status == IncidentStatus.CLOSED
    assert out.resolved_at is not None


@pytest.mark.asyncio
async def test_dismiss_unknown_incident_raises_404() -> None:
    from fastapi import HTTPException

    from src.api.routes.incidents import _incidents, dismiss_incident

    _incidents.clear()
    with pytest.raises(HTTPException) as exc_info:
        await dismiss_incident("nope")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_remediate_refuses_when_already_remediating() -> None:
    """Anti-storm guard: a second remediate while one is in flight is a no-op."""
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress", status=IncidentStatus.REMEDIATING)
    heal = AsyncMock(return_value={"success": True})
    with patch("src.remediation.t3_client.chaos_heal", new=heal):
        out = await remediate_incident(MagicMock(), inc.id)

    heal.assert_not_awaited()
    assert out["success"] is False
    assert out["error_code"] == "already_remediating"
    assert inc.status == IncidentStatus.REMEDIATING


@pytest.mark.asyncio
async def test_analysis_automatic_does_not_deadlock_in_remediating() -> None:
    """D-item5: a high-confidence ("automatic") RCA must NOT flip the incident to
    REMEDIATING from analysis — there is no executor for that state, so the
    anti-storm guard would then permanently lock the operator out of remediating.
    It caps at PENDING_APPROVAL so the incident stays actionable."""
    from src.api.routes.incidents import _trigger_analysis
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=False, service="nextcloud")
    inc.status = IncidentStatus.ANALYZING

    graph_result = {
        "rca_result": {"metadata": {"root_cause": "rc", "causal_chain": ["a"]}},
        "confidence": 0.97,
        "authorization_level": "automatic",  # high-confidence verdict
        "steps_completed": ["annotate", "reasoning", "validate"],
    }
    req = MagicMock()
    req.app.state.incident_graph.ainvoke = AsyncMock(return_value=graph_result)

    await _trigger_analysis(req, inc, enable_thinking=False)

    # Capped at PENDING_APPROVAL, NOT REMEDIATING.
    assert inc.status == IncidentStatus.PENDING_APPROVAL


@pytest.mark.asyncio
async def test_analysis_builds_remediation_plan_from_rca_steps() -> None:
    """W4-A: after RCA, incident.remediation_plan is built from the RCA's
    remediation_steps (the UI renders it)."""
    from src.api.routes.incidents import _trigger_analysis

    inc = _seed(demo=True, scenario="cpu_stress")
    graph_result = {
        "rca_result": {
            "metadata": {
                "root_cause": "rc",
                "causal_chain": ["a"],
                "remediation_steps": [
                    {"action": "Throttle CPU-bound jobs", "risk": "low"},
                    {"action": "Restart the nextcloud container", "risk": "high"},
                ],
            }
        },
        "confidence": 0.88,
        "authorization_level": "approval",
        "steps_completed": ["annotate", "reasoning", "validate"],
    }
    req = MagicMock()
    req.app.state.incident_graph.ainvoke = AsyncMock(return_value=graph_result)

    await _trigger_analysis(req, inc, enable_thinking=False)

    plan = inc.remediation_plan
    assert plan is not None
    assert len(plan.steps) == 2
    assert plan.steps[0].action == "Throttle CPU-bound jobs"
    assert plan.steps[0].risk == "low"
    assert plan.steps[1].risk == "high"
    # Highest step risk wins overall; high-risk step requires approval.
    assert plan.overall_risk == "high"
    assert plan.requires_approval is True
    assert plan.incident_id == inc.id


@pytest.mark.asyncio
async def test_analysis_builds_minimal_plan_when_no_steps() -> None:
    """W4-A: with no structured remediation_steps, a minimal 1-step plan is built."""
    from src.api.routes.incidents import _trigger_analysis

    inc = _seed(demo=True, scenario="cpu_stress")
    graph_result = {
        "rca_result": {"metadata": {"root_cause": "rc", "causal_chain": ["a"]}},
        "confidence": 0.9,
        "authorization_level": "approval",
        "steps_completed": ["reasoning"],
    }
    req = MagicMock()
    req.app.state.incident_graph.ainvoke = AsyncMock(return_value=graph_result)

    await _trigger_analysis(req, inc, enable_thinking=False)

    plan = inc.remediation_plan
    assert plan is not None
    assert len(plan.steps) == 1
    assert "nextcloud" in plan.steps[0].action


@pytest.mark.asyncio
async def test_analysis_then_remediate_is_not_locked_out() -> None:
    """End-to-end of the deadlock fix: after a high-confidence analysis the
    operator can still remediate (the incident is PENDING_APPROVAL, not stuck in
    REMEDIATING with already_remediating)."""
    from src.api.routes.incidents import _trigger_analysis, remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress")
    inc.status = IncidentStatus.ANALYZING

    graph_result = {
        "rca_result": {"metadata": {"root_cause": "rc", "causal_chain": ["a"]}},
        "confidence": 0.97,
        "authorization_level": "automatic",
        "steps_completed": ["annotate", "reasoning", "validate"],
    }
    analyze_req = MagicMock()
    analyze_req.app.state.incident_graph.ainvoke = AsyncMock(return_value=graph_result)
    await _trigger_analysis(analyze_req, inc, enable_thinking=False)
    assert inc.status == IncidentStatus.PENDING_APPROVAL

    # Now remediate — must NOT be refused with already_remediating.
    rem_req, _captured, _validator = _validator_request(can_proceed=True)
    with patch(
        "src.remediation.t3_client.chaos_heal",
        new=AsyncMock(return_value={"success": True, "detail": "healed"}),
    ), patch(
        "src.remediation.t3_client.t3_status",
        new=AsyncMock(return_value=_healed_status("cpu_stress")),
    ):
        out = await remediate_incident(rem_req, inc.id)

    assert out.get("error_code") != "already_remediating"
    assert out["success"] is True
    assert inc.status == IncidentStatus.RESOLVED


@pytest.mark.asyncio
async def test_remediate_demo_blocked_in_production_without_flag(monkeypatch) -> None:
    """The demo heal path honours the production kill-switch (AIOPS_ENABLE_DEMO)."""
    from fastapi import HTTPException

    from src.api.routes.incidents import remediate_incident

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("AIOPS_ENABLE_DEMO", raising=False)
    inc = _seed(demo=True, scenario="cpu_stress")
    heal = AsyncMock(return_value={"success": True})
    with patch("src.remediation.t3_client.chaos_heal", new=heal):
        with pytest.raises(HTTPException) as exc_info:
            await remediate_incident(MagicMock(), inc.id)

    assert exc_info.value.status_code == 403
    heal.assert_not_awaited()
