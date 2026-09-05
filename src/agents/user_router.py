"""
Constitutional AIOps - per-user model routing (BYOK spec Phase B).

Selects which ReasoningAgent / ModelRouter a REQUEST should use, so a public
multi-tenant instance routes each user's LLM traffic to that user's own
endpoint instead of the owner's global one:

  * synthetic user (AUTH off) or an admin  -> the shared global agent on
    app.state (single-tenant self-host stays byte-identical; the global env
    endpoint is the admin / self-host default, BYOK Decision #3),
  * a regular user WITH a complete endpoint -> a per-user agent bound to a
    router built from THEIR config (cached on app.state, rebuilt when they
    edit it, closed on shutdown),
  * a regular user WITHOUT an endpoint      -> None: the caller returns a clear
    "configure your LLM endpoint" error. A regular user never inherits the
    owner key.

The per-user routers are cached (bounded, lock-guarded) because building one
opens two httpx clients; a config edit invalidates the cache entry via
``invalidate_user`` so the next request rebuilds it.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from src.agents.model_router import ModelRouter
from src.agents.reasoning_agent import ReasoningAgent
from src.auth import user_llm
from src.auth.deps import is_synthetic

logger = logging.getLogger(__name__)

# Bound the number of distinct per-user routers kept alive at once. On a small
# public box this is far more than the concurrent-user count; the oldest entry
# is evicted (and its clients closed) past the cap.
_MAX_USER_AGENTS = 32


@dataclass
class _CachedAgent:
    fingerprint: str
    agent: ReasoningAgent
    router: ModelRouter


def _cache(app) -> "dict[str, _CachedAgent]":
    cache = getattr(app.state, "user_agents", None)
    if cache is None:
        cache = {}
        app.state.user_agents = cache
    return cache


def _lock(app) -> asyncio.Lock:
    lock = getattr(app.state, "user_agents_lock", None)
    if lock is None:
        lock = asyncio.Lock()
        app.state.user_agents_lock = lock
    return lock


async def _close_entry(entry: _CachedAgent) -> None:
    try:
        await entry.router.close()
    except Exception as exc:  # noqa: BLE001 - close is best-effort
        logger.debug("per-user router close failed (ignored): %s", exc)


async def _build(cfg: dict[str, Any]) -> _CachedAgent:
    """Build a fresh per-user router + reasoning agent from a resolved config."""
    router = ModelRouter(
        fast_agent_url=cfg["fastAgentUrl"],
        reasoning_agent_url=cfg["reasoningAgentUrl"],
    )
    # reconfigure() sets the served model names + the (decrypted) bearer key and
    # rebuilds the two httpx clients with that auth header.
    await router.reconfigure(
        fast_url=cfg["fastAgentUrl"],
        reasoning_url=cfg["reasoningAgentUrl"],
        fast_model=cfg["fastAgentModel"],
        reasoning_model=cfg["reasoningAgentModel"],
        fast_api_key=cfg["apiKey"],
        reasoning_api_key=cfg["apiKey"],
    )
    agent = ReasoningAgent(model_router=router)
    return _CachedAgent(
        fingerprint=user_llm.config_fingerprint(cfg), agent=agent, router=router
    )


async def _get_or_build(app, user_id: str, cfg: dict[str, Any]) -> _CachedAgent:
    fingerprint = user_llm.config_fingerprint(cfg)
    cache = _cache(app)
    entry = cache.get(user_id)
    if entry is not None and entry.fingerprint == fingerprint:
        return entry

    async with _lock(app):
        # Re-check under the lock (another request may have built it).
        entry = cache.get(user_id)
        if entry is not None and entry.fingerprint == fingerprint:
            return entry
        if entry is not None:
            await _close_entry(entry)
            cache.pop(user_id, None)
        # Evict the oldest entries while at/over the cap.
        while len(cache) >= _MAX_USER_AGENTS:
            old_uid, old_entry = next(iter(cache.items()))
            cache.pop(old_uid, None)
            await _close_entry(old_entry)
        new_entry = await _build(cfg)
        cache[user_id] = new_entry
        logger.info("Built per-user model router for user %s", user_id)
        return new_entry


async def resolve_reasoning_agent(request, user) -> "tuple[Optional[ReasoningAgent], bool]":
    """Return ``(agent, is_per_user)`` for this request.

    ``agent`` is None only for a regular user with no configured endpoint (the
    caller must surface a "configure your endpoint" error). ``is_per_user`` is
    informational (True when the returned agent is that user's own).
    """
    global_agent = getattr(request.app.state, "reasoning_agent", None)
    if is_synthetic(user) or getattr(user, "role", "user") == "admin":
        return global_agent, False
    cfg = user_llm.get_user_llm(getattr(user, "id", ""))
    if cfg is None:
        return None, False
    entry = await _get_or_build(request.app, user.id, cfg)
    return entry.agent, True


async def resolve_model_router(request, user) -> "tuple[Optional[ModelRouter], bool]":
    """Like :func:`resolve_reasoning_agent` but returns the raw ModelRouter.

    For the surfaces that call the router directly rather than through the
    reasoning agent. The global router is returned for synthetic/admin users.
    """
    global_router = getattr(request.app.state, "model_router", None)
    if is_synthetic(user) or getattr(user, "role", "user") == "admin":
        return global_router, False
    cfg = user_llm.get_user_llm(getattr(user, "id", ""))
    if cfg is None:
        return None, False
    entry = await _get_or_build(request.app, user.id, cfg)
    return entry.router, True


async def invalidate_user(app, user_id: str) -> None:
    """Drop (and close) a user's cached router after they edit their endpoint."""
    cache = _cache(app)
    async with _lock(app):
        entry = cache.pop(user_id, None)
    if entry is not None:
        await _close_entry(entry)


async def close_all(app) -> None:
    """Close every cached per-user router (call at app shutdown)."""
    cache = _cache(app)
    async with _lock(app):
        entries = list(cache.values())
        cache.clear()
    for entry in entries:
        await _close_entry(entry)


__all__ = [
    "close_all",
    "invalidate_user",
    "resolve_model_router",
    "resolve_reasoning_agent",
]
