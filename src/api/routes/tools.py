"""
Constitutional AIOps - Tools API Routes

Exposes MCP tools through REST API for frontend and external integrations.

Research Paper (Section 4.5) defines 5 MCP tools:
1. find_similar_incidents - Neo4j query for similar past incidents
2. get_component_dependencies - Graph traversal for impact analysis
3. restart_service - Docker service restart
4. scale_service - Container replica scaling
5. analyze_time_series_anomaly - Statistical analysis (Z-score)
"""

import asyncio
import logging
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.utils.audit import get_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Action-tool gating constants (restart_service / scale_service)
# ---------------------------------------------------------------------------

# The two tools that mutate real containers. Everything else is read-only.
ACTION_TOOLS: tuple[str, ...] = ("restart_service", "scale_service")

# Master kill-switch: action tools stay refused unless this env var is truthy.
ACTION_TOOLS_ENV = "AIOPS_ENABLE_ACTION_TOOLS"

# Comma-separated extra container names allowed as action targets
# (same pattern as AIOPS_DEMO_CONTAINER_WHITELIST in demo.py).
ACTION_CONTAINER_WHITELIST_ENV = "AIOPS_ACTION_CONTAINER_WHITELIST"

# scale_service replica clamp — keeps a typo like 500 from forking the host.
MIN_SCALE_REPLICAS = 0
MAX_SCALE_REPLICAS = 5

# Defense-in-depth: even whitelisted names must look like docker names, never
# like CLI flags or shell metacharacters.
_CONTAINER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _action_tools_enabled() -> bool:
    """True when the operator has explicitly enabled action tools via env."""
    return os.getenv(ACTION_TOOLS_ENV, "").lower() in ("1", "true", "yes")


def _allowed_action_containers() -> set[str]:
    """Containers action tools may target: nextcloud by default, extendable
    via a comma-separated AIOPS_ACTION_CONTAINER_WHITELIST."""
    extra = os.getenv(ACTION_CONTAINER_WHITELIST_ENV, "")
    allowed = {"nextcloud"}
    allowed.update(name.strip() for name in extra.split(",") if name.strip())
    return allowed


def _resolve_action_container(service_name: Any) -> Optional[str]:
    """Resolve a requested service name to a whitelisted container name.

    Accepts the bare name or the platform's ``aiops-`` prefixed convention,
    but ONLY if the resolved name is on the whitelist AND is a syntactically
    safe docker name. Returns None when no whitelisted match exists.
    """
    if not isinstance(service_name, str) or not service_name.strip():
        return None
    name = service_name.strip()
    allowed = _allowed_action_containers()
    for candidate in (name, f"aiops-{name}"):
        if candidate in allowed and _CONTAINER_NAME_RE.match(candidate):
            return candidate
    return None


class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    context: dict[str, Any] | None = Field(None, description="Additional context")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tool_name": "find_similar",
                    "parameters": {
                        "title": "Database connection timeout",
                        "category": "performance",
                        "affected_services": ["api-gateway", "user-service"],
                        "limit": 5
                    }
                },
                {
                    "tool_name": "analyze_logs",
                    "parameters": {
                        "service_name": "api-gateway",
                        "time_range_minutes": 30,
                        "log_level": "error"
                    }
                }
            ]
        }
    }


class ToolCallResponse(BaseModel):
    """Response from tool call."""
    success: bool
    data: Any
    error: str | None = None
    # Machine-readable refusal/failure class so the frontend can render
    # distinct states (e.g. "action_tools_disabled", "approval_required").
    error_code: str | None = None
    execution_time_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    """Tool information."""
    name: str
    description: str
    category: str
    parameters: dict[str, Any]
    requires_approval: bool
    risk_level: str
    # Gating metadata: action tools report enabled=False (with the env var in
    # gated_by) until AIOPS_ENABLE_ACTION_TOOLS is set, so the frontend can be
    # data-driven instead of hardcoding which tools are disabled.
    enabled: bool = True
    gated_by: str | None = None


class ToolListResponse(BaseModel):
    """Response listing all tools."""
    tools: list[ToolInfo]
    total: int


def _apply_action_gating(tool: ToolInfo) -> ToolInfo:
    """Stamp enabled/gated_by metadata onto action-class tool definitions."""
    if tool.category == "action" or tool.name in ACTION_TOOLS:
        tool.enabled = _action_tools_enabled()
        tool.gated_by = ACTION_TOOLS_ENV
    return tool


@router.get(
    "/",
    response_model=ToolListResponse,
    summary="List Tools",
    description="List all available MCP tools",
)
async def list_tools(request: Request) -> ToolListResponse:
    """
    List all available MCP tools.

    Returns:
        List of tool definitions
    """
    mcp_server = getattr(request.app.state, "mcp_server", None)

    if mcp_server is None:
        # Return tool list - all 5 tools from Research Paper Section 4.5
        default_tools = [
            ToolInfo(
                name="find_similar",
                description="Find similar incidents from Neo4j episodic memory (top-k similar past incidents)",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Incident title to search for"},
                        "category": {"type": "string", "description": "Incident category"},
                        "affected_services": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["title"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="get_dependencies",
                description="Get service dependency graph from Neo4j for impact analysis",
                category="query",
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
            ToolInfo(
                name="restart_service",
                description="Restart a whitelisted Docker container (docker restart). Gated by AIOPS_ENABLE_ACTION_TOOLS and constitutional validation.",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to restart — must be on the action container whitelist (default: nextcloud)"},
                        "graceful": {"type": "boolean", "default": True, "description": "Whether to perform a graceful restart"},
                        "reason": {"type": "string", "description": "Reason for restart (recorded in the audit trail)"},
                    },
                    "required": ["service_name", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            ToolInfo(
                name="scale_service",
                description="Scale Docker Compose service replicas. Replica count is clamped to 0-5. Gated by AIOPS_ENABLE_ACTION_TOOLS and constitutional validation.",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to scale — must be on the action container whitelist (default: nextcloud)"},
                        "target_replicas": {"type": "integer", "minimum": 0, "maximum": 5, "description": "Target replica count (clamped to 0-5)"},
                        "reason": {"type": "string", "description": "Reason for scaling (recorded in the audit trail)"},
                    },
                    "required": ["service_name", "target_replicas", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            ToolInfo(
                name="analyze_logs",
                description="Analyze logs from Loki for patterns and anomalies",
                category="analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to analyze"},
                        "time_range_minutes": {"type": "integer", "default": 30, "description": "Time window in minutes to analyze"},
                        "log_level": {"type": "string", "enum": ["all", "error", "warn", "info"], "default": "error", "description": "Minimum log level to analyze"},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="analyze_time_series_anomaly",
                description="Statistical analysis of metrics using Z-score for anomaly detection",
                category="analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to analyze"},
                        "metric_name": {"type": "string", "description": "Specific PromQL metric name to analyze (optional; defaults to all summary metrics)"},
                        "time_range_minutes": {"type": "integer", "default": 60, "description": "Time window in minutes for the analysis"},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            # Phase-2 tools
            ToolInfo(
                name="query_recent_logs",
                description="Query recent log entries from Loki for a service within a time window",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name (use 'all' for all services)"},
                        "time_range_minutes": {"type": "integer", "default": 15, "description": "How many minutes back to query"},
                        "limit": {"type": "integer", "default": 50, "description": "Maximum number of log entries to return"},
                        "query": {"type": "string", "description": "Optional LogQL query override"},
                    },
                    "required": ["service"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="query_metric",
                description="Query Prometheus metrics for a service over a time range",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                        "time_range_minutes": {"type": "integer", "default": 30, "description": "Time window in minutes to query"},
                        "metrics": {"type": "array", "items": {"type": "string"}, "description": "Optional list of PromQL queries (defaults to summary metrics)"},
                    },
                    "required": ["service"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="list_containers",
                description="List Docker containers and their status (running, stopped, health)",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "all_containers": {"type": "boolean", "default": False, "description": "Include stopped containers (default: running only)"},
                        "name_filter": {"type": "string", "description": "Optional substring filter on container name"},
                    },
                    "required": [],
                },
                requires_approval=False,
                risk_level="low",
            ),
        ]
        default_tools = [_apply_action_gating(t) for t in default_tools]
        return ToolListResponse(tools=default_tools, total=len(default_tools))

    tools = mcp_server.list_tools()
    return ToolListResponse(
        tools=[_apply_action_gating(ToolInfo(**t)) for t in tools],
        total=len(tools),
    )


@router.get(
    "/{tool_name}",
    response_model=ToolInfo,
    summary="Get Tool",
    description="Get detailed information about a specific tool",
)
async def get_tool(request: Request, tool_name: str) -> ToolInfo:
    """
    Get tool definition by name.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool definition
    """
    mcp_server = getattr(request.app.state, "mcp_server", None)

    if mcp_server is None:
        # Tool definitions matching Research Paper Section 4.5
        tool_definitions = {
            "find_similar": ToolInfo(
                name="find_similar",
                description="Find similar incidents from Neo4j episodic memory (top-k similar past incidents)",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Incident title to search for"},
                        "category": {"type": "string", "description": "Incident category"},
                        "affected_services": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["title"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            "get_dependencies": ToolInfo(
                name="get_dependencies",
                description="Get service dependency graph from Neo4j for impact analysis",
                category="query",
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
            "restart_service": ToolInfo(
                name="restart_service",
                description="Restart a whitelisted Docker container (docker restart). Gated by AIOPS_ENABLE_ACTION_TOOLS and constitutional validation.",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to restart — must be on the action container whitelist (default: nextcloud)"},
                        "graceful": {"type": "boolean", "default": True, "description": "Whether to perform a graceful restart"},
                        "reason": {"type": "string", "description": "Reason for restart (recorded in the audit trail)"},
                    },
                    "required": ["service_name", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            "scale_service": ToolInfo(
                name="scale_service",
                description="Scale Docker Compose service replicas. Replica count is clamped to 0-5. Gated by AIOPS_ENABLE_ACTION_TOOLS and constitutional validation.",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to scale — must be on the action container whitelist (default: nextcloud)"},
                        "target_replicas": {"type": "integer", "minimum": 0, "maximum": 5, "description": "Target replica count (clamped to 0-5)"},
                        "reason": {"type": "string", "description": "Reason for scaling (recorded in the audit trail)"},
                    },
                    "required": ["service_name", "target_replicas", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            "analyze_logs": ToolInfo(
                name="analyze_logs",
                description="Analyze logs from Loki for patterns and anomalies",
                category="analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to analyze"},
                        "time_range_minutes": {"type": "integer", "default": 30},
                        "log_level": {"type": "string", "enum": ["all", "error", "warn", "info"]},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            "analyze_time_series_anomaly": ToolInfo(
                name="analyze_time_series_anomaly",
                description="Statistical analysis of metrics using Z-score for anomaly detection",
                category="analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string", "description": "Service to analyze"},
                        "metric_name": {"type": "string", "description": "Specific metric (optional)"},
                        "time_range_minutes": {"type": "integer", "default": 60},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            # Phase-2 tools
            "query_recent_logs": ToolInfo(
                name="query_recent_logs",
                description="Query recent log entries from Loki for a service within a time window",
                category="query",
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
            "query_metric": ToolInfo(
                name="query_metric",
                description="Query Prometheus metrics for a service over a time range",
                category="query",
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
            "list_containers": ToolInfo(
                name="list_containers",
                description="List Docker containers and their status (running, stopped, health)",
                category="query",
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
        }

        if tool_name not in tool_definitions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )
        return _apply_action_gating(tool_definitions[tool_name])

    tool = mcp_server.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    return _apply_action_gating(ToolInfo(
        name=tool.name,
        description=tool.description,
        category=tool.category.value,
        parameters=tool.parameters,
        requires_approval=tool.requires_approval,
        risk_level=tool.risk_level,
    ))


@router.post(
    "/call",
    response_model=ToolCallResponse,
    summary="Call Tool",
    description="Execute an MCP tool with the given parameters",
)
async def call_tool(
    request: Request,
    tool_call: ToolCallRequest,
) -> ToolCallResponse:
    """
    Execute a tool with REAL implementations.

    Tools requiring approval will go through Constitutional AI validation.

    Args:
        tool_call: Tool name, parameters, and context

    Returns:
        Tool execution result from actual system queries
    """
    start_time = time.time()

    # Get system components
    episode_store = getattr(request.app.state, "episode_store", None)
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    try:
        # ==================== find_similar ====================
        if tool_call.tool_name == "find_similar":
            return await _execute_find_similar(
                episode_store, tool_call.parameters, start_time
            )

        # ==================== get_dependencies ====================
        elif tool_call.tool_name == "get_dependencies":
            return await _execute_get_dependencies(
                neo4j_client, tool_call.parameters, start_time
            )

        # ==================== analyze_logs ====================
        elif tool_call.tool_name == "analyze_logs":
            return await _execute_analyze_logs(
                telemetry_collector, tool_call.parameters, start_time
            )

        # ==================== analyze_time_series_anomaly ====================
        elif tool_call.tool_name == "analyze_time_series_anomaly":
            return await _execute_analyze_time_series(
                telemetry_collector, tool_call.parameters, start_time
            )

        # ==================== restart_service / scale_service ====================
        # Action-class tools mutate real containers (docker restart / compose
        # --scale on the host socket). They MUST pass the constitutional gate —
        # the REST path used to execute them directly, bypassing the validator
        # entirely despite requires_approval=True on their metadata.
        elif tool_call.tool_name in ACTION_TOOLS:
            return await _run_action_tool(request, tool_call, start_time)

        # ==================== query_recent_logs ====================
        elif tool_call.tool_name == "query_recent_logs":
            return await _execute_query_recent_logs(
                telemetry_collector, tool_call.parameters, start_time
            )

        # ==================== query_metric ====================
        elif tool_call.tool_name == "query_metric":
            return await _execute_query_metric(
                telemetry_collector, tool_call.parameters, start_time
            )

        # ==================== list_containers ====================
        elif tool_call.tool_name == "list_containers":
            return await _execute_list_containers(
                tool_call.parameters, start_time
            )

        # ==================== analyze_time_series_anomaly ====================
        elif tool_call.tool_name == "analyze_time_series_anomaly":
            return await _execute_analyze_time_series(
                telemetry_collector, tool_call.parameters, start_time
            )

        else:
            return ToolCallResponse(
                success=False,
                data=None,
                error=f"Tool '{tool_call.tool_name}' not found",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_find_similar(
    episode_store: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Find similar incidents from Neo4j episodic memory."""
    if episode_store is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Episode store not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    from src.memory.episode_store import Episode

    # Create search episode from parameters
    search_episode = Episode(
        episode_id="search",
        incident_id="search",
        title=params.get("title", ""),
        description=params.get("description", params.get("title", "")),
        severity=params.get("severity", "info"),
        category=params.get("category", "unknown"),
        detected_at=datetime.utcnow(),
        affected_services=params.get("affected_services", []),
    )

    similar_episodes = await episode_store.find_similar_episodes(
        search_episode,
        limit=params.get("limit", 5),
        min_similarity=0.7,
    )

    # Format results
    similar_incidents = []
    for ep, similarity in similar_episodes:
        similar_incidents.append({
            "incident_id": ep.incident_id,
            "episode_id": ep.episode_id,
            "title": ep.title,
            "similarity_score": round(similarity, 3),
            "root_cause": ep.root_cause,
            "severity": ep.severity,
            "category": ep.category,
            "resolution": ep.outcome,
            "detected_at": ep.detected_at.isoformat() if ep.detected_at else None,
        })

    return ToolCallResponse(
        success=True,
        data={
            "similar_incidents": similar_incidents,
            "total_found": len(similar_incidents),
            "search_title": params.get("title", ""),
        },
        execution_time_ms=(time.time() - start_time) * 1000,
        metadata={"source": "neo4j_episodic_memory"},
    )


async def _execute_get_dependencies(
    neo4j_client: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Get service dependencies from Neo4j graph."""
    service_name = params.get("service_name")
    if not service_name:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service_name parameter required",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if neo4j_client is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Neo4j client not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    try:
        # depth arrives from the raw JSON body and is interpolated into the
        # variable-length path below (Neo4j cannot parameterize path bounds) —
        # coerce + clamp it so it can never carry injected Cypher.
        try:
            depth = int(params.get("depth", 2))
        except (TypeError, ValueError):
            depth = 2
        depth = max(1, min(depth, 5))

        async with neo4j_client.session() as session:
            # Get downstream dependencies (services this service depends on)
            downstream_result = await session.run(
                f"""
                MATCH (s:Service {{name: $name}})-[:DEPENDS_ON*1..{depth}]->(dep:Service)
                RETURN DISTINCT dep.name as name
                """,
                name=service_name,
            )
            downstream_data = await downstream_result.data()
            downstream = [r["name"] for r in downstream_data if r["name"]]

            # Get upstream dependencies (services that depend on this one)
            upstream_result = await session.run(
                f"""
                MATCH (up:Service)-[:DEPENDS_ON*1..{depth}]->(s:Service {{name: $name}})
                RETURN DISTINCT up.name as name
                """,
                name=service_name,
            )
            upstream_data = await upstream_result.data()
            upstream = [r["name"] for r in upstream_data if r["name"]]

        return ToolCallResponse(
            success=True,
            data={
                "service": service_name,
                "dependencies": {
                    "upstream": upstream,
                    "downstream": downstream,
                },
                "depth": depth,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "neo4j_graph"},
        )

    except Exception as e:
        logger.error(f"Neo4j query failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Neo4j query failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_analyze_logs(
    telemetry_collector: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Analyze logs from Loki."""
    service_name = params.get("service_name")
    if not service_name:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service_name parameter required",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if telemetry_collector is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Telemetry collector not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    try:
        duration = params.get("time_range_minutes", 30)
        end_time = datetime.utcnow()
        start_query = end_time - timedelta(minutes=duration)

        logs = await telemetry_collector.query_logs(
            service=service_name,
            start_time=start_query,
            end_time=end_time,
            limit=200,
        )

        # Analyze log patterns
        total_logs = len(logs) if logs else 0
        error_logs = [l for l in (logs or []) if l.level.lower() in ("error", "fatal", "critical")]
        warning_logs = [l for l in (logs or []) if l.level.lower() in ("warn", "warning")]

        # Find top error patterns
        error_messages = [l.message[:100] for l in error_logs]
        error_patterns = Counter(error_messages).most_common(5)

        # Sample logs
        sample_errors = []
        for log in error_logs[:5]:
            sample_errors.append({
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "level": log.level,
                "message": log.message[:200],
            })

        return ToolCallResponse(
            success=True,
            data={
                "service": service_name,
                "time_range_minutes": duration,
                "summary": {
                    "total_logs": total_logs,
                    "error_count": len(error_logs),
                    "warning_count": len(warning_logs),
                },
                "top_errors": [
                    {"pattern": pattern[:100], "count": count}
                    for pattern, count in error_patterns
                ],
                "sample_errors": sample_errors,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "loki"},
        )

    except Exception as e:
        logger.error(f"Log analysis failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Log analysis failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_analyze_time_series(
    telemetry_collector: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Analyze time series metrics for anomalies (Z-score analysis)."""
    service_name = params.get("service_name")
    metric_name = params.get("metric_name")

    if not service_name:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service_name parameter required",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if telemetry_collector is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Telemetry collector not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    try:
        duration = params.get("time_range_minutes", 60)
        end_time = datetime.utcnow()
        start_query = end_time - timedelta(minutes=duration)

        metrics = await telemetry_collector.query_metrics(
            service=service_name,
            start_time=start_query,
            end_time=end_time,
        )

        if not metrics:
            return ToolCallResponse(
                success=True,
                data={
                    "service": service_name,
                    "anomalies_detected": 0,
                    "message": "No metrics data available",
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Filter by metric name if specified
        if metric_name:
            metrics = [m for m in metrics if m.name == metric_name]

        # Group metrics by name
        metric_groups: dict[str, list[float]] = {}
        for m in metrics:
            if m.name not in metric_groups:
                metric_groups[m.name] = []
            metric_groups[m.name].append(m.value)

        # Perform Z-score analysis on each metric
        anomalies = []
        for name, values in metric_groups.items():
            if len(values) < 3:
                continue

            # Calculate mean and std
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = variance ** 0.5 if variance > 0 else 0

            if std_val > 0:
                # Find values with Z-score > 2
                for val in values:
                    z_score = (val - mean_val) / std_val
                    if abs(z_score) > 2:
                        anomalies.append({
                            "metric": name,
                            "value": round(val, 3),
                            "z_score": round(z_score, 3),
                            "mean": round(mean_val, 3),
                            "std": round(std_val, 3),
                        })

        return ToolCallResponse(
            success=True,
            data={
                "service": service_name,
                "time_range_minutes": duration,
                "metrics_analyzed": len(metric_groups),
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies[:10],  # Limit to top 10
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "prometheus", "method": "z_score"},
        )

    except Exception as e:
        logger.error(f"Time series analysis failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Time series analysis failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


@dataclass
class ActionGateDecision:
    """Outcome of the constitutional gate for an action tool call.

    `verdict` carries the serialized constitutional validation report whenever
    the validator actually ran — on refusals AND on allowed calls — so callers
    can always surface it to the user.
    """
    allowed: bool
    error: Optional[str] = None
    error_code: Optional[str] = None
    verdict: Optional[dict[str, Any]] = None


def _constitutional_verdict(report: Any) -> dict[str, Any]:
    """Serialize a ValidationReport into a JSON-safe verdict payload."""
    violations = []
    for v in getattr(report, "violations", None) or []:
        principle = getattr(v, "principle", None)
        violations.append({
            "principle_id": getattr(principle, "id", None),
            "principle_name": getattr(principle, "name", None),
            "severity": getattr(v, "severity", None),
            "reason": getattr(v, "reason", None),
        })
    authorization = getattr(report, "authorization_level", None)
    overall = getattr(report, "overall_result", None)
    return {
        "can_proceed": bool(getattr(report, "can_proceed", False)),
        "requires_approval": bool(getattr(report, "requires_approval", False)),
        "authorization_level": getattr(authorization, "value", None),
        "overall_result": getattr(overall, "value", None),
        "confidence": getattr(report, "confidence", None),
        "principles": {
            "tier1_safety_passed": bool(getattr(report, "tier1_passed", False)),
            "tier2_operational_passed": bool(getattr(report, "tier2_passed", False)),
            "tier3_learning_passed": bool(getattr(report, "tier3_passed", False)),
        },
        "violations": violations,
        "warnings": list(getattr(report, "warnings", None) or []),
        "explanation": getattr(report, "explanation", ""),
    }


def _audit_action_attempt(
    tool_name: str,
    parameters: dict[str, Any],
    outcome: str,
    error_code: Optional[str] = None,
    verdict: Optional[dict[str, Any]] = None,
) -> None:
    """Write one audit line per action-tool attempt (allowed OR refused).

    Audit failures must never break the API response — log and continue.
    """
    try:
        get_audit_logger().log_tool_invocation(
            tool_name=tool_name,
            parameters=parameters,
            actor_id="rest_tools_call",
            context={
                "outcome": outcome,
                "error_code": error_code,
                "constitutional": verdict,
            },
        )
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Audit logging failed for {tool_name}: {e}")


def _action_tool_gate(request: Request, tool_call: "ToolCallRequest") -> ActionGateDecision:
    """Constitutional gate for action-class (mutating) tools.

    Returns a structured ActionGateDecision. Layers, in order:
    1. Action tools are refused unless AIOPS_ENABLE_ACTION_TOOLS is set
       (`error_code="action_tools_disabled"`) — production default.
    2. The live ConstitutionalValidator must be available
       (`error_code="validator_unavailable"`).
    3. The target service must resolve to a whitelisted container
       (`error_code="container_not_whitelisted"`).
    4. The validator must allow the action: blocked verdicts come back as
       `validation_blocked`; verdicts needing a human come back as
       `approval_required` and are NOT executed (the human-approval execution
       flow is intentionally not wired to this REST path).
    The serialized verdict is attached whenever validation ran.
    """
    params = tool_call.parameters or {}

    if not _action_tools_enabled():
        return ActionGateDecision(
            allowed=False,
            error=(
                f"'{tool_call.tool_name}' is an action tool and is disabled: it mutates real "
                f"containers. Set {ACTION_TOOLS_ENV}=true on the backend to allow "
                "constitutionally-gated execution."
            ),
            error_code="action_tools_disabled",
        )

    validator = getattr(request.app.state, "validator", None)
    if validator is None:
        return ActionGateDecision(
            allowed=False,
            error=(
                "Constitutional validator unavailable — refusing to execute an action "
                "tool without validation."
            ),
            error_code="validator_unavailable",
        )

    container = _resolve_action_container(params.get("service_name"))
    if container is None:
        return ActionGateDecision(
            allowed=False,
            error=(
                f"Service '{params.get('service_name')}' is not on the action-tool container "
                f"whitelist ({', '.join(sorted(_allowed_action_containers()))}). Extend it via "
                f"{ACTION_CONTAINER_WHITELIST_ENV} if this is intentional."
            ),
            error_code="container_not_whitelisted",
        )

    try:
        confidence = float(params.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    caller_context = tool_call.context if isinstance(tool_call.context, dict) else {}

    # Populate the constitutional context so the Tier-1/Tier-2 principles that
    # read incident/scope/resource signals actually evaluate instead of seeing
    # empty inputs (previously P1.2/P1.3/P2.1 were inert on every live path):
    #  - active_incident: a remediation that came from the incident/approve flow
    #    is by definition acting on an active incident, so P1.2 can evaluate
    #    (it now passes for human_approved remediations and blocks unapproved ones).
    #  - action_scope: a restart/scale of one whitelisted container is a single,
    #    minimal-intervention action — declare it so P2.1 is meaningful instead
    #    of never firing.
    derived_context: dict[str, Any] = {}
    caller_source = caller_context.get("source")
    if caller_source in {"incident_remediate", "approve_to_run"}:
        derived_context["active_incident"] = True
    derived_context.setdefault("action_scope", caller_context.get("action_scope", "single"))

    context: dict[str, Any] = {
        "service": params.get("service_name"),
        "parameters": params,
        "source": "rest_tools_call",
        "target_replicas": params.get("target_replicas"),
    }
    # Layer order: gate-derived defaults < caller-supplied context < gate-owned
    # keys. Callers (e.g. agents) may supply extra validation context such as
    # telemetry_evidence/human_approved/resource_usage; the UI sends none, so
    # P2.2 keeps it at approval. The gate-owned keys above always win for the
    # service/parameters/source/target_replicas identity fields.
    context = {**derived_context, **caller_context, **context}
    report = validator.validate(
        action_id=f"tool-{tool_call.tool_name}-{int(time.time() * 1000)}",
        action_description=(
            f"{tool_call.tool_name} via POST /api/v1/tools/call "
            f"on service '{params.get('service_name')}'"
        ),
        action_type="restart" if tool_call.tool_name == "restart_service" else "scale",
        confidence=confidence,
        context=context,
    )
    verdict = _constitutional_verdict(report)

    if not report.can_proceed:
        return ActionGateDecision(
            allowed=False,
            error=(
                f"Constitutional validation blocked execution "
                f"(authorization={verdict['authorization_level']}): {report.explanation}"
            ),
            error_code="validation_blocked",
            verdict=verdict,
        )
    if report.requires_approval:
        return ActionGateDecision(
            allowed=False,
            error=(
                f"Constitutional validation refused automatic execution — human approval "
                f"required (authorization={verdict['authorization_level']}): {report.explanation}"
            ),
            error_code="approval_required",
            verdict=verdict,
        )
    return ActionGateDecision(allowed=True, verdict=verdict)


async def _run_action_tool(
    request: Request,
    tool_call: "ToolCallRequest",
    start_time: float,
) -> ToolCallResponse:
    """Gate, execute, and audit an action tool call (restart/scale)."""
    decision = _action_tool_gate(request, tool_call)
    params = tool_call.parameters or {}

    if not decision.allowed:
        _audit_action_attempt(
            tool_call.tool_name, params, outcome="refused",
            error_code=decision.error_code, verdict=decision.verdict,
        )
        metadata: dict[str, Any] = {"gated_by": ACTION_TOOLS_ENV}
        if decision.verdict is not None:
            metadata["constitutional"] = decision.verdict
        return ToolCallResponse(
            success=False,
            data=None,
            error=decision.error,
            error_code=decision.error_code,
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata=metadata,
        )

    if tool_call.tool_name == "restart_service":
        response = await _execute_restart_service(params, start_time)
    else:
        response = await _execute_scale_service(params, start_time)

    # The verdict is part of the payload on success AND failure.
    if decision.verdict is not None:
        response.metadata = {**response.metadata, "constitutional": decision.verdict}
    _audit_action_attempt(
        tool_call.tool_name, params,
        outcome="executed" if response.success else "execution_failed",
        error_code=response.error_code, verdict=decision.verdict,
    )
    return response


def _docker_restart_container(container_name: str) -> None:
    """Restart a local container via the docker SDK over the mounted socket.

    The production backend image mounts /var/run/docker.sock but ships NO
    docker CLI binary, so shelling out to ``docker restart`` fails there with
    FileNotFoundError; the SDK talks to the socket directly. timeout=10 keeps
    the CLI's default stop-grace semantics.
    """
    import docker  # type: ignore[import]

    client = docker.from_env()
    try:
        client.containers.get(container_name).restart(timeout=10)
    finally:
        client.close()


async def _execute_restart_service(
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Restart a whitelisted Docker container.

    Defense in depth: re-checks the container whitelist itself (the gate also
    checks it) so no dispatch path can restart an arbitrary container.
    """
    service_name = params.get("service_name")
    if not service_name:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service_name parameter required",
            error_code="invalid_parameters",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Remote routing: containers that live on the t3 host (default nextcloud-db)
    # cannot be reached by the local docker daemon, so dispatch their restart to
    # the t3 control agent over HTTP. nextcloud stays LOCAL by default.
    from src.remediation.executor import resolve_remediation_target

    if resolve_remediation_target(service_name) == "t3":
        from src.remediation import t3_client

        remote = await t3_client.restart_remote(service_name)
        if remote.get("success"):
            return ToolCallResponse(
                success=True,
                data={
                    "service": service_name,
                    "container": remote.get("container", service_name),
                    "action": "restart",
                    "status": "completed",
                    "graceful": params.get("graceful", True),
                    "reason": params.get("reason", "No reason provided"),
                },
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={"source": "t3"},
            )
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"t3 restart failed: {remote.get('error', 'unknown error')}",
            error_code="execution_failed",
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "t3"},
        )

    container_name = _resolve_action_container(service_name)
    if container_name is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error=(
                f"Service '{service_name}' is not on the action-tool container whitelist "
                f"({', '.join(sorted(_allowed_action_containers()))})."
            ),
            error_code="container_not_whitelisted",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    reason = params.get("reason", "No reason provided")
    graceful = params.get("graceful", True)

    try:
        # to_thread workers are not cancellable: on the 60s cap we report
        # execution_timeout but the SDK restart may still complete in the
        # background. The SDK's own stop-grace (timeout=10) is the real bound;
        # this outer cap only protects the event loop from a hung socket.
        await asyncio.wait_for(
            asyncio.to_thread(_docker_restart_container, container_name),
            timeout=60,
        )
        return ToolCallResponse(
            success=True,
            data={
                "service": service_name,
                "container": container_name,
                "action": "restart",
                "status": "completed",
                "graceful": graceful,
                "reason": reason,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "docker"},
        )
    except TimeoutError:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Restart operation timed out",
            error_code="execution_timeout",
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    except ImportError:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Docker SDK not available",
            error_code="execution_failed",
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    except Exception as e:
        logger.error(f"Service restart failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Docker restart failed: {str(e)}",
            error_code="execution_failed",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_scale_service(
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Scale a whitelisted Docker Compose service.

    Defense in depth: re-checks the container whitelist and clamps the replica
    count to [MIN_SCALE_REPLICAS, MAX_SCALE_REPLICAS] regardless of input.
    """
    import subprocess

    service_name = params.get("service_name")
    target_replicas = params.get("target_replicas")

    if not service_name:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service_name parameter required",
            error_code="invalid_parameters",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if target_replicas is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="target_replicas parameter required",
            error_code="invalid_parameters",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    container_name = _resolve_action_container(service_name)
    if container_name is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error=(
                f"Service '{service_name}' is not on the action-tool container whitelist "
                f"({', '.join(sorted(_allowed_action_containers()))})."
            ),
            error_code="container_not_whitelisted",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # bool is an int subclass — reject it explicitly, then coerce + clamp.
    if isinstance(target_replicas, bool) or not isinstance(target_replicas, (int, str)):
        target_replicas = None
    try:
        requested_replicas = int(target_replicas)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ToolCallResponse(
            success=False,
            data=None,
            error="target_replicas must be an integer",
            error_code="invalid_parameters",
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    applied_replicas = max(MIN_SCALE_REPLICAS, min(requested_replicas, MAX_SCALE_REPLICAS))

    reason = params.get("reason", "No reason provided")

    try:
        # For Docker Compose scaling
        cmd = ["docker", "compose", "up", "-d", "--scale", f"{container_name}={applied_replicas}"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return ToolCallResponse(
                success=True,
                data={
                    "service": service_name,
                    "container": container_name,
                    "action": "scale",
                    "target_replicas": applied_replicas,
                    "requested_replicas": requested_replicas,
                    "clamped": applied_replicas != requested_replicas,
                    "status": "completed",
                    "reason": reason,
                },
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={"source": "docker_compose"},
            )
        else:
            return ToolCallResponse(
                success=False,
                data=None,
                error=f"Scale operation failed: {result.stderr}",
                error_code="execution_failed",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    except subprocess.TimeoutExpired:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Scale operation timed out",
            error_code="execution_timeout",
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    except Exception as e:
        logger.error(f"Service scale failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Service scale failed: {str(e)}",
            error_code="execution_failed",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_query_recent_logs(
    telemetry_collector: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Query recent logs from Loki via TelemetryCollector.query_logs."""
    service = params.get("service", "")
    if not service:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service parameter required",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if telemetry_collector is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Telemetry collector not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    try:
        duration = params.get("time_range_minutes", 15)
        limit = params.get("limit", 50)
        query_override = params.get("query")

        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(minutes=duration)

        logs = await telemetry_collector.query_logs(
            service=service,
            start_time=start_dt,
            end_time=end_dt,
            query=query_override,
            limit=limit,
        )

        entries = []
        for log in (logs or []):
            entries.append({
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "level": log.level,
                "message": log.message[:300],
                "service": log.service,
            })

        return ToolCallResponse(
            success=True,
            data={
                "service": service,
                "time_range_minutes": duration,
                "total_entries": len(entries),
                "entries": entries,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "loki"},
        )

    except Exception as e:
        logger.error(f"query_recent_logs failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Log query failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_query_metric(
    telemetry_collector: Any,
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """Query Prometheus metrics via TelemetryCollector.query_metrics."""
    service = params.get("service", "")
    if not service:
        return ToolCallResponse(
            success=False,
            data=None,
            error="service parameter required",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    if telemetry_collector is None:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Telemetry collector not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    try:
        duration = params.get("time_range_minutes", 30)
        metrics_list = params.get("metrics") or None

        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(minutes=duration)

        metric_points = await telemetry_collector.query_metrics(
            service=service,
            start_time=start_dt,
            end_time=end_dt,
            metrics=metrics_list,
        )

        points = []
        for mp in (metric_points or []):
            points.append({
                "timestamp": mp.timestamp.isoformat() if mp.timestamp else None,
                "name": mp.name,
                "value": mp.value,
            })

        return ToolCallResponse(
            success=True,
            data={
                "service": service,
                "time_range_minutes": duration,
                "total_points": len(points),
                "metrics": points,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "prometheus"},
        )

    except Exception as e:
        logger.error(f"query_metric failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Metric query failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def _execute_list_containers(
    params: dict,
    start_time: float,
) -> ToolCallResponse:
    """List Docker containers (read-only). Mirrors logic from infrastructure route."""
    include_all = params.get("all_containers", False)
    name_filter = params.get("name_filter", "")

    try:
        import docker  # type: ignore[import]

        client = docker.from_env()
        raw = client.containers.list(all=include_all)

        containers = []
        for c in raw:
            name: str = c.name
            if name_filter and name_filter.lower() not in name.lower():
                continue
            state = c.attrs.get("State", {})
            health_state = state.get("Health", {})
            health = health_state.get("Status") if health_state else None
            image = c.image.tags[0] if c.image.tags else str(c.image.id)[:12]
            containers.append({
                "name": name,
                "status": c.status,
                "health": health,
                "image": image,
            })

        client.close()

        return ToolCallResponse(
            success=True,
            data={
                "total": len(containers),
                "containers": containers,
                "include_stopped": include_all,
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            metadata={"source": "docker"},
        )

    except ImportError:
        return ToolCallResponse(
            success=False,
            data=None,
            error="Docker SDK not available",
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    except Exception as e:
        logger.error(f"list_containers failed: {e}")
        return ToolCallResponse(
            success=False,
            data=None,
            error=f"Container list failed: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


async def execute_tool_call(
    request: Any,
    tool_name: str,
    parameters: dict[str, Any],
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Programmatic tool execution for internal use (e.g., from chat.py).

    Args:
        request: FastAPI request with app state
        tool_name: Name of the tool to execute
        parameters: Tool parameters
        context: Optional validation context forwarded to the constitutional
            gate for action tools (e.g. ``telemetry_evidence`` for an
            evidence-backed, human-approved or high-confidence remediation).

    Returns:
        Dictionary with tool results
    """
    start_time = time.time()

    # Get system components from request
    episode_store = getattr(request.app.state, "episode_store", None)
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    try:
        if tool_name == "find_similar":
            result = await _execute_find_similar(episode_store, parameters, start_time)
        elif tool_name == "get_dependencies":
            result = await _execute_get_dependencies(neo4j_client, parameters, start_time)
        elif tool_name == "analyze_logs":
            result = await _execute_analyze_logs(telemetry_collector, parameters, start_time)
        elif tool_name == "analyze_time_series_anomaly":
            result = await _execute_analyze_time_series(telemetry_collector, parameters, start_time)
        elif tool_name in ACTION_TOOLS:
            # The programmatic path used to dispatch restart/scale straight to
            # the executors, bypassing the constitutional gate entirely. Route
            # it through the same gate + audit pipeline as the REST endpoint.
            result = await _run_action_tool(
                request,
                ToolCallRequest(tool_name=tool_name, parameters=parameters, context=context),
                start_time,
            )
        elif tool_name == "query_recent_logs":
            result = await _execute_query_recent_logs(telemetry_collector, parameters, start_time)
        elif tool_name == "query_metric":
            result = await _execute_query_metric(telemetry_collector, parameters, start_time)
        elif tool_name == "list_containers":
            result = await _execute_list_containers(parameters, start_time)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Convert ToolCallResponse to dict. Carry metadata through so callers
        # (chat.py) can surface the constitutional verdict in metadata.constitutional.
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "error_code": result.error_code,
            "execution_time_ms": result.execution_time_ms,
            "metadata": getattr(result, "metadata", None),
        }

    except Exception as e:
        logger.error(f"execute_tool_call error for {tool_name}: {e}")
        return {"success": False, "error": str(e)}


__all__ = ["router", "execute_tool_call"]
