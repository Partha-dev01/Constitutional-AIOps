"""
Constitutional AIOps - Notification inbox (in-app alert center).

Records notify-worthy events -- an action awaiting approval, an action the
constitutional validator blocked, a webhook test -- so the UI can show WHAT
fired, not just which channels Settings has configured. This closes the gap
where Settings -> Notifications wired up channels but nothing surfaced the
alerts in the app itself.

Design constraints (see the 5e brainstorm):
  * Fired SYNCHRONOUSLY in-request only. There is NO background worker, poller,
    or delivery daemon -- that would fight the sleep-when-idle deployment.
  * Emitting a notification must NEVER break the request that triggered it, so
    every disk operation is best-effort and swallows its own errors.

Persistence is a single small JSON file holding a bounded, newest-first list.
A flat file (not the append-only JSONL the audit trail uses) is deliberate:
the inbox needs mutable read-state (mark-read) and a clear operation, which an
append-only log does not express cleanly. The list is capped so the file stays
tiny and the whole thing loads/saves in well under a millisecond.
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Allowed severities, ordered least -> most severe. Anything else is coerced to
# "info" so a bad caller can never inject an arbitrary style class downstream.
NOTIFICATION_SEVERITIES = ("info", "warning", "error", "critical")

# Keep the inbox bounded. Old alerts fall off the end once this many accumulate.
_DEFAULT_MAX_ITEMS = 200


class Notification:
    """A single inbox entry. Plain data; serialised to/from the JSON file."""

    __slots__ = (
        "id",
        "timestamp",
        "type",
        "severity",
        "title",
        "message",
        "source",
        "resource_id",
        "read",
    )

    def __init__(
        self,
        *,
        type: str,
        severity: str,
        title: str,
        message: str,
        source: str = "system",
        resource_id: Optional[str] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        read: bool = False,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.type = type
        self.severity = severity if severity in NOTIFICATION_SEVERITIES else "info"
        self.title = title
        self.message = message
        self.source = source
        self.resource_id = resource_id
        self.read = bool(read)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "resource_id": self.resource_id,
            "read": self.read,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        return cls(
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            type=data.get("type", "system"),
            severity=data.get("severity", "info"),
            title=data.get("title", ""),
            message=data.get("message", ""),
            source=data.get("source", "system"),
            resource_id=data.get("resource_id"),
            read=bool(data.get("read", False)),
        )


class NotificationStore:
    """Bounded, newest-first, file-backed notification inbox."""

    def __init__(
        self,
        path: Optional[Path] = None,
        max_items: int = _DEFAULT_MAX_ITEMS,
    ) -> None:
        base = Path(path) if path else Path(os.getenv("AIOPS_NOTIFICATIONS_DIR", "logs/notifications"))
        self._file = base / "notifications.json"
        self._max_items = max_items
        self._lock = threading.Lock()
        self._items: list[Notification] = []
        self._load()
        logger.info("NotificationStore initialized, file=%s", self._file)

    # -- persistence (best-effort; never raises) ---------------------------

    def _load(self) -> None:
        try:
            if self._file.exists():
                raw = json.loads(self._file.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    self._items = [Notification.from_dict(d) for d in raw if isinstance(d, dict)]
        except Exception as exc:  # noqa: BLE001 - a bad file must not crash boot
            logger.warning("Could not load notifications from %s: %s", self._file, exc)
            self._items = []

    def _persist_locked(self) -> None:
        """Write the current list. Caller holds the lock. Never raises."""
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            payload = [n.to_dict() for n in self._items]
            tmp = self._file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            tmp.replace(self._file)
        except Exception as exc:  # noqa: BLE001 - persistence is a nicety
            logger.warning("Could not persist notifications to %s: %s", self._file, exc)

    # -- mutations ---------------------------------------------------------

    def add(
        self,
        *,
        type: str,
        severity: str,
        title: str,
        message: str,
        source: str = "system",
        resource_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Record a notification (newest first) and return it as a dict."""
        note = Notification(
            type=type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            resource_id=resource_id,
        )
        with self._lock:
            self._items.insert(0, note)
            if len(self._items) > self._max_items:
                del self._items[self._max_items:]
            self._persist_locked()
        return note.to_dict()

    def mark_read(self, ids: Optional[list[str]] = None, mark_all: bool = False) -> int:
        """Mark the given ids (or all) as read. Returns how many changed."""
        changed = 0
        with self._lock:
            id_set = set(ids or [])
            for n in self._items:
                if (mark_all or n.id in id_set) and not n.read:
                    n.read = True
                    changed += 1
            if changed:
                self._persist_locked()
        return changed

    def clear(self) -> int:
        """Remove every notification. Returns how many were removed."""
        with self._lock:
            removed = len(self._items)
            self._items = []
            if removed:
                self._persist_locked()
        return removed

    # -- reads -------------------------------------------------------------

    def list(
        self,
        limit: int = 100,
        unread_only: bool = False,
        severity: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            items = self._items
            if unread_only:
                items = [n for n in items if not n.read]
            if severity:
                items = [n for n in items if n.severity == severity]
            return [n.to_dict() for n in items[:limit]]

    def unread_count(self) -> int:
        with self._lock:
            return sum(1 for n in self._items if not n.read)

    def total(self) -> int:
        with self._lock:
            return len(self._items)


# Global instance ---------------------------------------------------------

_store: Optional[NotificationStore] = None


def get_notification_store() -> NotificationStore:
    """Get the global notification store, creating it on first use."""
    global _store
    if _store is None:
        _store = NotificationStore()
    return _store


def set_notification_store(store: NotificationStore) -> None:
    """Replace the global store (used by tests)."""
    global _store
    _store = store


def notify(
    *,
    type: str,
    severity: str,
    title: str,
    message: str,
    source: str = "system",
    resource_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Record a notification. Best-effort: returns None (never raises) on error.

    Safe to call from inside request handlers -- a failure here must never take
    down the request that triggered the alert.
    """
    try:
        note = get_notification_store().add(
            type=type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            resource_id=resource_id,
        )
    except Exception as exc:  # noqa: BLE001 - notifying is never load-bearing
        logger.warning("notify() failed for %s/%s: %s", type, title, exc)
        return None

    # Fan out to any configured outbound webhooks (Track 1). Lazy import keeps
    # this foundational module import-cycle-free; dispatch is fire-and-forget and
    # swallows its own errors, so a webhook problem never affects the caller.
    try:
        from src.notifications import webhook

        webhook.dispatch(note)
    except Exception as exc:  # noqa: BLE001 - delivery is never load-bearing
        logger.debug("webhook dispatch failed for %s: %s", type, exc)
    return note
