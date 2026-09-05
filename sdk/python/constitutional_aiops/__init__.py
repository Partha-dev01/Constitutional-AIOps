"""Official Python client for the Constitutional AIOps REST API.

Pre-release scaffold. This hand-written layer talks to the app's ``/api/v1``
surface with the standard library only. It is the seed for the generated client
(``openapi-python-client``) described in the developer-platform spec.

Quick start::

    from constitutional_aiops import AIOpsClient

    client = AIOpsClient("https://your-instance.example.com", token="caiops_pat_...")

    for incident in client.paginate("/incidents/", severity="critical"):
        print(incident["id"], incident["title"])

Personal access tokens are not built yet. Until they are, run the SDK against an
instance with ``AUTH_REQUIRED`` unset, or pass a session token you already hold.
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
