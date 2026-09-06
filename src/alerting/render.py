"""
Constitutional AIOps - message rendering for remote alerting (Track 1).

Turns a stored notification dict (the same shape the in-app inbox and the
outbound webhook use) into the two rendered forms the chat adapters need:

  * ``to_plain(note)``         -> plain UTF-8 text (Matrix ``m.text`` body; also a
                                  safe fallback anywhere HTML is not wanted).
  * ``to_telegram_html(note)`` -> Telegram ``parse_mode="HTML"`` text, with every
                                  dynamic value HTML-escaped so a title like
                                  ``<b>oops`` or ``<script>`` cannot inject markup
                                  or make Telegram reject the message.

Pure and dependency-free: no network, no config, no I/O. Every field is optional
and tolerated when missing, because a caller must never break on a malformed note.
"""

from __future__ import annotations

from html import escape
from typing import Any

_PRODUCT = "Constitutional AIOps"


def _sev(note: dict[str, Any]) -> str:
    s = str(note.get("severity", "") or "").strip().lower()
    return s or "info"


def _rows(note: dict[str, Any]) -> list[tuple[str, str]]:
    """Ordered (label, value) pairs for the optional trailing fields."""
    rows: list[tuple[str, str]] = []
    resource = str(note.get("resource_id") or "").strip()
    if resource:
        rows.append(("service", resource))
    source = str(note.get("source") or "").strip()
    if source:
        rows.append(("source", source))
    return rows


def to_plain(note: dict[str, Any]) -> str:
    """Render ``note`` as plain multi-line text (Matrix body / generic fallback)."""
    title = str(note.get("title") or "Notification").strip()
    message = str(note.get("message") or "").strip()
    lines = [_PRODUCT, f"[{_sev(note).upper()}] {title}"]
    if message:
        lines.append(message)
    for label, value in _rows(note):
        lines.append(f"{label}: {value}")
    return "\n".join(lines)


def to_telegram_html(note: dict[str, Any]) -> str:
    """Render ``note`` for Telegram parse_mode=HTML (dynamic values escaped).

    Telegram HTML keeps literal newlines, so this uses ``\\n`` between lines and
    a minimal, always-supported tag subset (``<b>``). Only labels are bolded; all
    caller-supplied text is escaped with ``&``/``<``/``>`` replaced.
    """
    title = escape(str(note.get("title") or "Notification").strip(), quote=False)
    message = escape(str(note.get("message") or "").strip(), quote=False)
    lines = [
        f"<b>{escape(_PRODUCT, quote=False)}</b>",
        f"<b>[{_sev(note).upper()}]</b> {title}",
    ]
    if message:
        lines.append(message)
    for label, value in _rows(note):
        lines.append(
            f"<b>{escape(label, quote=False)}</b>: {escape(value, quote=False)}"
        )
    return "\n".join(lines)


__all__ = ["to_plain", "to_telegram_html"]
