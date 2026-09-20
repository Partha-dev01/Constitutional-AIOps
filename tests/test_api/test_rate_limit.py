"""M2: the endpoints that cost money or change infrastructure are throttled.

Only /auth/login and /auth/signup had any ceiling. Bedrock bills per token and
/chat had none, so with public signup enabled token spend was unbounded and
unwatched (no aiops budget even covered Bedrock). /tools/call and the action
approve/execute/remediate group restart real containers.

These cover the window mechanics and the keying, which is where this kind of
control usually goes wrong: a per-IP key that the caller can rotate, or an
attempt charged after the work instead of before.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.rate_limit import SlidingWindow, caller_key, client_ip


class TestSlidingWindow:
    def test_allows_up_to_the_limit_then_refuses(self):
        w = SlidingWindow("t", max_events=3, window_seconds=60)
        for _ in range(3):
            w.check("k", now=1000.0)
        with pytest.raises(HTTPException) as exc:
            w.check("k", now=1000.0)
        assert exc.value.status_code == 429

    def test_window_slides(self):
        w = SlidingWindow("t", max_events=2, window_seconds=60)
        w.check("k", now=1000.0)
        w.check("k", now=1001.0)
        with pytest.raises(HTTPException):
            w.check("k", now=1002.0)
        # past the window, the old events age out
        w.check("k", now=1100.0)

    def test_keys_are_independent(self):
        w = SlidingWindow("t", max_events=1, window_seconds=60)
        w.check("a", now=1000.0)
        w.check("b", now=1000.0)
        with pytest.raises(HTTPException):
            w.check("a", now=1000.0)

    def test_attempt_is_charged_before_the_work(self):
        """A caller must not escape the window by causing failures."""
        w = SlidingWindow("t", max_events=2, window_seconds=60)
        w.check("k", now=1000.0)
        w.check("k", now=1000.0)
        with pytest.raises(HTTPException):
            w.check("k", now=1000.0)

    def test_retry_after_header_is_set(self):
        w = SlidingWindow("t", max_events=1, window_seconds=42)
        w.check("k", now=1000.0)
        with pytest.raises(HTTPException) as exc:
            w.check("k", now=1000.0)
        assert exc.value.headers["Retry-After"] == "42"

    def test_reset_clears_state(self):
        w = SlidingWindow("t", max_events=1, window_seconds=60)
        w.check("k", now=1000.0)
        w.reset()
        w.check("k", now=1000.0)


def _request(xff=None, peer="203.0.113.9"):
    req = MagicMock()
    req.headers.get.return_value = xff
    req.client.host = peer
    return req


class TestKeying:
    def test_spoofed_forwarded_prefix_is_ignored(self):
        """The trusted proxy appends on the RIGHT, so parse from the right."""
        assert client_ip(_request(xff="1.1.1.1, 10.0.0.2")) == "10.0.0.2"

    def test_falls_back_to_the_peer_without_a_forwarded_header(self):
        assert client_ip(_request(xff=None, peer="198.51.100.5")) == "198.51.100.5"

    def test_tolerates_a_bare_mock_request(self):
        """Route handlers are called directly with MagicMock all over this suite."""
        assert client_ip(MagicMock()) == "unknown"

    def test_authenticated_caller_is_keyed_by_identity_not_address(self):
        """Otherwise one user behind a shared NAT throttles everyone else."""
        user = MagicMock()
        user.id = "u-123"
        assert caller_key(_request(), user) == "user:u-123"

    def test_anonymous_caller_falls_back_to_address(self):
        assert caller_key(_request(peer="198.51.100.7"), None) == "ip:198.51.100.7"


class TestWsTokenNotIssuedUnderAuth:
    """H4: the WS token was one shared, never-rotated secret in a query string.

    Caddy logs the request line, so it sat in `docker logs` in plaintext. The
    session cookie is checked first and is sufficient, so under AUTH_REQUIRED the
    backend now issues nothing and the socket authenticates from the cookie.
    Self-host runs without in-app auth still need the token and still get it.
    """

    @pytest.mark.asyncio
    async def test_token_is_withheld_when_auth_is_required(self, monkeypatch):
        import src.main as main

        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setenv("WS_TOKEN", "super-secret")
        assert await main.get_ws_token() == {"token": ""}

    @pytest.mark.asyncio
    async def test_token_is_still_issued_without_in_app_auth(self, monkeypatch):
        import src.main as main

        monkeypatch.setenv("AUTH_REQUIRED", "false")
        monkeypatch.setenv("WS_TOKEN", "super-secret")
        assert await main.get_ws_token() == {"token": "super-secret"}
