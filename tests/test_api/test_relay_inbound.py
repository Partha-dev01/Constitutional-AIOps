"""
Inbound ChatOps relay endpoint (Track 1 T1d) tests.

Mounts just the relay router on a bare app (no full lifespan) and drives it with
real HMAC headers. Covers: fail-closed when no secret is set, signature + replay
rejection, unknown/empty payloads, the happy path (per-user chat + reply-out),
the no-endpoint notice, and real cost-fence-D enforcement.
"""

import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.alerting import relay_hmac
from src.alerting.inbound import InboundBinding
from src.api.routes.relay import router as relay_router
from src.auth import store
from src.auth.deps import SYNTHETIC_USER_ID

_SECRET = "relay-test-secret-value"


class _FakeAgent:
    def __init__(self):
        self.calls = []

    async def chat(self, message, *args, **kwargs):
        self.calls.append(message)
        return SimpleNamespace(content=f"reply::{message}", metadata={"tokens_used": 9})


def _binding():
    return InboundBinding(
        owner_id="",  # system/self-host -> synthetic admin
        channel="telegram",
        reply_token="bot-token",
        reply_target="42",
        homeserver="",
        routing_id="rid-1",
        webhook_secret="whsec",
    )


@pytest.fixture
def relay(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AIOPS_COST_FENCE_ENABLED", raising=False)
    monkeypatch.delenv("AIOPS_COST_FENCE_DAILY_TOKENS", raising=False)
    store.init_db()

    sent = []
    monkeypatch.setattr(
        "src.api.routes.relay.telegram_adapter.send",
        lambda token, target, text, html=True: sent.append((token, target, text)) or (True, "ok"),
    )
    monkeypatch.setattr("src.api.routes.relay.inbound_bindings.resolve", lambda ch, rid: _binding())

    app = FastAPI()
    app.include_router(relay_router, prefix="/api/v1/relay")
    agent = _FakeAgent()
    app.state.reasoning_agent = agent
    client = TestClient(app)
    return SimpleNamespace(client=client, sent=sent, agent=agent, monkeypatch=monkeypatch, app=app)


def _post(client, payload, *, secret=_SECRET, skew=0):
    body = json.dumps(payload).encode("utf-8")
    ts, sig = relay_hmac.sign(secret, body)
    if skew:
        ts = str(int(ts) + skew)
        _, sig = relay_hmac.sign(secret, body, timestamp=int(ts))
    return client.post(
        "/api/v1/relay/inbound",
        content=body,
        headers={
            relay_hmac._TS_HEADER: ts,
            relay_hmac._SIG_HEADER: sig,
            "Content-Type": "application/json",
        },
    )


def _payload(text="restart the api"):
    return {"channel": "telegram", "routingId": "rid-1", "text": text}


class TestAuth:
    def test_no_secret_is_disabled(self, relay, monkeypatch):
        monkeypatch.delenv("AIOPS_RELAY_HMAC_SECRET", raising=False)
        r = _post(relay.client, _payload())
        assert r.status_code == 503
        assert r.json()["status"] == "disabled"

    def test_bad_signature_rejected(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        body = json.dumps(_payload()).encode("utf-8")
        ts, _ = relay_hmac.sign(_SECRET, body)
        r = relay.client.post(
            "/api/v1/relay/inbound",
            content=body,
            headers={relay_hmac._TS_HEADER: ts, relay_hmac._SIG_HEADER: "deadbeef"},
        )
        assert r.status_code == 401
        assert relay.agent.calls == []

    def test_replayed_timestamp_rejected(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        r = _post(relay.client, _payload(), skew=-1000)  # far outside the window
        assert r.status_code == 401

    def test_wrong_secret_rejected(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        r = _post(relay.client, _payload(), secret="not-the-secret")
        assert r.status_code == 401


class TestHappyPath:
    def test_relays_and_replies(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        r = _post(relay.client, _payload("why is svc down"))
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert relay.agent.calls == ["why is svc down"]
        # replied out to the STORED chat with the agent's answer
        assert relay.sent and relay.sent[-1][1] == "42"
        assert "reply::why is svc down" in relay.sent[-1][2]
        # usage recorded for the acting (synthetic admin) user
        tokens, requests = store.llm_usage_today(SYNTHETIC_USER_ID)
        assert tokens == 9 and requests == 1

    def test_unknown_binding_ignored(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        monkeypatch.setattr("src.api.routes.relay.inbound_bindings.resolve", lambda ch, rid: None)
        r = _post(relay.client, _payload())
        assert r.status_code == 200 and r.json()["status"] == "ignored"
        assert relay.agent.calls == []

    def test_empty_text_noop(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        r = _post(relay.client, _payload(""))
        assert r.status_code == 200 and r.json()["status"] == "empty"
        assert relay.agent.calls == []

    def test_no_endpoint_notice(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        relay.app.state.reasoning_agent = None  # admin path with no global agent
        r = _post(relay.client, _payload())
        assert r.status_code == 200 and r.json()["status"] == "no_endpoint"
        assert relay.sent and "endpoint" in relay.sent[-1][2].lower()


class TestCostFence:
    def test_over_budget_blocks_before_chat(self, relay, monkeypatch):
        monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _SECRET)
        monkeypatch.setenv("AIOPS_COST_FENCE_ENABLED", "true")
        monkeypatch.setenv("AIOPS_COST_FENCE_DAILY_TOKENS", "10")
        store.add_llm_usage(SYNTHETIC_USER_ID, 10)  # already at the cap
        r = _post(relay.client, _payload())
        assert r.status_code == 200 and r.json()["status"] == "budget"
        assert relay.agent.calls == []  # never spent
        assert "budget" in relay.sent[-1][2].lower()
