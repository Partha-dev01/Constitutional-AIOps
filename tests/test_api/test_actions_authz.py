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
