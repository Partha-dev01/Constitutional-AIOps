"""
Constitutional AIOps - System Prompts API Routes

Provides endpoints for viewing and customizing system prompts
for the Fast Agent and Reasoning Agent.
"""

import logging
from typing import Any

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

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

# In-memory storage for prompt customizations
_custom_prompts: dict[str, str] = {}


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

    # Store customization
    _custom_prompts[prompt_name] = body.prompt

    logger.info(f"Updated prompt '{prompt_name}'")

    # Update the agent's prompt if available
    try:
        if default.agent == "fast":
            fast_annotator = getattr(request.app.state, "fast_annotator", None)
            if fast_annotator and hasattr(fast_annotator, "set_system_prompt"):
                fast_annotator.set_system_prompt(prompt_name, body.prompt)
        elif default.agent == "reasoning":
            reasoning_agent = getattr(request.app.state, "reasoning_agent", None)
            if reasoning_agent and hasattr(reasoning_agent, "set_system_prompt"):
                reasoning_agent.set_system_prompt(prompt_name, body.prompt)
    except Exception as e:
        logger.warning(f"Failed to update agent prompt: {e}")

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

    # Remove customization
    _custom_prompts.pop(prompt_name, None)

    logger.info(f"Reset prompt '{prompt_name}' to default")

    return await get_prompt(request, prompt_name)


__all__ = ["router"]
