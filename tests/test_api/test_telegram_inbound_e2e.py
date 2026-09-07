"""
End-to-end MOCKED Telegram ChatOps validation (Track 1 T1d) - no bot token, no
network.

The per-seam unit tests already cover the Telegram adapter (test_alerting.py:
verify / send / set_webhook against a scripted httpx), the webhook auto-register
(sync_telegram_webhook), and the /relay/inbound endpoint (test_relay_inbound.py).
But each of those stubs out either ``resolve`` or ``send``, so none of them proves
the WHOLE round trip lines up. This module does: it drives the REAL config store,
the REAL binding resolution and the REAL reply adapter as one flow, mocking only
``api.telegram.org`` and the LLM agent. That is what "we don't have a bot token
but a user will" needs validated - if a routingId, webhook secret, chat id or the
token-decrypt on the reply path were mismatched between registration and reply,
this test fails where the isolated unit tests would not.

Flow proven, all with a FAKE token:
  1. an admin enables Telegram inbound -> the config is stored (token encrypted)
     with a minted opaque routingId + webhook secret;
  2. enabling it registers the bot's webhook at ``<relay-base>/telegram/<routingId>``
     with that secret (Bot API ``setWebhook``);
  3. a message Telegram would deliver for that routingId arrives HMAC-signed at
     ``/relay/inbound``, is resolved from the stored config, chatted, and replied
     back out via ``sendMessage`` to the STORED chat id - never to the sender.
"""

import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.alerting import config as alert_config
from src.alerting import inbound as alert_inbound
from src.alerting import relay_hmac
from src.alerting import telegram as alert_telegram
from src.api.routes.relay import router as relay_router
from src.auth import store

_HMAC_SECRET = "e2e-relay-hmac-secret-value"
_RELAY_BASE = "https://api-gw.example.com"
_FAKE_TOKEN = "111222:FAKE-bot-token-not-real-abc"  # never a live bot token
_CHAT_ID = "424242"


class _FakeResp:
    """A Bot API 200 ``{ok:true}`` - i.e. a valid token, so the flow proceeds."""

    status_code = 200

    @staticmethod
    def json():
        return {"ok": True, "result": True}


class _FakeTelegramClient:
    """Records every Bot API POST (url, json body) instead of hitting the network.

    Matches how ``telegram._post`` uses httpx: ``with httpx.Client(timeout=...)``
    then ``client.post(url, json=payload)``.
    """

    def __init__(self, recorder):
        self._rec = recorder

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def post(self, url, headers=None, json=None):
        self._rec.append((url, json))
        return _FakeResp()


class _FakeAgent:
    """Stand-in reasoning agent - the box's LLM, not Telegram - so no endpoint is needed."""

    def __init__(self):
        self.calls = []

    async def chat(self, message, *_a, **_k):
        self.calls.append(message)
        return SimpleNamespace(content=f"RCA for: {message}", metadata={"tokens_used": 7})


@pytest.fixture
def tg_e2e(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "tg-e2e-fernet-secret")
    monkeypatch.setenv("AIOPS_RELAY_PUBLIC_URL", _RELAY_BASE)
    monkeypatch.setenv("AIOPS_RELAY_HMAC_SECRET", _HMAC_SECRET)
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)  # system/self-host config path
    monkeypatch.delenv("AIOPS_COST_FENCE_ENABLED", raising=False)

    from src.auth import crypto

    crypto.reset_cache()
    store.init_db()

    # One recorder shared by BOTH Telegram-side calls the flow makes: set_webhook
    # (registration) and sendMessage (reply). Both go through this module's httpx.
    tg_calls: list = []
    monkeypatch.setattr(
        alert_telegram.httpx,
        "Client",
        lambda timeout=None: _FakeTelegramClient(tg_calls),
    )

    # An admin enables Telegram inbound with a (fake) token + chat id. apply_update
    # encrypts the token at rest and mints the opaque routingId + webhook secret.
    stored = alert_config.apply_update(
        {},
        {
            "telegram": {
                "enabled": True,
                "chatId": _CHAT_ID,
                "botToken": _FAKE_TOKEN,
                "inboundEnabled": True,
                "minSeverity": "info",
            },
            "matrix": {"enabled": False},
        },
    )
    # resolve_telegram reads the system alerting config; feed it the stored dict
    # (the same seam the existing inbound tests use), so the REAL resolver runs.
    monkeypatch.setattr(alert_inbound, "_system_alerting", lambda: stored)

    app = FastAPI()
    app.include_router(relay_router, prefix="/api/v1/relay")
    agent = _FakeAgent()
    app.state.reasoning_agent = agent
    client = TestClient(app)

    yield SimpleNamespace(client=client, agent=agent, stored=stored, tg_calls=tg_calls)

    crypto.reset_cache()


def _post_inbound(client, routing_id, text):
    """POST an inbound relay payload with a valid relay HMAC (as the Lambda would)."""
    body = json.dumps({"channel": "telegram", "routingId": routing_id, "text": text}).encode("utf-8")
    ts, sig = relay_hmac.sign(_HMAC_SECRET, body)
    return client.post(
        "/api/v1/relay/inbound",
        content=body,
        headers={
            relay_hmac._TS_HEADER: ts,
            relay_hmac._SIG_HEADER: sig,
            "Content-Type": "application/json",
        },
    )


def test_enable_inbound_registers_webhook_then_message_round_trips(tg_e2e):
    from src.auth.crypto import decrypt_secret

    tg = tg_e2e.stored["telegram"]
    routing_id = tg["routingId"]
    assert routing_id  # minted on inbound-enable; the opaque inbound address

    # 1) Enabling inbound registers the bot's webhook at OUR relay edge, with the
    #    same secret the relay mirror will check.
    action, detail = alert_inbound.sync_telegram_webhook({}, tg)
    assert action == "registered", detail
    reg_url, reg_body = tg_e2e.tg_calls[-1]
    assert reg_url.endswith("/setWebhook")
    assert f"bot{_FAKE_TOKEN}" in reg_url  # token travels in the URL path, not the body
    assert reg_body["url"] == f"{_RELAY_BASE}/telegram/{routing_id}"
    assert reg_body["secret_token"] == decrypt_secret(tg["webhookSecret"])

    # 2) A message Telegram delivers for that routingId is resolved from the stored
    #    config, chatted, and replied back out to the STORED chat.
    n_before = len(tg_e2e.tg_calls)
    r = _post_inbound(tg_e2e.client, routing_id, "why is nextcloud-db unhealthy?")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert tg_e2e.agent.calls == ["why is nextcloud-db unhealthy?"]

    reply_calls = tg_e2e.tg_calls[n_before:]
    assert len(reply_calls) == 1  # exactly one outbound reply
    reply_url, reply_body = reply_calls[0]
    assert reply_url.endswith("/sendMessage")
    assert f"bot{_FAKE_TOKEN}" in reply_url  # the stored token decrypts on the reply path
    assert reply_body["chat_id"] == _CHAT_ID  # reply goes to the OWNER's stored chat
    assert "RCA for: why is nextcloud-db unhealthy?" in reply_body["text"]


def test_message_for_unknown_routing_id_is_ignored(tg_e2e):
    # A stranger who finds the endpoint but not a live routingId drives nothing:
    # no agent call, no outbound send, a benign 200.
    r = _post_inbound(tg_e2e.client, "rid-does-not-exist", "run something for me")
    assert r.status_code == 200 and r.json()["status"] == "ignored"
    assert tg_e2e.agent.calls == []
    assert tg_e2e.tg_calls == []  # nothing was sent to Telegram


def test_disabling_inbound_deregisters_the_webhook(tg_e2e):
    on = tg_e2e.stored
    off = alert_config.apply_update(
        on,
        {
            "telegram": {
                "enabled": True,
                "chatId": _CHAT_ID,
                "botToken": None,  # keep the stored token
                "inboundEnabled": False,
            },
            "matrix": {"enabled": False},
        },
    )
    n_before = len(tg_e2e.tg_calls)
    action, _ = alert_inbound.sync_telegram_webhook(on["telegram"], off["telegram"])
    assert action == "removed"
    assert len(tg_e2e.tg_calls) == n_before + 1
    assert tg_e2e.tg_calls[-1][0].endswith("/deleteWebhook")
