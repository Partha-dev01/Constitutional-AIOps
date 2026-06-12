"""
Constitutional AIOps - Auth API Routes.

Login/logout/session endpoints plus admin-only user management. The session
travels as the httpOnly ``aiops_session`` cookie (Authorization: Bearer is
accepted as a fallback by the dependency layer).

Public (no auth):  POST /login, GET /config
Authed:            GET /me, POST /logout
Admin-only:        GET /users, POST /users, DELETE /users/{username},
                   POST /users/{username}/password

NOTE: login deliberately takes a JSON body (NOT OAuth2PasswordRequestForm,
which would require python-multipart — absent from the minimal CI install).
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from src.auth import store
from src.auth.deps import (
    User,
    auth_required,
    coerce_user,
    get_current_user,
    is_synthetic,
    require_admin,
    require_user,
)
from src.auth.tokens import COOKIE_NAME, SESSION_TTL_SECONDS, sign_session

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Login throttle: per-IP, 5 failures -> locked for 15 minutes (stdlib dict of
# failure timestamps; a successful login clears the caller's slate).
# ---------------------------------------------------------------------------

THROTTLE_MAX_FAILURES = 5
THROTTLE_WINDOW_SECONDS = 15 * 60

_failed_logins: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    """First IP of x-forwarded-for (Caddy fronts the app), else client.host."""
    forwarded = ""
    try:
        forwarded = request.headers.get("x-forwarded-for") or ""
    except Exception:  # noqa: BLE001 - tolerate mock/partial request objects
        forwarded = ""
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return host if isinstance(host, str) and host else "unknown"


def _recent_failures(ip: str, now: float) -> list[float]:
    cutoff = now - THROTTLE_WINDOW_SECONDS
    recent = [t for t in _failed_logins.get(ip, []) if t > cutoff]
    if recent:
        _failed_logins[ip] = recent
    else:
        _failed_logins.pop(ip, None)
    return recent


def _is_locked(ip: str, now: float) -> bool:
    return len(_recent_failures(ip, now)) >= THROTTLE_MAX_FAILURES


def _record_failure(ip: str, now: float) -> None:
    _failed_logins.setdefault(ip, []).append(now)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    everywhere: bool = False


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=512)
    role: str = Field("user", pattern="^(user|admin)$")


class PasswordChangeRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=512)


def _public_user(username: str, role: str) -> dict[str, str]:
    return {"username": username, "role": role}


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    summary="Log in",
    description="Verify credentials, set the httpOnly session cookie, return the user.",
)
async def login(request: Request, body: LoginRequest, response: Response) -> dict[str, Any]:
    ip = _client_ip(request)
    now = time.time()
    if _is_locked(ip, now):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 15 minutes.",
        )

    record = store.authenticate(body.username, body.password)
    if record is None:
        _record_failure(ip, now)
        logger.info("Failed login for username=%r from ip=%s", body.username, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    _failed_logins.pop(ip, None)
    token = sign_session(record)
    expires_at = datetime.fromtimestamp(now + SESSION_TTL_SECONDS, tz=timezone.utc)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    logger.info("User %s logged in from ip=%s", record.username, ip)
    return {
        "user": _public_user(record.username, record.role),
        "expires_at": expires_at.isoformat(),
    }


@router.post(
    "/logout",
    summary="Log out",
    description="Clear the session cookie; body {everywhere:true} also invalidates every session.",
)
async def logout(
    request: Request,
    response: Response,
    body: Optional[LogoutRequest] = None,
) -> dict[str, Any]:
    everywhere = bool(body and body.everywhere)
    if everywhere:
        current = get_current_user(request)
        if current is not None and not is_synthetic(current):
            store.bump_token_version(current.username)
            logger.info("User %s logged out everywhere", current.username)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True, "everywhere": everywhere}


@router.get(
    "/me",
    summary="Current user",
    description="Return the calling user (synthetic admin while AUTH_REQUIRED is off).",
)
async def me(user: User = Depends(require_user)) -> dict[str, str]:
    user = coerce_user(user)
    return _public_user(user.username, user.role)


@router.get(
    "/config",
    summary="Auth config (public)",
    description="Whether in-app auth is enforced. Public: the SPA needs it pre-login.",
)
async def get_auth_config() -> dict[str, bool]:
    return {"auth_required": auth_required()}


# ---------------------------------------------------------------------------
# Admin-only user management
# ---------------------------------------------------------------------------


@router.get(
    "/users",
    summary="List users (admin)",
)
async def admin_list_users(admin: User = Depends(require_admin)) -> dict[str, Any]:
    admin = coerce_user(admin)
    users = store.list_users()
    return {
        "items": [
            {
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Create user (admin)",
)
async def admin_create_user(
    body: UserCreateRequest, admin: User = Depends(require_admin)
) -> dict[str, str]:
    admin = coerce_user(admin)
    try:
        record = store.create_user(body.username, body.password, role=body.role)
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "already exists" in detail
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail) from exc
    logger.info("Admin %s created user %s (role=%s)", admin.username, record.username, record.role)
    return _public_user(record.username, record.role)


@router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (admin)",
)
async def admin_delete_user(
    username: str, admin: User = Depends(require_admin)
) -> None:
    admin = coerce_user(admin)
    if username == admin.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    if not store.delete_user(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )
    logger.info("Admin %s deleted user %s", admin.username, username)


@router.post(
    "/users/{username}/password",
    summary="Set a user's password (admin)",
)
async def admin_set_password(
    username: str, body: PasswordChangeRequest, admin: User = Depends(require_admin)
) -> dict[str, Any]:
    admin = coerce_user(admin)
    try:
        changed = store.set_password(username, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    if not changed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )
    logger.info("Admin %s set a new password for %s", admin.username, username)
    return {"ok": True}


__all__ = ["router"]
