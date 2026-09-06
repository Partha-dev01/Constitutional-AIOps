"""Official Python client for the Constitutional AIOps REST API.

Pre-release scaffold. This hand-written layer talks to the app's ``/api/v1``
surface with the standard library only. It is the seed for the generated client
(``openapi-python-client``) described in the developer-platform spec.

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

from .client import AIOpsClient
from .errors import (
    AIOpsError,
    AuthError,
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
]

__version__ = "0.1.0"
