"""
Tests for the auth API routes + dependencies.

Follows the established test_settings.py pattern: route functions are invoked
DIRECTLY with MagicMock requests and monkeypatched env — src.main is never
imported (langgraph is absent in the minimal CI install) and no FastAPI test
client / python-multipart is needed (login takes a JSON body).
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Response

from src.api.routes import auth as auth_routes
from src.auth import deps, store, tokens
from src.auth.deps import User


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    """Fresh tmp data dir, fixed secret, enforcement OFF, clean throttle."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "route-test-secret")
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)
    monkeypatch.delenv("AUTH_ADMIN_USER", raising=False)
    monkeypatch.delenv("AUTH_ADMIN_PASSWORD", raising=False)
    auth_routes._failed_logins.clear()
    store.init_db()
    yield tmp_path
    auth_routes._failed_logins.clear()


def _request(ip: str = "10.0.0.1", cookies=None, headers=None) -> MagicMock:
    request = MagicMock()
    request.headers = headers or {}
    request.cookies = cookies or {}
    request.client.host = ip
    return request


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_ok_sets_session_cookie(self, auth_env):
        store.create_user("alice", "alices-long-password", role="user")
        response = Response()

        result = await auth_routes.login(
            _request(),
            auth_routes.LoginRequest(username="alice", password="alices-long-password"),
            response,
        )

        assert result["user"] == {"username": "alice", "role": "user"}
        assert "expires_at" in result
        cookie = response.headers.get("set-cookie")
        assert cookie is not None
        assert cookie.startswith(f"{tokens.COOKIE_NAME}=")
        assert "HttpOnly" in cookie
        assert "Path=/" in cookie
        assert "SameSite=lax" in cookie.lower() or "samesite=lax" in cookie.lower()
        # The cookie value is a real, verifiable session token.
        token_value = cookie.split(";")[0].split("=", 1)[1]
        claims = tokens.verify_session(token_value)
        assert claims is not None and claims["name"] == "alice"

    @pytest.mark.asyncio
    async def test_login_bad_credentials_401(self, auth_env):
        store.create_user("alice", "alices-long-password")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.login(
                _request(),
                auth_routes.LoginRequest(username="alice", password="wrong-password"),
                Response(),
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user_401(self, auth_env):
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.login(
                _request(),
                auth_routes.LoginRequest(username="ghost", password="whatever-pass"),
                Response(),
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_throttle_locks_after_five_failures(self, auth_env):
        store.create_user("alice", "alices-long-password")
        bad = auth_routes.LoginRequest(username="alice", password="wrong-password")

        for _ in range(5):
            with pytest.raises(HTTPException) as exc_info:
                await auth_routes.login(_request(ip="9.9.9.9"), bad, Response())
            assert exc_info.value.status_code == 401

        # 6th attempt from the SAME ip: locked out, even with GOOD creds.
        good = auth_routes.LoginRequest(username="alice", password="alices-long-password")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.login(_request(ip="9.9.9.9"), good, Response())
        assert exc_info.value.status_code == 429

        # A different ip is unaffected.
        result = await auth_routes.login(_request(ip="8.8.8.8"), good, Response())
        assert result["user"]["username"] == "alice"

    @pytest.mark.asyncio
    async def test_throttle_uses_trusted_proxy_hop_not_spoofed_prefix(self, auth_env):
        # Behind a single trusted Caddy hop the REAL client IP is the right-most
        # XFF entry (the one Caddy appends), NOT the left-most attacker-supplied
        # one. The throttle must key off the trusted (right-most) value.
        bad = auth_routes.LoginRequest(username="ghost", password="whatever-pass")
        headers = {"x-forwarded-for": "203.0.113.7, 10.0.0.2"}
        for _ in range(5):
            with pytest.raises(HTTPException):
                await auth_routes.login(_request(headers=headers), bad, Response())
        # Keyed on the trusted hop (10.0.0.2), NOT the spoofable left prefix.
        assert "10.0.0.2" in auth_routes._failed_logins
        assert "203.0.113.7" not in auth_routes._failed_logins

    @pytest.mark.asyncio
    async def test_spoofed_xff_cannot_dodge_lockout(self, auth_env):
        # An attacker behind the same Caddy hop rotates the LEFT (spoofable) XFF
        # entry on every request to try to dodge the per-IP lockout. Because the
        # throttle keys on the right-most trusted hop, all attempts collapse to
        # the same key and the lockout still trips on the 6th try.
        store.create_user("alice", "alices-long-password")
        good = auth_routes.LoginRequest(username="alice", password="alices-long-password")
        bad = auth_routes.LoginRequest(username="alice", password="wrong-password")
        for i in range(5):
            spoofed = {"x-forwarded-for": f"1.2.3.{i}, 10.0.0.9"}
            with pytest.raises(HTTPException) as exc_info:
                await auth_routes.login(_request(headers=spoofed), bad, Response())
            assert exc_info.value.status_code == 401
        # 6th attempt with GOOD creds but the same trusted hop: still locked.
        locked = {"x-forwarded-for": "9.9.9.9, 10.0.0.9"}
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.login(_request(headers=locked), good, Response())
        assert exc_info.value.status_code == 429
        # Only the trusted hop accumulated failures.
        assert "10.0.0.9" in auth_routes._failed_logins
        assert all(k == "10.0.0.9" for k in auth_routes._failed_logins)

    @pytest.mark.asyncio
    async def test_client_ip_falls_back_to_peer_without_xff(self, auth_env):
        # No XFF header at all -> use the TCP peer (request.client.host).
        assert auth_routes._client_ip(_request(ip="198.51.100.5")) == "198.51.100.5"

    @pytest.mark.asyncio
    async def test_successful_login_clears_failures(self, auth_env):
        store.create_user("alice", "alices-long-password")
        bad = auth_routes.LoginRequest(username="alice", password="wrong-password")
        good = auth_routes.LoginRequest(username="alice", password="alices-long-password")
        for _ in range(3):
            with pytest.raises(HTTPException):
                await auth_routes.login(_request(ip="7.7.7.7"), bad, Response())
        await auth_routes.login(_request(ip="7.7.7.7"), good, Response())
        assert "7.7.7.7" not in auth_routes._failed_logins


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, auth_env):
        response = Response()
        result = await auth_routes.logout(_request(), response, None)
        assert result["ok"] is True
        cookie = response.headers.get("set-cookie")
        assert cookie is not None and cookie.startswith(f"{tokens.COOKIE_NAME}=")
        assert 'Max-Age=0' in cookie or "expires" in cookie.lower()

    @pytest.mark.asyncio
    async def test_logout_everywhere_bumps_token_version(self, auth_env):
        record = store.create_user("alice", "alices-long-password")
        token = tokens.sign_session(record)
        request = _request(cookies={tokens.COOKIE_NAME: token})

        result = await auth_routes.logout(
            request, Response(), auth_routes.LogoutRequest(everywhere=True)
        )
        assert result["everywhere"] is True
        assert store.get_by_username("alice").token_version == 2
        # The old token is now rejected by the dependency layer.
        assert deps.get_current_user(request) is None


# ---------------------------------------------------------------------------
# GET /config + GET /me
# ---------------------------------------------------------------------------


class TestConfigAndMe:
    @pytest.mark.asyncio
    async def test_config_public_shape_default_off(self, auth_env):
        assert await auth_routes.get_auth_config() == {
            "auth_required": False,
            "signup_enabled": False,
            "captcha_provider": "",
            "captcha_site_key": "",
        }

    @pytest.mark.asyncio
    async def test_config_reflects_enforcement(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        config = await auth_routes.get_auth_config()
        assert config["auth_required"] is True
        assert config["signup_enabled"] is False

    @pytest.mark.asyncio
    async def test_me_returns_user_shape(self, auth_env):
        result = await auth_routes.me(User(id="u1", username="alice", role="user"))
        assert result == {"username": "alice", "role": "user"}

    @pytest.mark.asyncio
    async def test_me_returns_synthetic_admin_when_called_without_di(self, auth_env):
        # Direct call without DI mirrors the AUTH_REQUIRED=false passthrough.
        result = await auth_routes.me()
        assert result == {"username": "admin", "role": "admin"}


# ---------------------------------------------------------------------------
# require_user / require_admin dependencies
# ---------------------------------------------------------------------------


class TestRequireUser:
    @pytest.mark.asyncio
    async def test_passthrough_synthetic_admin_when_flag_unset(self, auth_env):
        user = await deps.require_user(_request())
        assert user.role == "admin"
        assert user.username == "admin"
        assert deps.is_synthetic(user) is True

    @pytest.mark.asyncio
    async def test_synthetic_admin_username_from_env(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_ADMIN_USER", "operator")
        user = await deps.require_user(_request())
        assert user.username == "operator"

    @pytest.mark.asyncio
    async def test_401_when_enforced_and_no_token(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        with pytest.raises(HTTPException) as exc_info:
            await deps.require_user(_request())
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_cookie_accepted_when_enforced(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        record = store.create_user("alice", "alices-long-password")
        token = tokens.sign_session(record)
        user = await deps.require_user(_request(cookies={tokens.COOKIE_NAME: token}))
        assert user.username == "alice"
        assert deps.is_synthetic(user) is False

    @pytest.mark.asyncio
    async def test_bearer_fallback_accepted_when_enforced(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        record = store.create_user("alice", "alices-long-password")
        token = tokens.sign_session(record)
        user = await deps.require_user(
            _request(headers={"authorization": f"Bearer {token}"})
        )
        assert user.username == "alice"

    @pytest.mark.asyncio
    async def test_stale_token_version_rejected(self, auth_env, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        record = store.create_user("alice", "alices-long-password")
        token = tokens.sign_session(record)
        store.bump_token_version("alice")
        with pytest.raises(HTTPException) as exc_info:
            await deps.require_user(_request(cookies={tokens.COOKIE_NAME: token}))
        assert exc_info.value.status_code == 401


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_admin_passes(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        assert await deps.require_admin(admin) == admin

    @pytest.mark.asyncio
    async def test_user_role_gets_403(self, auth_env):
        with pytest.raises(HTTPException) as exc_info:
            await deps.require_admin(User(id="u1", username="alice", role="user"))
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Admin user management routes
# ---------------------------------------------------------------------------


class TestAdminUserRoutes:
    @pytest.mark.asyncio
    async def test_create_list_delete_users(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        created = await auth_routes.admin_create_user(
            auth_routes.UserCreateRequest(
                username="alice", password="alices-long-password", role="user"
            ),
            admin,
        )
        assert created == {"username": "alice", "role": "user"}

        listed = await auth_routes.admin_list_users(admin)
        assert listed["total"] == 1
        assert listed["items"][0]["username"] == "alice"

        await auth_routes.admin_delete_user("alice", admin)
        assert store.get_by_username("alice") is None

    @pytest.mark.asyncio
    async def test_create_duplicate_user_409(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        body = auth_routes.UserCreateRequest(
            username="alice", password="alices-long-password", role="user"
        )
        await auth_routes.admin_create_user(body, admin)
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.admin_create_user(body, admin)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_weak_password_400(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.admin_create_user(
                auth_routes.UserCreateRequest(
                    username="alice", password="short", role="user"
                ),
                admin,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_self_refused(self, auth_env):
        store.create_user("boss", "boss-long-password", role="admin")
        admin = User(id="a1", username="boss", role="admin")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.admin_delete_user("boss", admin)
        assert exc_info.value.status_code == 400
        assert store.get_by_username("boss") is not None

    @pytest.mark.asyncio
    async def test_delete_unknown_user_404(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        with pytest.raises(HTTPException) as exc_info:
            await auth_routes.admin_delete_user("ghost", admin)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_set_password_route(self, auth_env):
        admin = User(id="a1", username="boss", role="admin")
        store.create_user("alice", "alices-long-password")
        result = await auth_routes.admin_set_password(
            "alice", auth_routes.PasswordChangeRequest(password="a-new-long-password"), admin
        )
        assert result == {"ok": True}
        assert store.authenticate("alice", "a-new-long-password") is not None


# ---------------------------------------------------------------------------
# Router registration (static inspection — never import src.main)
# ---------------------------------------------------------------------------


class TestRouterRegistration:
    def test_auth_router_wired_into_main(self):
        from pathlib import Path

        main_src = Path(__file__).resolve().parents[2] / "src" / "main.py"
        text = main_src.read_text(encoding="utf-8")
        assert "auth_router" in text
        assert "include_router(auth_router" in text
        # Protected routers carry the require_user dependency.
        assert "Depends(require_user)" in text


# ---------------------------------------------------------------------------
# Chat ownership scoping
# ---------------------------------------------------------------------------


class TestChatOwnershipScoping:
    @pytest.mark.asyncio
    async def test_list_conversations_filters_by_owner(self, auth_env, monkeypatch):
        from src.api.routes import chat as chat_module
        from src.api.schemas.chat import ConversationHistory

        def conv(conv_id: str, owner):
            return ConversationHistory(
                conversation_id=conv_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                owner=owner,
            )

        monkeypatch.setattr(
            chat_module,
            "_conversations",
            {
                "c-alice": conv("c-alice", "alice"),
                "c-bob": conv("c-bob", "bob"),
                "c-legacy": conv("c-legacy", None),
            },
        )

        alice = User(id="u1", username="alice", role="user")
        # Direct call: pass limit/offset explicitly (the route defaults are now
        # fastapi Query markers, only resolved under real DI).
        result = await chat_module.list_conversations(limit=20, offset=0, user=alice)
        ids = {item["conversation_id"] for item in result["items"]}
        assert ids == {"c-alice"}
        assert result["total"] == 1

        # Admins additionally see legacy owner-less conversations.
        admin = User(id="a1", username="root", role="admin")
        result = await chat_module.list_conversations(limit=20, offset=0, user=admin)
        ids = {item["conversation_id"] for item in result["items"]}
        assert ids == {"c-legacy"}

    @pytest.mark.asyncio
    async def test_get_and_delete_enforce_ownership(self, auth_env, monkeypatch):
        from src.api.routes import chat as chat_module
        from src.api.schemas.chat import ConversationHistory

        conversations = {
            "c-bob": ConversationHistory(
                conversation_id="c-bob",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                owner="bob",
            )
        }
        monkeypatch.setattr(chat_module, "_conversations", conversations)

        alice = User(id="u1", username="alice", role="user")
        with pytest.raises(HTTPException) as exc_info:
            await chat_module.get_conversation("c-bob", alice)
        assert exc_info.value.status_code == 404
        with pytest.raises(HTTPException) as exc_info:
            await chat_module.delete_conversation("c-bob", alice)
        assert exc_info.value.status_code == 404

        bob = User(id="u2", username="bob", role="user")
        fetched = await chat_module.get_conversation("c-bob", bob)
        assert fetched.conversation_id == "c-bob"
        await chat_module.delete_conversation("c-bob", bob)
        assert "c-bob" not in conversations
