"""
Constitutional AIOps - Telegram Bot API adapter for remote alerting (Track 1).

RAW HTTP over the existing ``httpx`` dependency: NO ``python-telegram-bot`` (it
bundles an async application/job-queue framework that fights this sync,
in-request, no-daemon delivery path). Only two Bot API methods are used:

  * ``getMe``      -> ``verify`` a bot token (Settings "Test").
  * ``sendMessage``-> deliver an alert to a chat.

All calls go to the FIXED host ``api.telegram.org`` (so there is no SSRF surface
here, unlike the user-supplied Matrix homeserver). The bot token travels in the
URL PATH, so this module is careful to never log a URL or an exception that could
embed it -- only the method, HTTP status and Telegram's own ``description``.

Every function is best-effort and NEVER raises: a delivery failure must not break
the request that triggered the alert.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"
_TIMEOUT = httpx.Timeout(5.0, connect=4.0)


def _post(token: str, method: str, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """POST a Bot API ``method`` and normalise the ``{ok, result, description}`` reply.

    Returns ``(ok, detail, data)``. ``ok`` is true only on a 2xx whose body has
    ``ok: true``. ``detail`` carries Telegram's ``description`` on a logical error
    (e.g. "chat not found", "Unauthorized") or an ``HTTP <code>`` / transport
    reason otherwise. Never raises; never echoes the token.
    """
    url = f"{_API_BASE}/bot{token}/{method}"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, json=payload)
    except httpx.RequestError as exc:
        return False, f"unreachable ({type(exc).__name__})", {}
    except Exception as exc:  # noqa: BLE001 - a delivery must never raise
        return False, f"error ({type(exc).__name__})", {}
    try:
        data = resp.json()
    except Exception:  # noqa: BLE001 - a non-JSON body is just a failure
        data = {}
    if not isinstance(data, dict):
        data = {}
    if 200 <= resp.status_code < 300 and data.get("ok"):
        return True, f"HTTP {resp.status_code}", data
    detail = str(data.get("description") or "").strip()
    return False, detail or f"HTTP {resp.status_code}", data


def verify(token: str) -> tuple[bool, str, str]:
    """Validate a bot token via ``getMe``. Returns ``(ok, detail, bot_username)``."""
    token = (token or "").strip()
    if not token:
        return False, "no bot token", ""
    ok, detail, data = _post(token, "getMe", {})
    username = ""
    result = data.get("result")
    if ok and isinstance(result, dict):
        username = str(result.get("username") or "")
    return ok, detail, username


def send(token: str, chat_id: str, text: str, *, html: bool = True) -> tuple[bool, str]:
    """Send ``text`` to ``chat_id``. Returns ``(ok, detail)``. Never raises.

    ``chat_id`` may be a numeric id or an ``@channelusername`` -- both are passed
    through verbatim. With ``html`` (default) the text is sent as
    ``parse_mode="HTML"``; the caller is responsible for escaping dynamic values
    (see ``render.to_telegram_html``).
    """
    token = (token or "").strip()
    chat_id = (chat_id or "").strip()
    if not token or not chat_id:
        return False, "telegram not configured"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if html:
        payload["parse_mode"] = "HTML"
    ok, detail, _ = _post(token, "sendMessage", payload)
    return ok, detail


# ---------------------------------------------------------------------------
# Webhook lifecycle (inbound ChatOps, T1d): register the bot with Telegram so it
# delivers each message to our off-box relay edge. Without this a valid bot token
# still receives NOTHING - Telegram must be told the URL. Registration is what
# makes "any user's proper token just works" true, so it runs automatically when
# an admin enables inbound (src/alerting/inbound.sync_telegram_webhook).
# ---------------------------------------------------------------------------

# Only the update types the relay actually handles (see aws/lambda/relay
# _extract_message + src/api/routes/relay). Keeping this narrow means Telegram
# never wakes the box for reactions/joins/channel posts the relay would drop.
_DEFAULT_ALLOWED_UPDATES = ["message", "edited_message"]


def set_webhook(
    token: str,
    url: str,
    *,
    secret_token: str = "",
    allowed_updates: list[str] | None = None,
    drop_pending_updates: bool = False,
) -> tuple[bool, str]:
    """Point the bot's webhook at ``url`` (Bot API ``setWebhook``). Returns ``(ok, detail)``.

    ``url`` must be HTTPS on a Telegram-supported port (443/80/88/8443). When
    ``secret_token`` is set Telegram echoes it back in every delivery as the
    ``X-Telegram-Bot-Api-Secret-Token`` header, which the off-box relay checks
    before it will act (or wake the box). The secret_token alphabet Telegram
    accepts (``A-Z a-z 0-9 _ -``, 1-256 chars) is exactly what
    ``secrets.token_urlsafe`` produces, so our stored webhookSecret is passed
    through verbatim. Best-effort; never raises; never echoes the token.
    """
    token = (token or "").strip()
    url = (url or "").strip()
    if not token or not url:
        return False, "telegram webhook not configured"
    payload: dict[str, Any] = {
        "url": url,
        "allowed_updates": allowed_updates or _DEFAULT_ALLOWED_UPDATES,
    }
    if secret_token:
        payload["secret_token"] = secret_token
    if drop_pending_updates:
        payload["drop_pending_updates"] = True
    ok, detail, _ = _post(token, "setWebhook", payload)
    return ok, detail


def delete_webhook(token: str, *, drop_pending_updates: bool = False) -> tuple[bool, str]:
    """Remove the bot's webhook (Bot API ``deleteWebhook``). Returns ``(ok, detail)``.

    Idempotent: Telegram returns ``ok: true`` even when no webhook was set, so
    calling this on an on->off inbound toggle is always safe.
    """
    token = (token or "").strip()
    if not token:
        return False, "no bot token"
    payload: dict[str, Any] = {}
    if drop_pending_updates:
        payload["drop_pending_updates"] = True
    ok, detail, _ = _post(token, "deleteWebhook", payload)
    return ok, detail


def webhook_info(token: str) -> tuple[bool, str, dict[str, Any]]:
    """Current webhook status (Bot API ``getWebhookInfo``). Returns ``(ok, detail, result)``.

    ``result`` carries Telegram's WebhookInfo (``url``, ``pending_update_count``,
    ``last_error_message`` ...) so a caller can confirm registration or surface a
    delivery error. ``{}`` on any failure.
    """
    token = (token or "").strip()
    if not token:
        return False, "no bot token", {}
    ok, detail, data = _post(token, "getWebhookInfo", {})
    result = data.get("result")
    return ok, detail, result if isinstance(result, dict) else {}


__all__ = ["verify", "send", "set_webhook", "delete_webhook", "webhook_info"]
