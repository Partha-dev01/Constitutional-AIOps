"""Smoke tests for the hand-written AIOpsClient.

Standard-library ``unittest`` only, no test-runner dependency (run with
``python -m unittest`` from ``sdk/python``). ``urllib.request.urlopen`` is
monkeypatched so nothing hits the network; the tests assert URL/method/param/body
construction, the typed-error mapping, and the 0.2.0 retry policy.
"""

from __future__ import annotations

import io
import unittest
import urllib.error
from typing import Any, Dict, List, Optional
from unittest import mock

from constitutional_aiops import (
    AIOpsClient,
    AuthError,
    ConstitutionalRefusal,
    NotFound,
    RateLimited,
    INSIGHT_KINDS,
    INSIGHT_TIERS,
    INSIGHT_UNAVAILABLE_REASONS,
)
from constitutional_aiops import __version__


class _FakeResp:
    def __init__(self, body: str = "{}") -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_exc: Any) -> bool:
        return False


def _http_error(code: int, body: str = "{}", headers: Optional[Dict[str, str]] = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "http://x/api/v1/test", code, "err", headers or {}, io.BytesIO(body.encode("utf-8"))
    )


class RequestConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = AIOpsClient("https://host.example.com", token="aiops_pat_abc")

    def _capture(self, resp: _FakeResp) -> List[Any]:
        calls: List[Any] = []

        def fake_urlopen(req: Any, timeout: float = 0) -> _FakeResp:  # noqa: ARG001
            calls.append(req)
            return resp

        return calls, fake_urlopen  # type: ignore[return-value]

    def test_base_url_appends_api_v1_once(self) -> None:
        self.assertTrue(AIOpsClient("https://h")._base.endswith("/api/v1"))
        self.assertEqual(AIOpsClient("https://h/api/v1")._base.count("/api/v1"), 1)

    def test_get_with_params_drops_none_and_sends_bearer(self) -> None:
        calls, fake = self._capture(_FakeResp('{"items": []}'))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.similar_incidents("inc-1", limit=None)
        req = calls[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertNotIn("?", req.full_url)  # limit=None dropped -> no query string
        self.assertTrue(req.full_url.endswith("/api/v1/incidents/inc-1/similar"))
        self.assertEqual(req.get_header("Authorization"), "Bearer aiops_pat_abc")

    def test_query_param_encoded(self) -> None:
        calls, fake = self._capture(_FakeResp("{}"))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.cancel_action("act-9", reason="stale")
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.endswith("/actions/act-9/cancel?reason=stale"))

    def test_post_body_serialized(self) -> None:
        calls, fake = self._capture(_FakeResp('{"id": "tok-1"}'))
        with mock.patch("urllib.request.urlopen", fake):
            out = self.client.create_token({"name": "ci", "scopes": ["read"]})
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertIn(b'"name": "ci"', req.data)
        self.assertEqual(out, {"id": "tok-1"})

    def test_new_endpoints_hit_expected_paths(self) -> None:
        cases = {
            lambda: self.client.action_stats(): "/api/v1/actions/stats",
            lambda: self.client.graph_stats(): "/api/v1/graph/stats",
            lambda: self.client.audit_event_types(): "/api/v1/audit/event-types",
            lambda: self.client.unread_count(): "/api/v1/notifications/unread-count",
            lambda: self.client.metrics(): "/api/v1/metrics",
            lambda: self.client.reasoning_agent_stats(): "/api/v1/agents/reasoning/stats",
        }
        for call, expected in cases.items():
            calls, fake = self._capture(_FakeResp("{}"))
            with mock.patch("urllib.request.urlopen", fake):
                call()
            self.assertTrue(calls[0].full_url.endswith(expected), calls[0].full_url)


class GenerativeUIAndToolsTests(unittest.TestCase):
    """0.3.0 surface: generative-UI insights, the tool registry, chat decisions."""

    def setUp(self) -> None:
        self.client = AIOpsClient("https://host.example.com", token="aiops_pat_abc")

    def _capture(self, resp: _FakeResp):
        calls: List[Any] = []

        def fake_urlopen(req: Any, timeout: float = 0) -> _FakeResp:  # noqa: ARG001
            calls.append(req)
            return resp

        return calls, fake_urlopen

    def test_explain_posts_kind_tier_payload(self) -> None:
        calls, fake = self._capture(_FakeResp('{"available": false, "reason": "no_endpoint"}'))
        with mock.patch("urllib.request.urlopen", fake):
            out = self.client.explain("anomaly", {"count": 3}, tier="reasoning")
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.endswith("/api/v1/insights/explain"))
        self.assertIn(b'"kind": "anomaly"', req.data)
        self.assertIn(b'"tier": "reasoning"', req.data)
        self.assertIn(b'"payload"', req.data)
        self.assertEqual(out, {"available": False, "reason": "no_endpoint"})

    def test_explain_defaults_to_fast_tier(self) -> None:
        calls, fake = self._capture(_FakeResp("{}"))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.explain("spike", {"value": 1})
        self.assertIn(b'"tier": "fast"', calls[0].data)

    def test_set_insight_preferences_sends_only_given_fields(self) -> None:
        calls, fake = self._capture(_FakeResp("{}"))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.set_insight_preferences(enabled=True)
        req = calls[0]
        self.assertEqual(req.get_method(), "PUT")
        self.assertTrue(req.full_url.endswith("/api/v1/insights/preferences"))
        self.assertIn(b'"enabled": true', req.data)
        self.assertNotIn(b"autoExplain", req.data)

    def test_set_insight_preferences_maps_auto_explain(self) -> None:
        calls, fake = self._capture(_FakeResp("{}"))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.set_insight_preferences(auto_explain=True)
        self.assertIn(b'"autoExplain": true', calls[0].data)

    def test_decide_chat_action_posts_decision(self) -> None:
        calls, fake = self._capture(_FakeResp('{"status": "executed", "success": true}'))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.decide_chat_action("act-77", approved=True, comment="ok")
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.endswith("/api/v1/chat/actions/act-77/decision"))
        self.assertIn(b'"approved": true', req.data)
        self.assertIn(b'"comment": "ok"', req.data)

    def test_delete_conversation_uses_delete(self) -> None:
        calls, fake = self._capture(_FakeResp("{}"))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.delete_conversation("conv-1")
        req = calls[0]
        self.assertEqual(req.get_method(), "DELETE")
        self.assertTrue(req.full_url.endswith("/api/v1/chat/conversations/conv-1"))

    def test_call_tool_posts_name_and_parameters(self) -> None:
        calls, fake = self._capture(_FakeResp('{"success": true, "data": {}}'))
        with mock.patch("urllib.request.urlopen", fake):
            self.client.call_tool("find_similar", {"title": "db timeout"})
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.endswith("/api/v1/tools/call"))
        self.assertIn(b'"tool_name": "find_similar"', req.data)
        self.assertIn(b'"title": "db timeout"', req.data)

    def test_registry_read_paths(self) -> None:
        cases = {
            lambda: self.client.tools(): "/api/v1/tools/",
            lambda: self.client.get_tool("restart_service"): "/api/v1/tools/restart_service",
            lambda: self.client.insight_preferences(): "/api/v1/insights/preferences",
        }
        for call, expected in cases.items():
            calls, fake = self._capture(_FakeResp("{}"))
            with mock.patch("urllib.request.urlopen", fake):
                call()
            self.assertTrue(calls[0].full_url.endswith(expected), calls[0].full_url)

    def test_insight_vocab_constants(self) -> None:
        for kind in ("anomaly", "incident", "graph_copilot", "generic"):
            self.assertIn(kind, INSIGHT_KINDS)
        self.assertEqual(set(INSIGHT_TIERS), {"fast", "reasoning"})
        self.assertIn("ai_widgets_disabled", INSIGHT_UNAVAILABLE_REASONS)
        self.assertIn("budget_reached", INSIGHT_UNAVAILABLE_REASONS)


class ErrorMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = AIOpsClient("https://h")

    def _raise(self, err: urllib.error.HTTPError):
        def fake_urlopen(req: Any, timeout: float = 0):  # noqa: ARG001
            raise err

        return fake_urlopen

    def test_401_404_429_map(self) -> None:
        for code, exc_type in [(401, AuthError), (404, NotFound), (429, RateLimited)]:
            with mock.patch("urllib.request.urlopen", self._raise(_http_error(code, '{"detail": "x"}'))):
                with self.assertRaises(exc_type):
                    self.client.get_incident("i")

    def test_constitutional_refusal(self) -> None:
        body = '{"detail": {"error_code": "approval_required", "message": "held"}}'
        with mock.patch("urllib.request.urlopen", self._raise(_http_error(403, body))):
            with self.assertRaises(ConstitutionalRefusal) as ctx:
                self.client.execute_action("a")
        self.assertEqual(ctx.exception.error_code, "approval_required")


class RetryPolicyTests(unittest.TestCase):
    def test_429_retried_then_succeeds(self) -> None:
        client = AIOpsClient("https://h", max_retries=1)
        seq = [_http_error(429, headers={"Retry-After": "0"}), _FakeResp('{"ok": true}')]

        def fake_urlopen(req: Any, timeout: float = 0):  # noqa: ARG001
            item = seq.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with mock.patch("constitutional_aiops.client.time.sleep"):
            with mock.patch("urllib.request.urlopen", fake_urlopen):
                out = client.create_action({"x": 1})  # POST + 429 -> retry is safe
        self.assertEqual(out, {"ok": True})
        self.assertEqual(seq, [])

    def test_post_5xx_not_retried_but_get_5xx_is(self) -> None:
        # POST 503 -> raised immediately (a write must never be silently resent)
        client = AIOpsClient("https://h", max_retries=3)
        calls = {"n": 0}

        def post_fail(req: Any, timeout: float = 0):  # noqa: ARG001
            calls["n"] += 1
            raise _http_error(503)

        with mock.patch("constitutional_aiops.client.time.sleep"):
            with mock.patch("urllib.request.urlopen", post_fail):
                with self.assertRaises(Exception):
                    client.create_action({"x": 1})
        self.assertEqual(calls["n"], 1)

        # GET 503 -> retried then succeeds
        seq: List[Any] = [_http_error(503), _FakeResp("{}")]

        def get_flaky(req: Any, timeout: float = 0):  # noqa: ARG001
            item = seq.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with mock.patch("constitutional_aiops.client.time.sleep"):
            with mock.patch("urllib.request.urlopen", get_flaky):
                client.graph_stats()
        self.assertEqual(seq, [])


class VersionTests(unittest.TestCase):
    def test_version_string_present(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
