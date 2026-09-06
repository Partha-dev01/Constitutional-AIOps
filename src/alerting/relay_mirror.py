"""
Constitutional AIOps - box-side DynamoDB mirror for inbound relay bindings (T1d).

The off-box relay Lambda must authenticate a Telegram webhook and map its
``routingId`` to an owner BEFORE it decides whether to wake the box - so it cannot
ask the (possibly sleeping) box. Instead the box PUSHES a tiny mirror of its
opted-in bindings into DynamoDB whenever the alerting config changes; the Lambda
only ever reads that table.

Each row: ``{routingId, channel, ownerId, webhookSecret}``. The webhookSecret is
stored DECRYPTED here (the Lambda compares it to Telegram's
``X-Telegram-Bot-Api-Secret-Token`` header); the bot token never leaves the box.
DynamoDB is encrypted at rest, and this is a webhook secret, not a bearer token.

Best-effort and fail-open: a no-op when ``RELAY_BINDINGS_TABLE`` is unset (every
non-relay deployment, including all tests and the current box) or when boto3 is
unavailable, and every AWS error is swallowed so saving alerting settings never
fails because of the mirror.
"""

from __future__ import annotations

import logging
import os

from src.alerting import inbound
from src.auth.crypto import decrypt_secret

logger = logging.getLogger(__name__)


def _table() -> str:
    return (os.environ.get("RELAY_BINDINGS_TABLE", "") or "").strip()


def _client():
    import boto3  # imported lazily: the box has it, dev/test/CI need not

    return boto3.client("dynamodb")


def enabled() -> bool:
    """True only when a bindings table is configured (i.e. the relay is provisioned)."""
    return bool(_table())


def sync(*, client=None) -> None:
    """Reconcile the DynamoDB bindings mirror to the current alerting config.

    Puts every opted-in Telegram binding and DELETES any configured-but-disabled
    one (a routingId is kept in config across an off/on toggle, so a disabled
    binding must be actively removed from the mirror or the Lambda would keep
    accepting it). No-op + swallow on any missing prerequisite or AWS error.
    """
    table = _table()
    if not table:
        return
    try:
        client = client or _client()
    except Exception as exc:  # noqa: BLE001
        logger.debug("relay mirror: boto3 unavailable (%s); skipping", exc)
        return
    for owner_id, cfg in inbound.iter_configs():
        tg = cfg.get("telegram")
        if not isinstance(tg, dict):
            continue
        routing_id = str(tg.get("routingId") or "").strip()
        if not routing_id:
            continue
        try:
            if tg.get("inboundEnabled"):
                secret = decrypt_secret((tg.get("webhookSecret") or "").strip())
                client.put_item(
                    TableName=table,
                    Item={
                        "routingId": {"S": routing_id},
                        "channel": {"S": "telegram"},
                        "ownerId": {"S": owner_id},
                        "webhookSecret": {"S": secret},
                    },
                )
            else:
                client.delete_item(
                    TableName=table, Key={"routingId": {"S": routing_id}}
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("relay mirror: sync failed for %s: %s", routing_id, exc)


__all__ = ["enabled", "sync"]
