"""
Constitutional AIOps - HMAC-signed session tokens (stdlib only).

Token format:  base64url(json_payload) + "." + base64url(hmac_sha256_signature)

The signature is computed over the base64url payload segment with a server
secret (AUTH_SECRET_KEY env, else an auto-generated key file under the app
data dir). Payload claims: {sub, name, role, tv, exp}. All comparisons are
constant-time; verification never raises — it returns None for anything that
is not a valid, unexpired, correctly-signed token.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any, Optional

from src.auth.store import UserRecord, data_dir

logger = logging.getLogger(__name__)

COOKIE_NAME = "aiops_session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

_SECRET_FILENAME = "auth_secret.key"


def _get_secret() -> bytes:
    """Return the signing secret: AUTH_SECRET_KEY env, else a generated file.

    The fallback file (${AIOPS_DATA_DIR}/auth_secret.key) is created with
    secrets.token_hex(32) on first use so restarts keep sessions valid without
    any operator action. Never commit it.
    """
    env_secret = os.environ.get("AUTH_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret.encode("utf-8")

    key_file = data_dir() / _SECRET_FILENAME
    try:
        if key_file.exists():
            existing = key_file.read_text(encoding="utf-8").strip()
            if existing:
                return existing.encode("utf-8")
        generated = secrets.token_hex(32)
        key_file.write_text(generated, encoding="utf-8")
        try:
            os.chmod(key_file, 0o600)
        except OSError:  # pragma: no cover - best-effort on Windows
            pass
        logger.info("Generated new auth secret key at %s", key_file)
        return generated.encode("utf-8")
    except OSError as exc:  # pragma: no cover - unwritable data dir
        # Last resort: a process-local secret (sessions die on restart) is
        # still safer than refusing all logins.
        logger.error("Cannot persist auth secret (%s); using process-local key", exc)
        return secrets.token_hex(32).encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def sign_session(user: UserRecord, ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    """Create a signed session token for a stored user."""
    claims = {
        "sub": user.id,
        "name": user.username,
        "role": user.role,
        "tv": user.token_version,
        "exp": int(time.time()) + int(ttl_seconds),
    }
    payload = _b64url_encode(
        json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(_get_secret(), payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_b64url_encode(signature)}"


def verify_session(token: str) -> Optional[dict[str, Any]]:
    """Verify a session token; return its claims dict, or None when invalid.

    Checks (in order): structure, signature (constant-time), JSON payload
    shape, and expiry. NOTE: token_version (tv) freshness against the user
    store is the caller's job (src/auth/deps.py) — this module is DB-free.
    """
    if not isinstance(token, str) or not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    payload_b64, signature_b64 = parts
    try:
        provided_sig = _b64url_decode(signature_b64)
    except (ValueError, TypeError):
        return None
    expected_sig = hmac.new(
        _get_secret(), payload_b64.encode("ascii", errors="replace"), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(expected_sig, provided_sig):
        return None
    try:
        claims = json.loads(_b64url_decode(payload_b64))
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or exp < time.time():
        return None
    if not isinstance(claims.get("sub"), str) or not isinstance(claims.get("name"), str):
        return None
    return claims


def sign_value(payload: dict[str, Any], ttl_seconds: int) -> str:
    """Sign an arbitrary short-lived payload with the same secret as sessions.

    Used for out-of-band links (e.g. email verification). The caller's dict is
    copied and stamped with an ``exp`` claim; read_value enforces it.
    """
    claims = dict(payload)
    claims["exp"] = int(time.time()) + int(ttl_seconds)
    encoded = _b64url_encode(
        json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(_get_secret(), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_b64url_encode(signature)}"


def read_value(token: str) -> Optional[dict[str, Any]]:
    """Verify a sign_value() token; return its claims or None (never raises)."""
    if not isinstance(token, str) or not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    payload_b64, signature_b64 = parts
    try:
        provided_sig = _b64url_decode(signature_b64)
    except (ValueError, TypeError):
        return None
    expected_sig = hmac.new(
        _get_secret(), payload_b64.encode("ascii", errors="replace"), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(expected_sig, provided_sig):
        return None
    try:
        claims = json.loads(_b64url_decode(payload_b64))
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or exp < time.time():
        return None
    return claims


__all__ = [
    "COOKIE_NAME",
    "SESSION_TTL_SECONDS",
    "read_value",
    "sign_session",
    "sign_value",
    "verify_session",
]
