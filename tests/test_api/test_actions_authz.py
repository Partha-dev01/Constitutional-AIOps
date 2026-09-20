"""R4 security: POST /api/v1/actions skip_validation is admin-only.

skip_validation marks an action APPROVED and bypasses the constitutional
validation of the record. It is documented "admin only" but had no admin
check — any authenticated user (including a public-signup role=user account)
could forge an auto-approved, unvalidated action record. These tests pin the
enforcement: refused for a non-admin under AUTH_REQUIRED, allowed for an admin,
and unchanged (allowed) when auth enforcement is off (synthetic admin).

Per CI constraints the route module is imported directly; src.main (which pulls
langgraph, absent from the minimal CI install) is never imported.
"""

from unittest.mock import MagicMock

import pytest


def _action_create(skip_validation: bool = False):
    from src.api.schemas.action import ActionCreate, ActionType

    return ActionCreate(
        action_type=ActionType.RESTART_SERVICE,
        description="restart nextcloud to clear a leak",
        target_service="nextcloud",
        confidence=0.95,
        skip_validation=skip_validation,
    )


def _request() -> MagicMock:
    request = MagicMock()
    # No confidence calculator / validator wired: the skip_validation branch
    # returns an APPROVED action before either is consulted.
    request.app.state.confidence_calculator = None
    request.app.state.validator = None
    return request


class TestSkipValidationAuthz:
    @pytest.mark.asyncio
    async def test_non_admin_cannot_skip_validation(self, monkeypatch):
        from fastapi import HTTPException

        from src.api.routes import actions as actions_route
        from src.auth.deps import User

        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setattr(
            actions_route,
            "get_current_user",
            lambda request: User(id="u1", username="alice", role="user"),
        )
        with pytest.raises(HTTPException) as exc:
            await actions_route.create_action(_request(), _action_create(skip_validation=True))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_may_skip_validation(self, monkeypatch):
        from src.api.routes import actions as actions_route
        from src.api.schemas.action import ActionStatus
        from src.auth.deps import User

        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setattr(
            actions_route,
            "get_current_user",
            lambda request: User(id="a1", username="root", role="admin"),
        )
        action = await actions_route.create_action(
            _request(), _action_create(skip_validation=True)
        )
        assert action.status == ActionStatus.APPROVED

    @pytest.mark.asyncio
    async def test_skip_validation_allowed_when_auth_off(self, monkeypatch):
        # Auth enforcement off => the request already runs as the synthetic
        # admin, so the dev / self-host default is unchanged (no 403).
        from src.api.routes import actions as actions_route
        from src.api.schemas.action import ActionStatus

        monkeypatch.delenv("AUTH_REQUIRED", raising=False)
        action = await actions_route.create_action(
            _request(), _action_create(skip_validation=True)
        )
        assert action.status == ActionStatus.APPROVED


class TestCallerContextSanitiser:
    """C1: POST /tools/call must not let its body assert the gate's own inputs.

    src/constitutional/validator.py honours context["human_approved"], and the
    tools route merged arbitrary caller JSON into that context. A request body
    of {"context": {"human_approved": true}} therefore authorised itself and the
    constitutional gate became decoration. The sanitiser runs at the HTTP
    boundary only, so in-process callers (incidents.py, actions.py, chat.py)
    keep supplying real approval state through execute_tool_call().
    """

    def test_strips_every_validator_trusted_key(self):
        from src.api.routes.tools import _sanitize_caller_context

        hostile = {
            "human_approved": True,
            "telemetry_evidence": True,
            "audit_enabled": False,
            "active_incident": True,
            "action_scope": "single",
            "confidence": 1.0,
            "resource_usage": 0,
            "outcome_tracking": True,
            "is_temporary_fix": False,
            "permanent_fix_planned": True,
            "source": "incident_remediate",
        }
        assert _sanitize_caller_context(hostile) == {}

    def test_keeps_keys_the_validator_does_not_trust(self):
        from src.api.routes.tools import _sanitize_caller_context

        cleaned = _sanitize_caller_context(
            {"human_approved": True, "note": "hello", "trace_id": "abc"}
        )
        assert cleaned == {"note": "hello", "trace_id": "abc"}

    def test_non_dict_context_becomes_empty(self):
        from src.api.routes.tools import _sanitize_caller_context

        assert _sanitize_caller_context(None) == {}
        assert _sanitize_caller_context("human_approved=true") == {}

    def test_source_cannot_forge_an_active_incident(self):
        """"source" drives the gate's active_incident derivation, so it goes too."""
        from src.api.routes.tools import _sanitize_caller_context

        assert "source" not in _sanitize_caller_context({"source": "approve_to_run"})


class TestApproverComesFromTheSession:
    """C2: the audit trail must not name whoever the request body says it does."""

    @pytest.mark.asyncio
    async def test_body_supplied_approver_is_ignored(self):
        from src.api.routes.actions import _actions, approve_action, create_action
        from src.api.schemas.action import ActionApproval, ActionStatus

        from src.api.schemas.action import ActionCreate, ActionType

        _actions.clear()
        # Medium confidence so the action actually lands in AWAITING_APPROVAL.
        # The shared _action_create() helper uses 0.95, which auto-approves and
        # would make this test skip itself into uselessness.
        action = await create_action(
            _request(),
            ActionCreate(
                action_type=ActionType.SCALE_UP,
                description="scale up the api service",
                target_service="api-service",
                confidence=0.75,
            ),
        )
        assert action.status == ActionStatus.AWAITING_APPROVAL

        approved = await approve_action(
            action.id,
            ActionApproval(approved=True, approved_by="not-the-caller"),
        )

        assert approved.approved_by == "admin"
        assert approved.approved_by != "not-the-caller"
        # and the audit entry agrees with the action record
        approved_events = [e for e in approved.audit_log if e.get("event") == "approved"]
        assert approved_events
        assert approved_events[-1]["details"]["approved_by"] == "admin"
