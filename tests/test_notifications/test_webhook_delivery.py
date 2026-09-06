"""
Tests for outbound webhook delivery (Track 1): the SSRF guard, the blocking
``deliver`` (signing + status handling), recipient resolution, severity-filtered
``dispatch``, and the ``notify() -> dispatch`` wiring.

No real network: httpx.Client is monkeypatched with a fake, and getaddrinfo is
monkeypatched where the guard is under test.
"""

import hashlib
import hmac
import json
from unittest.mock import MagicMock

import pytest

from src.notifications import store as note_store
from src.notifications import webhook


# ---------------------------------------------------------------------------
# webhook_target_error (SSRF guard)
# ---------------------------------------------------------------------------


class TestTargetGuard:
    def test_rejects_non_http_scheme(self):
        assert webhook.webhook_target_error("ftp://example.com") is not None

    def test_rejects_missing_host(self):
        assert webhook.webhook_target_error("http://") is not None

    def test_rejects_loopback(self):
        assert webhook.webhook_target_error("http://127.0.0.1/hook") is not None

    def test_rejects_private(self):
        assert webhook.webhook_target_error("http://10.1.2.3/hook") is not None

    def test_allows_public_ip_literal(self):
        # An IP literal skips DNS; 93.184.216.34 is a public address.
        assert webhook.webhook_target_error("https://93.184.216.34/hook") is None


# ---------------------------------------------------------------------------
# deliver
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


class _FakeClient:
    """Captures the last POST; returns a preset status code."""

    last: dict = {}

    def __init__(self, status_code=200, boom=False, timeout=None):
        self._status = status_code
        self._boom = boom

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, content=None, headers=None):
        _FakeClient.last = {"url": url, "content": content, "headers": headers}
        if self._boom:
            import httpx

            raise httpx.RequestError("boom")
        return _FakeResp(self._status)


class TestDeliver:
    def test_2xx_is_ok_and_signs_when_secret_set(self, monkeypatch):
        monkeypatch.setattr(webhook, "webhook_target_error", lambda url: None)
        monkeypatch.setattr(webhook.httpx, "Client", lambda timeout=None: _FakeClient(200))
        ok, detail = webhook.deliver("https://hooks.example.com/x", {"a": 1}, secret="s3cr3t")
        assert ok is True and "200" in detail
        sent = _FakeClient.last
        expected = hmac.new(b"s3cr3t", sent["content"], hashlib.sha256).hexdigest()
        assert sent["headers"]["X-AIOPS-Signature"] == f"sha256={expected}"
        # Body is the exact JSON that was signed.
        assert json.loads(sent["content"]) == {"a": 1}

    def test_no_signature_without_secret(self, monkeypatch):
        monkeypatch.setattr(webhook, "webhook_target_error", lambda url: None)
        monkeypatch.setattr(webhook.httpx, "Client", lambda timeout=None: _FakeClient(200))
        webhook.deliver("https://hooks.example.com/x", {"a": 1})
        assert "X-AIOPS-Signature" not in _FakeClient.last["headers"]

    def test_non_2xx_is_not_ok(self, monkeypatch):
        monkeypatch.setattr(webhook, "webhook_target_error", lambda url: None)
        monkeypatch.setattr(webhook.httpx, "Client", lambda timeout=None: _FakeClient(500))
        ok, detail = webhook.deliver("https://hooks.example.com/x", {})
        assert ok is False and "500" in detail

    def test_guard_blocks_before_any_request(self, monkeypatch):
        monkeypatch.setattr(webhook, "webhook_target_error", lambda url: "nope")
        # If deliver tried to POST this would raise; the guard must return first.
        ok, detail = webhook.deliver("http://10.0.0.1/x", {})
        assert ok is False and detail == "nope"

    def test_request_error_is_swallowed(self, monkeypatch):
        monkeypatch.setattr(webhook, "webhook_target_error", lambda url: None)
        monkeypatch.setattr(webhook.httpx, "Client", lambda timeout=None: _FakeClient(boom=True))
        ok, detail = webhook.deliver("https://hooks.example.com/x", {})
        assert ok is False and "unreachable" in detail


# ---------------------------------------------------------------------------
# iter_webhook_targets
# ---------------------------------------------------------------------------


@pytest.fixture
def user_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "webhook-test-secret")
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)
    from src.auth import store as user_store

    user_store.init_db()
    yield tmp_path


class TestTargets:
    def test_system_target_only_when_auth_off(self, user_env, monkeypatch):
        monkeypatch.setattr(
            webhook,
            "_system_notifications",
            lambda: {"webhookEnabled": True, "webhookUrl": "https://sys.example.com/h"},
        )
        targets = list(webhook.iter_webhook_targets())
        assert targets == [("https://sys.example.com/h", "", "warning")]

    def test_disabled_system_yields_nothing(self, user_env, monkeypatch):
        monkeypatch.setattr(
            webhook,
            "_system_notifications",
            lambda: {"webhookEnabled": False, "webhookUrl": "https://sys.example.com/h"},
        )
        assert list(webhook.iter_webhook_targets()) == []

    def test_per_admin_override_when_auth_on(self, user_env, monkeypatch):
        from src.auth import store as user_store

        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setattr(webhook, "_system_notifications", lambda: {})
        admin = user_store.create_user("boss", "boss-long-password", role="admin")
        user_store.create_user("alice", "alices-long-password", role="user")
        user_store.set_user_settings(
            admin.id,
            {"notifications": {"webhookEnabled": True, "webhookUrl": "https://admin.example.com/h",
                               "webhookSecret": "k", "webhookMinSeverity": "error"}},
        )
        targets = list(webhook.iter_webhook_targets())
        assert targets == [("https://admin.example.com/h", "k", "error")]

    def test_dedup_system_and_admin_same_url(self, user_env, monkeypatch):
        from src.auth import store as user_store

        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setattr(
            webhook,
            "_system_notifications",
            lambda: {"webhookEnabled": True, "webhookUrl": "https://same.example.com/h"},
        )
        admin = user_store.create_user("boss", "boss-long-password", role="admin")
        user_store.set_user_settings(
            admin.id,
            {"notifications": {"webhookEnabled": True, "webhookUrl": "https://same.example.com/h"}},
        )
        targets = list(webhook.iter_webhook_targets())
        assert len(targets) == 1


# ---------------------------------------------------------------------------
# dispatch (severity filter + meta skip) + notify() wiring
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_severity_filter(self, monkeypatch):
        monkeypatch.setattr(
            webhook, "iter_webhook_targets", lambda: [("https://x/y", "", "warning")]
        )
        fired = []
        monkeypatch.setattr(webhook, "_fire", lambda url, secret, payload: fired.append(url))

        webhook.dispatch({"type": "action.blocked", "severity": "info"})
        assert fired == []  # info < warning
        webhook.dispatch({"type": "action.blocked", "severity": "error"})
        assert fired == ["https://x/y"]  # error >= warning

    def test_meta_webhook_events_skipped(self, monkeypatch):
        monkeypatch.setattr(
            webhook, "iter_webhook_targets", lambda: [("https://x/y", "", "info")]
        )
        fired = []
        monkeypatch.setattr(webhook, "_fire", lambda url, secret, payload: fired.append(url))
        webhook.dispatch({"type": "webhook.test", "severity": "critical"})
        assert fired == []

    def test_notify_invokes_dispatch(self, tmp_path, monkeypatch):
        # Isolate the inbox to a temp file, then confirm notify() forwards the
        # stored note to webhook.dispatch.
        store = note_store.NotificationStore(path=tmp_path)
        note_store.set_notification_store(store)
        seen = {}
        monkeypatch.setattr(webhook, "dispatch", lambda note: seen.update(note))
        note_store.notify(type="action.blocked", severity="error", title="t", message="m")
        assert seen.get("type") == "action.blocked"
        assert seen.get("severity") == "error"
        note_store.set_notification_store(None)  # reset global
