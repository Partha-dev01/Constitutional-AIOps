"""SEC-M1: one account must not be able to read another account's records.

`_actions` and `_incidents` were process-global dicts with no owner, so any
authenticated account could list every record and fetch any record by id. C2
had already gated the *mutations* behind an admin role, which is why this was
latent rather than exploited, but reads were wide open and public signup is on.

The two rules under test, and they are deliberately different from chat's:

* actions and incidents are operational records, so an **admin sees
  everything** and a non-admin sees only what they created;
* anything unowned, including everything the telemetry pipeline raises, is
  **admin-only** rather than world-readable. Fail closed.

Per the CI constraint the route modules are imported directly; `src.main`
pulls langgraph, which the minimal CI install does not have.
"""

from unittest.mock import MagicMock

import pytest

from src.api.scoping import PIPELINE_OWNER, can_access, owner_or_404
from src.auth.deps import User

ADMIN = User(id="1", username="admin", role="admin")
ALICE = User(id="2", username="alice", role="user")
BOB = User(id="3", username="bob", role="user")


def _request() -> MagicMock:
    from src.constitutional.validator import ConstitutionalValidator

    request = MagicMock()
    request.app.state.confidence_calculator = None
    request.app.state.validator = ConstitutionalValidator()
    return request


def _list_actions(route, user):
    """Direct call: FastAPI is not here to resolve the Query(...) defaults, so
    every filter is passed explicitly as None."""
    return route.list_actions(
        user=user,
        page=1,
        page_size=100,
        status=None,
        action_type=None,
        target_service=None,
        incident_id=None,
        requires_approval=None,
    )


def _list_incidents(route, user):
    return route.list_incidents(
        user=user,
        page=1,
        page_size=100,
        status=None,
        severity=None,
        category=None,
        service=None,
        search=None,
    )


# ---------------------------------------------------------------------------
# The rule itself
# ---------------------------------------------------------------------------

class TestCanAccess:
    def test_admin_sees_everything(self):
        for owner in ("alice", "bob", None, "", PIPELINE_OWNER):
            assert can_access(owner, ADMIN) is True, owner

    def test_owner_sees_their_own(self):
        assert can_access("alice", ALICE) is True

    def test_a_different_account_does_not(self):
        assert can_access("alice", BOB) is False

    @pytest.mark.parametrize("owner", [None, "", PIPELINE_OWNER])
    def test_unowned_records_are_admin_only(self, owner):
        """The fail-closed half. A record nobody owns is not everybody's."""
        assert can_access(owner, ALICE) is False

    def test_an_account_named_system_cannot_claim_pipeline_records(self):
        """`Action.created_by` defaults to the literal "system", so a user who
        registered that username would otherwise inherit every pipeline record."""
        impostor = User(id="9", username=PIPELINE_OWNER, role="user")
        assert can_access(PIPELINE_OWNER, impostor) is False

    def test_owner_or_404_raises_404_never_403(self):
        """403 would confirm the id exists, which is an enumeration oracle."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            owner_or_404("alice", BOB, "Action X not found")
        assert exc.value.status_code == 404

    def test_owner_or_404_is_silent_for_the_owner(self):
        owner_or_404("alice", ALICE, "nope")


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def _action_create(**kw):
    from src.api.schemas.action import ActionCreate, ActionType

    payload = dict(
        action_type=ActionType.RESTART_SERVICE,
        description="restart the worker",
        target_service="workers",
        confidence=0.95,
    )
    payload.update(kw)
    return ActionCreate(**payload)


@pytest.mark.asyncio
class TestActionScoping:
    async def test_create_records_the_caller_not_the_literal_system(self):
        """`created_by` existed all along and was hardcoded, so nothing knew
        who filed an action. That is what made scoping impossible."""
        from src.api.routes import actions as route

        action = await route.create_action(_request(), _action_create(), user=ALICE)
        assert action.created_by == "alice"

    async def test_one_account_cannot_fetch_another_accounts_action(self):
        from fastapi import HTTPException

        from src.api.routes import actions as route

        action = await route.create_action(_request(), _action_create(), user=ALICE)
        with pytest.raises(HTTPException) as exc:
            await route.get_action(action.id, user=BOB)
        assert exc.value.status_code == 404

    async def test_the_owner_can_fetch_it(self):
        from src.api.routes import actions as route

        action = await route.create_action(_request(), _action_create(), user=ALICE)
        assert (await route.get_action(action.id, user=ALICE)).id == action.id

    async def test_admin_can_fetch_it(self):
        from src.api.routes import actions as route

        action = await route.create_action(_request(), _action_create(), user=ALICE)
        assert (await route.get_action(action.id, user=ADMIN)).id == action.id

    async def test_list_hides_other_accounts(self):
        from src.api.routes import actions as route

        route._actions.clear()
        mine = await route.create_action(_request(), _action_create(), user=ALICE)
        theirs = await route.create_action(_request(), _action_create(), user=BOB)

        ids = {a.id for a in (await _list_actions(route, ALICE)).items}
        assert mine.id in ids
        assert theirs.id not in ids, "alice must not see bob's action"

        all_ids = {a.id for a in (await _list_actions(route, ADMIN)).items}
        assert {mine.id, theirs.id} <= all_ids, "admin must see both"

    async def test_list_total_does_not_leak_the_hidden_count(self):
        """Scoping after paging would still report someone else's total."""
        from src.api.routes import actions as route

        route._actions.clear()
        await route.create_action(_request(), _action_create(), user=ALICE)
        for _ in range(3):
            await route.create_action(_request(), _action_create(), user=BOB)

        assert (await _list_actions(route, ALICE)).total == 1

    async def test_stats_are_scoped_too(self):
        from src.api.routes import actions as route

        route._actions.clear()
        await route.create_action(_request(), _action_create(), user=ALICE)
        await route.create_action(_request(), _action_create(), user=BOB)

        assert (await route.get_action_stats(user=ALICE)).total == 1
        assert (await route.get_action_stats(user=ADMIN)).total == 2

    async def test_cancel_is_refused_for_a_non_owner(self):
        """Cancel is the one mutating action route C2 did NOT gate on admin,
        so ownership is the only thing standing in front of it."""
        from fastapi import HTTPException

        from src.api.routes import actions as route

        action = await route.create_action(_request(), _action_create(), user=ALICE)
        with pytest.raises(HTTPException) as exc:
            await route.cancel_action(action.id, reason="not mine", user=BOB)
        assert exc.value.status_code == 404

        cancelled = await route.cancel_action(action.id, reason="mine", user=ALICE)
        assert cancelled.status.value == "cancelled"

    async def test_pending_approvals_are_scoped(self):
        from src.api.routes import actions as route

        route._actions.clear()
        await route.create_action(
            _request(),
            _action_create(incident_id="inc-1", confidence=0.85),
            user=ALICE,
        )
        seen_by_bob = (await route.get_pending_approvals(user=BOB)).actions
        assert seen_by_bob == []


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestIncidentScoping:
    async def test_a_pipeline_incident_is_admin_only(self):
        """The real exposure: a public-signup account reading the operator's
        infrastructure incidents. Nothing the pipeline raises has an owner."""
        from fastapi import HTTPException

        from src.api.routes import incidents as route
        from src.api.schemas.incident import Incident, IncidentStatus, ServiceInfo

        route._incidents.clear()
        route._incident_owner.clear()
        from datetime import datetime

        now = datetime.utcnow()
        route._incidents["INC-PIPE"] = Incident(
            id="INC-PIPE",
            title="disk filling on nextcloud-host",
            description="pipeline raised",
            severity="high",
            category="resource",
            affected_services=[ServiceInfo(name="nextcloud")],
            source="telemetry",
            status=IncidentStatus.DETECTING,
            created_at=now,
            updated_at=now,
            detected_at=now,
        )

        with pytest.raises(HTTPException) as exc:
            await route.get_incident("INC-PIPE", user=ALICE)
        assert exc.value.status_code == 404

        assert (await route.get_incident("INC-PIPE", user=ADMIN)).id == "INC-PIPE"
        assert (await _list_incidents(route, ALICE)).items == []
        assert len((await _list_incidents(route, ADMIN)).items) == 1

    async def test_a_user_filed_incident_belongs_to_that_user(self):
        from fastapi import HTTPException

        from src.api.routes import incidents as route
        from src.api.schemas.incident import IncidentCreate, ServiceInfo

        route._incidents.clear()
        route._incident_owner.clear()
        created = await route.create_incident(
            _request(),
            IncidentCreate(
                title="my app is down",
                description="filed by alice",
                severity="medium",
                category="availability",
                affected_services=[ServiceInfo(name="alice-app")],
                auto_analyze=False,
            ),
            user=ALICE,
        )
        assert route._incident_owner[created.id] == "alice"
        assert (await route.get_incident(created.id, user=ALICE)).id == created.id
        with pytest.raises(HTTPException):
            await route.get_incident(created.id, user=BOB)

    async def test_update_is_refused_for_a_non_owner(self):
        """PATCH was left authenticated-only on purpose (triage notes), so
        ownership is what stops a stranger editing someone else's incident."""
        from fastapi import HTTPException

        from src.api.routes import incidents as route
        from src.api.schemas.incident import IncidentCreate, IncidentUpdate, ServiceInfo

        route._incidents.clear()
        route._incident_owner.clear()
        created = await route.create_incident(
            _request(),
            IncidentCreate(
                title="mine incident",
                description="d",
                severity="low",
                category="availability",
                affected_services=[ServiceInfo(name="svc-x")],
                auto_analyze=False,
            ),
            user=ALICE,
        )
        with pytest.raises(HTTPException) as exc:
            await route.update_incident(
                created.id, IncidentUpdate(assigned_to="bob"), user=BOB
            )
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Ownership has to survive a restart
# ---------------------------------------------------------------------------

def test_incident_owner_round_trips_through_persistence(tmp_path, monkeypatch):
    """An owner held only in memory would be lost on redeploy, and every
    incident would come back admin-only."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    import importlib

    from src.persistence import store as ps

    importlib.reload(ps)
    from datetime import datetime

    from src.api.schemas.incident import Incident, IncidentStatus, ServiceInfo

    now = datetime.utcnow()
    inc = Incident(
        id="INC-OWN",
        title="title here",
        description="d",
        severity="low",
        category="availability",
        affected_services=[ServiceInfo(name="svc-x")],
        source="manual",
        status=IncidentStatus.DETECTING,
        created_at=now,
        updated_at=now,
        detected_at=now,
    )
    ps.save_incident(inc, owner="alice")
    assert ps.load_all_incident_owners() == {"INC-OWN": "alice"}

    # A later save that does not carry the owner must not erase it: the
    # analyze/remediate paths re-persist the record without touching ownership.
    ps.save_incident(inc, owner=None)
    assert ps.load_all_incident_owners() == {"INC-OWN": "alice"}
