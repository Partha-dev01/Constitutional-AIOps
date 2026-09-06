"""
Inbound ChatOps relay Lambda for Constitutional AIOps (Track 1 T1d).

The box sleeps when idle, so it cannot hold an open Telegram connection. This
tiny always-on Lambda is the inbound edge: Telegram delivers each message here by
webhook (zero idle cost), and the Lambda decides what to do WITHOUT waking the box
unless it has to.

Per Telegram webhook POST to ``/telegram/{routingId}``:
  1. Authenticate: Telegram echoes the per-binding secret as the
     ``X-Telegram-Bot-Api-Secret-Token`` header. It must equal the secret stored
     for this ``routingId`` in the bindings mirror (DynamoDB). No match -> 401,
     nothing else happens (a stranger who guesses a routingId is refused here,
     before any EC2 call).
  2. Rate-limit per binding AND globally (DynamoDB atomic counters in fixed time
     buckets) so a noisy chat can neither spam the box nor run the wake bill up.
  3. Extract the message text + sender, build the box-side payload.
  4. If the box is RUNNING, forward it straight to the backend
     ``/api/v1/relay/inbound`` over the shared-secret HMAC.
     If the box is STOPPED/asleep, enqueue the payload to SQS and StartInstances;
     the box drains the queue at boot (scripts/relay-drain.sh) and replies then.

Always returns 200 to Telegram (a non-2xx makes Telegram retry-storm); every
failure is swallowed to a benign 200. Stdlib + boto3 only (boto3 ships in the
Lambda runtime). Clients are created lazily so the module imports cleanly in unit
tests with no AWS credentials.

Environment:
  RELAY_BINDINGS_TABLE   (required)  DynamoDB table, PK ``routingId`` (string)
  RELAY_QUEUE_URL        (required)  SQS queue the box drains at boot
  TARGET_INSTANCE_ID     (required)  the box to wake, e.g. i-0123...
  BACKEND_URL            (required)  box base URL, e.g. https://aiops-node.example.com
  AIOPS_RELAY_HMAC_SECRET(required)  shared secret for the box /relay/inbound HMAC
  RELAY_MSGS_PER_MIN         optional, default 10  (per-binding message ceiling/min)
  RELAY_WAKES_PER_HOUR       optional, default 6   (per-binding wake ceiling/hour)
  RELAY_GLOBAL_WAKES_PER_HOUR optional, default 30 (all-bindings wake ceiling/hour)
  (AWS_REGION is provided by the Lambda runtime.)
"""

import hashlib
import hmac
import json
import os
import time
import urllib.request

import boto3

_TABLE = os.environ.get("RELAY_BINDINGS_TABLE", "")
_QUEUE_URL = os.environ.get("RELAY_QUEUE_URL", "")
_INSTANCE_ID = os.environ.get("TARGET_INSTANCE_ID", "")
_BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
_HMAC_SECRET = os.environ.get("AIOPS_RELAY_HMAC_SECRET", "")

_MSGS_PER_MIN = int(os.environ.get("RELAY_MSGS_PER_MIN", "10"))
_WAKES_PER_HOUR = int(os.environ.get("RELAY_WAKES_PER_HOUR", "6"))
_GLOBAL_WAKES_PER_HOUR = int(os.environ.get("RELAY_GLOBAL_WAKES_PER_HOUR", "30"))

_HTTP_TIMEOUT = 5  # seconds for the box forward (Lambda timeout should be ~10s)
_INBOUND_PATH = "/api/v1/relay/inbound"

_ec2 = None
_ddb = None
_sqs = None


def _ec2c():
    global _ec2
    if _ec2 is None:
        _ec2 = boto3.client("ec2")
    return _ec2


def _ddbc():
    global _ddb
    if _ddb is None:
        _ddb = boto3.client("dynamodb")
    return _ddb


def _sqsc():
    global _sqs
    if _sqs is None:
        _sqs = boto3.client("sqs")
    return _sqs


def _ok(status: str) -> dict:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps({"status": status}),
    }


def _deny(code: int) -> dict:
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps({"status": "denied"}),
    }


def _routing_id(event) -> str:
    """Last path segment of /telegram/{routingId} (Function URL payload v2)."""
    path = ""
    if isinstance(event, dict):
        path = event.get("rawPath") or ""
        if not path:
            rc = event.get("requestContext") or {}
            http = rc.get("http") if isinstance(rc, dict) else None
            if isinstance(http, dict):
                path = http.get("path") or ""
    return path.rstrip("/").rsplit("/", 1)[-1] if path else ""


def _header(event, name: str) -> str:
    headers = (event or {}).get("headers") or {}
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value or ""
    return ""


def _binding(routing_id: str) -> dict:
    """Fetch {webhookSecret, ownerId} for a routingId, or {} when absent."""
    try:
        resp = _ddbc().get_item(
            TableName=_TABLE, Key={"routingId": {"S": routing_id}}
        )
    except Exception as exc:  # noqa: BLE001
        print(f"relay: bindings lookup failed: {exc}")
        return {}
    item = resp.get("Item") or {}
    return {
        "webhookSecret": (item.get("webhookSecret") or {}).get("S", ""),
        "ownerId": (item.get("ownerId") or {}).get("S", ""),
    }


def _rate_ok(key: str, limit: int, window_sec: int) -> bool:
    """Atomic fixed-window counter in DynamoDB. True while under ``limit``.

    The window bucket is embedded in the sort key so old buckets age out via TTL
    and each ADD is atomic (no read-modify-write race). Fails OPEN on a DB error
    so a transient DynamoDB blip never silences alerts entirely."""
    if limit <= 0:
        return True
    bucket = int(time.time()) // window_sec
    pk = f"RL#{key}#{bucket}"
    try:
        resp = _ddbc().update_item(
            TableName=_TABLE,
            Key={"routingId": {"S": pk}},
            UpdateExpression="ADD n :one SET ttl = :ttl",
            ExpressionAttributeValues={
                ":one": {"N": "1"},
                ":ttl": {"N": str((bucket + 2) * window_sec)},
            },
            ReturnValues="UPDATED_NEW",
        )
        count = int(resp.get("Attributes", {}).get("n", {}).get("N", "1"))
        return count <= limit
    except Exception as exc:  # noqa: BLE001
        print(f"relay: rate-limit check failed (allowing): {exc}")
        return True


def _extract_message(body: str) -> tuple[str, str]:
    """Return (text, sender) from a Telegram update body. ("","") when not a text
    message (edits, joins, etc. are ignored)."""
    try:
        update = json.loads(body or "{}")
    except ValueError:
        return "", ""
    if not isinstance(update, dict):
        return "", ""
    msg = update.get("message") or update.get("edited_message") or {}
    if not isinstance(msg, dict):
        return "", ""
    text = str(msg.get("text") or "").strip()
    frm = msg.get("from") or {}
    sender = str(frm.get("id") or "") if isinstance(frm, dict) else ""
    return text, sender


def _instance_state() -> str:
    try:
        resp = _ec2c().describe_instances(InstanceIds=[_INSTANCE_ID])
        reservations = resp.get("Reservations", [])
        instances = reservations[0]["Instances"] if reservations else []
        return instances[0]["State"]["Name"] if instances else "unknown"
    except Exception as exc:  # noqa: BLE001
        print(f"relay: describe failed: {exc}")
        return "unknown"


def _forward(payload: dict) -> bool:
    """POST the payload straight to the running box over the relay HMAC."""
    body = json.dumps(payload).encode("utf-8")
    ts = str(int(time.time()))
    sig = hmac.new(
        _HMAC_SECRET.encode("utf-8"), f"{ts}.".encode("utf-8") + body, hashlib.sha256
    ).hexdigest()
    req = urllib.request.Request(
        f"{_BACKEND_URL}{_INBOUND_PATH}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-AIOPS-Relay-Timestamp": ts,
            "X-AIOPS-Relay-Signature": sig,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            resp.read()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"relay: forward failed: {exc}")
        return False


def _enqueue(payload: dict) -> None:
    try:
        _sqsc().send_message(QueueUrl=_QUEUE_URL, MessageBody=json.dumps(payload))
    except Exception as exc:  # noqa: BLE001
        print(f"relay: enqueue failed: {exc}")


def handler(event, context):  # noqa: ARG001 - Lambda signature
    if not (_TABLE and _INSTANCE_ID and _HMAC_SECRET):
        return _ok("misconfigured")

    routing_id = _routing_id(event)
    if not routing_id:
        return _ok("no_routing")

    binding = _binding(routing_id)
    secret = binding.get("webhookSecret", "")
    if not secret or not hmac.compare_digest(
        secret, _header(event, "X-Telegram-Bot-Api-Secret-Token")
    ):
        return _deny(401)

    # Per-binding message rate limit (cheap DoS/abuse bound; drops silently).
    if not _rate_ok(routing_id, _MSGS_PER_MIN, 60):
        return _ok("rate_limited")

    text, sender = _extract_message(event.get("body") or "")
    if not text:
        return _ok("no_text")

    payload = {"channel": "telegram", "routingId": routing_id, "text": text, "sender": sender}

    state = _instance_state()
    if state == "running":
        _forward(payload)
        return _ok("forwarded")

    # Asleep / transitioning: enqueue for the boot-time drain, then (from a fully
    # stopped state, and only within the wake rate limits) start the box.
    _enqueue(payload)
    if state == "stopped":
        if not _rate_ok(routing_id, _WAKES_PER_HOUR, 3600):
            return _ok("queued_wake_limited")
        if not _rate_ok("GLOBAL", _GLOBAL_WAKES_PER_HOUR, 3600):
            return _ok("queued_global_limited")
        try:
            _ec2c().start_instances(InstanceIds=[_INSTANCE_ID])
        except Exception as exc:  # noqa: BLE001
            print(f"relay: start failed: {exc}")
        return _ok("queued_waking")
    return _ok("queued")
