"""
Constitutional AIOps - inbound ChatOps relay endpoint (Track 1 T1d).

``POST /api/v1/relay/inbound`` is the box-side landing point for a message that a
remote user sent to the bot (Telegram) and the off-box relay Lambda forwarded in
(directly when the box is awake, or via the SQS drain at boot). It is mounted
WITHOUT the session dependency other routers carry: a browser never calls it. Its
only auth is the shared-secret HMAC (:mod:`src.alerting.relay_hmac`) over the exact
body, so it is safe to expose unauthenticated at the routing layer.

Flow per request:
  1. Verify the relay HMAC (fail-closed: 503 when no secret is configured, 401 on
     a bad/replayed signature).
  2. Resolve the opted-in binding from ``{channel, routingId}``. Unknown -> a
     benign 200 ``ignored`` (the Lambda already rate-limited; don't leak).
  3. Enforce the per-user cost fence (cost-fence-D). Over budget -> reply a short
     notice out to the chat and return 200 ``budget``.
  4. Route the text through the caller's OWN reasoning agent (BYOK per-user
     routing). No endpoint -> reply a notice and return 200 ``no_endpoint``.
  5. Record token usage, then reply the agent's answer back out via the channel.

Everything is best-effort past auth: a downstream failure returns a 200 with a
status so the relay/drain does not retry-storm.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.alerting import inbound as inbound_bindings
from src.alerting import matrix as matrix_adapter
from src.alerting import relay_hmac
from src.alerting import telegram as telegram_adapter
from src.auth import store as user_store
from src.auth.deps import User, synthetic_admin
from src.agents.user_router import resolve_reasoning_agent
from src.cost import fence

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_BODY = 16 * 1024  # a chat command is tiny; cap to refuse oversized posts
_MAX_REPLY_CHARS = 3500  # keep well under Telegram's 4096 hard limit


def _secret() -> str:
    return (os.environ.get("AIOPS_RELAY_HMAC_SECRET", "") or "").strip()


def _json(status_code: int, payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload)


def _reply(binding: inbound_bindings.InboundBinding, text: str) -> None:
    """Best-effort reply back out to the origin chat/room (plain text)."""
    text = (text or "").strip()[:_MAX_REPLY_CHARS] or "(no response)"
    try:
        if binding.channel == "telegram":
            telegram_adapter.send(binding.reply_token, binding.reply_target, text, html=False)
        elif binding.channel == "matrix":
            matrix_adapter.send(
                binding.homeserver, binding.reply_token, binding.reply_target, text
            )
    except Exception as exc:  # noqa: BLE001 - a reply must never raise
        logger.debug("relay reply failed (ignored): %s", exc)


def _resolve_user(owner_id: str) -> User:
    """The app User a binding acts as. "" (system/self-host) -> synthetic admin."""
    if not owner_id:
        return synthetic_admin()
    record = user_store.get_by_id(owner_id)
    if record is None:
        return synthetic_admin()
    return User(id=record.id, username=record.username, role=record.role)


def _tokens_used(response: Any, prompt: str) -> int:
    """Prefer the model's reported completion tokens; else a cheap estimate over
    prompt + reply so the ledger still advances for a served request."""
    meta = getattr(response, "metadata", None)
    if isinstance(meta, dict):
        reported = meta.get("tokens_used")
        if isinstance(reported, int) and reported > 0:
            return reported
    content = getattr(response, "content", "") or ""
    return fence.estimate_tokens(prompt) + fence.estimate_tokens(content)


@router.post("/inbound")
async def relay_inbound(request: Request):
    secret = _secret()
    if not secret:
        return _json(503, {"status": "disabled"})

    body = await request.body()
    if len(body) > _MAX_BODY:
        return _json(413, {"status": "too_large"})

    ok, reason = relay_hmac.verify(
        secret,
        body,
        request.headers.get(relay_hmac._TS_HEADER, ""),
        request.headers.get(relay_hmac._SIG_HEADER, ""),
    )
    if not ok:
        logger.warning("relay inbound rejected: %s", reason)
        return _json(401, {"status": "unauthorized"})

    try:
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return _json(400, {"status": "bad_json"})
    if not isinstance(payload, dict):
        return _json(400, {"status": "bad_json"})

    channel = str(payload.get("channel") or "").strip().lower()
    routing_id = str(payload.get("routingId") or "").strip()
    text = str(payload.get("text") or "").strip()

    binding = inbound_bindings.resolve(channel, routing_id)
    if binding is None:
        # Unknown/disabled binding: benign no-op (do not leak, do not error).
        return _json(200, {"status": "ignored"})
    if not text:
        return _json(200, {"status": "empty"})

    user = _resolve_user(binding.owner_id)

    decision = fence.check(user.id)
    if not decision.allowed:
        _reply(binding, f"Daily budget reached ({decision.reason}). Try again tomorrow.")
        return _json(200, {"status": "budget"})

    agent, _per_user = await resolve_reasoning_agent(request, user)
    if agent is None:
        _reply(
            binding,
            "No LLM endpoint is configured for your account. Add one in Settings first.",
        )
        return _json(200, {"status": "no_endpoint"})

    try:
        response = await agent.chat(text)
    except Exception as exc:  # noqa: BLE001 - surface a clean message, never a 500
        logger.warning("relay chat failed: %s", exc)
        _reply(binding, "Sorry, I could not process that right now.")
        return _json(200, {"status": "error"})

    fence.record(user.id, _tokens_used(response, text))
    _reply(binding, getattr(response, "content", "") or "(no response)")
    return _json(200, {"status": "ok"})


__all__ = ["router"]
