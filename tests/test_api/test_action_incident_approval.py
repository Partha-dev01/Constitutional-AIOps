"""P1.2's approval route must survive the validator (ISS-112 follow-on).

P1.2 is the only Tier-1 principle whose text carries its own remedy: "Never
take destructive actions during active incidents WITHOUT EXPLICIT APPROVAL."
The validator implements that faithfully, an approved remediation does not
violate it.

The proposal path could not express it. `POST /actions` validates a brand new
action, where nothing has been approved yet by definition, so the context it
builds carries `active_incident` and no `human_approved`. P1.2 therefore fired,
Tier 1 failed, and the status decision mapped that to REJECTED. `approve_action`
refuses anything not AWAITING_APPROVAL, so the action could never be approved:
the principle demanded an approval that the flow had already made unreachable.

Before ISS-112 this was mostly invisible because P1.2 matched action names
exactly, so only a literal `scale_down` reached it. Token matching makes
`restart_service` reach it too, which is the entire remediation surface, so the
deadlock has to be closed in the same change.

Per CI constraints the route module is imported directly; src.main (which pulls
langgraph, absent from the minimal CI install) is never imported.
"""

from unittest.mock import MagicMock

import pytest


def _request() -> MagicMock:
    """A request whose app state carries a REAL constitutional validator."""
    from src.constitutional.validator import ConstitutionalValidator

    request = MagicMock()
    request.app.state.confidence_calculator = None
    request.app.state.validator = ConstitutionalValidator()
    return request


def _incident_linked_restart():
    from src.api.schemas.action import ActionCreate, ActionType

    return ActionCreate(
        action_type=ActionType.RESTART_SERVICE,
        description="restart nextcloud, it is the incident's blast radius",
        target_service="nextcloud",
        incident_id="inc-1",
        confidence=0.85,
        evidence={"telemetry_evidence": True},
    )


@pytest.mark.asyncio
async def test_incident_linked_restart_awaits_approval_instead_of_rejection():
    from src.api.routes import actions as actions_route
    from src.api.schemas.action import ActionStatus

    action = await actions_route.create_action(_request(), _incident_linked_restart())

    assert action.status == ActionStatus.AWAITING_APPROVAL, (
        f"status was {action.status.value}; a P1.2-only violation must stay "
        f"approvable, otherwise the principle's own remedy is unreachable"
    )
    assert action.requires_approval is True
    assert action.validation is not None
    assert any(v["principle_id"] == "P1.2" for v in action.validation.violations)


@pytest.mark.asyncio
async def test_that_action_can_then_actually_be_approved():
    """The point of the previous test. An approvable status that approve_action
    still refuses would be the same deadlock wearing a different label."""
    from src.api.routes import actions as actions_route
    from src.api.routes.auth import User
    from src.api.schemas.action import ActionApproval, ActionStatus

    action = await actions_route.create_action(_request(), _incident_linked_restart())

    approved = await actions_route.approve_action(
        action_id=action.id,
        approval=ActionApproval(approved=True, reason="on call, going ahead"),
        admin=User(id=1, username="admin", role="admin"),
    )
    assert approved.status == ActionStatus.APPROVED
    assert approved.approved_by == "admin"


@pytest.mark.asyncio
async def test_a_security_change_is_still_rejected_outright():
    """The escape hatch is P1.2 ONLY, and this is the case that proves it.

    `rotate_credentials` is a P1.4 violation (a security noun with a non-read
    verb). P1.4's published text also ends "without explicit approval", but the
    validator does NOT implement that clause for it, unlike P1.2. So the route
    must keep rejecting it rather than inventing an approval route the gate does
    not recognise. The asymmetry itself is logged as ISS-113; it is a safety
    decision, not something to settle inside an ISS-112 fix.
    """
    from src.api.routes import actions as actions_route
    from src.api.schemas.action import ActionCreate, ActionStatus, ActionType

    action = await actions_route.create_action(
        _request(),
        ActionCreate(
            action_type=ActionType.ROTATE_CREDENTIALS,
            description="rotate the database credentials",
            target_service="postgres",
            incident_id="inc-1",
            confidence=0.95,
        ),
    )
    assert action.status == ActionStatus.REJECTED
    assert any(v["principle_id"] == "P1.4" for v in action.validation.violations)


@pytest.mark.asyncio
async def test_data_loss_during_an_incident_is_not_made_approvable():
    """Directly on the validator, so the assertion cannot drift with the route."""
    from src.constitutional.validator import ConstitutionalValidator

    report = ConstitutionalValidator().validate(
        action_id="dl-1",
        action_description="purge",
        action_type="purge_index",
        confidence=0.95,
        context={"active_incident": True},
    )
    critical = {v.principle.id for v in report.violations if v.severity == "critical"}
    assert "P1.1" in critical, "data loss must still be a Tier-1 violation"
    assert critical != {"P1.2"}, (
        "the route's approval escape hatch keys on P1.2 being the ONLY critical "
        "violation; this action must not qualify"
    )
