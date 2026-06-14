"""
Constitutional AIOps - Editable platform-topology schema API.

Makes the platform topology graph EDITABLE (like the system prompt) and lets
the 14B reasoning model GENERATE a candidate schema from a natural-language
prompt — guardrailed so a bad generation can never break the live view.

Flow (locked decision: "Preview + Apply, with fallback"):
    user prompt → 14B generates candidate → STRICT validation → returned as a
    PREVIEW (not applied) → user clicks Apply (PUT) → persisted + becomes the
    live topology. The auto-discovered topology is ALWAYS restorable (reset).

Endpoints (mounted at ``/api/v1/topology``):
    GET    /schema           current editable schema (custom if set, else the
                             discovered seed) + active mode.
    PUT    /schema           validate + persist a user-edited schema → mode=custom
                             (this is "Apply").
    POST   /schema/generate  body {prompt}; 14B generates → validate → PREVIEW
                             (NOT persisted). Retries once on bad LLM output,
                             then returns a structured error. Never crashes,
                             never persists unvalidated output.
    POST   /schema/reset     revert to discovered (mode=discovered).

The persisted custom schema is honoured by ``GET /api/v1/graph/topology`` via
``render_custom_topology`` so an applied schema renders byte-identically to the
discovered one (see ``src/api/routes/graph_topology.py``).
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.persistence import store as persistence_store
from src.topology.schema import (
    ALLOWED_EDGE_KINDS,
    ALLOWED_NODE_KINDS,
    ALLOWED_RELATIONSHIPS,
    MAX_EDGES,
    MAX_NODES,
    SchemaValidationError,
    TopologySchema,
    discovered_schema_from_seed,
    validate_topology_schema,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models (the frontend Settings-editor contract)
# ---------------------------------------------------------------------------

class TopologySchemaResponse(BaseModel):
    """Current editable schema + active mode.

    ``mode`` is ``custom`` when an operator-applied schema is live, else
    ``discovered`` (the seed topology, returned as an editable starting point).
    """

    mode: str = Field(..., description="discovered | custom")
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class TopologySchemaUpdate(BaseModel):
    """An operator-edited schema to validate + persist (the 'Apply' request)."""

    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


class GenerateSchemaRequest(BaseModel):
    """Natural-language prompt for the 14B schema generator."""

    prompt: str = Field(..., min_length=1, max_length=4000)


class GenerateSchemaResponse(BaseModel):
    """A validated candidate schema returned as a PREVIEW (not persisted)."""

    preview: bool = True
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    note: str = Field("", description="Optional info note (e.g. retry happened)")


# ---------------------------------------------------------------------------
# Schema <-> dict helpers
# ---------------------------------------------------------------------------

def _schema_to_payload(schema: TopologySchema) -> dict[str, list[dict[str, Any]]]:
    """Serialise a validated ``TopologySchema`` to plain ``{"nodes","edges"}`` dicts."""
    return {
        "nodes": [n.model_dump() for n in schema.nodes],
        "edges": [e.model_dump() for e in schema.edges],
    }


def _current_editable_schema() -> tuple[str, TopologySchema]:
    """Return ``(mode, schema)`` for the current editable topology.

    Custom schema if one is persisted and mode is custom, otherwise the
    discovered seed topology as an editable starting point. A corrupt/invalid
    persisted custom schema fails soft to the discovered seed — the editor is
    never handed a broken document.
    """
    mode = persistence_store.get_topology_mode()
    if mode == persistence_store.TOPOLOGY_MODE_CUSTOM:
        raw = persistence_store.load_topology_schema()
        if raw is not None:
            try:
                return mode, validate_topology_schema(raw)
            except SchemaValidationError as exc:
                logger.warning(
                    "Persisted custom topology schema is invalid; "
                    "falling back to discovered: %s",
                    exc.errors,
                )
    return persistence_store.TOPOLOGY_MODE_DISCOVERED, discovered_schema_from_seed()


# ---------------------------------------------------------------------------
# LLM generation prompt (handholding: exact schema + kinds + example + current)
# ---------------------------------------------------------------------------

_GENERATE_SYSTEM_PROMPT = (
    "You are a platform-architecture assistant for an AIOps system. You output "
    "ONLY a single JSON object describing a service topology. Never include "
    "prose, markdown, code fences, or <think> tags — JSON only."
)

_GENERATE_PROMPT_TEMPLATE = """Modify or extend the CURRENT platform topology to satisfy this request:

REQUEST:
{user_prompt}

You must return a SINGLE JSON object with exactly two keys, "nodes" and "edges":

{{
  "nodes": [
    {{"id": "string-unique", "label": "Human Label", "kind": "<one allowed kind>",
      "tier": 0, "port": 8000, "description": "what it does"}}
  ],
  "edges": [
    {{"source": "node-id", "target": "node-id",
      "relationship": "DEPENDS_ON", "kind": "static"}}
  ]
}}

STRICT RULES — a response breaking ANY rule is rejected:
- Output JSON ONLY. No markdown, no ```json fences, no commentary.
- Every node "id" is unique and non-empty.
- "kind" MUST be one of: {allowed_kinds}.
- "tier" is an integer >= 0 (0 = entry point, higher = deeper dependency).
- "port" is an integer 0-65535 or omit it; "description" is a short string.
- Every edge "source" and "target" MUST be the "id" of a node you listed.
- "relationship" MUST be one of: {allowed_relationships}.
- "kind" on an edge MUST be one of: {allowed_edge_kinds}.
- At most {max_nodes} nodes and {max_edges} edges.
- PREFER modifying/extending the CURRENT topology below over inventing a new
  one. Keep existing ids stable unless the request says to rename them. Do NOT
  invent fields beyond the ones shown above.

CURRENT topology (your starting point):
{current_schema}

EXAMPLE of a valid response:
{example}

Return ONLY the JSON object now."""

_EXAMPLE_SCHEMA = {
    "nodes": [
        {
            "id": "caddy",
            "label": "Caddy",
            "kind": "gateway",
            "tier": 0,
            "port": 443,
            "description": "Reverse proxy / TLS entrypoint",
        },
        {
            "id": "backend",
            "label": "Backend",
            "kind": "backend",
            "tier": 1,
            "port": 8000,
            "description": "FastAPI orchestrator",
        },
        {
            "id": "neo4j",
            "label": "Neo4j",
            "kind": "datastore",
            "tier": 2,
            "port": 7687,
            "description": "Graph database",
        },
    ],
    "edges": [
        {"source": "caddy", "target": "backend", "relationship": "DEPENDS_ON", "kind": "static"},
        {"source": "backend", "target": "neo4j", "relationship": "DEPENDS_ON", "kind": "static"},
    ],
}


def _build_generate_prompt(user_prompt: str, current: TopologySchema) -> str:
    """Compose the careful, fully-specified generate prompt for the 14B."""
    return _GENERATE_PROMPT_TEMPLATE.format(
        user_prompt=user_prompt.strip(),
        allowed_kinds=", ".join(sorted(ALLOWED_NODE_KINDS)),
        allowed_relationships=", ".join(sorted(ALLOWED_RELATIONSHIPS)),
        allowed_edge_kinds=", ".join(sorted(ALLOWED_EDGE_KINDS)),
        max_nodes=MAX_NODES,
        max_edges=MAX_EDGES,
        current_schema=json.dumps(_schema_to_payload(current), indent=2),
        example=json.dumps(_EXAMPLE_SCHEMA, indent=2),
    )


def _extract_content(response: Any) -> str:
    """Pull the text content out of an OpenAI-compatible completion response.

    The ModelRouter returns ``{"choices": [{"message": {"content": ...}}]}``.
    Defensively handle a plain string or a missing key too.
    """
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        try:
            return str(response["choices"][0]["message"]["content"] or "")
        except (KeyError, IndexError, TypeError):
            return ""
    content = getattr(response, "content", None)
    return str(content) if content is not None else ""


def _parse_json_object(text: str) -> Any:
    """Best-effort extract + parse a JSON object from raw LLM text.

    Strips <think> tags and ```json fences, then falls back to the first {...}
    span. Returns the parsed value (caller validates) or raises ValueError.
    """
    cleaned = text.strip()
    if "</think>" in cleaned:
        cleaned = cleaned.split("</think>")[-1].strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1].strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            cleaned = cleaned[start:end]
    return json.loads(cleaned)


async def _generate_once(
    model_router: Any, prompt: str
) -> TopologySchema:
    """One generate attempt: call the 14B, parse, sanitise + strict-validate.

    Raises ``SchemaValidationError`` (bad/invalid output) or ``ValueError``
    (unparseable JSON) — both are caught by the caller for the retry logic.
    """
    response = await model_router.reasoning_completion(
        prompt,
        max_tokens=2048,
        system_prompt=_GENERATE_SYSTEM_PROMPT,
    )
    text = _extract_content(response)
    parsed = _parse_json_object(text)  # may raise ValueError
    # validate_topology_schema sanitises/clamps before validating.
    return validate_topology_schema(parsed)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/schema",
    response_model=TopologySchemaResponse,
    summary="Get Editable Topology Schema",
    description=(
        "Return the current editable platform-topology schema — the persisted "
        "custom schema when mode is custom, otherwise the auto-discovered seed "
        "topology as an editable starting point — plus the active mode."
    ),
)
async def get_topology_schema() -> TopologySchemaResponse:
    """Return the current editable schema + mode."""
    mode, schema = _current_editable_schema()
    payload = _schema_to_payload(schema)
    return TopologySchemaResponse(mode=mode, nodes=payload["nodes"], edges=payload["edges"])


@router.put(
    "/schema",
    response_model=TopologySchemaResponse,
    summary="Apply (Save) Topology Schema",
    description=(
        "Validate and persist a user-edited topology schema, setting mode=custom. "
        "Rejects a malformed schema with a structured 422 (the guardrail) so a "
        "broken schema is never persisted or made live."
    ),
)
async def put_topology_schema(body: TopologySchemaUpdate) -> TopologySchemaResponse:
    """Validate + persist an edited schema ('Apply'). 422 on invalid input."""
    try:
        schema = validate_topology_schema(body.model_dump())
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid topology schema", "errors": exc.errors},
        )

    payload = _schema_to_payload(schema)
    persistence_store.save_topology_schema(payload)
    logger.info(
        "Custom topology schema applied: %d nodes, %d edges",
        len(payload["nodes"]),
        len(payload["edges"]),
    )
    return TopologySchemaResponse(
        mode=persistence_store.TOPOLOGY_MODE_CUSTOM,
        nodes=payload["nodes"],
        edges=payload["edges"],
    )


@router.post(
    "/schema/generate",
    response_model=GenerateSchemaResponse,
    summary="Generate Topology Schema (LLM preview)",
    description=(
        "Have the Qwen3-14B reasoning model generate a candidate topology schema "
        "from a natural-language prompt. The candidate is strictly validated and "
        "returned as a PREVIEW (NOT persisted). Retries once on invalid LLM "
        "output, then returns a structured 422. Never crashes, never persists "
        "unvalidated output."
    ),
)
async def generate_topology_schema(
    request: Request, body: GenerateSchemaRequest
) -> GenerateSchemaResponse:
    """Generate → validate → PREVIEW. Retry once, then structured 422."""
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning model not available.",
        )

    _, current = _current_editable_schema()
    prompt = _build_generate_prompt(body.prompt, current)

    last_errors: list[str] = []
    note = ""
    for attempt in range(2):  # initial try + one retry
        try:
            schema = await _generate_once(model_router, prompt)
            payload = _schema_to_payload(schema)
            if attempt > 0:
                note = "Recovered on retry after an invalid first generation."
            return GenerateSchemaResponse(
                preview=True,
                nodes=payload["nodes"],
                edges=payload["edges"],
                note=note,
            )
        except SchemaValidationError as exc:
            last_errors = exc.errors
            logger.warning(
                "LLM topology generation invalid (attempt %d): %s", attempt + 1, exc.errors
            )
        except ValueError as exc:
            last_errors = [f"could not parse JSON from model output: {exc}"]
            logger.warning(
                "LLM topology generation unparseable (attempt %d): %s", attempt + 1, exc
            )
        except Exception as exc:  # noqa: BLE001 - the LLM call must never crash the route
            last_errors = [f"model call failed: {exc}"]
            logger.warning(
                "LLM topology generation call failed (attempt %d): %s", attempt + 1, exc
            )

    # Both attempts failed — structured error, nothing persisted.
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": "The model could not produce a valid topology schema. "
            "Try rephrasing the request.",
            "errors": last_errors,
        },
    )


@router.post(
    "/schema/reset",
    response_model=TopologySchemaResponse,
    summary="Reset Topology Schema to Discovered",
    description=(
        "Revert to the auto-discovered topology (mode=discovered), dropping any "
        "applied custom schema. The discovered topology is always restorable."
    ),
)
async def reset_topology_schema() -> TopologySchemaResponse:
    """Revert to discovered mode (the always-available fallback)."""
    persistence_store.reset_topology_mode()
    schema = discovered_schema_from_seed()
    payload = _schema_to_payload(schema)
    logger.info("Topology schema reset to discovered")
    return TopologySchemaResponse(
        mode=persistence_store.TOPOLOGY_MODE_DISCOVERED,
        nodes=payload["nodes"],
        edges=payload["edges"],
    )


__all__ = ["router"]
