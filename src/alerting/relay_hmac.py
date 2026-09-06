"""
Constitutional AIOps - timestamped HMAC for the inbound ChatOps relay (Track 1 T1d).

The inbound relay endpoint (``POST /api/v1/relay/inbound``) is mounted WITHOUT a
session dependency: it is reached by the off-box relay Lambda (and the boot-time
SQS drain), never by a browser. Its only authentication is a shared-secret HMAC
over the exact request body plus a timestamp, so a request cannot be forged or
replayed without ``AIOPS_RELAY_HMAC_SECRET``.

Wire format (headers on the POST):
  * ``X-AIOPS-Relay-Timestamp``  unix seconds (integer, as a string)
  * ``X-AIOPS-Relay-Signature``  hex SHA-256 HMAC of ``f"{ts}.".encode()+body``

The timestamp is inside the signed material AND range-checked (``max_skew``) so a
captured request cannot be replayed indefinitely. Signature comparison is
constant-time. Stdlib only.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional, Tuple

_TS_HEADER = "X-AIOPS-Relay-Timestamp"
_SIG_HEADER = "X-AIOPS-Relay-Signature"
_DEFAULT_MAX_SKEW = 300  # seconds either side of now


def _mac(secret: str, body: bytes, timestamp: str) -> str:
    msg = f"{timestamp}.".encode("utf-8") + (body or b"")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def sign(secret: str, body: bytes, *, timestamp: Optional[int] = None) -> Tuple[str, str]:
    """Return ``(timestamp_str, signature_hex)`` for ``body``.

    Used by the SQS drain (and tests) to build the two headers. ``timestamp``
    defaults to now; pass one to reproduce a signature deterministically.
    """
    ts = str(int(timestamp if timestamp is not None else time.time()))
    return ts, _mac(secret, body or b"", ts)


def verify(
    secret: str,
    body: bytes,
    timestamp: str,
    signature: str,
    *,
    max_skew: int = _DEFAULT_MAX_SKEW,
    now: Optional[int] = None,
) -> Tuple[bool, str]:
    """Verify a relay signature over ``body``. Returns ``(ok, reason)``.

    Fails closed on a missing secret, a non-integer/out-of-window timestamp, or a
    signature mismatch. ``reason`` is a short, non-secret label for logs.
    """
    if not secret:
        return False, "relay secret not configured"
    if not timestamp or not signature:
        return False, "missing relay auth headers"
    try:
        ts_int = int(timestamp)
    except (TypeError, ValueError):
        return False, "bad timestamp"
    current = int(now if now is not None else time.time())
    if abs(current - ts_int) > max_skew:
        return False, "timestamp outside allowed window"
    expected = _mac(secret, body or b"", str(ts_int))
    if not hmac.compare_digest(expected, signature.strip()):
        return False, "signature mismatch"
    return True, ""


__all__ = ["sign", "verify", "_TS_HEADER", "_SIG_HEADER"]
