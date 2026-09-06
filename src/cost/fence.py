"""
Constitutional AIOps - per-user LLM spend fence (cost-fence-D).

A small, dependency-free daily token budget per user. It bounds the surfaces a
tenant can drive autonomously - primarily the inbound ChatOps relay
(``POST /api/v1/relay/inbound``), which lets a remote user spend LLM tokens with
no browser session in front of it. Without a fence, a noisy or hijacked chat/room
could run a hosted box's owner budget up; with it, each user has a bounded daily
allowance that refuses further spend once exhausted.

Design:
  * Per-user config lives under the ``costFence`` key of the user's
    ``user_settings`` row: ``{"enabled": bool, "dailyTokenLimit": int}``.
  * An instance default comes from env (``AIOPS_COST_FENCE_ENABLED`` /
    ``AIOPS_COST_FENCE_DAILY_TOKENS``) so a self-host operator can set one ceiling
    for everyone without editing each row. A per-user row overrides the default.
  * Usage is tallied per UTC day in the ``llm_usage`` ledger
    (:mod:`src.auth.store`): :func:`check` reads it, :func:`record` adds to it.
  * ``limit <= 0`` means UNLIMITED (fence off). The default is off, so the
    hosted/GPU stack behaves byte-identically until an operator opts in.

Nothing here imports a web framework: :func:`check` returns a plain
:class:`FenceDecision` and the caller (the relay route) turns a denial into an
HTTP 429.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from src.auth import store as user_store

_FENCE_KEY = "costFence"
_TRUE = ("1", "true", "yes", "on")


def _env_default_enabled() -> bool:
    return (os.environ.get("AIOPS_COST_FENCE_ENABLED", "") or "").strip().lower() in _TRUE


def _env_default_limit() -> int:
    raw = (os.environ.get("AIOPS_COST_FENCE_DAILY_TOKENS", "") or "").strip()
    try:
        val = int(raw)
    except ValueError:
        return 0
    return val if val > 0 else 0


@dataclass(frozen=True)
class FenceConfig:
    """Effective fence config for one user."""

    enabled: bool
    daily_token_limit: int  # <= 0 means unlimited

    @property
    def active(self) -> bool:
        """True only when the fence actually caps spend (on AND a positive limit)."""
        return self.enabled and self.daily_token_limit > 0


@dataclass(frozen=True)
class FenceDecision:
    """The outcome of a :func:`check`."""

    allowed: bool
    limit: int      # effective daily limit (0 = unlimited)
    used: int       # tokens already spent today
    remaining: int  # max(limit - used, 0); -1 when unlimited
    reason: str     # "" when allowed, else a short human-readable reason


def resolve_config(user_id: str) -> FenceConfig:
    """Return a user's effective fence config (their row overrides the env default)."""
    enabled = _env_default_enabled()
    limit = _env_default_limit()
    if user_id:
        settings = user_store.get_user_settings(user_id) or {}
        raw = settings.get(_FENCE_KEY)
        if isinstance(raw, dict):
            if "enabled" in raw:
                enabled = bool(raw.get("enabled"))
            if "dailyTokenLimit" in raw:
                try:
                    lim = int(raw.get("dailyTokenLimit") or 0)
                except (TypeError, ValueError):
                    lim = limit
                limit = lim if lim > 0 else 0
    return FenceConfig(enabled=enabled, daily_token_limit=limit)


def check(user_id: str, *, config: Optional[FenceConfig] = None) -> FenceDecision:
    """Decide whether ``user_id`` may spend more LLM tokens today.

    An inactive fence (disabled, or a non-positive limit) always allows and
    reports ``limit=0`` / ``remaining=-1`` (unlimited). An active fence denies
    once today's tally has reached the limit.
    """
    cfg = config or resolve_config(user_id)
    used, _requests = user_store.llm_usage_today(user_id) if user_id else (0, 0)
    if not cfg.active:
        return FenceDecision(allowed=True, limit=0, used=used, remaining=-1, reason="")
    remaining = cfg.daily_token_limit - used
    if remaining <= 0:
        return FenceDecision(
            allowed=False,
            limit=cfg.daily_token_limit,
            used=used,
            remaining=0,
            reason=f"daily token budget of {cfg.daily_token_limit} reached",
        )
    return FenceDecision(
        allowed=True,
        limit=cfg.daily_token_limit,
        used=used,
        remaining=remaining,
        reason="",
    )


def record(user_id: str, tokens: int) -> None:
    """Add spent tokens (and one request) to the user's daily tally.

    Best-effort and never raises (see :func:`src.auth.store.add_llm_usage`).
    """
    if not user_id:
        return
    user_store.add_llm_usage(user_id, tokens)


def set_config(user_id: str, *, enabled: bool, daily_token_limit: int) -> None:
    """Persist a user's fence config, merging into their settings row.

    Preserves the other ``user_settings`` consumers (llm/alerting/notifications).
    A ``daily_token_limit <= 0`` is normalised to 0 (unlimited).
    """
    if not user_id:
        return
    settings = user_store.get_user_settings(user_id) or {}
    try:
        lim = int(daily_token_limit or 0)
    except (TypeError, ValueError):
        lim = 0
    settings[_FENCE_KEY] = {
        "enabled": bool(enabled),
        "dailyTokenLimit": lim if lim > 0 else 0,
    }
    user_store.set_user_settings(user_id, settings)


def public_view(user_id: str) -> dict[str, Any]:
    """A UI-safe snapshot of the user's fence plus today's usage."""
    cfg = resolve_config(user_id)
    used, requests = user_store.llm_usage_today(user_id) if user_id else (0, 0)
    return {
        "enabled": cfg.enabled,
        "dailyTokenLimit": cfg.daily_token_limit,
        "usedToday": used,
        "requestsToday": requests,
        "remaining": max(cfg.daily_token_limit - used, 0) if cfg.active else None,
    }


def estimate_tokens(text: str) -> int:
    """A cheap, endpoint-agnostic token estimate (~4 chars/token, min 1).

    Used only when an LLM response carries no ``usage`` block, so the ledger
    still advances for a served request. Deliberately conservative-ish; the
    fence is a coarse safety bound, not a billing meter.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


__all__ = [
    "FenceConfig",
    "FenceDecision",
    "check",
    "estimate_tokens",
    "public_view",
    "record",
    "resolve_config",
    "set_config",
]
