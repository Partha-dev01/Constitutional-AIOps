"""
Constitutional AIOps - remote-alerting dispatch (Track 1).

The chat-channel sibling of ``src.notifications.webhook.dispatch``: called by
``notify()`` for every emitted notification, it fans the note out to each enabled
Telegram / Matrix target whose minimum-severity filter it clears, delivering on a
one-shot daemon thread that dies as soon as its request returns (NO poller /
worker). Fire-and-forget: returns immediately and never raises, so an alerting
problem can never affect the caller.

Meta events (``alerting.*`` and ``webhook.*`` -- the test/delivery diagnostics
the two channels emit) are skipped so a "test" never forwards itself or the other
channel's test into a real room.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from src.alerting import config as alert_config
from src.alerting import matrix as matrix_channel
from src.alerting import render
from src.alerting import telegram as telegram_channel
from src.notifications.webhook import SEVERITY_RANK

logger = logging.getLogger(__name__)

_META_PREFIXES = ("alerting.", "webhook.")


def _fire_telegram(token: str, chat_id: str, note: dict[str, Any]) -> None:
    def _run() -> None:
        ok, detail = telegram_channel.send(token, chat_id, render.to_telegram_html(note))
        if not ok:
            logger.info("Telegram alert delivery failed: %s", detail)

    threading.Thread(target=_run, name="aiops-telegram", daemon=True).start()


def _fire_matrix(homeserver: str, token: str, room_id: str, note: dict[str, Any]) -> None:
    def _run() -> None:
        ok, detail = matrix_channel.send(homeserver, token, room_id, render.to_plain(note))
        if not ok:
            logger.info("Matrix alert delivery failed: %s", detail)

    threading.Thread(target=_run, name="aiops-matrix", daemon=True).start()


def dispatch(note: dict[str, Any]) -> None:
    """Push a just-emitted notification to every entitled, severity-matching channel.

    Fire-and-forget; never raises.
    """
    try:
        ntype = str(note.get("type", ""))
        if ntype.startswith(_META_PREFIXES):
            return
        note_rank = SEVERITY_RANK.get(str(note.get("severity", "info")), 0)
        for tg in alert_config.iter_telegram_targets():
            if note_rank >= SEVERITY_RANK.get(tg.min_severity, 1):
                _fire_telegram(tg.token, tg.chat_id, note)
        for mx in alert_config.iter_matrix_targets():
            if note_rank >= SEVERITY_RANK.get(mx.min_severity, 1):
                _fire_matrix(mx.homeserver, mx.token, mx.room_id, note)
    except Exception as exc:  # noqa: BLE001 - dispatch is never load-bearing
        logger.debug("Alerting dispatch skipped: %s", exc)


__all__ = ["dispatch"]
