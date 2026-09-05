"""
Tests for the admin-only Notification inbox.

Covers:
  * NotificationStore: add / list / unread_count / mark_read / clear, the
    newest-first order, the bounded cap, and severity coercion.
  * notify(): best-effort, never raises.
  * Routes: admin-gated on every verb; list returns notifications + unread;
    unknown severity -> 400; unread_only + mark-all behaviour end to end.
"""

import pytest


# --------------------------------------------------------------------------
# Store
# --------------------------------------------------------------------------
class TestNotificationStore:
    def _store(self, tmp_path, **kw):
        from src.notifications.store import NotificationStore

        return NotificationStore(path=tmp_path, **kw)

    def test_add_and_list_newest_first(self, tmp_path):
        s = self._store(tmp_path)
        s.add(type="a", severity="info", title="first", message="m1")
        s.add(type="b", severity="warning", title="second", message="m2")
        items = s.list()
        assert [n["title"] for n in items] == ["second", "first"]
        assert s.total() == 2

    def test_unread_count_and_mark_read(self, tmp_path):
        s = self._store(tmp_path)
        n1 = s.add(type="a", severity="info", title="t1", message="m")
        s.add(type="a", severity="info", title="t2", message="m")
        assert s.unread_count() == 2
        assert s.mark_read(ids=[n1["id"]]) == 1
        assert s.unread_count() == 1
        assert s.mark_read(mark_all=True) == 1
        assert s.unread_count() == 0
        # Nothing left to change.
        assert s.mark_read(mark_all=True) == 0

    def test_unread_only_and_severity_filter(self, tmp_path):
        s = self._store(tmp_path)
        read_one = s.add(type="a", severity="error", title="err", message="m")
        s.add(type="a", severity="info", title="info", message="m")
        s.mark_read(ids=[read_one["id"]])
        assert [n["title"] for n in s.list(unread_only=True)] == ["info"]
        assert [n["title"] for n in s.list(severity="error")] == ["err"]

    def test_clear(self, tmp_path):
        s = self._store(tmp_path)
        s.add(type="a", severity="info", title="t", message="m")
        assert s.clear() == 1
        assert s.total() == 0
        assert s.clear() == 0

    def test_bounded_cap(self, tmp_path):
        s = self._store(tmp_path, max_items=3)
        for i in range(6):
            s.add(type="a", severity="info", title=f"t{i}", message="m")
        items = s.list()
        assert len(items) == 3
        # The three most recent survive, newest first.
        assert [n["title"] for n in items] == ["t5", "t4", "t3"]

    def test_bad_severity_coerced_to_info(self, tmp_path):
        s = self._store(tmp_path)
        note = s.add(type="a", severity="explode", title="t", message="m")
        assert note["severity"] == "info"

    def test_persists_across_instances(self, tmp_path):
        s1 = self._store(tmp_path)
        s1.add(type="a", severity="warning", title="kept", message="m")
        s2 = self._store(tmp_path)
        assert [n["title"] for n in s2.list()] == ["kept"]

    def test_notify_is_best_effort(self, tmp_path, monkeypatch):
        import src.notifications.store as store_mod

        # A store whose add() blows up must not propagate out of notify().
        class _Boom:
            def add(self, **kw):
                raise RuntimeError("disk gone")

        monkeypatch.setattr(store_mod, "get_notification_store", lambda: _Boom())
        assert store_mod.notify(type="a", severity="info", title="t", message="m") is None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    """Point the route module's global store at an isolated temp store."""
    from src.notifications.store import NotificationStore, set_notification_store

    store = NotificationStore(path=tmp_path)
    set_notification_store(store)
    yield store
    set_notification_store(None)  # type: ignore[arg-type]


class TestNotificationsAuthz:
    @pytest.mark.asyncio
    async def test_list_forbidden_for_non_admin(self, temp_store):
        from fastapi import HTTPException
        from src.api.routes.notifications import list_notifications
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await list_notifications(User(id="u1", username="bob", role="user"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_unread_count_forbidden_for_non_admin(self, temp_store):
        from fastapi import HTTPException
        from src.api.routes.notifications import unread_count
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await unread_count(User(id="u1", username="bob", role="user"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_mark_read_forbidden_for_non_admin(self, temp_store):
        from fastapi import HTTPException
        from src.api.routes.notifications import MarkReadRequest, mark_read
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await mark_read(User(id="u1", username="bob", role="user"), MarkReadRequest(all=True))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_clear_forbidden_for_non_admin(self, temp_store):
        from fastapi import HTTPException
        from src.api.routes.notifications import clear_notifications
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await clear_notifications(User(id="u1", username="bob", role="user"))
        assert exc.value.status_code == 403


class TestNotificationsBehaviour:
    @pytest.mark.asyncio
    async def test_admin_list_and_unread(self, temp_store):
        from src.api.routes.notifications import list_notifications
        from src.auth.deps import User

        temp_store.add(type="action.approval", severity="warning", title="one", message="m")
        temp_store.add(type="webhook.test", severity="info", title="two", message="m")

        res = await list_notifications(
            User(id="a1", username="admin", role="admin"),
            limit=100, unread_only=False, severity=None,
        )
        assert res["count"] == 2
        assert res["unread"] == 2
        assert [n["title"] for n in res["notifications"]] == ["two", "one"]

    @pytest.mark.asyncio
    async def test_unknown_severity_rejected(self, temp_store):
        from fastapi import HTTPException
        from src.api.routes.notifications import list_notifications
        from src.auth.deps import User

        with pytest.raises(HTTPException) as exc:
            await list_notifications(
                User(id="a1", username="admin", role="admin"),
                severity="explode",
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_mark_all_read_then_clear(self, temp_store):
        from src.api.routes.notifications import MarkReadRequest, clear_notifications, mark_read
        from src.auth.deps import User

        temp_store.add(type="a", severity="info", title="t1", message="m")
        temp_store.add(type="a", severity="info", title="t2", message="m")
        admin = User(id="a1", username="admin", role="admin")

        marked = await mark_read(admin, MarkReadRequest(all=True))
        assert marked["updated"] == 2
        assert marked["unread"] == 0

        cleared = await clear_notifications(admin)
        assert cleared["cleared"] == 2
