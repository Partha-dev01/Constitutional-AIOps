"""Official Python client for the Constitutional AIOps REST API.

A published, dependency-free ergonomic client. This hand-written layer talks to
the app's ``/api/v1`` surface with the standard library only, and ships beside a
generated typed core (``openapi-python-client``, the ``typed`` extra) that covers
the full endpoint surface; see the developer-platform guide.

Quick start::

    from constitutional_aiops import AIOpsClient

    client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")

    for incident in client.paginate("/incidents/", severity="critical"):
        print(incident["id"], incident["title"])

Create a personal access token in the app (Settings, or ``POST /api/v1/auth/tokens``)
and pass it as ``token``; it is sent as ``Authorization: Bearer aiops_pat_...``.
Against a single-user instance with ``AUTH_REQUIRED`` unset the token is optional.

For a fully typed client over every endpoint, install the ``typed`` extra and use
the generated core (``from constitutional_aiops_client import Client``); see
``../README.md``.
"""

from .client import (
    AIOpsClient,
    INSIGHT_KINDS,
    INSIGHT_TIERS,
    INSIGHT_UNAVAILABLE_REASONS,
)
from .errors import (
    AIOpsError,
    AuthError,
    CONSTITUTIONAL_CODES,
    ConstitutionalRefusal,
    NotFound,
    RateLimited,
)

__all__ = [
    "AIOpsClient",
    "AIOpsError",
    "AuthError",
    "ConstitutionalRefusal",
    "NotFound",
    "RateLimited",
    "CONSTITUTIONAL_CODES",
    "INSIGHT_KINDS",
    "INSIGHT_TIERS",
    "INSIGHT_UNAVAILABLE_REASONS",
]

# Single source of truth: read the installed distribution version, falling back to
# the literal for a source checkout that was never installed. This is the fix for
# the 0.1.x drift where this literal lagged the manifest.
try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("constitutional-aiops")
except Exception:  # pragma: no cover - source checkout without install metadata
    __version__ = "0.3.0"
