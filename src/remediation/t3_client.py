"""
Constitutional AIOps - t3 control-agent HTTP client.

The AIOps backend runs in a container on the GPU VM and cannot reach the docker
daemon on the remote t3 host (where nextcloud + nextcloud-db run). This async
client talks to the small token-secured control agent deployed on the t3 to:
  - inject chaos scenarios (``chaos_start`` / ``chaos_heal``)
  - read live scenario/container status (``t3_status``)
  - remediate by restarting a remote container (``restart_remote``)

Uses httpx (already a backend dep). NO new dependencies.

Conventions (CONTRACT 4):
  - Base URL: persisted settings ``remediation.demoTargetUrl`` first, else env
    ``DEMO_TARGET_URL``, else "" (empty -> every call fails closed).
  - Auth: ``Authorization: Bearer <DEMO_AGENT_TOKEN>``.
  - Timeout: httpx.AsyncClient(timeout=8.0).
  - On any error / non-2xx / empty base url: ``{"success": False, "error": "..."}``.
  - On success: the parsed JSON body merged with ``{"success": True}``.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Env var holding the t3 agent base URL (settings JSON takes priority).
DEMO_TARGET_URL_ENV = "DEMO_TARGET_URL"
# Env var holding the shared bearer token (matches the agent's DEMO_AGENT_TOKEN).
DEMO_AGENT_TOKEN_ENV = "DEMO_AGENT_TOKEN"

_TIMEOUT_SECONDS = 8.0


def _base_url() -> str:
    """Resolve the t3 agent base URL.

    Priority: persisted settings ``remediation.demoTargetUrl`` -> env
    ``DEMO_TARGET_URL`` -> "". A trailing slash is stripped so we can join
    paths with a single leading slash.
    """
    url = ""
    try:
        # Imported lazily so importing this module never drags in the settings
        # route stack (and so tests can monkeypatch the persisted store cheaply).
        from src.api.routes.settings import _load_persisted

        persisted = _load_persisted() or {}
        url = (persisted.get("remediation", {}) or {}).get("demoTargetUrl", "") or ""
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read persisted demoTargetUrl: %s", exc)
        url = ""

    if not url:
        url = os.getenv(DEMO_TARGET_URL_ENV, "") or ""

    return url.strip().rstrip("/")


def _auth_headers() -> dict[str, str]:
    """Bearer-token header from env DEMO_AGENT_TOKEN (empty token -> no header)."""
    token = os.getenv(DEMO_AGENT_TOKEN_ENV, "") or ""
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _ok(payload: Any) -> dict[str, Any]:
    """Wrap a successful agent response, merging in success=True."""
    if isinstance(payload, dict):
        return {**payload, "success": True}
    # Non-object JSON (list/str/number) — keep it under a "result" key.
    return {"success": True, "result": payload}


def _fail(reason: str) -> dict[str, Any]:
    """Uniform failure envelope."""
    return {"success": False, "error": reason}


async def _request(method: str, path: str, json_body: dict | None = None) -> dict[str, Any]:
    """Perform a single authenticated request to the t3 agent.

    Returns the parsed JSON merged with success=True on a 2xx, otherwise a
    ``{"success": False, "error": ...}`` envelope. Never raises.
    """
    base = _base_url()
    if not base:
        return _fail("demo target url not configured")

    url = f"{base}{path}"
    headers = _auth_headers()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.request(method, url, headers=headers, json=json_body)
    except Exception as exc:  # noqa: BLE001 — network/transport errors fail closed
        logger.warning("t3 agent request failed (%s %s): %s", method, url, exc)
        return _fail(f"request error: {exc}")

    if not (200 <= response.status_code < 300):
        detail = ""
        try:
            detail = response.text[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        return _fail(f"agent returned HTTP {response.status_code}: {detail}".strip())

    try:
        body = response.json()
    except Exception as exc:  # noqa: BLE001
        return _fail(f"invalid JSON from agent: {exc}")

    return _ok(body)


async def chaos_start(scenario: str) -> dict:
    """Start a chaos scenario on the t3 (POST /chaos/{scenario}/start)."""
    return await _request("POST", f"/chaos/{scenario}/start")


async def chaos_heal(scenario: str) -> dict:
    """Heal a chaos scenario on the t3 (POST /chaos/{scenario}/heal)."""
    return await _request("POST", f"/chaos/{scenario}/heal")


async def t3_status() -> dict:
    """Fetch live scenario + container status from the t3 (GET /status)."""
    return await _request("GET", "/status")


async def restart_remote(container: str) -> dict:
    """Restart a container on the t3 (POST /remediate/restart)."""
    return await _request("POST", "/remediate/restart", json_body={"container": container})


__all__ = ["chaos_start", "chaos_heal", "t3_status", "restart_remote"]
