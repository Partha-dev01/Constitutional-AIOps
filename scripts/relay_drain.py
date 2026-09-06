#!/usr/bin/env python3
"""
Boot-time SQS drain for the inbound ChatOps relay (Track 1 T1d).

Runs once at boot (systemd oneshot, aws/systemd/aiops-relay-drain.service) AFTER
the app is up. Pulls any messages the relay Lambda queued while the box was asleep,
signs each with the shared relay HMAC, and POSTs it to the LOCAL backend
``/api/v1/relay/inbound`` - which resolves the user, enforces the cost fence, runs
the chat, and replies out. Exits the moment the queue is empty, so the box returns
to its idle-stop schedule (a oneshot that exits keeps the box free to sleep).

Uses the AWS CLI (already on the host) for SQS and stdlib for HMAC + HTTP, so the
host needs no boto3. Reads its config from the same box ``.env`` the app uses
(RELAY_QUEUE_URL, AIOPS_RELAY_HMAC_SECRET), surfaced by the systemd unit's
EnvironmentFile. Best-effort throughout: a failed POST leaves the message on the
queue (visibility timeout) for a later boot rather than dropping it.
"""

import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.request

QUEUE_URL = os.environ.get("RELAY_QUEUE_URL", "")
SECRET = os.environ.get("AIOPS_RELAY_HMAC_SECRET", "")
BACKEND = os.environ.get("RELAY_LOCAL_URL", "http://localhost:8000").rstrip("/")
REGION = (
    os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
    or "us-east-1"
)
_INBOUND = "/api/v1/relay/inbound"
_MAX_ROUNDS = 1000  # hard bound so a stuck message can never loop forever


def _aws(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["aws", *args, "--region", REGION, "--output", "json"],
        capture_output=True,
        text=True,
    )


def _receive() -> list:
    r = _aws(
        "sqs", "receive-message", "--queue-url", QUEUE_URL,
        "--max-number-of-messages", "10", "--wait-time-seconds", "2",
        "--visibility-timeout", "30",
    )
    if r.returncode != 0:
        print("relay-drain: receive failed:", (r.stderr or "").strip())
        return []
    try:
        return json.loads(r.stdout or "{}").get("Messages", []) or []
    except ValueError:
        return []


def _post(body: bytes) -> bool:
    ts = str(int(time.time()))
    sig = hmac.new(
        SECRET.encode("utf-8"), f"{ts}.".encode("utf-8") + body, hashlib.sha256
    ).hexdigest()
    req = urllib.request.Request(
        BACKEND + _INBOUND,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-AIOPS-Relay-Timestamp": ts,
            "X-AIOPS-Relay-Signature": sig,
        },
    )
    try:
        urllib.request.urlopen(req, timeout=5).read()
        return True
    except Exception as exc:  # noqa: BLE001
        print("relay-drain: post failed:", exc)
        return False


def main() -> int:
    if not QUEUE_URL:
        print("relay-drain: RELAY_QUEUE_URL unset; nothing to do")
        return 0
    if not SECRET:
        print("relay-drain: AIOPS_RELAY_HMAC_SECRET unset; refusing")
        return 0
    drained = 0
    for _ in range(_MAX_ROUNDS):
        messages = _receive()
        if not messages:
            break
        for m in messages:
            body = (m.get("Body") or "").encode("utf-8")
            if _post(body):
                _aws(
                    "sqs", "delete-message", "--queue-url", QUEUE_URL,
                    "--receipt-handle", m["ReceiptHandle"],
                )
                drained += 1
    print(f"relay-drain: drained {drained} message(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
