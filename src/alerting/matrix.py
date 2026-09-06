"""
Constitutional AIOps - Matrix Client-Server API adapter for remote alerting (Track 1).

RAW HTTP over the existing ``httpx`` dependency: NO ``matrix-nio`` (its value is
E2EE via libolm, a C-extension packaging burden not needed to post plaintext
alerts into a room). Only three Client-Server v3 calls are used:

  * ``GET  /_matrix/client/v3/account/whoami``                     -> ``verify``.
  * ``POST /_matrix/client/v3/rooms/{roomId}/join``                -> join once.
  * ``PUT  /_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}``
                                                                    -> deliver.

The homeserver is a USER-SUPPLIED URL, so every request is SSRF-guarded with the
same resolver the webhook uses (refuses loopback / private / link-local /
reserved, which blocks the cloud metadata endpoint and internal services). The
access token travels in an ``Authorization: Bearer`` header (never the URL).

Every function is best-effort and NEVER raises.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any
from urllib.parse import quote

import httpx

from src.notifications.webhook import webhook_target_error

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(5.0, connect=4.0)


def _base(homeserver: str) -> str:
    return homeserver.rstrip("/")


def _json(resp: httpx.Response) -> dict[str, Any]:
    try:
        data = resp.json()
    except Exception:  # noqa: BLE001
        return {}
    return data if isinstance(data, dict) else {}


def _err(data: dict[str, Any], status_code: int) -> str:
    """Prefer Matrix's ``errcode``/``error`` over a bare HTTP status."""
    errcode = str(data.get("errcode") or "").strip()
    error = str(data.get("error") or "").strip()
    if errcode and error:
        return f"{errcode}: {error}"
    return errcode or error or f"HTTP {status_code}"


def verify(homeserver: str, token: str) -> tuple[bool, str, str]:
    """Validate a homeserver + access token via ``whoami``. Returns ``(ok, detail, user_id)``."""
    homeserver = (homeserver or "").strip()
    token = (token or "").strip()
    if not homeserver or not token:
        return False, "matrix not configured", ""
    guard = webhook_target_error(homeserver)
    if guard is not None:
        return False, guard, ""
    url = f"{_base(homeserver)}/_matrix/client/v3/account/whoami"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.RequestError as exc:
        return False, f"unreachable ({type(exc).__name__})", ""
    except Exception as exc:  # noqa: BLE001
        return False, f"error ({type(exc).__name__})", ""
    data = _json(resp)
    if 200 <= resp.status_code < 300:
        return True, f"HTTP {resp.status_code}", str(data.get("user_id") or "")
    return False, _err(data, resp.status_code), ""


def _join(homeserver: str, token: str, room_id: str) -> bool:
    """Best-effort join (idempotent when already a member). True on success."""
    url = f"{_base(homeserver)}/_matrix/client/v3/rooms/{quote(room_id, safe='')}/join"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, headers={"Authorization": f"Bearer {token}"}, json={})
    except Exception:  # noqa: BLE001 - join is only a best-effort precondition
        return False
    return 200 <= resp.status_code < 300


def _send_once(
    homeserver: str, token: str, room_id: str, body: str
) -> tuple[bool, str, int, str]:
    """One PUT of an ``m.text`` event. Returns ``(ok, detail, status_code, errcode)``."""
    txn = uuid.uuid4().hex
    url = (
        f"{_base(homeserver)}/_matrix/client/v3/rooms/"
        f"{quote(room_id, safe='')}/send/m.room.message/{txn}"
    )
    payload = {"msgtype": "m.text", "body": body}
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.put(
                url, headers={"Authorization": f"Bearer {token}"}, json=payload
            )
    except httpx.RequestError as exc:
        return False, f"unreachable ({type(exc).__name__})", 0, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"error ({type(exc).__name__})", 0, ""
    data = _json(resp)
    if 200 <= resp.status_code < 300 and data.get("event_id"):
        return True, f"HTTP {resp.status_code}", resp.status_code, ""
    return (
        False,
        _err(data, resp.status_code),
        resp.status_code,
        str(data.get("errcode") or ""),
    )


def send(homeserver: str, token: str, room_id: str, body: str) -> tuple[bool, str]:
    """Send ``body`` as a plain ``m.text`` message to ``room_id``. Never raises.

    ``room_id`` must be an INTERNAL id (``!opaque:server``), not a ``#alias`` --
    aliases would need an extra resolve call and are rejected with a clear message.
    On a first-time membership rejection the adapter joins once and retries, so
    steady-state delivery is a single request.
    """
    homeserver = (homeserver or "").strip()
    token = (token or "").strip()
    room_id = (room_id or "").strip()
    if not homeserver or not token or not room_id:
        return False, "matrix not configured"
    if not room_id.startswith("!"):
        return False, "room id must be an internal id starting with '!', not a #alias"
    guard = webhook_target_error(homeserver)
    if guard is not None:
        return False, guard

    ok, detail, status_code, errcode = _send_once(homeserver, token, room_id, body)
    if ok:
        return True, detail
    # Not a member yet? Join once and retry (covers the very first alert to a room
    # the bot was invited to but has not yet joined).
    if errcode == "M_FORBIDDEN" or status_code in (403, 404):
        if _join(homeserver, token, room_id):
            ok, detail, _, _ = _send_once(homeserver, token, room_id, body)
    return ok, detail


__all__ = ["verify", "send"]
