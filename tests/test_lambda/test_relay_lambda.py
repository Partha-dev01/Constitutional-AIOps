"""Unit tests for the inbound ChatOps relay Lambda (Track 1 T1d).

The handler lives at aws/lambda/relay/handler.py, outside the importable `src`
package and depending on boto3 (provided by the Lambda runtime). We load it by
path with a stub boto3, set its env before import (module globals read env at
import time), and drive fake DynamoDB / EC2 / SQS clients set on the module.

Coverage:
  * webhook-secret mismatch -> 401, no EC2/SQS calls
  * running box            -> forward to backend, no start/enqueue
  * stopped box            -> enqueue + exactly one StartInstances
  * per-binding rate limit -> dropped, no wake
  * empty / non-text / no-routing updates -> benign 200, no side effects
  * _forward builds the timestamped relay HMAC headers
"""

import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

_HANDLER_PATH = Path(__file__).resolve().parents[2] / "aws" / "lambda" / "relay" / "handler.py"


class FakeDdb:
    def __init__(self, bindings):
        self.bindings = bindings  # {routingId: {"webhookSecret":.., "ownerId":..}}
        self.counters = {}

    def get_item(self, TableName, Key):  # noqa: N803
        rid = Key["routingId"]["S"]
        b = self.bindings.get(rid)
        if not b:
            return {}
        return {"Item": {"webhookSecret": {"S": b["webhookSecret"]}, "ownerId": {"S": b["ownerId"]}}}

    def update_item(self, TableName, Key, UpdateExpression, ExpressionAttributeValues, ReturnValues):  # noqa: N803
        pk = Key["routingId"]["S"]
        self.counters[pk] = self.counters.get(pk, 0) + 1
        return {"Attributes": {"n": {"N": str(self.counters[pk])}}}


class FakeEc2:
    def __init__(self, state="stopped"):
        self.state = state
        self.start_calls = []

    def describe_instances(self, InstanceIds):  # noqa: N803
        return {"Reservations": [{"Instances": [{"State": {"Name": self.state}}]}]}

    def start_instances(self, InstanceIds):  # noqa: N803
        self.start_calls.append(list(InstanceIds))
        self.state = "pending"
        return {}


class FakeSqs:
    def __init__(self):
        self.sent = []

    def send_message(self, QueueUrl, MessageBody):  # noqa: N803
        self.sent.append(MessageBody)
        return {}


def _load(monkeypatch, *, bindings=None, state="stopped"):
    monkeypatch.setenv("RELAY_BINDINGS_TABLE", "relay-bindings")
    monkeypatch.setenv("RELAY_QUEUE_URL", "https://sqs/queue")
    monkeypatch.setenv("TARGET_INSTANCE_ID", "i-relaytest000000000")
    monkeypatch.setenv("BACKEND_URL", "https://box.example.com")
    monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", "relay-secret")
    stub = types.ModuleType("boto3")
    stub.client = lambda *a, **k: None
    saved = sys.modules.get("boto3")
    sys.modules["boto3"] = stub
    try:
        spec = importlib.util.spec_from_file_location("relay_handler_under_test", _HANDLER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if saved is not None:
            sys.modules["boto3"] = saved
        else:
            sys.modules.pop("boto3", None)
    mod._ddb = FakeDdb(bindings or {"rid-1": {"webhookSecret": "whsec", "ownerId": ""}})
    mod._ec2 = FakeEc2(state=state)
    mod._sqs = FakeSqs()
    return mod


def _event(routing="rid-1", secret="whsec", text="hi", raw_path=None):
    body = json.dumps({"message": {"text": text, "from": {"id": "77"}}}) if text is not None else "{}"
    path = raw_path if raw_path is not None else f"/telegram/{routing}"
    return {
        "rawPath": path,
        "headers": {"x-telegram-bot-api-secret-token": secret},
        "body": body,
    }


def test_secret_mismatch_denied(monkeypatch):
    mod = _load(monkeypatch, state="running")
    forwarded = []
    monkeypatch.setattr(mod, "_forward", lambda p: forwarded.append(p) or True)
    resp = mod.handler(_event(secret="wrong"), None)
    assert resp["statusCode"] == 401
    assert forwarded == []
    assert mod._ec2.start_calls == []


def test_running_forwards(monkeypatch):
    mod = _load(monkeypatch, state="running")
    forwarded = []
    monkeypatch.setattr(mod, "_forward", lambda p: forwarded.append(p) or True)
    resp = mod.handler(_event(text="why down"), None)
    assert resp["statusCode"] == 200 and json.loads(resp["body"])["status"] == "forwarded"
    assert forwarded and forwarded[0]["text"] == "why down"
    assert mod._ec2.start_calls == []
    assert mod._sqs.sent == []


def test_stopped_enqueues_and_wakes(monkeypatch):
    mod = _load(monkeypatch, state="stopped")
    resp = mod.handler(_event(text="status"), None)
    assert json.loads(resp["body"])["status"] == "queued_waking"
    assert len(mod._ec2.start_calls) == 1
    assert len(mod._sqs.sent) == 1
    assert json.loads(mod._sqs.sent[0])["text"] == "status"


def test_per_binding_rate_limit(monkeypatch):
    mod = _load(monkeypatch, state="running")
    mod._MSGS_PER_MIN = 1
    monkeypatch.setattr(mod, "_forward", lambda p: True)
    first = mod.handler(_event(), None)
    second = mod.handler(_event(), None)
    assert json.loads(first["body"])["status"] == "forwarded"
    assert json.loads(second["body"])["status"] == "rate_limited"


def test_empty_text_noop(monkeypatch):
    mod = _load(monkeypatch, state="running")
    monkeypatch.setattr(mod, "_forward", lambda p: True)
    resp = mod.handler(_event(text=""), None)
    assert json.loads(resp["body"])["status"] == "no_text"
    assert mod._sqs.sent == []


def test_no_routing_id(monkeypatch):
    mod = _load(monkeypatch, state="running")
    resp = mod.handler(_event(raw_path=""), None)
    assert json.loads(resp["body"])["status"] == "no_routing"


def test_forward_builds_hmac_headers(monkeypatch):
    mod = _load(monkeypatch, state="running")
    captured = {}

    class _Resp:
        def read(self):
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
        captured["body"] = req.data
        return _Resp()

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    ok = mod._forward({"channel": "telegram", "routingId": "rid-1", "text": "hi"})
    assert ok is True
    assert captured["url"].endswith("/api/v1/relay/inbound")
    assert "x-aiops-relay-timestamp" in captured["headers"]
    assert len(captured["headers"]["x-aiops-relay-signature"]) == 64  # sha256 hex
