"""
Constitutional AIOps - inbound ChatOps binding resolution (Track 1 T1d/T1e).

Outbound alerting (telegram.py / matrix.py / config.py) fans a notification OUT
to a chat. This module is the reverse edge: given a message that arrived FROM a
chat (relayed in by the off-box Lambda), find which app user it belongs to and
the credentials to reply with - so a remote operator can drive the box from
Telegram/Matrix.

Security model (why a stranger who finds the bot cannot drive someone's box):
  * Inbound is OPT-IN per binding: a stored channel config only resolves when its
    ``inboundEnabled`` flag is set. Enabling it is an admin action.
  * The binding key is opaque: Telegram inbound is addressed by a generated
    ``routingId`` (not the guessable chat id), and the Lambda additionally checks
    a per-binding webhook secret before it ever forwards.
  * The reply always goes back to the STORED chat/room, never to an arbitrary
    sender - so even a spoofed relay payload can only ever talk to the owner's
    own configured chat.

The stored config is the same ``alerting`` dict outbound uses (system settings
file for self-host, or an admin's ``user_settings`` row for multi-tenant), with
three inbound-only telegram fields added: ``inboundEnabled`` (bool),
``routingId`` (opaque str), ``webhookSecret`` (Fernet-encrypted; the value
Telegram echoes as ``X-Telegram-Bot-Api-Secret-Token``).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterable, NamedTuple, Optional

from src.auth import store as user_store
from src.auth.crypto import decrypt_secret

logger = logging.getLogger(__name__)

# Public HTTPS base of this deployment's inbound webhook edge (the API Gateway /
# relay front, e.g. https://<api-id>.execute-api.<region>.amazonaws.com). The box
# ``.env`` carries it as AIOPS_RELAY_PUBLIC_URL. Empty on a plain self-host with
# no off-box relay: webhook auto-registration is then skipped (the admin can
# register a webhook to their own always-on endpoint out-of-band).
_RELAY_PUBLIC_URL_ENV = "AIOPS_RELAY_PUBLIC_URL"


class InboundBinding(NamedTuple):
    owner_id: str        # "" for the system/self-host config, else the admin user id
    channel: str         # "telegram" | "matrix"
    reply_token: str     # decrypted bot/access token used to reply
    reply_target: str    # chat_id (telegram) or room_id (matrix)
    homeserver: str      # matrix only ("" for telegram)
    routing_id: str
    webhook_secret: str  # decrypted (telegram); "" otherwise


def _system_alerting() -> dict[str, Any]:
    try:
        from src.api.routes.settings import _load_persisted

        cfg = _load_persisted().get("alerting")
        return cfg if isinstance(cfg, dict) else {}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read system alerting config: %s", exc)
        return {}


def iter_configs() -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield ``(owner_id, alerting_dict)`` for the system config then each admin.

    ``owner_id`` is "" for the system/self-host config. Admin rows are only read
    when AUTH is required (self-host / tests never touch users.db for this), the
    same guard the outbound path uses.
    """
    system = _system_alerting()
    if system:
        yield "", system
    try:
        from src.auth.deps import auth_required

        if not auth_required():
            return
        for user in user_store.list_users():
            if user.role != "admin":
                continue
            per_user = user_store.get_user_settings(user.id) or {}
            cfg = per_user.get("alerting")
            if isinstance(cfg, dict):
                yield user.id, cfg
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not enumerate inbound bindings: %s", exc)


def _telegram_binding(owner_id: str, tg: Any) -> Optional[InboundBinding]:
    if not isinstance(tg, dict) or not tg.get("inboundEnabled"):
        return None
    routing_id = str(tg.get("routingId") or "").strip()
    token = decrypt_secret((tg.get("botToken") or "").strip())
    chat_id = str(tg.get("chatId") or "").strip()
    if not routing_id or not token or not chat_id:
        return None
    return InboundBinding(
        owner_id=owner_id,
        channel="telegram",
        reply_token=token,
        reply_target=chat_id,
        homeserver="",
        routing_id=routing_id,
        webhook_secret=decrypt_secret((tg.get("webhookSecret") or "").strip()),
    )


def resolve_telegram(routing_id: str) -> Optional[InboundBinding]:
    """Find the opted-in Telegram binding for an opaque ``routing_id``.

    None when no config has inbound enabled for that id. The reply always targets
    the STORED chat id, so this can never be steered to talk to a stranger.
    """
    routing_id = (routing_id or "").strip()
    if not routing_id:
        return None
    for owner_id, cfg in iter_configs():
        binding = _telegram_binding(owner_id, cfg.get("telegram"))
        if binding is not None and binding.routing_id == routing_id:
            return binding
    return None


def resolve(channel: str, routing_id: str) -> Optional[InboundBinding]:
    """Resolve a binding for a channel. Telegram is wired (T1d); Matrix (T1e) is
    reserved (its inbound side is an Application Service / scheduled poll, built
    separately)."""
    if (channel or "").strip().lower() == "telegram":
        return resolve_telegram(routing_id)
    return None


def mirror_entries() -> list[dict[str, Any]]:
    """The off-box relay's binding/allowlist mirror rows (one per opted-in Telegram
    binding). The Lambda reads these to authenticate the Telegram webhook and map a
    ``routingId`` to an owner BEFORE it wakes the box - so it never has to reach a
    sleeping box just to reject spam. Secrets are the ones the relay itself needs
    (the Telegram webhook secret); the bot token stays on the box."""
    rows: list[dict[str, Any]] = []
    for owner_id, cfg in iter_configs():
        tg = cfg.get("telegram")
        binding = _telegram_binding(owner_id, tg)
        if binding is None:
            continue
        rows.append(
            {
                "routingId": binding.routing_id,
                "channel": "telegram",
                "ownerId": owner_id,
                "webhookSecret": binding.webhook_secret,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Webhook auto-registration (T1d): the piece that makes a valid bot token "just
# work". Enabling inbound already generates a routingId + webhookSecret and mirrors
# them to DynamoDB; this tells TELEGRAM to deliver to our edge at that routingId,
# echoing the webhookSecret. Without it a correct token receives nothing.
# ---------------------------------------------------------------------------


def public_relay_base() -> str:
    """The deployment's public webhook edge base URL, or "" when none is set."""
    return (os.environ.get(_RELAY_PUBLIC_URL_ENV, "") or "").strip().rstrip("/")


def public_webhook_url(routing_id: str) -> str:
    """Full Telegram webhook URL for a routingId (``<base>/telegram/<routingId>``).

    "" when no relay base is configured or the routingId is blank. The relay only
    reads the LAST path segment as the routingId, so a stage prefix is irrelevant.
    """
    base = public_relay_base()
    routing_id = (routing_id or "").strip()
    if not base or not routing_id:
        return ""
    return f"{base}/telegram/{routing_id}"


def sync_telegram_webhook(old_tg: Any, new_tg: Any) -> tuple[str, str]:
    """Reconcile the bot's Telegram webhook to a just-saved telegram config.

    Registers the webhook when inbound is enabled and fully configured, removes it
    on a real on->off transition, and no-ops otherwise. Returns ``(action, detail)``
    with ``action`` in {registered, removed, skipped, failed}. Best-effort: never
    raises (a webhook call must never break saving alerting settings).
    """
    from src.alerting import telegram as telegram_adapter

    new_tg = new_tg if isinstance(new_tg, dict) else {}
    old_tg = old_tg if isinstance(old_tg, dict) else {}
    now_on = bool(new_tg.get("inboundEnabled"))
    was_on = bool(old_tg.get("inboundEnabled"))
    token = decrypt_secret((new_tg.get("botToken") or "").strip())

    if now_on:
        base = public_relay_base()
        if not base:
            return "skipped", f"{_RELAY_PUBLIC_URL_ENV} not set"
        routing_id = str(new_tg.get("routingId") or "").strip()
        secret = decrypt_secret((new_tg.get("webhookSecret") or "").strip())
        if not token or not routing_id or not secret:
            return "skipped", "telegram inbound not fully configured"
        ok, detail = telegram_adapter.set_webhook(
            token,
            f"{base}/telegram/{routing_id}",
            secret_token=secret,
            drop_pending_updates=True,
        )
        return ("registered" if ok else "failed"), detail

    # Inbound now off: only actively deregister on a real on->off flip (and only
    # while we still hold a token to call with). A never-enabled save is a no-op.
    if was_on and token:
        ok, detail = telegram_adapter.delete_webhook(token, drop_pending_updates=True)
        return ("removed" if ok else "failed"), detail
    return "skipped", "inbound disabled"


__all__ = [
    "InboundBinding",
    "iter_configs",
    "mirror_entries",
    "public_relay_base",
    "public_webhook_url",
    "resolve",
    "resolve_telegram",
    "sync_telegram_webhook",
]
