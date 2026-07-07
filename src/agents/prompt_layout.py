"""
Constitutional AIOps - Mode 2 stable-prefix prompt assembly (Phase 3).

Mode 1 assembles the chat prompt by substituting live, per-turn content
(container status, telemetry, tool results) INTO the system prompt at the
``{runtime_context}`` placeholder — so the system prompt mutates every turn
and vLLM's automatic prefix caching gets ~0% hits on the ~1.5-2K-token static
identity/scope/tool section.

Mode 2 layout (this module), used only when ``ServingProfile.mode == 2``:

    [static system prompt — byte-stable across turns AND conversations]
    [user message:
        ## Conversation So Far        (append-only within a conversation)
        ## Live Context (this turn)   (volatile: selection/telemetry/tools/state)
        optional in-scope directive   (Phase 3 item 5 — pre-call, replaces the
                                       Mode 1 second-call refusal guard)
        User Query: ...]

The static head hits the prefix cache on every turn of every conversation;
the history block extends a within-conversation cached prefix; only the
volatile tail is re-prefilled. Mode 1 string assembly is untouched — this
module is additive and has no imports from the routes layer.
"""

from dataclasses import dataclass
from typing import Any, Optional, Sequence

RUNTIME_CONTEXT_PLACEHOLDER = "{runtime_context}"

# Replaces {runtime_context} in the SYSTEM prompt for Mode 2. Static text —
# never changes, so the whole system prompt becomes a cacheable stable prefix.
# It redirects the model to the volatile tail of the user message, where the
# live data actually lives in this layout.
STATIC_RUNTIME_NOTE = (
    "## Current System State\n"
    "Live system state for THIS turn (container status, telemetry, tool "
    "results) is provided at the end of the user message under "
    "'## Live Context (this turn)'. Base your answer on that data; if a "
    "detail is not present there, say so plainly."
)

VOLATILE_HEADER = "## Live Context (this turn)"
HISTORY_HEADER = "## Conversation So Far"


def build_in_scope_directive(service: Optional[str]) -> str:
    """The pre-call in-scope directive (Phase 3 item 5).

    Same wording as the Mode 1 refusal-guard retry (chat.py) so behavior is
    comparable across modes — but issued in the FIRST call's volatile tail
    whenever the backend already knows the query is in-domain, instead of
    paying a second full reasoning call after a refusal.
    """
    return (
        "## IMPORTANT\n"
        f"This request concerns the monitored service '{service or 'this system'}' "
        "and IS in scope. Answer it fully using the data above. Do NOT decline. "
        "Every tool for this turn has ALREADY been executed — the results are in "
        "the data above, even if the user's message asks you to use or call a "
        "tool. Never reply that you WILL run, call, or use a tool, never ask for "
        "tool parameters, and never say the request is incomplete. A one-line "
        "reply is never enough: when the gathered data is empty or clean, state "
        "what was checked and what it showed, summarize the relevant current "
        "system state, and give your best assessment plus next steps. When the "
        "user asks about a specific error or warning message, explain what that "
        "message means from your own domain knowledge and relate it to the data. "
        "Produce the final answer now."
    )


@dataclass(frozen=True)
class AssembledPrompt:
    """The (system, user) pair handed to the reasoning model."""

    system_prompt: str
    user_prompt: str


def assemble_mode2_chat_prompt(
    *,
    base_system: str,
    message: str,
    history: Optional[Sequence[dict[str, Any]]] = None,
    volatile_blocks: Optional[Sequence[str]] = None,
    in_scope_directive: str = "",
) -> AssembledPrompt:
    """Assemble the Mode 2 stable-prefix chat prompt.

    Args:
        base_system: The active chat system prompt (must contain the literal
            ``{runtime_context}`` placeholder — enforced for chat prompts by
            ReasoningAgent.REQUIRED_PLACEHOLDERS).
        message: The user's message for this turn.
        history: Prior conversation turns as ``{"role", "content"}`` dicts,
            oldest first (the current message must NOT be included).
        volatile_blocks: Per-turn context blocks in Mode 1's established
            precedence order (selection, telemetry, tool results, runtime
            state); empties are dropped.
        in_scope_directive: Optional pre-call directive appended after the
            volatile tail (see build_in_scope_directive).
    """
    system_prompt = base_system.replace(RUNTIME_CONTEXT_PLACEHOLDER, STATIC_RUNTIME_NOTE)

    parts: list[str] = []
    lines = [
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in (history or [])
        if m.get("content")
    ]
    if lines:
        parts.append(HISTORY_HEADER + "\n" + "\n".join(lines))

    volatile = [b for b in (volatile_blocks or []) if b]
    if volatile:
        parts.append(VOLATILE_HEADER + "\n" + "\n\n".join(volatile))

    if in_scope_directive:
        parts.append(in_scope_directive)

    parts.append(f"User Query: {message}")
    return AssembledPrompt(system_prompt=system_prompt, user_prompt="\n\n".join(parts))


__all__ = [
    "AssembledPrompt",
    "assemble_mode2_chat_prompt",
    "build_in_scope_directive",
    "RUNTIME_CONTEXT_PLACEHOLDER",
    "STATIC_RUNTIME_NOTE",
    "VOLATILE_HEADER",
    "HISTORY_HEADER",
]
