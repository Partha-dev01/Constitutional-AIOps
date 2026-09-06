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


__all__ = ["verify", "send"]
