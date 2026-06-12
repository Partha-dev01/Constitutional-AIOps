"""
Tests for src/auth/store.py — SQLite user store (tmp AIOPS_DATA_DIR per test).
"""

import pytest

from src.auth import store


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Point the user store at a fresh temp data dir for each test."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    store.init_db()
    yield tmp_path


class TestCreateAndGet:
    def test_create_user_and_get_by_username(self, tmp_store):
        record = store.create_user("alice", "alices-long-password", role="user")
        assert record.username == "alice"
        assert record.role == "user"
        assert record.token_version == 1
        assert record.password_hash.startswith("scrypt$")

        fetched = store.get_by_username("alice")
        assert fetched == record

    def test_get_unknown_username_returns_none(self, tmp_store):
        assert store.get_by_username("nobody") is None

    def test_duplicate_username_raises(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        with pytest.raises(ValueError, match="already exists"):
            store.create_user("alice", "another-long-password")

    def test_invalid_role_raises(self, tmp_store):
        with pytest.raises(ValueError, match="Role"):
            store.create_user("bob", "bobs-long-password", role="superuser")

    def test_policy_enforced_on_create(self, tmp_store):
        with pytest.raises(ValueError):
            store.create_user("bob", "short")

    def test_list_and_count_and_delete(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        store.create_user("bob", "bobs-long-password")
        assert store.count_users() == 2
        assert {u.username for u in store.list_users()} == {"alice", "bob"}

        assert store.delete_user("bob") is True
        assert store.delete_user("bob") is False  # already gone
        assert store.count_users() == 1


class TestAuthenticate:
    def test_authenticate_ok(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        record = store.authenticate("alice", "alices-long-password")
        assert record is not None
        assert record.username == "alice"

    def test_authenticate_bad_password(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        assert store.authenticate("alice", "wrong-password-1") is None

    def test_authenticate_unknown_user(self, tmp_store):
        assert store.authenticate("ghost", "any-password-here") is None


class TestEnsureInitialAdmin:
    def test_bootstrap_creates_admin_once(self, tmp_store, monkeypatch):
        monkeypatch.setenv("AUTH_ADMIN_USER", "rootadmin")
        monkeypatch.setenv("AUTH_ADMIN_PASSWORD", "rootadmin-strong-pass")

        created = store.ensure_initial_admin()
        assert created is not None
        assert created.role == "admin"
        # Idempotent: second call is a no-op
        assert store.ensure_initial_admin() is None
        assert store.count_users() == 1

    def test_bootstrap_skipped_when_envs_missing(self, tmp_store, monkeypatch):
        monkeypatch.delenv("AUTH_ADMIN_USER", raising=False)
        monkeypatch.delenv("AUTH_ADMIN_PASSWORD", raising=False)
        assert store.ensure_initial_admin() is None
        assert store.count_users() == 0

    def test_bootstrap_skipped_when_table_not_empty(self, tmp_store, monkeypatch):
        store.create_user("existing", "existing-long-pass")
        monkeypatch.setenv("AUTH_ADMIN_USER", "rootadmin")
        monkeypatch.setenv("AUTH_ADMIN_PASSWORD", "rootadmin-strong-pass")
        assert store.ensure_initial_admin() is None
        assert store.count_users() == 1

    def test_bootstrap_skipped_on_weak_password(self, tmp_store, monkeypatch):
        monkeypatch.setenv("AUTH_ADMIN_USER", "rootadmin")
        monkeypatch.setenv("AUTH_ADMIN_PASSWORD", "short")
        assert store.ensure_initial_admin() is None
        assert store.count_users() == 0


class TestTokenVersionAndPassword:
    def test_bump_token_version(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        assert store.bump_token_version("alice") == 2
        assert store.bump_token_version("alice") == 3
        assert store.get_by_username("alice").token_version == 3

    def test_bump_unknown_user_returns_none(self, tmp_store):
        assert store.bump_token_version("ghost") is None

    def test_set_password_rotates_hash_and_bumps_tv(self, tmp_store):
        store.create_user("alice", "alices-long-password")
        before = store.get_by_username("alice")
        assert store.set_password("alice", "a-brand-new-password") is True
        after = store.get_by_username("alice")
        assert after.password_hash != before.password_hash
        assert after.token_version == before.token_version + 1
        assert store.authenticate("alice", "a-brand-new-password") is not None
        assert store.authenticate("alice", "alices-long-password") is None

    def test_set_password_unknown_user(self, tmp_store):
        assert store.set_password("ghost", "whatever-long-pass") is False


class TestUserSettings:
    def test_settings_roundtrip_and_overwrite(self, tmp_store):
        record = store.create_user("alice", "alices-long-password")
        assert store.get_user_settings(record.id) is None

        store.set_user_settings(record.id, {"notifications": {"emailEnabled": True}})
        assert store.get_user_settings(record.id) == {
            "notifications": {"emailEnabled": True}
        }

        store.set_user_settings(record.id, {"notifications": {"emailEnabled": False}})
        assert store.get_user_settings(record.id) == {
            "notifications": {"emailEnabled": False}
        }
