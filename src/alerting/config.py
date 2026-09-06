"""
Constitutional AIOps - remote-alerting config: storage shape, redaction, targets.

The stored config lives under an ``alerting`` key, either in the system settings
file (self-host / AUTH off) or in an admin's ``user_settings`` row (multi-tenant),
exactly mirroring how ``src.notifications.webhook`` resolves its two tiers. Shape:

    {
      "telegram": {"enabled": bool, "botToken": "<enc>", "chatId": str,
                   "minSeverity": "info|warning|error|critical"},
      "matrix":   {"enabled": bool, "accessToken": "<enc>", "homeserver": str,
                   "roomId": str, "minSeverity": ...},
    }

Secrets (``botToken`` / ``accessToken``) are Fernet-encrypted at rest via
``src.auth.crypto`` and are NEVER returned by the API -- ``public_view`` reduces
each to a boolean "set" flag. ``apply_update`` writes with the same
null-leaves / ``""``-clears / value-sets convention the models BYOK key uses.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, NamedTuple, Optional

from src.auth import store as user_store
from src.auth.crypto import decrypt_secret, encrypt_secret
from src.notifications.webhook import SEVERITY_RANK

logger = logging.getLogger(__name__)

_DEFAULT_SEVERITY = "warning"


def _norm_sev(value: Any) -> str:
    v = str(value or "").strip().lower()
    return v if v in SEVERITY_RANK else _DEFAULT_SEVERITY


class TelegramTarget(NamedTuple):
    token: str
    chat_id: str
    min_severity: str


class MatrixTarget(NamedTuple):
    homeserver: str
    token: str
    room_id: str
    min_severity: str


# ---------------------------------------------------------------------------
# Stored dict -> resolved (decrypted) delivery target
# ---------------------------------------------------------------------------

def telegram_target(cfg: Any) -> Optional[TelegramTarget]:
    """Resolve an enabled+configured Telegram target, decrypting the token.

    None when disabled or missing a token / chat id.
    """
    if not isinstance(cfg, dict) or not cfg.get("enabled"):
        return None
    token = decrypt_secret((cfg.get("botToken") or "").strip())
    chat_id = (cfg.get("chatId") or "").strip()
    if not token or not chat_id:
        return None
    return TelegramTarget(token, chat_id, _norm_sev(cfg.get("minSeverity")))


def matrix_target(cfg: Any) -> Optional[MatrixTarget]:
    """Resolve an enabled+configured Matrix target, decrypting the access token."""
    if not isinstance(cfg, dict) or not cfg.get("enabled"):
        return None
    token = decrypt_secret((cfg.get("accessToken") or "").strip())
    homeserver = (cfg.get("homeserver") or "").strip()
    room_id = (cfg.get("roomId") or "").strip()
    if not token or not homeserver or not room_id:
        return None
    return MatrixTarget(homeserver, token, room_id, _norm_sev(cfg.get("minSeverity")))


# ---------------------------------------------------------------------------
# Two-tier resolution (system config + per-admin overrides), mirroring webhook
# ---------------------------------------------------------------------------

def _system_alerting() -> dict[str, Any]:
    """The system-wide ``alerting`` config (covers AUTH-off / self-host)."""
    try:
        from src.api.routes.settings import _load_persisted

        cfg = _load_persisted().get("alerting")
        return cfg if isinstance(cfg, dict) else {}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read system alerting config: %s", exc)
        return {}


def _iter_admin_alerting() -> Iterable[dict[str, Any]]:
    """Yield each admin's stored ``alerting`` dict, only when AUTH is required.

    Skipping the DB read while AUTH_REQUIRED is off keeps self-host (and the test
    suite) from touching users.db just to emit a notification -- same guard the
    webhook path uses.
    """
    from src.auth.deps import auth_required

    if not auth_required():
        return
    try:
        for user in user_store.list_users():
            if user.role != "admin":
                continue
            per_user = user_store.get_user_settings(user.id) or {}
            cfg = per_user.get("alerting")
            if isinstance(cfg, dict):
                yield cfg
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not enumerate per-user alerting targets: %s", exc)


def iter_telegram_targets() -> Iterable[TelegramTarget]:
    """Every enabled Telegram target (system + admin overrides), deduped by chat id."""
    seen: set[str] = set()
    system = telegram_target(_system_alerting().get("telegram"))
    if system and system.chat_id not in seen:
        seen.add(system.chat_id)
        yield system
    for cfg in _iter_admin_alerting():
        target = telegram_target(cfg.get("telegram"))
        if target and target.chat_id not in seen:
            seen.add(target.chat_id)
            yield target


def iter_matrix_targets() -> Iterable[MatrixTarget]:
    """Every enabled Matrix target (system + admin overrides), deduped by room."""
    seen: set[tuple[str, str]] = set()
    system = matrix_target(_system_alerting().get("matrix"))
    if system:
        key = (system.homeserver, system.room_id)
        if key not in seen:
            seen.add(key)
            yield system
    for cfg in _iter_admin_alerting():
        target = matrix_target(cfg.get("matrix"))
        if target:
            key = (target.homeserver, target.room_id)
            if key not in seen:
                seen.add(key)
                yield target


# ---------------------------------------------------------------------------
# API surface: stored dict <-> public (redacted) view, and update application
# ---------------------------------------------------------------------------

def public_view(alerting: Any) -> dict[str, Any]:
    """Redact a stored ``alerting`` dict for the API: tokens become boolean flags."""
    alerting = alerting if isinstance(alerting, dict) else {}
    tg = alerting.get("telegram") if isinstance(alerting.get("telegram"), dict) else {}
    mx = alerting.get("matrix") if isinstance(alerting.get("matrix"), dict) else {}
    return {
        "telegram": {
            "enabled": bool(tg.get("enabled")),
            "chatId": str(tg.get("chatId") or ""),
            "tokenSet": bool((tg.get("botToken") or "").strip()),
            "minSeverity": _norm_sev(tg.get("minSeverity")),
        },
        "matrix": {
            "enabled": bool(mx.get("enabled")),
            "homeserver": str(mx.get("homeserver") or ""),
            "roomId": str(mx.get("roomId") or ""),
            "accessTokenSet": bool((mx.get("accessToken") or "").strip()),
            "minSeverity": _norm_sev(mx.get("minSeverity")),
        },
    }


def _apply_secret(stored: dict[str, Any], key: str, incoming: Optional[str]) -> str:
    """Resolve the new stored (encrypted) secret: None leaves, "" clears, value sets."""
    if incoming is None:
        return str(stored.get(key) or "")  # leave the previously stored ciphertext
    return encrypt_secret(incoming)  # "" -> "" (cleared); any value -> enc::v1::…


def apply_update(existing: Any, incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge an incoming update onto the stored config, encrypting secrets.

    ``incoming`` is the dumped update model. Token fields are None (leave the
    stored token untouched), ``""`` (clear it) or a value (set it). Routing ids
    and toggles are replaced outright.
    """
    existing = existing if isinstance(existing, dict) else {}
    tg_old = existing.get("telegram") if isinstance(existing.get("telegram"), dict) else {}
    mx_old = existing.get("matrix") if isinstance(existing.get("matrix"), dict) else {}
    tg_in = incoming.get("telegram") or {}
    mx_in = incoming.get("matrix") or {}
    return {
        "telegram": {
            "enabled": bool(tg_in.get("enabled")),
            "chatId": str(tg_in.get("chatId") or "").strip(),
            "botToken": _apply_secret(tg_old, "botToken", tg_in.get("botToken")),
            "minSeverity": _norm_sev(tg_in.get("minSeverity")),
        },
        "matrix": {
            "enabled": bool(mx_in.get("enabled")),
            "homeserver": str(mx_in.get("homeserver") or "").strip(),
            "roomId": str(mx_in.get("roomId") or "").strip(),
            "accessToken": _apply_secret(mx_old, "accessToken", mx_in.get("accessToken")),
            "minSeverity": _norm_sev(mx_in.get("minSeverity")),
        },
    }


__all__ = [
    "TelegramTarget",
    "MatrixTarget",
    "telegram_target",
    "matrix_target",
    "iter_telegram_targets",
    "iter_matrix_targets",
    "public_view",
    "apply_update",
]
