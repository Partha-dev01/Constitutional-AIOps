"""
Constitutional AIOps - per-user LLM endpoint config (BYOK).

Multi-tenant core (BYOK spec Phase B). Each user's OWN bring-your-own LLM
endpoint config lives under the ``llm`` key of their ``user_settings`` row; the
API key is encrypted with :mod:`src.auth.crypto` before it is written. This is
separate from the instance-global endpoint (Settings -> Models / env), which
stays the admin + single-tenant self-host default: a regular user never
inherits the owner key (BYOK spec Decision #3).

Stored block shape (mirrors the global ``models`` block so the UI is uniform):

    {"fastAgentUrl", "fastAgentModel", "reasoningAgentUrl",
     "reasoningAgentModel", "apiKey"}      # apiKey stored ENCRYPTED (enc::v1::…)

Writes MERGE into the existing settings row, so a user's notification prefs (the
other consumer of ``user_settings``) are preserved.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.auth import store as user_store
from src.auth.crypto import decrypt_secret, encrypt_secret

logger = logging.getLogger(__name__)

_LLM_KEY = "llm"
_URL_FIELDS = (
    "fastAgentUrl",
    "fastAgentModel",
    "reasoningAgentUrl",
    "reasoningAgentModel",
)


def _raw_block(user_id: str) -> Optional[dict[str, Any]]:
    """The stored ``llm`` sub-dict (key still encrypted), or None when absent."""
    settings = user_store.get_user_settings(user_id) or {}
    block = settings.get(_LLM_KEY)
    return block if isinstance(block, dict) and block else None


def get_user_llm(user_id: str) -> Optional[dict[str, Any]]:
    """Return the user's endpoint config with the API key DECRYPTED, or None.

    For building an outbound router. Callers MUST NOT hand the key to a client.
    An incomplete block (any URL/model missing) is treated as unset -> None, so
    a half-filled row never routes to a broken endpoint.
    """
    block = _raw_block(user_id)
    if block is None:
        return None
    out = {f: str(block.get(f, "") or "").strip() for f in _URL_FIELDS}
    if not all(out[f] for f in _URL_FIELDS):
        return None
    out["apiKey"] = decrypt_secret(block.get("apiKey", "") or "")
    return out


def get_user_llm_public(user_id: str) -> Optional[dict[str, Any]]:
    """Return the user's endpoint config with an ``apiKeySet`` bool (no key).

    None when the user has no stored block at all (a partially-filled block is
    still returned so the UI can show + finish it).
    """
    block = _raw_block(user_id)
    if block is None:
        return None
    return {
        "fastAgentUrl": str(block.get("fastAgentUrl", "") or ""),
        "fastAgentModel": str(block.get("fastAgentModel", "") or ""),
        "reasoningAgentUrl": str(block.get("reasoningAgentUrl", "") or ""),
        "reasoningAgentModel": str(block.get("reasoningAgentModel", "") or ""),
        "apiKeySet": bool(decrypt_secret(block.get("apiKey", "") or "").strip()),
    }


def user_has_llm(user_id: str) -> bool:
    """True when the user has a COMPLETE, routable endpoint config."""
    return get_user_llm(user_id) is not None


def stored_api_key_plaintext(user_id: str) -> str:
    """Decrypted stored key (""), so a PUT that omits the key can keep it."""
    block = _raw_block(user_id)
    if block is None:
        return ""
    return decrypt_secret(block.get("apiKey", "") or "")


def set_user_llm(
    user_id: str,
    *,
    fast_agent_url: str,
    fast_agent_model: str,
    reasoning_agent_url: str,
    reasoning_agent_model: str,
    api_key_plaintext: str,
) -> None:
    """Persist the user's endpoint config, encrypting the key at rest.

    Reads the existing settings row and updates only the ``llm`` key, so the
    ``notifications`` block (the other user_settings consumer) survives.
    ``api_key_plaintext`` "" clears the key; the caller resolves the
    keep-existing (None) case before calling.
    """
    settings = user_store.get_user_settings(user_id) or {}
    settings[_LLM_KEY] = {
        "fastAgentUrl": (fast_agent_url or "").strip(),
        "fastAgentModel": (fast_agent_model or "").strip(),
        "reasoningAgentUrl": (reasoning_agent_url or "").strip(),
        "reasoningAgentModel": (reasoning_agent_model or "").strip(),
        "apiKey": encrypt_secret(api_key_plaintext or ""),
    }
    user_store.set_user_settings(user_id, settings)


def clear_user_llm(user_id: str) -> None:
    """Remove the user's endpoint config (preserving other settings keys)."""
    settings = user_store.get_user_settings(user_id) or {}
    if _LLM_KEY in settings:
        settings.pop(_LLM_KEY, None)
        user_store.set_user_settings(user_id, settings)


def config_fingerprint(cfg: dict[str, Any]) -> str:
    """Stable fingerprint of a resolved (decrypted) config for router caching.

    A change to any URL / model / key produces a new fingerprint, so a cached
    per-user router is rebuilt after the user edits their endpoint.
    """
    import hashlib

    parts = [str(cfg.get(f, "")) for f in _URL_FIELDS] + [str(cfg.get("apiKey", ""))]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


__all__ = [
    "clear_user_llm",
    "config_fingerprint",
    "get_user_llm",
    "get_user_llm_public",
    "set_user_llm",
    "stored_api_key_plaintext",
    "user_has_llm",
]
