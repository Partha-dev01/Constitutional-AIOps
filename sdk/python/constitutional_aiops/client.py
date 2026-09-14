"""A small, dependency-free client over the Constitutional AIOps REST API.

Standard library only (``urllib``, ``json``). This is the hand-written ergonomic
layer; the generated, fully typed core slots underneath it (see ``../README.md``).
The methods here return plain decoded JSON (dicts and lists), so the surface stays
zero-dependency and forward-compatible with the typed core.

Since 0.2.0 the ergonomic surface spans the high-value tags an operator or script
actually reaches: incidents, actions (through the constitutional gate), agents,
the episodic graph, audit, notifications, benchmark, metrics, chat, and
self-service personal access tokens. The long tail of the 127-path API stays
available through the generated typed core.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterator, List, Optional

from .errors import (
    AIOpsError,
    AuthError,
    ConstitutionalRefusal,
    NotFound,
    RateLimited,
)

_CONSTITUTIONAL_CODES = {
    "action_tools_disabled",
    "approval_required",
    "validation_blocked",
    "container_not_whitelisted",
}

# Statuses worth retrying, split by safety. 429 means the request was rejected
# before it did anything, so it is safe to retry on any method. 5xx/network
# failures are ambiguous for writes (the server may have acted), so they are only
# retried for idempotent GETs, never for a POST that might double-submit an action.
_RETRY_ANY_METHOD = {429}
_RETRY_GET_ONLY = {502, 503, 504}


class AIOpsClient:
    """Client for one Constitutional AIOps instance.

    Args:
        base_url: The instance origin, for example ``https://host.example.com``.
            ``/api/v1`` is appended automatically unless the URL already ends in
            an API path.
        token: A bearer token (a personal access token, ``aiops_pat_...``, or a
            session token you already hold). Optional against an instance running
            with ``AUTH_REQUIRED`` unset.
        timeout: Per-request timeout in seconds.
        max_retries: How many times to retry a transient failure. ``0`` (the
            default) never retries, keeping behavior predictable. Retries use
            exponential backoff and honor a ``Retry-After`` header. A 429 is
            retried on any method; 5xx and network errors are retried only for
            GET, so a POST is never silently resent.
        backoff: Base backoff in seconds; attempt ``n`` waits ``backoff * 2**n``
            unless the server sent a ``Retry-After``.
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 90.0,
        *,
        max_retries: int = 0,
        backoff: float = 0.5,
    ) -> None:
        base = base_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = base + "/api/v1"
        self._base = base
        self._token = token
        self._timeout = timeout
        self._max_retries = max(0, int(max_retries))
        self._backoff = max(0.0, float(backoff))

    # ── context manager (no persistent socket; supports `with` idiom) ──────────
    def __enter__(self) -> "AIOpsClient":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def close(self) -> None:
        """No-op. ``urllib`` holds no persistent connection; provided for symmetry."""

    # ── low-level request ────────────────────────────────────────────────────
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Issue one request and return the decoded JSON, raising a typed error."""
        method = method.upper()
        url = self._url(path, params)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                if self._retryable(method, exc.code) and attempt < self._max_retries:
                    self._sleep(attempt, exc)
                    attempt += 1
                    continue
                raise self._to_error(exc) from None
            except urllib.error.URLError as exc:
                if method == "GET" and attempt < self._max_retries:
                    self._sleep(attempt, None)
                    attempt += 1
                    continue
                raise AIOpsError(f"request failed: {exc.reason}") from None

    # ── pagination ───────────────────────────────────────────────────────────
    def paginate(self, path: str, *, page_size: int = 50, **filters: Any) -> Iterator[Dict[str, Any]]:
        """Yield every item across pages of a list endpoint.

        Works with the uniform ``{items, total, page, page_size, has_more}``
        envelope. Extra keyword filters (``status``, ``severity`` and the like)
        are passed straight through as query parameters.
        """
        page = 1
        while True:
            params: Dict[str, Any] = {"page": page, "page_size": page_size, **filters}
            payload = self.request("GET", path, params=params)
            items: List[Dict[str, Any]] = (payload or {}).get("items", [])
            for item in items:
                yield item
            if not (payload or {}).get("has_more"):
                return
            page += 1

    # ── incidents ─────────────────────────────────────────────────────────────
    def list_incidents(self, **filters: Any) -> Dict[str, Any]:
        """One page of incidents. Use ``paginate('/incidents/')`` for all of them."""
        return self.request("GET", "/incidents/", params=filters)

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/incidents/{incident_id}")

    def incident_stats(self) -> Dict[str, Any]:
        return self.request("GET", "/incidents/stats")

    def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("POST", "/incidents/", body=data)

    def update_incident(self, incident_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("PATCH", f"/incidents/{incident_id}", body=data)

    def similar_incidents(self, incident_id: str, *, limit: Optional[int] = None) -> Dict[str, Any]:
        return self.request("GET", f"/incidents/{incident_id}/similar", params={"limit": limit})

    # ── actions (every method still passes the constitutional gate) ────────────
    def list_actions(self, **filters: Any) -> Dict[str, Any]:
        """One page of actions. Use ``paginate('/actions/')`` for all of them."""
        return self.request("GET", "/actions/", params=filters)

    def get_action(self, action_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/actions/{action_id}")

    def pending_actions(self) -> Dict[str, Any]:
        return self.request("GET", "/actions/pending")

    def create_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose an action. The validator may hold it for approval or block it."""
        return self.request("POST", "/actions/", body=data)

    def approve_action(self, action_id: str, *, approved: bool, approved_by: str, comments: str = "") -> Any:
        """Approve or reject a pending action. Still passes the constitutional gate."""
        return self.request(
            "POST",
            f"/actions/{action_id}/approve",
            body={"approved": approved, "approved_by": approved_by, "comments": comments},
        )

    def execute_action(self, action_id: str) -> Any:
        """Execute an approved action. The kill-switch and validator still apply."""
        return self.request("POST", f"/actions/{action_id}/execute")

    def cancel_action(self, action_id: str, *, reason: Optional[str] = None) -> Any:
        return self.request("POST", f"/actions/{action_id}/cancel", params={"reason": reason})

    def action_stats(self) -> Dict[str, Any]:
        return self.request("GET", "/actions/stats")

    def confidence_formula(self) -> Dict[str, Any]:
        """The graduated-autonomy confidence formula the gate uses."""
        return self.request("GET", "/actions/confidence/formula")

    # ── agents ─────────────────────────────────────────────────────────────────
    def fast_agent_stats(self) -> Dict[str, Any]:
        return self.request("GET", "/agents/fast/stats")

    def fast_agent_activity(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        return self.request("GET", "/agents/fast/activity", params={"limit": limit, "offset": offset})

    def reasoning_agent_stats(self) -> Dict[str, Any]:
        return self.request("GET", "/agents/reasoning/stats")

    def reasoning_agent_activity(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        return self.request("GET", "/agents/reasoning/activity", params={"limit": limit, "offset": offset})

    # ── episodic graph ──────────────────────────────────────────────────────────
    def graph_stats(self) -> Dict[str, Any]:
        return self.request("GET", "/graph/stats")

    def topology(self, *, window_hours: Optional[int] = None, buckets: Optional[int] = None) -> Dict[str, Any]:
        return self.request("GET", "/graph/topology", params={"window_hours": window_hours, "buckets": buckets})

    def services(self, *, status_filter: Optional[str] = None) -> Dict[str, Any]:
        return self.request("GET", "/graph/services", params={"status_filter": status_filter})

    def episodes(self, **filters: Any) -> Dict[str, Any]:
        """Episodic-memory episodes. Filters: ``limit``, ``since_hours``, ``min_confidence`` and more."""
        return self.request("GET", "/graph/episodes", params=filters)

    def get_episode(self, episode_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/graph/episodes/{episode_id}")

    def similar_episodes(self, episode_id: str, *, limit: Optional[int] = None) -> Dict[str, Any]:
        return self.request("GET", f"/graph/episodes/{episode_id}/similar", params={"limit": limit})

    # ── audit ────────────────────────────────────────────────────────────────
    def audit_events(self, **filters: Any) -> Dict[str, Any]:
        """The audit trail. Filters: ``limit``, ``days``, ``event_type``, ``resource_type``, ``actor_id``."""
        return self.request("GET", "/audit/", params=filters)

    def audit_event_types(self) -> Any:
        return self.request("GET", "/audit/event-types")

    # ── personal access tokens (self-service) ──────────────────────────────────
    def list_tokens(self) -> Any:
        return self.request("GET", "/auth/tokens")

    def create_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mint a personal access token. The secret is returned once, here only."""
        return self.request("POST", "/auth/tokens", body=data)

    def revoke_token(self, token_id: str) -> Any:
        return self.request("DELETE", f"/auth/tokens/{token_id}")

    # ── notifications ──────────────────────────────────────────────────────────
    def notifications(self, **filters: Any) -> Dict[str, Any]:
        """The alert inbox. Filters: ``limit``, ``unread_only``, ``severity``."""
        return self.request("GET", "/notifications/", params=filters)

    def unread_count(self) -> Dict[str, Any]:
        return self.request("GET", "/notifications/unread-count")

    def mark_read(self, data: Dict[str, Any]) -> Any:
        return self.request("POST", "/notifications/read", body=data)

    def clear_notifications(self) -> Any:
        return self.request("DELETE", "/notifications/")

    # ── benchmark (reproduce the paper, or evaluate your own endpoint) ─────────
    def evaluate_endpoint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a few sample cases through the configured endpoint and score them."""
        return self.request("POST", "/benchmark/evaluate-endpoint", body=data)

    def benchmark_status(self) -> Dict[str, Any]:
        return self.request("GET", "/benchmark/status")

    def benchmark_results(self) -> Any:
        return self.request("GET", "/benchmark/results")

    # ── metrics ────────────────────────────────────────────────────────────────
    def metrics(self) -> Dict[str, Any]:
        return self.request("GET", "/metrics")

    def metrics_history(self, *, limit: Optional[int] = None, agent: Optional[str] = None) -> Dict[str, Any]:
        return self.request("GET", "/metrics/history", params={"limit": limit, "agent": agent})

    def metrics_latency(self, *, agent: Optional[str] = None) -> Dict[str, Any]:
        return self.request("GET", "/metrics/latency", params={"agent": agent})

    # ── chat ────────────────────────────────────────────────────────────────────
    def chat(self, message: str, *, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """One non-streaming chat turn. Use ``stream_chat`` for token-by-token output."""
        body: Dict[str, Any] = {"message": message}
        if conversation_id:
            body["conversation_id"] = conversation_id
        return self.request("POST", "/chat/", body=body)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Root-cause analysis over supplied context (the reasoning agent)."""
        return self.request("POST", "/chat/analyze", body=data)

    def list_conversations(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        return self.request("GET", "/chat/conversations", params={"limit": limit, "offset": offset})

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/chat/conversations/{conversation_id}")

    # ── chat streaming (SSE over the stdlib) ─────────────────────────────────
    def stream_chat(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        on_delta: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Stream a chat turn, returning the final ``done`` payload.

        The endpoint emits Server-Sent Events (``meta``, ``tool_result``,
        ``delta``, ``done``). ``on_delta`` receives each token chunk as it
        arrives; the return value is the complete response from the ``done``
        frame, whose ``message.content`` is authoritative.
        """
        url = self._url("/chat/stream", None)
        body = {"message": message}
        if conversation_id:
            body["conversation_id"] = conversation_id
        headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        done: Dict[str, Any] = {}
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                event = "message"
                for raw_line in resp:
                    line = raw_line.decode("utf-8").rstrip("\n")
                    if line.startswith("event:"):
                        event = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        payload = line[len("data:"):].strip()
                        if not payload:
                            continue
                        parsed = json.loads(payload)
                        if event == "delta" and on_delta:
                            on_delta(parsed.get("content", ""))
                        elif event == "done":
                            done = parsed
                        elif event == "error":
                            raise AIOpsError(parsed.get("message", "chat stream error"))
        except urllib.error.HTTPError as exc:
            raise self._to_error(exc) from None
        return done

    # ── internals ────────────────────────────────────────────────────────────
    def _url(self, path: str, params: Optional[Dict[str, Any]]) -> str:
        url = self._base + "/" + path.lstrip("/")
        if params:
            flat = [(k, v) for k, v in params.items() if v is not None]
            if flat:
                url = url + "?" + urllib.parse.urlencode(flat, doseq=True)
        return url

    def _retryable(self, method: str, status: int) -> bool:
        if status in _RETRY_ANY_METHOD:
            return True
        return method == "GET" and status in _RETRY_GET_ONLY

    def _sleep(self, attempt: int, exc: "Optional[urllib.error.HTTPError]") -> None:
        delay = self._backoff * (2 ** attempt)
        if exc is not None:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if retry_after:
                try:
                    delay = min(float(retry_after), 60.0)
                except ValueError:
                    pass
        if delay > 0:
            time.sleep(delay)

    def _to_error(self, exc: "urllib.error.HTTPError") -> AIOpsError:
        status = exc.code
        detail: Any = None
        error_code: Optional[str] = None
        try:
            parsed = json.loads(exc.read().decode("utf-8"))
            detail = parsed.get("detail", parsed) if isinstance(parsed, dict) else parsed
            if isinstance(detail, dict):
                error_code = detail.get("error_code")
        except Exception:
            detail = None
        message = str(detail) if detail else exc.reason

        if error_code in _CONSTITUTIONAL_CODES:
            return ConstitutionalRefusal(message, error_code=error_code, verdict=detail, status=status)
        if status == 401:
            return AuthError(message, status=status, details=detail)
        if status == 404:
            return NotFound(message, status=status, details=detail)
        if status == 429:
            return RateLimited(message, status=status, details=detail)
        return AIOpsError(message, status=status, details=detail)
