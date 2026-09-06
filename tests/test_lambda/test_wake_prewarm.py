"""Unit tests for the wake-on-visit Lambda's T4 smart pre-warm branch.

The handler lives at aws/lambda/wake_on_visit/handler.py, outside the importable
`src` package and depending on boto3 (which is provided by the AWS Lambda runtime,
not this app's requirements). So we load it by file path with a stub `boto3`
injected for the duration of the import -- the tests never need real boto3 or AWS
creds, and drive a fake EC2 client set directly on the module.

Coverage:
  * /prewarm + stopped        -> 202 "warming" + exactly one StartInstances
  * /prewarm + running/pending -> 202 no-op, zero StartInstances (no cost)
  * /prewarm + bot / no UA     -> 403, zero StartInstances (bots never wake it)
  * /prewarm + describe error  -> benign 202 "unknown", never a 5xx
  * /launch  (regression)      -> still the 200 holding page + StartInstances
  * path detection + the unconfigured-instance guard
"""

import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

_HANDLER_PATH = (
    Path(__file__).resolve().parents[2] / "aws" / "lambda" / "wake_on_visit" / "handler.py"
)

_REAL_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36"


class FakeEc2:
    """Minimal stand-in for the boto3 EC2 client used by the handler."""

    def __init__(self, state="stopped", ip="203.0.113.7", found=True, describe_error=None):
        self.state = state
        self.ip = ip
        self.found = found
        self.describe_error = describe_error
        self.start_calls = []

    def describe_instances(self, InstanceIds):  # noqa: N803 - boto3 kwarg name
        if self.describe_error is not None:
            raise self.describe_error
        if not self.found:
            return {"Reservations": []}
        return {
            "Reservations": [
                {"Instances": [{"State": {"Name": self.state}, "PublicIpAddress": self.ip}]}
            ]
        }

    def start_instances(self, InstanceIds):  # noqa: N803 - boto3 kwarg name
        self.start_calls.append(list(InstanceIds))
        self.state = "pending"
        return {}


def _load_handler():
    """Import the handler module fresh, with TARGET_INSTANCE_ID set and a stub
    boto3 in place so it loads regardless of whether real boto3 is installed."""
    os.environ["TARGET_INSTANCE_ID"] = "i-testprewarm0000000"
    stub = types.ModuleType("boto3")
    stub.client = lambda *a, **k: None  # never used: tests set _ec2 directly
    saved = sys.modules.get("boto3")
    sys.modules["boto3"] = stub
    try:
        spec = importlib.util.spec_from_file_location("wake_handler_under_test", _HANDLER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if saved is not None:
            sys.modules["boto3"] = saved
        else:
            sys.modules.pop("boto3", None)
    return mod


@pytest.fixture()
def mod():
    return _load_handler()


def _prewarm_event(ua=_REAL_UA):
    headers = {"user-agent": ua} if ua is not None else {}
    return {"rawPath": "/prewarm", "headers": headers, "requestContext": {"http": {"path": "/prewarm"}}}


def _launch_event(ua=_REAL_UA):
    return {"rawPath": "/launch", "headers": {"user-agent": ua}}


# --- /prewarm branch -------------------------------------------------------

def test_prewarm_stopped_starts_box(mod):
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"])["status"] == "warming"
    assert resp["headers"]["Cache-Control"] == "no-store"
    assert len(fake.start_calls) == 1
    assert fake.start_calls[0] == ["i-testprewarm0000000"]


def test_prewarm_running_is_noop(mod):
    fake = FakeEc2(state="running")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"])["status"] == "running"
    assert fake.start_calls == []  # never pays to start an already-up box


def test_prewarm_pending_is_noop(mod):
    fake = FakeEc2(state="pending")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"])["status"] == "pending"
    assert fake.start_calls == []


def test_prewarm_bot_refused_without_ec2_call(mod):
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(ua="curl/8.4.0"), None)
    assert resp["statusCode"] == 403
    assert fake.start_calls == []  # a bot must never wake the box


def test_prewarm_missing_ua_refused(mod):
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(ua=None), None)
    assert resp["statusCode"] == 403
    assert fake.start_calls == []


def test_prewarm_instance_not_found_is_benign(mod):
    fake = FakeEc2(found=False)
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"])["status"] == "unknown"
    assert fake.start_calls == []


def test_prewarm_describe_error_swallowed_to_202(mod):
    fake = FakeEc2(state="stopped", describe_error=RuntimeError("throttled"))
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 202  # background ping never surfaces a 5xx
    assert json.loads(resp["body"])["status"] == "unknown"
    assert fake.start_calls == []


def test_prewarm_unconfigured_instance_returns_500(mod):
    mod._INSTANCE_ID = ""  # the guard fires before the prewarm branch
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_prewarm_event(), None)
    assert resp["statusCode"] == 500
    assert fake.start_calls == []


# --- /launch regression: prewarm must not have changed it -------------------

def test_launch_stopped_still_serves_holding_page(mod):
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_launch_event(), None)
    assert resp["statusCode"] == 200  # holding page, not the 202 prewarm shape
    assert "text/html" in resp["headers"]["Content-Type"]
    assert len(fake.start_calls) == 1  # /launch still wakes a stopped box


def test_launch_bot_still_refused(mod):
    fake = FakeEc2(state="stopped")
    mod._ec2 = fake
    resp = mod.handler(_launch_event(ua="python-requests/2.31"), None)
    assert resp["statusCode"] == 403
    assert fake.start_calls == []


# --- path detection --------------------------------------------------------

def test_is_prewarm_path_detection(mod):
    assert mod._is_prewarm({"rawPath": "/prewarm"}) is True
    assert mod._is_prewarm({"rawPath": "/prewarm/"}) is True
    assert mod._is_prewarm({"requestContext": {"http": {"path": "/prewarm"}}}) is True
    assert mod._is_prewarm({"rawPath": "/launch"}) is False
    assert mod._is_prewarm({"rawPath": ""}) is False
    assert mod._is_prewarm({}) is False
