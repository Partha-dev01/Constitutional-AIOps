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


def _seed(*, demo: bool, scenario: str | None = None, service: str = "nextcloud"):
    from src.api.routes.incidents import _incidents
    from src.api.schemas.incident import (
        Incident,
        IncidentCategory,
        IncidentSeverity,
        IncidentStatus,
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
        status=IncidentStatus.PENDING_APPROVAL,
        created_at=now,
        updated_at=now,
        detected_at=now,
    )
    _incidents[inc.id] = inc
    return inc


@pytest.mark.asyncio
async def test_remediate_demo_incident_heals_via_t3() -> None:
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=True, scenario="cpu_stress")
    req = MagicMock()
    with patch(
        "src.remediation.t3_client.chaos_heal",
        new=AsyncMock(return_value={"success": True, "detail": "healed"}),
    ) as heal:
        out = await remediate_incident(req, inc.id)

    heal.assert_awaited_once_with("cpu_stress")
    assert out["success"] is True
    assert out["method"] == "demo_heal"
    assert out["status"] == "resolved"
    assert inc.status == IncidentStatus.RESOLVED
    assert inc.resolved_at is not None


@pytest.mark.asyncio
async def test_remediate_real_incident_uses_gated_executor() -> None:
    from src.api.routes.incidents import remediate_incident
    from src.api.schemas.incident import IncidentStatus

    inc = _seed(demo=False, service="nextcloud")
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
