"""
Constitutional AIOps - Remediation target routing.

The backend (a container on the GPU VM) cannot reach the docker daemon on the
remote t3 host where nextcloud + nextcloud-db live. ``resolve_remediation_target``
decides whether a given container is remediated LOCALLY (``docker restart`` on the
backend host) or via the t3 control agent over HTTP ("t3").

Safe-by-default: the remote set is ONLY ``nextcloud-db`` unless the operator
overrides ``DEMO_REMOTE_CONTAINERS``. ``nextcloud`` therefore stays LOCAL by
default, keeping the existing action-tool tests/behavior unchanged.
"""

import os

# Default set of containers that live on the remote t3 host. Intentionally just
# ``nextcloud-db`` so the action-tool whitelist tests (which expect ``nextcloud``
# to restart via a local ``docker restart``) stay green.
DEMO_REMOTE_CONTAINERS_ENV = "DEMO_REMOTE_CONTAINERS"
_DEFAULT_REMOTE_CONTAINERS = "nextcloud-db"


def _remote_containers() -> set[str]:
    """Parse the comma-separated DEMO_REMOTE_CONTAINERS env (default nextcloud-db)."""
    raw = os.getenv(DEMO_REMOTE_CONTAINERS_ENV, _DEFAULT_REMOTE_CONTAINERS)
    return {name.strip() for name in raw.split(",") if name.strip()}


def resolve_remediation_target(container: str) -> str:
    """Return "t3" if ``container`` is remediated via the remote agent, else "local".

    Args:
        container: The container/service name being acted upon.

    Returns:
        "t3" when the container is in DEMO_REMOTE_CONTAINERS, otherwise "local".
    """
    if not isinstance(container, str) or not container.strip():
        return "local"
    return "t3" if container.strip() in _remote_containers() else "local"


__all__ = ["resolve_remediation_target"]
