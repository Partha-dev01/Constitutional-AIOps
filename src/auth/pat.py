"""
Constitutional AIOps - Personal access tokens (stdlib only).

A PAT is a long-lived bearer credential a user creates to authenticate the
REST API / the SDK without a browser session. The plaintext is shown once at
creation; only its SHA-256 hash is stored (``src/auth/store.py`` access_tokens
table). Tokens are namespaced with a fixed prefix so the auth layer can tell a
PAT apart from an HMAC session token by inspection alone.

This module deliberately does NOT import ``src.auth.deps`` (which imports this
module): resolution returns a bare ``user_id`` string and the caller builds the
``User``. Verification never raises — it returns None for anything invalid.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple

from src.auth import store

logger = logging.getLogger(__name__)

PAT_PREFIX = "aiops_pat_"
# Prefix stored/displayed so an owner can identify a token in a listing without
# revealing it: the namespace plus the first 6 chars of the random body.
_DISPLAY_PREFIX_LEN = len(PAT_PREFIX) + 6


def hash_token(plaintext: str) -> str:
    """SHA-256 hex digest of a token. Same function used at create and verify."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def is_pat(token: str) -> bool:
    """True when ``token`` looks like one of our access tokens (by prefix)."""
    return isinstance(token, str) and token.startswith(PAT_PREFIX)


def generate() -> Tuple[str, str, str]:
    """Mint a fresh token. Returns (plaintext, token_hash, display_prefix).

    Only the caller ever sees the plaintext; the store keeps the hash + prefix.
    """
    plaintext = PAT_PREFIX + secrets.token_urlsafe(32)
    return plaintext, hash_token(plaintext), plaintext[:_DISPLAY_PREFIX_LEN]


def _is_expired(expires_at: Optional[str], now: datetime) -> bool:
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(expires_at)
    except ValueError:  # pragma: no cover - stored value is always isoformat
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp <= now


def resolve_user_id(token: str) -> Optional[str]:
    """Validate a presented PAT and return the owning user_id, or None.

    Rejects unknown, malformed, and expired tokens. On success, best-effort
    stamps ``last_used_at`` (throttled to at most once per minute to avoid a DB
    write on every API call).
    """
    if not is_pat(token):
        return None
    record = store.get_access_token_by_hash(hash_token(token))
    if record is None:
        return None
    now = datetime.now(timezone.utc)
    if _is_expired(record.expires_at, now):
        return None
    _maybe_touch(record, now)
    return record.user_id


def _maybe_touch(record: store.AccessTokenRecord, now: datetime) -> None:
    """Update last_used_at at most once per minute (write-amplification guard)."""
    last = record.last_used_at
    if last:
        try:
            prev = datetime.fromisoformat(last)
            if prev.tzinfo is None:
                prev = prev.replace(tzinfo=timezone.utc)
            if (now - prev).total_seconds() < 60:
                return
        except ValueError:  # pragma: no cover
            pass
    store.touch_access_token(record.id, now.isoformat())


__all__ = [
    "PAT_PREFIX",
    "generate",
    "hash_token",
    "is_pat",
    "resolve_user_id",
]
