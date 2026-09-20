"""Typed error hierarchy for the Constitutional AIOps client.

The hierarchy mirrors the TypeScript client so the two feel the same. The one
domain-specific error is ``ConstitutionalRefusal``, raised when the safety gate
blocks an action or holds it for human approval. It is not a failure of the SDK,
it is the product working as designed, so it carries the gate's own verdict.
"""

from __future__ import annotations

from typing import Any, Optional


class AIOpsError(Exception):
    """Base error for every client failure."""

    def __init__(self, message: str, *, status: Optional[int] = None, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details


class AuthError(AIOpsError):
    """401. Missing or invalid credentials."""


class NotFound(AIOpsError):
    """404. The resource does not exist."""


class RateLimited(AIOpsError):
    """429. A per-user cost fence or throttle rejected the call.

    ``retry_after`` is the server's ``Retry-After`` header in seconds when it
    sent one, and ``None`` otherwise. The hourly windows on chat, tools and
    actions send it, so a caller that catches this can wait the stated time
    instead of guessing.
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        details: Any = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, status=status, details=details)
        self.retry_after = retry_after


#: The gate's refusal codes, mirrored from the server. Public so a caller can
#: test ``err.error_code`` against the canonical set instead of hardcoding a
#: string. Matches ``CONSTITUTIONAL_CODES`` in the TypeScript client.
CONSTITUTIONAL_CODES = (
    "action_tools_disabled",
    "approval_required",
    "validation_blocked",
    "container_not_whitelisted",
)


class ConstitutionalRefusal(AIOpsError):
    """The constitutional gate blocked an action or requires approval.

    ``error_code`` is one of the gate's codes, for example
    ``action_tools_disabled``, ``approval_required``, ``validation_blocked`` or
    ``container_not_whitelisted``. ``verdict`` holds the validator's structured
    report when the response includes one.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        verdict: Any = None,
        status: Optional[int] = None,
    ) -> None:
        super().__init__(message, status=status, details=verdict)
        self.error_code = error_code
        self.verdict = verdict
