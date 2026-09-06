"""A small, dependency-free client over the Constitutional AIOps REST API.

Standard library only (``urllib``, ``json``). This is the hand-written ergonomic
layer; the generated, fully typed core will slot underneath it later (see
``../README.md``). The public surface here is stable and will not change when the
generated core lands.
"""

from __future__ import annotations

import json
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
    """

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: float = 90.0) -> None:
        base = base_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = base + "/api/v1"
        self._base = base
        self._token = token
        self._timeout = timeout

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
        url = self._url(path, params)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raise self._to_error(exc) from None
        except urllib.error.URLError as exc:
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

    # ── convenience wrappers (a small starter set) ───────────────────────────
    def list_incidents(self, **filters: Any) -> Dict[str, Any]:
        """One page of incidents. Use ``paginate('/incidents/')`` for all of them."""
        return self.request("GET", "/incidents/", params=filters)

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/incidents/{incident_id}")

    def pending_actions(self) -> Dict[str, Any]:
        return self.request("GET", "/actions/pending")

    def approve_action(self, action_id: str, *, approved: bool, approved_by: str, comments: str = "") -> Any:
        """Approve or reject a pending action. Still passes the constitutional gate."""
        return self.request(
            "POST",
            f"/actions/{action_id}/approve",
            body={"approved": approved, "approved_by": approved_by, "comments": comments},
        )

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
            url = url + "?" + urllib.parse.urlencode(flat, doseq=True)
        return url

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
