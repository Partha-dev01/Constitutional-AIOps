"""
Constitutional AIOps - LLM insight widgets (Track 2 W3) shared plumbing.

The dashboard "insight" widgets compute their primary view WITHOUT an LLM (the
no-LLM widgets shipped earlier: blast-radius, what-changed, anomaly-scan, and so
on). This router adds the small, opt-in, cost-fenced "explain" surface those
widgets call when a user explicitly asks for a plain-language hypothesis on top
of the computed numbers.

Design (every guard fail-closed so the hosted/GPU stack stays byte-identical):

  * ``POST /api/v1/insights/explain`` runs the FAST tier (or the heavier
    reasoning tier when a widget asks for it) via the caller's OWN router (BYOK
    per-user routing, same resolver the relay uses). It is:
      - opt-in: a user must turn ``ui.aiWidgets.enabled`` on first. Off -> no LLM
        call at all, a 200 with ``available=false, reason="ai_widgets_disabled"``.
      - cost-fenced: cost-fence-D (``src.cost.fence``) bounds daily spend. Over
        budget -> a 200 ``available=false, reason="budget_reached"``.
      - graceful: a regular user with no endpoint (or an unreachable one) gets a
        200 ``available=false, reason="no_endpoint"|"error"`` so the widget stays
        on its computed view and shows an "add an endpoint" hint.
    The response is ALWAYS 200 with a uniform ``ExplainResponse`` body so the
    client never has to special-case status codes: it renders the computed view
    and, when ``available`` is false, a small note keyed off ``reason``. This
    mirrors the relay's "benign status, never retry-storm" contract.
  * ``GET/PUT /api/v1/insights/preferences`` reads / writes the per-user
    ``ui.aiWidgets {enabled, autoExplain}`` opt-in block, merged into the same
    ``user_settings`` row as the llm / alerting / costFence blocks (never
    replacing it). The response also carries the fence's UI-safe budget snapshot
    so a widget can show remaining spend.

The prompt is built SERVER-side from a small allow-list of ``kind`` values and a
bounded payload, so a client cannot drive an arbitrary prompt or a huge one.
Everything the model returns is a hypothesis, not measured telemetry: the client
labels it as model-generated.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.agents.user_router import resolve_model_router
from src.auth import store as user_store
from src.auth.deps import SYNTHETIC_USER_ID, User, coerce_user, require_user
from src.cost import fence

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Per-user opt-in block: user_settings["ui"]["aiWidgets"] = {enabled, autoExplain}
# ---------------------------------------------------------------------------

_UI_KEY = "ui"
_WIDGETS_KEY = "aiWidgets"

# The fast tier writes a short plain-language hypothesis. Keep it small: this is a
# caption on top of an already-rendered widget, not a chat answer.
_MAX_TOKENS = 220
# A widget may opt into the heavier reasoning tier (e.g. next-best-action), which
# gets a little more room. Still a caption, and still cost-fenced.
_MAX_TOKENS_REASONING = 340
_MAX_PAYLOAD_CHARS = 2000

# What a client may ask us to explain. An unknown kind falls back to "generic"
# rather than being rejected, so a new widget can ship its client before its
# server template without breaking.
_KIND_INSTRUCTIONS: dict[str, str] = {
    "spike": (
        "A metric spike was detected. In 2 to 4 sentences, give the most likely "
        "explanations for the spike and one concrete next check. Be specific to "
        "the numbers provided."
    ),
    "anomaly": (
        "A statistical anomaly scan flagged the items below. In 2 to 4 sentences, "
        "summarise what stands out and the single most likely cause. Do not invent "
        "data that is not present."
    ),
    "diff": (
        "The two snapshots below changed. In 2 to 4 sentences, explain what changed "
        "and whether it looks benign or worth investigating."
    ),
    "blast_radius": (
        "The dependency edges below describe a service and its neighbours. In 2 to 4 "
        "sentences, describe the likely blast radius if this service degrades."
    ),
    "next_best_action": (
        "The incident timeline below lists the lifecycle stages of one or more "
        "incidents. In 2 to 4 sentences, name the single most useful next action "
        "for the on-call engineer and why. Prefer the least invasive step and do "
        "not invent stages that are not listed."
    ),
    "runbook": (
        "The remediation actions below are ranked by past success rate and how "
        "often each ran. In 2 to 4 sentences, say which action is the most "
        "reliable starting point for a similar incident and flag any low-sample "
        "or low-success entries to treat with caution."
    ),
    "generic": (
        "In 2 to 4 sentences, give a plain-language explanation of the data below "
        "for an on-call engineer. Do not speculate beyond what the data shows."
    ),
}

_SYSTEM_PROMPT = (
    "You are a concise SRE assistant. You explain observability data in plain "
    "language for an on-call engineer. You never fabricate numbers, you keep to 2 "
    "to 4 sentences, and you frame your answer as a hypothesis to check, not a "
    "measured fact."
)


class AiWidgetsPrefs(BaseModel):
    """The per-user opt-in state for the LLM insight widgets."""

    enabled: bool = False
    autoExplain: bool = False


class PreferencesResponse(BaseModel):
    """Current opt-in state plus the fence budget snapshot for the UI."""

    aiWidgets: AiWidgetsPrefs
    budget: dict[str, Any] = Field(default_factory=dict)


class PreferencesUpdate(BaseModel):
    """Patch for the opt-in block. A null leaf leaves that field unchanged."""

    enabled: bool | None = None
    autoExplain: bool | None = None


class ExplainRequest(BaseModel):
    """A request for a plain-language explanation of a widget's computed data."""

    kind: str = "generic"
    # "fast" (default) or "reasoning". A widget opts into the reasoning tier only
    # when the extra quality is worth the extra (still-fenced) spend.
    tier: str = "fast"
    payload: dict[str, Any] = Field(default_factory=dict)


class ExplainResponse(BaseModel):
    """Uniform result. ``available`` is false for every non-spend outcome."""

    available: bool
    explanation: str | None = None
    model_generated: bool = False
    reason: str | None = None
    tokens_used: int | None = None
    remaining: int | None = None


def _block_to_prefs(block: Any) -> AiWidgetsPrefs:
    if not isinstance(block, dict):
        return AiWidgetsPrefs()
    return AiWidgetsPrefs(
        enabled=bool(block.get("enabled", False)),
        autoExplain=bool(block.get("autoExplain", False)),
    )


def _synth_prefs_path() -> Path:
    """File that holds the synthetic (self-host) admin's opt-in block.

    The synthetic admin is not a real ``users`` row, so its opt-in cannot live in
    the FK-constrained ``user_settings`` table. It goes to a small JSON file under
    the data dir instead, the same "system file for the synthetic admin" pattern
    the alerting / notifications config uses.
    """
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "settings"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path / "ui_prefs.json"


def _read_prefs(user_id: str) -> AiWidgetsPrefs:
    """Read the user's aiWidgets opt-in block (default off)."""
    if not user_id:
        return AiWidgetsPrefs()
    if user_id == SYNTHETIC_USER_ID:
        try:
            p = _synth_prefs_path()
            data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        except Exception:  # noqa: BLE001 - a corrupt file just means "default off"
            data = {}
        return _block_to_prefs(data.get(_WIDGETS_KEY) if isinstance(data, dict) else None)
    settings = user_store.get_user_settings(user_id) or {}
    ui = settings.get(_UI_KEY)
    return _block_to_prefs(ui.get(_WIDGETS_KEY) if isinstance(ui, dict) else None)


def _write_prefs(user_id: str, update: PreferencesUpdate) -> AiWidgetsPrefs:
    """Merge an opt-in patch into the user's store (row or system file)."""
    current = _read_prefs(user_id)
    enabled = current.enabled if update.enabled is None else bool(update.enabled)
    auto = current.autoExplain if update.autoExplain is None else bool(update.autoExplain)
    block = {"enabled": enabled, "autoExplain": auto}
    if not user_id:
        return AiWidgetsPrefs(enabled=enabled, autoExplain=auto)
    if user_id == SYNTHETIC_USER_ID:
        p = _synth_prefs_path()
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({_WIDGETS_KEY: block}, indent=2), encoding="utf-8")
        tmp.replace(p)
    else:
        settings = user_store.get_user_settings(user_id) or {}
        ui = settings.get(_UI_KEY)
        if not isinstance(ui, dict):
            ui = {}
        ui[_WIDGETS_KEY] = block
        settings[_UI_KEY] = ui
        user_store.set_user_settings(user_id, settings)
    return AiWidgetsPrefs(enabled=enabled, autoExplain=auto)


def _build_prompt(kind: str, payload: dict[str, Any]) -> str:
    """Build a bounded user prompt from an allow-listed kind + a small payload."""
    instruction = _KIND_INSTRUCTIONS.get(kind, _KIND_INSTRUCTIONS["generic"])
    try:
        body = json.dumps(payload, default=str)
    except (TypeError, ValueError):
        body = str(payload)
    if len(body) > _MAX_PAYLOAD_CHARS:
        body = body[:_MAX_PAYLOAD_CHARS] + "...(truncated)"
    return f"{instruction}\n\nData:\n{body}"


def _content_of(result: dict[str, Any]) -> str:
    """Pull the assistant text out of an OpenAI-style completion dict."""
    try:
        choice = (result.get("choices") or [{}])[0]
        return str((choice.get("message") or {}).get("content") or "").strip()
    except (AttributeError, IndexError, TypeError):
        return ""


def _tokens_used(result: dict[str, Any], prompt: str, content: str) -> int:
    """Prefer the model's reported completion tokens; else estimate both sides."""
    usage = result.get("usage")
    if isinstance(usage, dict):
        reported = usage.get("completion_tokens")
        if isinstance(reported, int) and reported > 0:
            return fence.estimate_tokens(prompt) + reported
    return fence.estimate_tokens(prompt) + fence.estimate_tokens(content)


def _remaining_or_none(user_id: str) -> int | None:
    """Remaining daily budget for the UI, or None when the fence is unlimited."""
    decision = fence.check(user_id)
    return None if decision.remaining < 0 else decision.remaining


@router.get(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Get insight-widget preferences",
    description="Return the per-user LLM insight-widget opt-in state and budget.",
)
async def get_preferences(user: User = Depends(require_user)) -> PreferencesResponse:
    user = coerce_user(user)
    return PreferencesResponse(
        aiWidgets=_read_prefs(user.id),
        budget=fence.public_view(user.id),
    )


@router.put(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Update insight-widget preferences",
    description="Turn the opt-in LLM insight widgets on or off (per user).",
)
async def put_preferences(
    body: PreferencesUpdate,
    user: User = Depends(require_user),
) -> PreferencesResponse:
    user = coerce_user(user)
    prefs = _write_prefs(user.id, body)
    return PreferencesResponse(aiWidgets=prefs, budget=fence.public_view(user.id))


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Explain a widget's computed data",
    description=(
        "Return a short, model-generated plain-language explanation of a widget's "
        "already-computed data. Opt-in and cost-fenced; degrades to a uniform "
        "available=false body when disabled, over budget, or without an endpoint."
    ),
)
async def explain(
    request: Request,
    body: ExplainRequest,
    user: User = Depends(require_user),
) -> ExplainResponse:
    user = coerce_user(user)

    # 1. Opt-in gate: no spend, no LLM call, until the user turns it on.
    prefs = _read_prefs(user.id)
    if not prefs.enabled:
        return ExplainResponse(available=False, reason="ai_widgets_disabled")

    # 2. Cost fence (cost-fence-D). Over budget stays on the computed view.
    decision = fence.check(user.id)
    if not decision.allowed:
        return ExplainResponse(
            available=False,
            reason="budget_reached",
            remaining=0,
        )

    # 3. Resolve the caller's OWN fast tier (BYOK). None = no endpoint for them.
    router_obj, _per_user = await resolve_model_router(request, user)
    if router_obj is None:
        return ExplainResponse(available=False, reason="no_endpoint")

    prompt = _build_prompt(body.kind, body.payload if isinstance(body.payload, dict) else {})

    # A widget may ask for the heavier reasoning tier; anything else runs fast.
    # Both go through the caller's OWN router and both are cost-fenced, so the
    # tier only trades a little more spend for a better answer.
    reasoning = body.tier == "reasoning"
    completion = router_obj.reasoning_completion if reasoning else router_obj.fast_completion
    max_tokens = _MAX_TOKENS_REASONING if reasoning else _MAX_TOKENS

    try:
        result = await completion(
            prompt,
            max_tokens=max_tokens,
            system_prompt=_SYSTEM_PROMPT,
        )
    except Exception as exc:  # noqa: BLE001 - a widget explain must never 500
        logger.warning("insights explain failed: %s", exc)
        return ExplainResponse(available=False, reason="error")

    if not isinstance(result, dict):
        return ExplainResponse(available=False, reason="error")

    content = _content_of(result)
    tokens = _tokens_used(result, prompt, content)
    fence.record(user.id, tokens)

    if not content:
        return ExplainResponse(
            available=False,
            reason="empty",
            tokens_used=tokens,
            remaining=_remaining_or_none(user.id),
        )

    return ExplainResponse(
        available=True,
        explanation=content,
        model_generated=True,
        tokens_used=tokens,
        remaining=_remaining_or_none(user.id),
    )


__all__ = ["router"]
