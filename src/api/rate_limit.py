"""
Constitutional AIOps - per-caller sliding-window throttles.

Why this exists: only /auth/login and /auth/signup were throttled, so the
endpoints that actually cost money or change infrastructure were not. Bedrock is
billed per token and /chat had no ceiling at all, which combined with public
signup made token spend unbounded. /tools/call, the action approve/execute pair
and incident remediation change real containers.

The algorithm is the same per-IP sliding window auth.py already used, lifted here
so there is one implementation rather than a second, subtly different one. It is
in-process and therefore per-worker and reset by a restart, exactly like the auth
throttles. That is a deliberate floor, not a distributed rate limiter: it bounds a
runaway loop and a single abusive session, which is what the cost and blast-radius
problems here actually are.

Keying prefers the authenticated user id over the address, because a signed-in
caller is the thing being limited; the address is the fallback for anonymous or
partially-mocked requests.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import HTTPException, Request, status

# How many proxies we trust in front of the app. Caddy is one hop. A raw
# client-supplied X-Forwarded-For is fully spoofable, so the genuine peer is the
# value the trusted proxy APPENDED to the RIGHT; parse from the right and ignore
# anything the caller prepended. Mirrors the login throttle's original reasoning.
_TRUSTED_PROXY_HOPS = max(1, int(os.getenv("TRUSTED_PROXY_HOPS", "1")))


def client_ip(request: Request) -> str:
    """Resolve a throttle key the caller cannot trivially forge."""
    forwarded = ""
    try:
        raw = request.headers.get("x-forwarded-for") or ""
        # Route handlers in this suite are frequently called directly with a
        # MagicMock request, whose .get() returns another MagicMock: truthy, not
        # a string, and not iterable. Insist on a real str rather than letting
        # that explode inside the parser.
        forwarded = raw if isinstance(raw, str) else ""
    except Exception:  # noqa: BLE001 - tolerate mock/partial request objects
        forwarded = ""
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            idx = max(0, len(parts) - _TRUSTED_PROXY_HOPS)
            return parts[idx]
    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return host if isinstance(host, str) and host else "unknown"


def caller_key(request: Request, user: object = None) -> str:
    """Prefer the authenticated identity; fall back to the address."""
    user_id = getattr(user, "id", None)
    if isinstance(user_id, str) and user_id:
        return f"user:{user_id}"
    return f"ip:{client_ip(request)}"


class SlidingWindow:
    """A fixed-size sliding window of event timestamps per key."""

    def __init__(self, name: str, max_events: int, window_seconds: int, detail: str = ""):
        self.name = name
        self.max_events = max_events
        self.window_seconds = window_seconds
        self.detail = detail or (
            f"Too many {name} requests. Try again in a few minutes."
        )
        self._events: dict[str, list[float]] = {}

    def _recent(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        recent = [t for t in self._events.get(key, []) if t > cutoff]
        if recent:
            self._events[key] = recent
        else:
            self._events.pop(key, None)
        return recent

    def check(self, key: str, now: Optional[float] = None) -> None:
        """Record this attempt and raise 429 once the window is full.

        The attempt is charged BEFORE the work runs, so a caller cannot escape
        the window by triggering failures - the same ordering fix the signup
        throttle needed.
        """
        moment = time.time() if now is None else now
        recent = self._recent(key, moment)
        if len(recent) >= self.max_events:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.detail,
                headers={"Retry-After": str(self.window_seconds)},
            )
        self._events.setdefault(key, []).append(moment)

    def reset(self) -> None:
        """Drop all state (used by tests)."""
        self._events.clear()


# Chat drives Bedrock token spend, so this one is a cost control as much as an
# abuse control. Generous for a human conversation, bounded for a loop.
CHAT = SlidingWindow(
    "chat",
    max_events=int(os.getenv("AIOPS_RATE_CHAT_PER_HOUR", "120")),
    window_seconds=3600,
    detail="Too many chat requests. Try again shortly.",
)

# Tool calls and action execution change real infrastructure.
TOOLS = SlidingWindow(
    "tool",
    max_events=int(os.getenv("AIOPS_RATE_TOOLS_PER_HOUR", "120")),
    window_seconds=3600,
    detail="Too many tool calls. Try again shortly.",
)

ACTIONS = SlidingWindow(
    "action",
    max_events=int(os.getenv("AIOPS_RATE_ACTIONS_PER_HOUR", "60")),
    window_seconds=3600,
    detail="Too many action requests. Try again shortly.",
)

__all__ = [
    "ACTIONS",
    "CHAT",
    "TOOLS",
    "SlidingWindow",
    "caller_key",
    "client_ip",
]
