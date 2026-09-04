"""
Tests for the admin-only Audit Log viewer.

Covers:
  GET /api/v1/audit/            → admin-gated, newest-first, honest empty result
  GET /api/v1/audit/event-types → admin-gated list of known event types
  query_events() month-boundary fix (the viewer queries multi-day windows)
"""

import pytest


class TestAuditListAuthz:
    @pytest.mark.asyncio
    async def test_forbidden_for_non_admin(self):
        from fastapi import HTTPException
        from src.api.routes.audit import list_audit_events
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await list_audit_events(User(id="u1", username="bob", role="user"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_event_types_forbidden_for_non_admin(self):
        from fastapi import HTTPException
        from src.api.routes.audit import list_event_types
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await list_event_types(User(id="u1", username="bob", role="user"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_event_types_admin(self):
        from src.api.routes.audit import list_event_types
        from src.auth.deps import User

        res = await list_event_types(User(id="a1", username="admin", role="admin"))
        assert "constitutional.validation" in res["event_types"]
        assert "action.executed" in res["event_types"]


class TestAuditListBehaviour:
    @pytest.mark.asyncio
    async def test_admin_gets_events_newest_first(self, monkeypatch):
        import src.api.routes.audit as audit_mod
        from src.api.routes.audit import list_audit_events
        from src.auth.deps import User

        rows = [
            {"event_id": "1", "timestamp": "2026-09-01T10:00:00", "event_type": "action.created"},
            {"event_id": "3", "timestamp": "2026-09-03T10:00:00", "event_type": "action.executed"},
            {"event_id": "2", "timestamp": "2026-09-02T10:00:00", "event_type": "action.approved"},
        ]

        class _Logger:
            def query_events(self, **kwargs):
                return list(rows)

        monkeypatch.setattr(audit_mod, "get_audit_logger", lambda: _Logger())

        # Called directly (not via FastAPI), so pass explicit values rather than
        # the Query(...) default objects.
        res = await list_audit_events(
            User(id="a1", username="admin", role="admin"),
            limit=100, days=7, event_type=None, resource_type=None, actor_id=None,
        )
        assert res["count"] == 3
        # Newest first.
        assert [e["event_id"] for e in res["events"]] == ["3", "2", "1"]
        assert res["truncated"] is False

    @pytest.mark.asyncio
    async def test_unknown_event_type_rejected(self):
        from fastapi import HTTPException
        from src.api.routes.audit import list_audit_events
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await list_audit_events(
                User(id="a1", username="admin", role="admin"),
                event_type="not.a.real.event",
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_query_failure_returns_empty_not_500(self, monkeypatch):
        import src.api.routes.audit as audit_mod
        from src.api.routes.audit import list_audit_events
        from src.auth.deps import User

        class _Logger:
            def query_events(self, **kwargs):
                raise RuntimeError("disk gone")

        monkeypatch.setattr(audit_mod, "get_audit_logger", lambda: _Logger())

        res = await list_audit_events(
            User(id="a1", username="admin", role="admin"),
            limit=100, days=7, event_type=None, resource_type=None, actor_id=None,
        )
        assert res["events"] == []
        assert res["count"] == 0


class TestQueryEventsMonthBoundary:
    """The viewer queries windows of up to 90 days; the old
    ``current_date.replace(day=day+1)`` raised ValueError at every month end."""

    def test_query_spanning_month_boundary_does_not_raise(self, tmp_path):
        from datetime import datetime
        from src.utils.audit import AuditLogger

        logger = AuditLogger(log_dir=tmp_path)
        # A window that steps over 2026-01-31 -> 2026-02-01 (the old bug: day=32).
        events = logger.query_events(
            start_date=datetime(2026, 1, 30),
            end_date=datetime(2026, 2, 3),
        )
        assert events == []  # no files written, but crucially no exception
