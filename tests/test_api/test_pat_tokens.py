"""
Tests for personal access tokens (Track 3): store layer, the pat helper, the
deps integration, and the /auth/tokens routes.

Same direct-call pattern as test_auth_routes.py: route functions invoked with
MagicMock requests + real User objects; src.main is never imported.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.routes import auth as auth_routes
from src.auth import deps, pat, store
from src.auth.deps import User


@pytest.fixture
def token_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "pat-test-secret")
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)
    store.init_db()
    yield tmp_path


def _request(cookies=None, headers=None) -> MagicMock:
    request = MagicMock()
    request.headers = headers or {}
    request.cookies = cookies or {}
    request.client.host = "10.0.0.1"
    return request


# ---------------------------------------------------------------------------
# pat helper
# ---------------------------------------------------------------------------


class TestPatHelper:
    def test_generate_shape_and_hash_roundtrip(self):
        plaintext, token_hash, prefix = pat.generate()
        assert plaintext.startswith(pat.PAT_PREFIX)
        assert pat.is_pat(plaintext) is True
        assert token_hash == pat.hash_token(plaintext)
        assert prefix and plaintext.startswith(prefix)
        # The stored prefix is a fragment, not the whole secret.
        assert len(prefix) < len(plaintext)

    def test_is_pat_rejects_session_shaped_tokens(self):
        assert pat.is_pat("abc.def") is False
        assert pat.is_pat("") is False

    def test_resolve_unknown_token_is_none(self, token_env):
        assert pat.resolve_user_id(pat.PAT_PREFIX + "nope") is None

    def test_resolve_non_pat_is_none(self, token_env):
        assert pat.resolve_user_id("not-a-pat") is None

    def test_resolve_valid_token_returns_user_id_and_touches(self, token_env):
        user = store.create_user("alice", "alices-long-password")
        plaintext, token_hash, prefix = pat.generate()
        store.create_access_token(user.id, "cli", token_hash, prefix)
        assert pat.resolve_user_id(plaintext) == user.id
        # last_used_at is stamped on first resolve.
        rec = store.get_access_token_by_hash(token_hash)
        assert rec.last_used_at is not None

    def test_resolve_expired_token_is_none(self, token_env):
        user = store.create_user("alice", "alices-long-password")
        plaintext, token_hash, prefix = pat.generate()
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        store.create_access_token(user.id, "old", token_hash, prefix, expires_at=past)
        assert pat.resolve_user_id(plaintext) is None


# ---------------------------------------------------------------------------
# store layer
# ---------------------------------------------------------------------------


class TestStoreAccessTokens:
    def test_create_list_count_delete_scoped(self, token_env):
        u = store.create_user("alice", "alices-long-password")
        other = store.create_user("bob", "bobs-long-password-x")
        _, h1, p1 = pat.generate()
        rec = store.create_access_token(u.id, "one", h1, p1)
        assert store.count_access_tokens(u.id) == 1
        assert store.list_access_tokens(u.id)[0].name == "one"
        # bob cannot delete alice's token.
        assert store.delete_access_token(other.id, rec.id) is False
        assert store.count_access_tokens(u.id) == 1
        # alice can.
        assert store.delete_access_token(u.id, rec.id) is True
        assert store.count_access_tokens(u.id) == 0

    def test_delete_user_cascades_tokens(self, token_env):
        u = store.create_user("alice", "alices-long-password")
        _, h, p = pat.generate()
        store.create_access_token(u.id, "cli", h, p)
        assert store.count_access_tokens(u.id) == 1
        store.delete_user("alice")
        assert store.get_access_token_by_hash(h) is None


# ---------------------------------------------------------------------------
# deps integration: a PAT bearer authenticates when AUTH_REQUIRED=true
# ---------------------------------------------------------------------------


class TestDepsPatAuth:
    @pytest.mark.asyncio
    async def test_pat_bearer_resolves_to_user(self, token_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        u = store.create_user("alice", "alices-long-password", role="user")
        plaintext, h, p = pat.generate()
        store.create_access_token(u.id, "cli", h, p)
        user = await deps.require_user(
            _request(headers={"authorization": f"Bearer {plaintext}"})
        )
        assert user.username == "alice"
        assert user.role == "user"
        assert deps.is_synthetic(user) is False

    @pytest.mark.asyncio
    async def test_revoked_pat_is_rejected(self, token_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        u = store.create_user("alice", "alices-long-password")
        plaintext, h, p = pat.generate()
        rec = store.create_access_token(u.id, "cli", h, p)
        store.delete_access_token(u.id, rec.id)
        with pytest.raises(HTTPException) as exc_info:
            await deps.require_user(
                _request(headers={"authorization": f"Bearer {plaintext}"})
            )
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# routes
# ---------------------------------------------------------------------------


class TestTokenRoutes:
    @pytest.mark.asyncio
    async def test_create_returns_plaintext_once_then_list_hides_it(self, token_env):
        store.create_user("alice", "alices-long-password", role="user")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        created = await auth_routes.create_token(
            auth_routes.TokenCreateRequest(name="ci-bot"), alice
        )
        assert created["token"].startswith(pat.PAT_PREFIX)
        assert created["name"] == "ci-bot"
        assert created["prefix"] and "token" not in created["prefix"]

        listed = await auth_routes.list_tokens(alice)
        assert listed["total"] == 1
        item = listed["items"][0]
        assert "token" not in item  # secret never re-served
        assert item["prefix"] == created["prefix"]

    @pytest.mark.asyncio
    async def test_create_with_expiry_sets_expires_at(self, token_env):
        store.create_user("alice", "alices-long-password")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        created = await auth_routes.create_token(
            auth_routes.TokenCreateRequest(name="temp", expires_in_days=30), alice
        )
        assert created["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_revoke_removes_token(self, token_env):
        store.create_user("alice", "alices-long-password")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        created = await auth_routes.create_token(
            auth_routes.TokenCreateRequest(name="tmp"), alice
        )
        await auth_routes.revoke_token(created["id"], alice)
        assert (await auth_routes.list_tokens(alice))["total"] == 0

    @pytest.mark.asyncio
    async def test_revoke_someone_elses_token_404(self, token_env):
        store.create_user("alice", "alices-long-password")
        store.create_user("bob", "bobs-long-password-x")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        bob = User(id=store.get_by_username("bob").id, username="bob", role="user")
        created = await auth_routes.create_token(
            auth_routes.TokenCreateRequest(name="a"), alice
        )
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.revoke_token(created["id"], bob)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_synthetic_admin_cannot_create(self, token_env):
        # AUTH_REQUIRED off -> the caller is the synthetic admin; tokens are inert.
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.create_token(auth_routes.TokenCreateRequest(name="x"))
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_synthetic_list_is_empty(self, token_env):
        assert await auth_routes.list_tokens() == {"items": [], "total": 0}

    @pytest.mark.asyncio
    async def test_cap_enforced(self, token_env, monkeypatch):
        store.create_user("alice", "alices-long-password")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        monkeypatch.setattr(auth_routes, "MAX_ACCESS_TOKENS_PER_USER", 2)
        await auth_routes.create_token(auth_routes.TokenCreateRequest(name="a"), alice)
        await auth_routes.create_token(auth_routes.TokenCreateRequest(name="b"), alice)
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.create_token(auth_routes.TokenCreateRequest(name="c"), alice)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_blank_name_rejected(self, token_env):
        store.create_user("alice", "alices-long-password")
        alice = User(id=store.get_by_username("alice").id, username="alice", role="user")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.create_token(auth_routes.TokenCreateRequest(name="   "), alice)
        assert exc_info.value.status_code == 400
