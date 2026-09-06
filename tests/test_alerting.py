"""
Tests for remote alerting (Track 1, outbound): message rendering, the Telegram
and Matrix raw-httpx adapters (verify + send, SSRF guard, join-retry), config
resolution / redaction / update semantics, severity-filtered dispatch, and the
``notify() -> alerting.dispatch`` wiring.

No real network: ``httpx.Client`` is monkeypatched with a scripted fake, and the
Matrix SSRF guard is monkeypatched (or exercised with a loopback literal, which
it rejects without any DNS).
"""

import httpx
import pytest

from src.alerting import config as alert_config
from src.alerting import dispatch as alert_dispatch
from src.alerting import matrix as alert_matrix
from src.alerting import render
from src.alerting import telegram as alert_telegram
from src.notifications import store as note_store


# ---------------------------------------------------------------------------
# Scripted httpx fake
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


class _FakeClient:
    """Returns scripted responses per HTTP method and records every call.

    ``script`` maps "get"/"post"/"put" to a single ``_FakeResp`` (reused), a list
    consumed in order, or an exception instance to raise.
    """

    def __init__(self, script, recorder):
        self._script = script
        self._rec = recorder

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def _resp_for(self, method):
        item = self._script[method]
        if isinstance(item, list):
            item = item.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def get(self, url, headers=None, json=None):
        self._rec.append(("get", url, headers, json))
        return self._resp_for("get")

    def post(self, url, headers=None, json=None):
        self._rec.append(("post", url, headers, json))
        return self._resp_for("post")

    def put(self, url, headers=None, json=None):
        self._rec.append(("put", url, headers, json))
        return self._resp_for("put")


def _install(monkeypatch, module, script):
    recorder: list = []
    monkeypatch.setattr(
        module.httpx, "Client", lambda timeout=None: _FakeClient(script, recorder)
    )
    return recorder


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


class TestRender:
    def test_plain_has_product_severity_title_message(self):
        text = render.to_plain(
            {"severity": "error", "title": "DB down", "message": "no replicas",
             "resource_id": "nextcloud-db", "source": "monitor"}
        )
        assert "Constitutional AIOps" in text
        assert "[ERROR] DB down" in text
        assert "no replicas" in text
        assert "service: nextcloud-db" in text
        assert "source: monitor" in text

    def test_html_escapes_dynamic_values(self):
        html = render.to_telegram_html({"severity": "info", "title": "<script>x", "message": "a & b < c"})
        assert "&lt;script&gt;x" in html
        assert "a &amp; b &lt; c" in html
        assert "<script>" not in html
        # Our own bold markup is real tags, not escaped.
        assert "<b>Constitutional AIOps</b>" in html

    def test_missing_fields_tolerated(self):
        # An empty note must not raise and still names the product + a fallback title.
        text = render.to_plain({})
        assert "Constitutional AIOps" in text
        assert "[INFO] Notification" in text


# ---------------------------------------------------------------------------
# telegram adapter
# ---------------------------------------------------------------------------


class TestTelegram:
    def test_verify_ok_returns_username(self, monkeypatch):
        _install(monkeypatch, alert_telegram,
                 {"post": _FakeResp(200, {"ok": True, "result": {"username": "mybot"}})})
        ok, detail, username = alert_telegram.verify("123:abc")
        assert ok is True and username == "mybot"

    def test_verify_bad_token_uses_description(self, monkeypatch):
        _install(monkeypatch, alert_telegram,
                 {"post": _FakeResp(401, {"ok": False, "error_code": 401, "description": "Unauthorized"})})
        ok, detail, username = alert_telegram.verify("bad")
        assert ok is False and detail == "Unauthorized" and username == ""

    def test_verify_empty_token_short_circuits(self, monkeypatch):
        # No client should be built for an empty token.
        _install(monkeypatch, alert_telegram, {"post": _FakeResp(200, {"ok": True})})
        ok, _, _ = alert_telegram.verify("   ")
        assert ok is False

    def test_send_ok_posts_html(self, monkeypatch):
        rec = _install(monkeypatch, alert_telegram, {"post": _FakeResp(200, {"ok": True, "result": {}})})
        ok, detail = alert_telegram.send("123:abc", "555", "<b>hi</b>")
        assert ok is True
        _, url, _, body = rec[0]
        assert url.endswith("/sendMessage")
        assert body["chat_id"] == "555" and body["parse_mode"] == "HTML"

    def test_send_transport_error_is_swallowed(self, monkeypatch):
        _install(monkeypatch, alert_telegram, {"post": httpx.RequestError("boom")})
        ok, detail = alert_telegram.send("123:abc", "555", "hi")
        assert ok is False and "unreachable" in detail

    def test_send_unconfigured(self):
        assert alert_telegram.send("", "555", "hi")[0] is False
        assert alert_telegram.send("123:abc", "", "hi")[0] is False


# ---------------------------------------------------------------------------
# matrix adapter
# ---------------------------------------------------------------------------


class TestMatrix:
    def test_verify_ok_returns_user_id(self, monkeypatch):
        monkeypatch.setattr(alert_matrix, "webhook_target_error", lambda url: None)
        _install(monkeypatch, alert_matrix, {"get": _FakeResp(200, {"user_id": "@bot:hs"})})
        ok, detail, user_id = alert_matrix.verify("https://hs.example.com", "tok")
        assert ok is True and user_id == "@bot:hs"

    def test_verify_ssrf_guard_blocks_loopback(self):
        # Real guard, no monkeypatch: a loopback literal is rejected before any request.
        ok, detail, _ = alert_matrix.verify("http://127.0.0.1", "tok")
        assert ok is False and "non-public" in detail

    def test_verify_error_uses_errcode(self, monkeypatch):
        monkeypatch.setattr(alert_matrix, "webhook_target_error", lambda url: None)
        _install(monkeypatch, alert_matrix,
                 {"get": _FakeResp(401, {"errcode": "M_UNKNOWN_TOKEN", "error": "bad token"})})
        ok, detail, _ = alert_matrix.verify("https://hs.example.com", "tok")
        assert ok is False and "M_UNKNOWN_TOKEN" in detail

    def test_send_rejects_alias(self, monkeypatch):
        monkeypatch.setattr(alert_matrix, "webhook_target_error", lambda url: None)
        ok, detail = alert_matrix.send("https://hs.example.com", "tok", "#room:hs", "hi")
        assert ok is False and "alias" in detail

    def test_send_ok_puts_event(self, monkeypatch):
        monkeypatch.setattr(alert_matrix, "webhook_target_error", lambda url: None)
        rec = _install(monkeypatch, alert_matrix, {"put": _FakeResp(200, {"event_id": "$e1"})})
        ok, detail = alert_matrix.send("https://hs.example.com", "tok", "!r:hs", "hello")
        assert ok is True
        method, url, headers, body = rec[0]
        assert method == "put" and "/send/m.room.message/" in url
        assert headers["Authorization"] == "Bearer tok"
        assert body == {"msgtype": "m.text", "body": "hello"}

    def test_send_joins_then_retries_on_forbidden(self, monkeypatch):
        monkeypatch.setattr(alert_matrix, "webhook_target_error", lambda url: None)
        rec = _install(
            monkeypatch,
            alert_matrix,
            {
                # first PUT forbidden, join succeeds, second PUT ok
                "put": [
                    _FakeResp(403, {"errcode": "M_FORBIDDEN", "error": "not in room"}),
                    _FakeResp(200, {"event_id": "$e2"}),
                ],
                "post": _FakeResp(200, {"room_id": "!r:hs"}),
            },
        )
        ok, detail = alert_matrix.send("https://hs.example.com", "tok", "!r:hs", "hello")
        assert ok is True
        methods = [c[0] for c in rec]
        assert methods == ["put", "post", "put"]  # send, join, resend


# ---------------------------------------------------------------------------
# config: targets, redaction, update
# ---------------------------------------------------------------------------


@pytest.fixture
def secret_env(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET_KEY", "alerting-test-secret")
    from src.auth import crypto

    crypto.reset_cache()
    yield
    crypto.reset_cache()


class TestConfig:
    def test_targets_decrypt_and_gate_on_enabled(self, secret_env):
        stored = alert_config.apply_update(
            {},
            {
                "telegram": {"enabled": True, "chatId": "42", "botToken": "TG-secret",
                             "minSeverity": "error"},
                "matrix": {"enabled": True, "homeserver": "https://hs", "roomId": "!r:hs",
                           "accessToken": "MX-secret", "minSeverity": "warning"},
            },
        )
        tg = alert_config.telegram_target(stored["telegram"])
        assert tg is not None and tg.token == "TG-secret" and tg.chat_id == "42"
        assert tg.min_severity == "error"
        mx = alert_config.matrix_target(stored["matrix"])
        assert mx is not None and mx.token == "MX-secret" and mx.room_id == "!r:hs"

    def test_disabled_channel_is_no_target(self, secret_env):
        stored = alert_config.apply_update(
            {}, {"telegram": {"enabled": False, "chatId": "42", "botToken": "x"},
                 "matrix": {"enabled": False}}
        )
        assert alert_config.telegram_target(stored["telegram"]) is None

    def test_public_view_redacts_tokens(self, secret_env):
        stored = alert_config.apply_update(
            {}, {"telegram": {"enabled": True, "chatId": "42", "botToken": "s"},
                 "matrix": {"enabled": False, "accessToken": None}}
        )
        pub = alert_config.public_view(stored)
        assert pub["telegram"]["tokenSet"] is True
        # The raw/encrypted secret is never exposed -- only the boolean flag.
        assert "botToken" not in pub["telegram"]
        assert stored["telegram"]["botToken"] not in str(pub)
        assert pub["telegram"]["chatId"] == "42"
        assert pub["matrix"]["accessTokenSet"] is False

    def test_update_null_leaves_empty_clears_value_sets(self, secret_env):
        base = alert_config.apply_update(
            {}, {"telegram": {"enabled": True, "chatId": "1", "botToken": "keep"},
                 "matrix": {"enabled": False}}
        )
        # None -> token unchanged, other fields replaced
        left = alert_config.apply_update(
            base, {"telegram": {"enabled": True, "chatId": "2", "botToken": None},
                   "matrix": {"enabled": False}}
        )
        assert alert_config.telegram_target(left["telegram"]).token == "keep"
        assert left["telegram"]["chatId"] == "2"
        # "" -> cleared
        cleared = alert_config.apply_update(
            left, {"telegram": {"enabled": True, "chatId": "2", "botToken": ""},
                   "matrix": {"enabled": False}}
        )
        assert alert_config.public_view(cleared)["telegram"]["tokenSet"] is False
        assert alert_config.telegram_target(cleared["telegram"]) is None

    def test_iter_system_targets_when_auth_off(self, monkeypatch):
        monkeypatch.delenv("AUTH_REQUIRED", raising=False)
        monkeypatch.setattr(
            alert_config, "_system_alerting",
            lambda: {"telegram": {"enabled": True, "chatId": "9", "botToken": "plain"}},
        )
        targets = list(alert_config.iter_telegram_targets())
        assert [t.chat_id for t in targets] == ["9"]
        assert targets[0].token == "plain"  # legacy-plaintext decrypts verbatim

    def test_iter_dedups_admin_override_matching_system(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("AUTH_SECRET_KEY", "alerting-test-secret")
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        from src.auth import store as user_store

        user_store.init_db()
        admin = user_store.create_user("boss", "boss-long-password", role="admin")
        user_store.set_user_settings(
            admin.id,
            {"alerting": {"telegram": {"enabled": True, "chatId": "9", "botToken": "p"}}},
        )
        monkeypatch.setattr(
            alert_config, "_system_alerting",
            lambda: {"telegram": {"enabled": True, "chatId": "9", "botToken": "p"}},
        )
        targets = list(alert_config.iter_telegram_targets())
        assert len(targets) == 1  # same chat id deduped across the two tiers


# ---------------------------------------------------------------------------
# dispatch + notify wiring
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_severity_filter(self, monkeypatch):
        monkeypatch.setattr(
            alert_config, "iter_telegram_targets",
            lambda: [alert_config.TelegramTarget("t", "c", "warning")],
        )
        monkeypatch.setattr(alert_config, "iter_matrix_targets", lambda: [])
        fired = []
        monkeypatch.setattr(alert_dispatch, "_fire_telegram",
                            lambda token, chat, note: fired.append(chat))
        alert_dispatch.dispatch({"type": "action.blocked", "severity": "info"})
        assert fired == []  # info < warning
        alert_dispatch.dispatch({"type": "action.blocked", "severity": "error"})
        assert fired == ["c"]

    def test_meta_events_skipped(self, monkeypatch):
        monkeypatch.setattr(
            alert_config, "iter_telegram_targets",
            lambda: [alert_config.TelegramTarget("t", "c", "info")],
        )
        monkeypatch.setattr(alert_config, "iter_matrix_targets", lambda: [])
        fired = []
        monkeypatch.setattr(alert_dispatch, "_fire_telegram",
                            lambda token, chat, note: fired.append(chat))
        alert_dispatch.dispatch({"type": "alerting.test", "severity": "critical"})
        alert_dispatch.dispatch({"type": "webhook.test", "severity": "critical"})
        assert fired == []

    def test_notify_invokes_alerting_dispatch(self, tmp_path, monkeypatch):
        store = note_store.NotificationStore(path=tmp_path)
        note_store.set_notification_store(store)
        seen = {}
        monkeypatch.setattr(alert_dispatch, "dispatch", lambda note: seen.update(note))
        note_store.notify(type="action.blocked", severity="error", title="t", message="m")
        assert seen.get("type") == "action.blocked" and seen.get("severity") == "error"
        note_store.set_notification_store(None)
