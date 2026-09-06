"""
Constitutional AIOps - Outbound webhook delivery for notifications (Track 1).

The in-app notification inbox (``src.notifications.store``) is the single choke
point through which every operational alert flows. This module lets those alerts
ALSO be pushed to a user-configured webhook (Slack/Discord/generic), so an
operator does not have to be watching the app to hear about an incident.

Design constraints (carried from the inbox docstring):
  * NO background worker / poller / delivery daemon -- that would fight the
    sleep-when-idle deployment. Delivery is triggered in-request by ``notify()``
    and runs on a one-shot daemon thread that dies as soon as its POST returns.
  * Emitting a notification must NEVER break the request that triggered it, so
    every path here swallows its own errors.
  * SSRF-guarded exactly like the Settings "Send test" probe: the server refuses
    to POST to non-public addresses (loopback / private / link-local / reserved),
    which blocks the cloud metadata endpoint and internal services.

Scope: webhooks are resolved for ADMIN recipients only -- the same entitlement
as the notification inbox, which is admin-gated because these alerts describe the
operator's monitored infrastructure. This covers both tiers: the system-wide
config (AUTH_REQUIRED off / self-host) and each admin DB user's per-user override.
"""

import hashlib
import hmac
import ipaddress
import json
import logging
import socket
import threading
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import httpx

from src.auth import store as user_store

logger = logging.getLogger(__name__)

# Least -> most severe. A webhook's minimum-severity filter is compared on this
# scale, so "warning" delivers warning/error/critical but drops info.
SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2, "critical": 3}

_TIMEOUT = httpx.Timeout(4.0, connect=3.0)
_SIGNATURE_HEADER = "X-AIOPS-Signature"


def webhook_target_error(url: str) -> Optional[str]:
    """Return an error string if ``url`` is not a safe public http(s) target.

    None means the target looks safe to POST to. Resolves the host and rejects
    any address in a non-public range. (A determined attacker could still
    DNS-rebind between this check and the connect; this is defense-in-depth on
    top of the admin/ownership gate.)
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "URL must start with http:// or https://"
    host = parsed.hostname
    if not host:
        return "URL has no host"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return "host does not resolve"
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return "refusing to send to a non-public address"
    return None


def deliver(url: str, payload: dict[str, Any], secret: str = "") -> tuple[bool, str]:
    """POST ``payload`` as JSON to ``url`` (SSRF-guarded, blocking). Never raises.

    When ``secret`` is set, an ``X-AIOPS-Signature: sha256=<hex>`` header carries
    an HMAC-SHA256 of the exact request body so the recipient can authenticate it.
    Returns (ok, detail); ok is true only on a 2xx. Redirects are NOT followed.
    """
    guard = webhook_target_error(url)
    if guard is not None:
        return False, guard
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "Constitutional-AIOps"}
    if secret:
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers[_SIGNATURE_HEADER] = f"sha256={signature}"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, content=body, headers=headers)
    except httpx.RequestError as exc:
        return False, f"unreachable ({type(exc).__name__})"
    except Exception as exc:  # noqa: BLE001 - delivery must never raise
        return False, f"error ({type(exc).__name__})"
    return 200 <= resp.status_code < 300, f"HTTP {resp.status_code}"


def _target_from_config(cfg: dict[str, Any]) -> Optional[tuple[str, str, str]]:
    """Extract (url, secret, min_severity) from a notifications settings dict.

    None when the webhook is disabled or has no URL.
    """
    if not cfg.get("webhookEnabled"):
        return None
    url = (cfg.get("webhookUrl") or "").strip()
    if not url:
        return None
    secret = (cfg.get("webhookSecret") or "").strip()
    min_sev = cfg.get("webhookMinSeverity") or "warning"
    if min_sev not in SEVERITY_RANK:
        min_sev = "warning"
    return url, secret, min_sev


def _system_notifications() -> dict[str, Any]:
    """The system-wide notifications config (covers AUTH-off / self-host).

    Lazy import of the settings loaders keeps this module free of an import cycle
    (settings imports notifications.store, which imports this module).
    """
    try:
        from src.api.routes.settings import _load_persisted, _merge_with_defaults

        merged = _merge_with_defaults(_load_persisted())
        cfg = merged.get("notifications")
        return cfg if isinstance(cfg, dict) else {}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read system notifications config: %s", exc)
        return {}


def iter_webhook_targets() -> Iterable[tuple[str, str, str]]:
    """Yield (url, secret, min_severity) for every enabled, admin-entitled webhook.

    Deduped by URL so an admin whose per-user override mirrors the system URL is
    not double-sent. Never raises.
    """
    seen: set[str] = set()

    system_target = _target_from_config(_system_notifications())
    if system_target and system_target[0] not in seen:
        seen.add(system_target[0])
        yield system_target

    # Per-user admin overrides only exist in multi-tenant mode. Skipping the DB
    # read while AUTH_REQUIRED is off keeps self-host (and the test suite) from
    # ever touching users.db just to emit a notification.
    from src.auth.deps import auth_required

    if not auth_required():
        return

    try:
        for user in user_store.list_users():
            if user.role != "admin":
                continue
            per_user = user_store.get_user_settings(user.id) or {}
            cfg = per_user.get("notifications")
            if not isinstance(cfg, dict):
                continue
            target = _target_from_config(cfg)
            if target and target[0] not in seen:
                seen.add(target[0])
                yield target
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not enumerate per-user webhook targets: %s", exc)


def _fire(url: str, secret: str, payload: dict[str, Any]) -> None:
    """Deliver on a one-shot daemon thread (never blocks the caller)."""

    def _run() -> None:
        ok, detail = deliver(url, payload, secret)
        if not ok:
            logger.info("Webhook delivery to %s failed: %s", urlparse(url).hostname, detail)

    threading.Thread(target=_run, name="aiops-webhook", daemon=True).start()


def dispatch(note: dict[str, Any]) -> None:
    """Push a just-emitted notification to every entitled, severity-matching webhook.

    Called by ``notify()``. Fire-and-forget: returns immediately and never raises.
    Meta webhook.* notifications are skipped so a test/delivery event does not
    itself get forwarded.
    """
    try:
        ntype = str(note.get("type", ""))
        if ntype.startswith("webhook."):
            return
        note_rank = SEVERITY_RANK.get(str(note.get("severity", "info")), 0)
        payload = {
            "source": "Constitutional AIOps",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "event": note,
        }
        for url, secret, min_sev in iter_webhook_targets():
            if note_rank < SEVERITY_RANK.get(min_sev, 1):
                continue
            _fire(url, secret, payload)
    except Exception as exc:  # noqa: BLE001 - dispatch is never load-bearing
        logger.debug("Webhook dispatch skipped: %s", exc)


__all__ = [
    "SEVERITY_RANK",
    "deliver",
    "dispatch",
    "iter_webhook_targets",
    "webhook_target_error",
]
