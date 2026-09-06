"""Constitutional AIOps - canonical tool registry (single source of truth).

The 9 platform tools used to be declared THREE times, by hand, in three files:

* ``src/mcp/server.py``            (``ToolDefinition`` in ``_register_tools``)
* ``src/api/routes/tools.py``      (``ToolInfo`` in ``list_tools`` + ``get_tool``)
* ``src/agents/tool_calling.py``   (``ToolSpec`` in ``_TOOL_SPECS``)

Three hand-maintained copies drift: the agent catalogue even carried a comment
(*"schemas copied to match tools.py's ToolInfo declarations exactly"*) — a manual
sync that WILL rot. This module holds the one authoritative catalogue; the three
sites build their own representation (``ToolDefinition`` / ``ToolInfo`` /
``ToolSpec``) FROM it, so a new tool or a schema edit happens in exactly one place.

Design (deliberately behaviour-preserving, verified against the test-suite):

* ``parameters`` is the LEAN schema — the parameter SET the shared executors in
  ``routes/tools.py`` actually read. This keeps the chat agent's tool-catalogue
  prompt (the LLM-facing surface) byte-identical to the previous hand-written
  ``_TOOL_SPECS``. The MCP server's older per-tool schemas carried a handful of
  vestigial, never-read params (``instance_id``, ``timeout_seconds``,
  ``current_replicas``, ``direction``, ``include_patterns``, ``incident_id``);
  those were documentation-only and are intentionally dropped so the catalogue is
  accurate. No executor behaviour and no test depends on them.
* ``description`` is the user/UI + REST/MCP-listing wording. ``agent_description``
  is the chat tool-calling (LLM) wording — kept separate because the action tools'
  agent copy carries real behavioural guidance ("QUEUES for human approval; tell
  the user to approve or reject") that the listing copy does not.
* ``category`` / ``requires_approval`` / ``risk_level`` are identical across all
  three former sites and carried through unchanged.

Tool ORDER here is authoritative: ``TOOLS_BY_NAME`` preserves it, and the chat
agent's ``detect_named_tools`` returns matches in this order, so the order is part
of the behavioural contract (kept identical to the previous ``_TOOL_SPECS``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolMeta:
    """Canonical metadata for one platform tool.

    ``parameters`` is a JSON-Schema object (``{"type": "object", "properties":
    {...}, "required": [...]}``). ``is_action`` / ``required`` are derived so the
    consuming sites never hand-maintain them.
    """

    name: str
    category: str  # "query" | "action" | "analysis"
    description: str
    agent_description: str
    parameters: dict[str, Any]
    requires_approval: bool = False
    risk_level: str = "low"  # low | medium | high

    @property
    def is_action(self) -> bool:
        return self.category == "action"

    @property
    def required(self) -> list[str]:
        req = self.parameters.get("required", [])
        return [str(r) for r in req] if isinstance(req, list) else []


# ---------------------------------------------------------------------------
# The catalogue. Order is authoritative (see module docstring).
# ---------------------------------------------------------------------------

TOOLS: tuple[ToolMeta, ...] = (
    ToolMeta(
        name="find_similar",
        category="query",
        description="Find similar incidents from episodic memory based on symptoms, affected services, and error patterns",
        agent_description="Find similar past incidents from Neo4j episodic memory (top-k similar incidents).",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Incident title / search text"},
                "category": {"type": "string", "description": "Incident category"},
                "affected_services": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["title"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="get_dependencies",
        category="query",
        description="Get service dependency graph showing upstream and downstream services",
        agent_description="Get a service's upstream/downstream dependency graph from Neo4j for impact analysis.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "depth": {"type": "integer", "default": 2, "description": "Traversal depth"},
            },
            "required": ["service_name"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="analyze_logs",
        category="analysis",
        description="Analyze logs for a service to identify patterns, anomalies, and error clusters",
        agent_description="Analyze logs from Loki for a service: counts, top error patterns, samples.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "time_range_minutes": {"type": "integer", "default": 30},
                "log_level": {"type": "string", "enum": ["all", "error", "warn", "info"], "default": "error"},
            },
            "required": ["service_name"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="analyze_time_series_anomaly",
        category="analysis",
        description="Statistical Z-score anomaly detection on Prometheus metric time series for a service",
        agent_description="Z-score statistical anomaly detection over a service's Prometheus metrics.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "metric_name": {"type": "string", "description": "Specific PromQL metric (optional)"},
                "time_range_minutes": {"type": "integer", "default": 60},
            },
            "required": ["service_name"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="query_recent_logs",
        category="query",
        description="Query recent log entries from Loki for a service within a time window",
        agent_description="Query recent raw log entries from Loki for a service within a time window.",
        parameters={
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name (use 'all' for all)"},
                "time_range_minutes": {"type": "integer", "default": 15},
                "limit": {"type": "integer", "default": 50},
                "query": {"type": "string", "description": "Optional LogQL query override"},
            },
            "required": ["service"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="query_metric",
        category="query",
        description="Query Prometheus metrics for a service over a time range",
        agent_description="Query Prometheus metrics for a service over a time range.",
        parameters={
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name"},
                "time_range_minutes": {"type": "integer", "default": 30},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Optional PromQL queries"},
            },
            "required": ["service"],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="list_containers",
        category="query",
        description="List Docker containers and their status (running, stopped, health)",
        agent_description="List Docker containers and their status (running / stopped / health).",
        parameters={
            "type": "object",
            "properties": {
                "all_containers": {"type": "boolean", "default": False, "description": "Include stopped containers"},
                "name_filter": {"type": "string", "description": "Optional substring filter on container name"},
            },
            "required": [],
        },
        requires_approval=False,
        risk_level="low",
    ),
    ToolMeta(
        name="restart_service",
        category="action",
        description="Restart a whitelisted service container. Gated by AIOPS_ENABLE_ACTION_TOOLS; every call is validated against the constitutional principles first.",
        agent_description=(
            "Restart a whitelisted Docker container. ACTION tool — gated by "
            "AIOPS_ENABLE_ACTION_TOOLS and the constitutional validator. Calling "
            "it QUEUES the restart for human approval (it does not run "
            "immediately); tell the user to approve or reject the proposed action."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to restart (whitelisted, default nextcloud)"},
                "graceful": {"type": "boolean", "default": True},
                "reason": {"type": "string", "description": "Reason for restart (audited)"},
            },
            "required": ["service_name", "reason"],
        },
        requires_approval=True,
        risk_level="medium",
    ),
    ToolMeta(
        name="scale_service",
        category="action",
        description="Scale service replicas up or down (replica count clamped to 0-5). Gated by AIOPS_ENABLE_ACTION_TOOLS; every call is validated against the constitutional principles first.",
        agent_description=(
            "Scale a whitelisted Docker Compose service (replicas clamped 0-5). "
            "ACTION tool — gated by AIOPS_ENABLE_ACTION_TOOLS and the validator. "
            "Calling it QUEUES the scaling for human approval (it does not run "
            "immediately); tell the user to approve or reject the proposed action."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to scale (whitelisted, default nextcloud)"},
                "target_replicas": {"type": "integer", "minimum": 0, "maximum": 5},
                "reason": {"type": "string", "description": "Reason for scaling (audited)"},
            },
            "required": ["service_name", "target_replicas", "reason"],
        },
        requires_approval=True,
        risk_level="medium",
    ),
)

TOOLS_BY_NAME: dict[str, ToolMeta] = {tool.name: tool for tool in TOOLS}

# The mutating tools, in catalogue order. Consumers gate these behind
# AIOPS_ENABLE_ACTION_TOOLS + the constitutional validator.
ACTION_TOOL_NAMES: tuple[str, ...] = tuple(tool.name for tool in TOOLS if tool.is_action)


__all__ = ["ToolMeta", "TOOLS", "TOOLS_BY_NAME", "ACTION_TOOL_NAMES"]
