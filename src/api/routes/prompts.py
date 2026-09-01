"""
Constitutional AIOps - System Prompts API Routes

Provides endpoints for viewing and customizing system prompts
for the Fast Agent and Reasoning Agent.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.onboarding.generators import build_base_prompt

logger = logging.getLogger(__name__)

router = APIRouter()


class SystemPrompt(BaseModel):
    """System prompt configuration."""
    name: str
    description: str
    prompt: str
    agent: str = Field(..., description="Agent: fast or reasoning")
    editable: bool = True


class PromptUpdate(BaseModel):
    """Request to update a system prompt."""
    prompt: str = Field(..., min_length=10, max_length=10000)


class PromptsListResponse(BaseModel):
    """Response listing all prompts."""
    prompts: list[SystemPrompt]


class GeneratePromptRequest(BaseModel):
    """Onboarding wizard: draft a base prompt from services + topology.

    ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
    it with the reasoning model, FALLING BACK to the template on any failure so
    setup never breaks. The draft is NOT persisted — the wizard Applies it via
    ``PUT /prompts/reasoning_chat``.
    """

    services: list[dict[str, Any]] = Field(default_factory=list)
    topology: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["template", "llm"] = "template"


class GeneratePromptResponse(BaseModel):
    """A suggested base-prompt draft (preview, not persisted)."""

    prompt: str
    note: str = ""


# Default prompts
DEFAULT_PROMPTS = {
    "fast_annotator": SystemPrompt(
        name="fast_annotator",
        description="Fast Agent - Telemetry Annotation",
        agent="fast",
        prompt="""You are a Fast Telemetry Annotator for an AIOps system. Your role is to quickly classify and annotate incoming telemetry signals.

For each telemetry input, provide:
1. Severity: critical, high, medium, low, info
2. Category: performance, availability, security, configuration, network, database
3. Affected Services: list of services mentioned
4. Summary: One-line description
5. Action Required: immediate, monitor, investigate, none

Respond in JSON format. Be concise and accurate. /no_think""",
    ),
    "fast_classifier": SystemPrompt(
        name="fast_classifier",
        description="Fast Agent - Incident Classification",
        agent="fast",
        prompt="""You are an Incident Classifier for AIOps. Classify incidents quickly based on patterns.

Input: Raw incident data
Output: JSON with:
- category: string
- severity: string
- confidence: 0-1
- keywords: list
- related_services: list

Be fast and accurate. /no_think""",
    ),
    "reasoning_rca": SystemPrompt(
        name="reasoning_rca",
        description="Reasoning Agent - Root Cause Analysis",
        agent="reasoning",
        prompt="""You are an expert Root Cause Analysis (RCA) agent for infrastructure operations. Given telemetry signals and incident data, you must:

1. Analyze the causal chain of events
2. Identify the root cause with confidence score
3. List contributing factors
4. Provide evidence from telemetry
5. Suggest remediation actions

Format your response as structured JSON with:
- root_cause: string
- confidence: 0-1
- contributing_factors: list
- evidence: list of {source, data, relevance}
- remediation: list of steps with risk levels

Think step by step. Be thorough but actionable.""",
    ),
    "reasoning_chat": SystemPrompt(
        name="reasoning_chat",
        description="Reasoning Agent - Human Chat Interface",
        agent="reasoning",
        prompt="""You are an intelligent AIOps assistant helping infrastructure operators. You have access to:

1. Real-time telemetry (logs, metrics, traces)
2. Incident history and patterns
3. Service dependency graphs
4. Episodic memory of past resolutions

When operators ask questions:
- Provide clear, actionable answers
- Reference specific data when available
- Suggest next steps
- Warn about potential risks

Be helpful, professional, and safety-conscious. All actions requiring infrastructure changes must go through the Constitutional AI approval process.""",
    ),
    "reasoning_planning": SystemPrompt(
        name="reasoning_planning",
        description="Reasoning Agent - Remediation Planning",
        agent="reasoning",
        prompt="""You are a Remediation Planning agent for AIOps. Given an incident and RCA, create a safe remediation plan.

Constitutional AI Principles:
- Tier 1 (Safety): Never violate. Includes: minimize blast radius, no data loss, no security degradation
- Tier 2 (Operational): Require approval. Includes: service restarts, scaling, config changes
- Tier 3 (Learning): Soft guidelines. Includes: documentation, pattern learning

For each remediation step, specify:
1. Action type and target
2. Risk level (low/medium/high)
3. Rollback procedure
4. Validation method
5. Required approvals

Output structured JSON that the action executor can process.""",
    ),
}

# ---------------------------------------------------------------------------
# Persistence (session-14 W4)
#
# Before W4 the prompts API only mutated an in-memory dict and pushed to a
# `set_system_prompt` method that NEITHER agent implemented (hasattr-guarded,
# silently swallowed) — so UI prompt edits never reached the agents and never
# survived a restart. Now overrides are persisted under AIOPS_DATA_DIR and
# re-applied to the live agents at startup; PUT fails loudly if it cannot be
# applied. See docs/audits/SESSION14_PROMPT_CHAIN_AUDIT.md.
# ---------------------------------------------------------------------------


class _AgentUnavailableError(RuntimeError):
    """Raised when the target agent is not initialised on app.state."""


def _prompts_path() -> Path:
    """Path to the persisted prompt-overrides JSON (mirrors settings.py).

    Priority: AIOPS_DATA_DIR env (prod bind-mount) else repo-local data/settings.
    """
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "settings"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path / "prompts.json"


def _load_persisted() -> dict[str, str]:
    """Load persisted prompt overrides from disk; {} on any error."""
    try:
        p = _prompts_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Only keep known, editable prompt names with str values.
                return {
                    k: v
                    for k, v in data.items()
                    if k in DEFAULT_PROMPTS and isinstance(v, str)
                }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read persisted prompts: %s", exc)
    return {}


def _save_persisted(data: dict[str, str]) -> None:
    """Write the overrides dict to disk (atomic-ish: write then rename)."""
    p = _prompts_path()
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(p)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist prompts: %s", exc)


# In-memory cache of customizations, hydrated from disk at import so GET/list
# reflect persisted overrides immediately (the live agent push happens in
# apply_persisted_prompts at startup).
_custom_prompts: dict[str, str] = _load_persisted()


def _push_to_agent(app: FastAPI, prompt_name: str, agent_kind: str, text: str) -> None:
    """Apply a prompt override to the live agent.

    Raises:
        _AgentUnavailableError: the target agent is not on app.state.
        ValueError: the agent rejected the prompt (unknown name / empty /
            missing required placeholder).
    """
    attr = "fast_annotator" if agent_kind == "fast" else "reasoning_agent"
    agent = getattr(app.state, attr, None)
    if agent is None or not hasattr(agent, "set_system_prompt"):
        raise _AgentUnavailableError(
            f"{attr} is not initialised — prompt '{prompt_name}' was not applied"
        )
    agent.set_system_prompt(prompt_name, text)


def apply_persisted_prompts(app: FastAPI) -> list[str]:
    """Re-apply persisted prompt overrides to the live agents (startup hook).

    Called from the app lifespan after the agents are constructed. Skips (and
    logs) any override the agent rejects so one bad entry can't block startup.

    Returns:
        The list of prompt names successfully applied.
    """
    applied: list[str] = []
    for name, text in _load_persisted().items():
        default = DEFAULT_PROMPTS.get(name)
        if default is None:
            continue
        try:
            _push_to_agent(app, name, default.agent, text)
            applied.append(name)
        except (_AgentUnavailableError, ValueError) as exc:
            logger.warning("Skipped persisted prompt '%s': %s", name, exc)
    return applied


@router.get(
    "/",
    response_model=PromptsListResponse,
    summary="List Prompts",
    description="List all system prompts",
)
async def list_prompts(request: Request) -> PromptsListResponse:
    """List all system prompts with current values."""
    prompts = []

    for name, default in DEFAULT_PROMPTS.items():
        prompt_text = _custom_prompts.get(name, default.prompt)
        prompts.append(SystemPrompt(
            name=default.name,
            description=default.description,
            agent=default.agent,
            prompt=prompt_text,
            editable=default.editable,
        ))

    return PromptsListResponse(prompts=prompts)


@router.get(
    "/{prompt_name}",
    response_model=SystemPrompt,
    summary="Get Prompt",
    description="Get a specific system prompt",
)
async def get_prompt(request: Request, prompt_name: str) -> SystemPrompt:
    """Get a specific system prompt."""
    if prompt_name not in DEFAULT_PROMPTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found",
        )

    default = DEFAULT_PROMPTS[prompt_name]
    prompt_text = _custom_prompts.get(prompt_name, default.prompt)

    return SystemPrompt(
        name=default.name,
        description=default.description,
        agent=default.agent,
        prompt=prompt_text,
        editable=default.editable,
    )


@router.put(
    "/{prompt_name}",
    response_model=SystemPrompt,
    summary="Update Prompt",
    description="Update a system prompt",
)
async def update_prompt(
    request: Request,
    prompt_name: str,
    body: PromptUpdate,
) -> SystemPrompt:
    """Update a system prompt."""
    if prompt_name not in DEFAULT_PROMPTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found",
        )

    default = DEFAULT_PROMPTS[prompt_name]

    if not default.editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Prompt '{prompt_name}' is not editable",
        )

    # Apply to the live agent FIRST and fail loudly: a 200 here must mean the
    # edit is genuinely active, not silently dropped (the pre-W4 behaviour).
    try:
        _push_to_agent(request.app, prompt_name, default.agent, body.prompt)
    except ValueError as exc:
        # Agent rejected the prompt (empty / missing required placeholder).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except _AgentUnavailableError as exc:
        # Cannot verify application — do not half-persist; surface it.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # Applied successfully — now persist so it survives restart/redeploy.
    _custom_prompts[prompt_name] = body.prompt
    _save_persisted(_custom_prompts)
    logger.info(f"Updated prompt '{prompt_name}' (applied + persisted)")

    return SystemPrompt(
        name=default.name,
        description=default.description,
        agent=default.agent,
        prompt=body.prompt,
        editable=default.editable,
    )


@router.post(
    "/reset",
    response_model=PromptsListResponse,
    summary="Reset Prompts",
    description="Reset all prompts to defaults",
)
async def reset_prompts(request: Request) -> PromptsListResponse:
    """Reset all prompts to their default values."""
    global _custom_prompts
    _custom_prompts = {}
    _save_persisted(_custom_prompts)

    logger.info("Reset all prompts to defaults")

    # Reset agent prompts if available
    try:
        fast_annotator = getattr(request.app.state, "fast_annotator", None)
        if fast_annotator and hasattr(fast_annotator, "reset_prompts"):
            fast_annotator.reset_prompts()

        reasoning_agent = getattr(request.app.state, "reasoning_agent", None)
        if reasoning_agent and hasattr(reasoning_agent, "reset_prompts"):
            reasoning_agent.reset_prompts()
    except Exception as e:
        logger.warning(f"Failed to reset agent prompts: {e}")

    return await list_prompts(request)


@router.post(
    "/{prompt_name}/reset",
    response_model=SystemPrompt,
    summary="Reset Single Prompt",
    description="Reset a specific prompt to default",
)
async def reset_single_prompt(request: Request, prompt_name: str) -> SystemPrompt:
    """Reset a specific prompt to its default value."""
    if prompt_name not in DEFAULT_PROMPTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found",
        )

    # Remove customization + clear the live override on the agent.
    _custom_prompts.pop(prompt_name, None)
    _save_persisted(_custom_prompts)
    try:
        default = DEFAULT_PROMPTS[prompt_name]
        attr = "fast_annotator" if default.agent == "fast" else "reasoning_agent"
        agent = getattr(request.app.state, attr, None)
        if agent is not None and hasattr(agent, "reset_prompts"):
            agent.reset_prompts(prompt_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to clear live override for '%s': %s", prompt_name, exc)

    logger.info(f"Reset prompt '{prompt_name}' to default")

    return await get_prompt(request, prompt_name)


_BASE_PROMPT_SYSTEM = (
    "You are helping configure an AIOps assistant. Output ONLY the system prompt "
    "text for an operations assistant — no preamble, no markdown fences, no "
    "<think> tags, no commentary."
)


def _extract_prompt_text(response: Any) -> str:
    """Pull text out of an OpenAI-compatible completion (or a plain string)."""
    if isinstance(response, str):
        text = response
    elif isinstance(response, dict):
        try:
            text = str(response["choices"][0]["message"]["content"] or "")
        except (KeyError, IndexError, TypeError):
            text = ""
    else:
        content = getattr(response, "content", None)
        text = str(content) if content is not None else ""
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.strip()


@router.post(
    "/generate",
    response_model=GeneratePromptResponse,
    summary="Generate Base Prompt (onboarding)",
    description=(
        "Draft a base operations-assistant system prompt from the services + "
        "topology entered in the onboarding wizard. ``mode=template`` (default) "
        "is deterministic + offline; ``mode=llm`` refines it with the reasoning "
        "model and falls back to the template on any failure. The draft is NOT "
        "persisted — Apply it via PUT /prompts/reasoning_chat."
    ),
)
async def generate_base_prompt(
    request: Request, body: GeneratePromptRequest
) -> GeneratePromptResponse:
    """Deterministic (or LLM-refined) base-prompt draft. Never persists."""
    template = build_base_prompt(body.services, body.topology)

    if body.mode == "llm":
        model_router = getattr(request.app.state, "model_router", None)
        if model_router is None:
            return GeneratePromptResponse(
                prompt=template,
                note="No LLM endpoint is configured yet; drafted a template base "
                "prompt. Edit, then Save.",
            )
        user_prompt = (
            "Write a concise base system prompt for an AIOps operations assistant "
            "for this platform. Describe the platform accurately and instruct the "
            "assistant to ground answers in telemetry, reason with the service "
            "dependency graph, and route every infrastructure change through the "
            "Constitutional AI approval process. Here is a template to improve:\n\n"
            f"{template}"
        )
        try:
            response = await model_router.reasoning_completion(
                user_prompt, max_tokens=1200, system_prompt=_BASE_PROMPT_SYSTEM
            )
            text = _extract_prompt_text(response)
            if len(text) >= 10:
                return GeneratePromptResponse(
                    prompt=text[:10000],
                    note="AI-assisted draft. Review and edit, then Save.",
                )
            return GeneratePromptResponse(
                prompt=template,
                note="AI assist returned nothing usable; using the template. "
                "Edit, then Save.",
            )
        except Exception as exc:  # noqa: BLE001 - LLM must never break setup
            logger.warning(
                "Wizard LLM base-prompt generate failed; using template: %s", exc
            )
            return GeneratePromptResponse(
                prompt=template,
                note="AI assist was unavailable; using the template. Edit, then Save.",
            )

    return GeneratePromptResponse(
        prompt=template,
        note="Drafted a base prompt from your services. Review and edit, then Save.",
    )


__all__ = ["router", "apply_persisted_prompts"]
