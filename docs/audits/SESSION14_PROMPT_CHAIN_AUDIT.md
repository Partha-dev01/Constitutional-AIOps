# Session-14 W4 — Frontend→Backend Prompt-Passing Audit (and fix)

**Date:** 2026-06-12 · **Scope:** "checking if prompts are properly passing through … it has
internal issues" (user). Ground-up audit of every hop from the Settings prompt editor to the
live LLM call, plus the fix that makes the chain actually work end-to-end.

## TL;DR

Before this change, editing a system prompt in the UI **did nothing**: the edit was held in a
process-local dict, pushed to a method **neither agent implemented** (silently swallowed), never
persisted, and never reloaded. The API returned `200 OK` the whole time — a false success. Every
real call path read the **baked module constant**, so the agents never saw the edit.

The fix: real overlay methods on both agents (with validation), persistence under
`AIOPS_DATA_DIR`, startup re-application, and a **loud** `PUT` that only returns `200` when the
edit is genuinely applied.

## The chain, hop by hop

| # | Hop | Before (broken) | After (fixed) |
|---|-----|-----------------|---------------|
| 1 | **FE editor** → `PUT /api/v1/prompts/{name}` | Sent edit, always saw `200`, showed "saved". | Unchanged request; FE now surfaces non-2xx as a real error (frontend lane). |
| 2 | **Persistence** (`prompts.py`) | `_custom_prompts` in-memory dict only — lost on every restart/redeploy. | Persisted to `${AIOPS_DATA_DIR}/prompts.json` (atomic write); hydrated into `_custom_prompts` at import so `GET`/list reflect it immediately. |
| 3 | **Push to agent** (`prompts.py`) | `if hasattr(agent, "set_system_prompt")` — **neither `FastAnnotator` nor `ReasoningAgent` defined it** → branch never ran; wrapped in `try/except Exception → logger.warning` so even an error was swallowed. | Both agents implement `set_system_prompt`/`reset_prompts`. `PUT` applies to the agent **first**; `ValueError` → `422`, agent-not-initialised → `503`. Only on success does it persist + return `200`. |
| 4 | **Startup load** (`main.py`) | None — overrides (if they had worked) would vanish on restart. | Lifespan calls `apply_persisted_prompts(app)` after agents are built; re-applies every persisted override to the live agents (skips+logs any the agent rejects). |
| 5 | **Per-call-path usage** | All paths read the **baked constants** directly via `get_system_prompt`, which had no override layer. | `get_system_prompt` returns the override when present, else the constant. Verified call paths: chat → `ReasoningAgent.chat()` → `process()` → `_build_prompt()` → `get_system_prompt("chat")` (`reasoning_agent.py:589`); RCA → `get_system_prompt("rca")`; annotation → `FastAnnotator.process()` → `get_system_prompt()` (`fast_annotator.py:274`). |
| 6 | **Placeholder integrity** | n/a (edits never applied). | The chat prompt injects live state by replacing the literal `{runtime_context}` (`reasoning_agent.py:593`). `set_system_prompt` **rejects** a chat override that drops `{runtime_context}` (`422`), so an edit can't silently disable runtime grounding. |

## Key files

- `src/agents/reasoning_agent.py` — `set_system_prompt`/`reset_prompts`/override-aware
  `get_system_prompt`; `PROMPT_NAME_TO_MODE` (accepts `reasoning_rca|reasoning_chat|reasoning_planning`
  and bare modes); `REQUIRED_PLACEHOLDERS = {"chat": ("{runtime_context}",)}`.
- `src/agents/fast_annotator.py` — same overlay; only `fast_annotator` is a live prompt
  (**`fast_classifier` has no consumer** — documented, not wired).
- `src/api/routes/prompts.py` — persistence (`_prompts_path`/`_load_persisted`/`_save_persisted`),
  `apply_persisted_prompts(app)`, loud `PUT`, persist-on-reset.
- `src/main.py` — lifespan re-applies persisted overrides after agent construction.

## Known non-issues (intentionally left)

- **`fast_classifier`** prompt exists in `DEFAULT_PROMPTS` but no code path consumes it; editing it
  validates and persists but affects nothing. Surfacing/removing it is a UI decision, out of W4 scope.
- Overrides are **global**, not per-user (the prompts API is an operator/admin surface). Matches the
  existing settings model.

## Selection-context (Schema-mode) addendum

`ChatRequest.context` used to be stored on the conversation and **never read**. Session-14 routes a
recognised `source=="schema-graph"` selection into the chat runtime context
(`_render_selection_context`, capped at 8 items / 1200 chars) so the Graph "Schema mode" → "Ask AI"
flow is grounded; `metadata.selection_applied` flags when it fired.
