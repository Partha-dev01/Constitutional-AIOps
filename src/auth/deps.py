"""
Constitutional AIOps - FastAPI auth dependencies.

require_user honours the AUTH_REQUIRED rollout flag:

* AUTH_REQUIRED unset/false (default): every request gets a SYNTHETIC admin
  user (no DB or token check at all) — zero behavior change until the flag
  flips.
* AUTH_REQUIRED true: a valid session token is mandatory (httpOnly cookie
  ``aiops_session`` first, ``Authorization: Bearer <token>`` fallback) and a
  token whose ``tv`` claim no longer matches users.token_version is rejected.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi import Depends as _Depends

from src.auth import pat, store
from src.auth.tokens import COOKIE_NAME, verify_session

logger = logging.getLogger(__name__)

# Sentinel id for the synthetic pre-rollout admin (never a real DB id: real
# ids are uuid4 hexes).
SYNTHETIC_USER_ID = "__synthetic__"

_TRUTHY = ("1", "true", "yes", "on")


@dataclass(frozen=True)
class User:
    """Minimal authenticated-identity model passed to route handlers."""

    id: str
    username: str
    role: str


def auth_required() -> bool:
    """Is in-app auth enforcement enabled? (AUTH_REQUIRED env, default false)."""
    return os.environ.get("AUTH_REQUIRED", "").strip().lower() in _TRUTHY


def synthetic_admin() -> User:
    """The stand-in admin used while AUTH_REQUIRED is off."""
    username = os.environ.get("AUTH_ADMIN_USER", "").strip() or "admin"
    return User(id=SYNTHETIC_USER_ID, username=username, role="admin")


def is_synthetic(user: User) -> bool:
    """True for the pre-rollout synthetic admin (not a real DB user)."""
    return user.id == SYNTHETIC_USER_ID


def coerce_user(value: object) -> User:
    """Normalise the ``user`` route parameter to a real User instance.

    Route functions declare ``user: User = Depends(require_user)``; when the
    suite calls them DIRECTLY (the established test pattern — no FastAPI DI),
    the default is the Depends marker object. Coerce anything that is not a
    User into the synthetic admin, mirroring the AUTH_REQUIRED=false default.
    """
    if isinstance(value, User):
        return value
    return synthetic_admin()


def _token_from_request(request: Request) -> Optional[str]:
    """Extract the session token: cookie first, then Authorization: Bearer."""
    token: Optional[str] = None
    try:
        token = request.cookies.get(COOKIE_NAME)
    except Exception:  # noqa: BLE001 - tolerate mock/partial request objects
        token = None
    if token:
        return token
    header: Optional[str] = None
    try:
        header = request.headers.get("authorization")
    except Exception:  # noqa: BLE001
        header = None
    if header and header.lower().startswith("bearer "):
        candidate = header[7:].strip()
        if candidate:
            return candidate
    return None


def get_current_user(request: Request) -> Optional[User]:
    """Resolve the real user for this request, or None.

    Valid means: well-formed + correctly signed + unexpired token AND the
    user still exists AND the token's tv matches users.token_version (so
    "log out everywhere" / password changes invalidate old sessions).
    """
    token = _token_from_request(request)
    if not token:
        return None
    # Personal access tokens are namespaced by prefix, so a PAT and an HMAC
    # session token never collide. Resolve PATs against the access_tokens store
    # (revocation = row deletion; unaffected by token_version bumps).
    if pat.is_pat(token):
        user_id = pat.resolve_user_id(token)
        if user_id is None:
            return None
        record = store.get_by_id(user_id)
        if record is None:
            return None
        return User(id=record.id, username=record.username, role=record.role)
    claims = verify_session(token)
    if claims is None:
        return None
    record = store.get_by_username(str(claims.get("name", "")))
    if record is None:
        return None
    if record.id != claims.get("sub"):
        return None
    if record.token_version != claims.get("tv"):
        return None
    # Role comes from the DB row (authoritative), not the token claim.
    return User(id=record.id, username=record.username, role=record.role)


async def require_user(request: Request) -> User:
    """FastAPI dependency: the calling user (synthetic admin pre-rollout)."""
    if not auth_required():
        return synthetic_admin()
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(user: User = _Depends(require_user)) -> User:
    """FastAPI dependency: like require_user but admin-only (403 otherwise)."""
    user = coerce_user(user)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


__all__ = [
    "SYNTHETIC_USER_ID",
    "User",
    "auth_required",
    "coerce_user",
    "get_current_user",
    "is_synthetic",
    "require_admin",
    "require_user",
    "synthetic_admin",
]
