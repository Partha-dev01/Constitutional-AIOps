"""
Tests for public self-service signup (R3): src/auth/signup.py, the email
columns on src/auth/store.py, and the /signup + /verify routes.

Route functions are invoked directly with MagicMock requests + monkeypatched
env, mirroring tests/test_api/test_auth_routes.py (src.main is never imported).
"""

import sqlite3
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Response
from fastapi.responses import HTMLResponse

from src.api.routes import auth as auth_routes
from src.auth import signup, store


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def signup_env(tmp_path, monkeypatch):
    """Fresh tmp data dir + fixed secret + public signup ON + clean throttles."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "signup-test-secret")
    monkeypatch.setenv("AIOPS_ENABLE_PUBLIC_SIGNUP", "true")
    monkeypatch.delenv("SIGNUP_CAPTCHA_PROVIDER", raising=False)
    monkeypatch.delenv("SIGNUP_SMTP_HOST", raising=False)
    auth_routes._failed_logins.clear()
    auth_routes._signup_attempts.clear()
    store.init_db()
    yield tmp_path
    auth_routes._failed_logins.clear()
    auth_routes._signup_attempts.clear()


def _request(ip: str = "10.0.0.1", headers=None) -> MagicMock:
    request = MagicMock()
    request.headers = headers or {}
    request.cookies = {}
    request.client.host = ip
    return request


def _signup_body(username="newuser", email="new@example.com", password="a-long-password-1"):
    return auth_routes.SignupRequest(username=username, email=email, password=password)


# ---------------------------------------------------------------------------
# Store: email columns + migration
# ---------------------------------------------------------------------------


class TestStoreEmail:
    def test_create_with_email_and_lookup(self, signup_env):
        rec = store.create_user("u1", "a-long-password-1", email="Mixed@Case.COM")
        assert rec.email == "mixed@case.com"  # normalised
        assert rec.email_verified is False
        assert store.get_by_email("MIXED@case.com").username == "u1"

    def test_duplicate_email_rejected(self, signup_env):
        store.create_user("u1", "a-long-password-1", email="dupe@example.com")
        with pytest.raises(ValueError, match="already exists"):
            store.create_user("u2", "a-long-password-1", email="dupe@example.com")

    def test_mark_email_verified(self, signup_env):
        rec = store.create_user("u1", "a-long-password-1", email="v@example.com")
        assert store.mark_email_verified(rec.id) is True
        assert store.get_by_username("u1").email_verified is True
        assert store.mark_email_verified("no-such-id") is False

    def test_migration_adds_columns_to_old_db(self, tmp_path, monkeypatch):
        """A pre-email users.db gets the columns added by init_db, and reads work."""
        monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
        db = tmp_path / "users.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,"
            " password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',"
            " token_version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO users VALUES ('id1','legacy','scrypt$x','admin',1,'2026-01-01T00:00:00+00:00')"
        )
        conn.commit()
        conn.close()

        store.init_db()  # runs the ALTER migration
        legacy = store.get_by_username("legacy")
        assert legacy is not None
        assert legacy.email is None
        assert legacy.email_verified is False


# ---------------------------------------------------------------------------
# signup module helpers
# ---------------------------------------------------------------------------


class TestSignupModule:
    def test_signup_enabled_reads_env(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_PUBLIC_SIGNUP", "true")
        assert signup.signup_enabled() is True
        monkeypatch.setenv("AIOPS_ENABLE_PUBLIC_SIGNUP", "false")
        assert signup.signup_enabled() is False
        monkeypatch.delenv("AIOPS_ENABLE_PUBLIC_SIGNUP", raising=False)
        assert signup.signup_enabled() is False

    def test_email_validation(self):
        assert signup.is_valid_email("a@b.co")
        assert not signup.is_valid_email("nope")
        assert not signup.is_valid_email("a@b")
        assert not signup.is_valid_email("")

    def test_captcha_disabled_passes(self, monkeypatch):
        monkeypatch.delenv("SIGNUP_CAPTCHA_PROVIDER", raising=False)
        assert signup.verify_captcha("anything", "1.2.3.4") is True

    def test_captcha_provider_without_secret_fails_closed(self, monkeypatch):
        monkeypatch.setenv("SIGNUP_CAPTCHA_PROVIDER", "turnstile")
        monkeypatch.delenv("SIGNUP_CAPTCHA_SECRET", raising=False)
        assert signup.verify_captcha("token", "1.2.3.4") is False

    def test_verify_token_roundtrip_and_tamper(self, signup_env):
        tok = signup.make_verify_token("user-id-1", "e@example.com")
        claims = signup.read_verify_token(tok)
        assert claims and claims["sub"] == "user-id-1"
        assert signup.read_verify_token("garbage") is None
        assert signup.read_verify_token(tok[:-2] + "zz") is None

    def test_send_email_without_smtp_logs_and_succeeds(self, monkeypatch):
        monkeypatch.delenv("SIGNUP_SMTP_HOST", raising=False)
        assert signup.send_verification_email("e@example.com", "tok") is True

    def test_public_config_shape(self, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_PUBLIC_SIGNUP", "true")
        monkeypatch.setenv("SIGNUP_CAPTCHA_PROVIDER", "hcaptcha")
        monkeypatch.setenv("SIGNUP_CAPTCHA_SITE_KEY", "sitekey123")
        cfg = signup.public_config()
        assert cfg == {
            "signup_enabled": True,
            "captcha_provider": "hcaptcha",
            "captcha_site_key": "sitekey123",
        }


# ---------------------------------------------------------------------------
# POST /signup + GET /verify routes
# ---------------------------------------------------------------------------


class TestSignupRoute:
    @pytest.mark.asyncio
    async def test_signup_disabled_is_404(self, signup_env, monkeypatch):
        monkeypatch.setenv("AIOPS_ENABLE_PUBLIC_SIGNUP", "false")
        with pytest.raises(HTTPException) as exc:
            await auth_routes.signup(_request(), _signup_body(), Response())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_signup_happy_path_creates_and_logs_in(self, signup_env):
        response = Response()
        result = await auth_routes.signup(_request(), _signup_body(), response)
        assert result["user"] == {"username": "newuser", "role": "user"}
        assert "expires_at" in result
        cookie = response.headers.get("set-cookie")
        assert cookie is not None and cookie.startswith("aiops_session=")
        assert "HttpOnly" in cookie
        # Persisted as a role=user with the email recorded, unverified.
        rec = store.get_by_username("newuser")
        assert rec.role == "user" and rec.email == "new@example.com"
        assert rec.email_verified is False

    @pytest.mark.asyncio
    async def test_signup_duplicate_username_conflict(self, signup_env):
        await auth_routes.signup(_request(), _signup_body(), Response())
        with pytest.raises(HTTPException) as exc:
            await auth_routes.signup(
                _request(), _signup_body(email="other@example.com"), Response()
            )
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_signup_invalid_email_rejected(self, signup_env):
        with pytest.raises(HTTPException) as exc:
            await auth_routes.signup(
                _request(), _signup_body(email="not-an-email"), Response()
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_throttled_per_ip(self, signup_env):
        ip = "203.0.113.42"
        for i in range(auth_routes.SIGNUP_MAX_PER_WINDOW):
            await auth_routes.signup(
                _request(ip=ip), _signup_body(username=f"u{i}", email=f"u{i}@example.com"), Response()
            )
        with pytest.raises(HTTPException) as exc:
            await auth_routes.signup(
                _request(ip=ip), _signup_body(username="blocked", email="b@example.com"), Response()
            )
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_invalid_email_attempts_count_toward_throttle(self, signup_env):
        # R4: a malformed-email probe must still be charged against the per-IP
        # window, otherwise the throttle is trivially bypassed by never sending
        # a valid email. After MAX bad attempts even a valid signup is locked.
        ip = "198.51.100.7"
        for _ in range(auth_routes.SIGNUP_MAX_PER_WINDOW):
            with pytest.raises(HTTPException) as bad:
                await auth_routes.signup(
                    _request(ip=ip), _signup_body(email="not-an-email"), Response()
                )
            assert bad.value.status_code == 400
        with pytest.raises(HTTPException) as locked:
            await auth_routes.signup(
                _request(ip=ip), _signup_body(email="ok@example.com"), Response()
            )
        assert locked.value.status_code == 429

    @pytest.mark.asyncio
    async def test_verify_marks_email_verified(self, signup_env):
        rec = store.create_user("v1", "a-long-password-1", email="v1@example.com")
        tok = signup.make_verify_token(rec.id, "v1@example.com")
        page = await auth_routes.verify_email(tok)
        assert isinstance(page, HTMLResponse) and page.status_code == 200
        assert store.get_by_username("v1").email_verified is True

    @pytest.mark.asyncio
    async def test_verify_bad_token_is_400(self, signup_env):
        page = await auth_routes.verify_email("garbage")
        assert isinstance(page, HTMLResponse) and page.status_code == 400
