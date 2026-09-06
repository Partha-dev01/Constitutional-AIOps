"""
Constitutional AIOps - MCP Action Server

Model Context Protocol server that provides tools for infrastructure management.
All tools are validated through Constitutional AI before execution.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from enum import Enum

from src.tools.registry import TOOLS

logger = logging.getLogger(__name__)

# Action-class tools (restart/scale) are gated off unless this env var is set.
# Mirrors the REST gate in src/api/routes/tools.py.
ACTION_TOOLS_ENV = "AIOPS_ENABLE_ACTION_TOOLS"


def _action_tools_enabled() -> bool:
    """True when the operator has explicitly enabled action tools via env."""
    return os.getenv(ACTION_TOOLS_ENV, "").lower() in ("1", "true", "yes")


class ToolCategory(str, Enum):
    """Tool categories for organization."""
    QUERY = "query"
    ACTION = "action"
    ANALYSIS = "analysis"


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    category: ToolCategory
    parameters: dict[str, Any]
    requires_approval: bool = False
    risk_level: str = "low"  # low, medium, high
    handler: Optional[Callable] = None


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPActionServer:
    """
    MCP Action Server for Constitutional AIOps.

    Provides 5 core tools:
    1. find_similar - Find similar incidents from episodic memory
    2. get_dependencies - Get service dependency graph
    3. restart_service - Restart a service (requires approval for production)
    4. scale_service - Scale service replicas
    5. analyze_logs - Analyze logs for patterns and anomalies
    """

    def __init__(
        self,
        episode_store=None,
        neo4j_client=None,
        telemetry_collector=None,
        validator=None,
    ):
        """
        Initialize MCP Action Server.

        Args:
            episode_store: Episode store for similarity search
            neo4j_client: Neo4j client for graph queries
            telemetry_collector: Telemetry collector for log analysis
            validator: Constitutional AI validator
        """
        self.episode_store = episode_store
        self.neo4j_client = neo4j_client
        self.telemetry_collector = telemetry_collector
        self.validator = validator

        # Register tools
        self._tools: dict[str, ToolDefinition] = {}
        self._register_tools()

        logger.info(f"MCPActionServer initialized with {len(self._tools)} tools")

    def _register_tools(self):
        """Register all available tools from the shared registry.

        The tool catalogue (names, descriptions, JSON-schemas, gating metadata)
        lives in ``src/tools/registry.py``. Here each registry entry is bound to
        its local async handler; adding or editing a tool happens in the registry,
        not in this file.
        """
        handlers: dict[str, Callable] = {
            "find_similar": self._find_similar,
            "get_dependencies": self._get_dependencies,
            "restart_service": self._restart_service,
            "scale_service": self._scale_service,
            "analyze_logs": self._analyze_logs,
            "query_recent_logs": self._query_recent_logs,
            "query_metric": self._query_metric,
            "list_containers": self._list_containers,
            "analyze_time_series_anomaly": self._analyze_time_series_anomaly,
        }
        for meta in TOOLS:
            self._tools[meta.name] = ToolDefinition(
                name=meta.name,
                description=meta.description,
                category=ToolCategory(meta.category),
                parameters=meta.parameters,
                requires_approval=meta.requires_approval,
                risk_level=meta.risk_level,
                handler=handlers[meta.name],
            )

    def _tool_enabled(self, tool: ToolDefinition) -> bool:
        """Whether the tool is currently callable: read-only tools always are;
        action-class tools require the AIOPS_ENABLE_ACTION_TOOLS env gate."""
        if tool.category is not ToolCategory.ACTION:
            return True
        return _action_tools_enabled()

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools with their definitions.

        Includes per-tool gating metadata (`enabled`, `gated_by`) so clients
        (frontend) can derive action-tool availability from the listing
        instead of hardcoding it.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "parameters": tool.parameters,
                "requires_approval": tool.requires_approval,
                "risk_level": tool.risk_level,
                "enabled": self._tool_enabled(tool),
                "gated_by": ACTION_TOOLS_ENV if tool.category is ToolCategory.ACTION else None,
            }
            for tool in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._tools.get(name)

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Additional context (incident_id, user, etc.)

        Returns:
            ToolResult with execution outcome
        """
        import time
        start_time = time.perf_counter()

        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found",
            )

        # Action-class tools are gated off unless explicitly enabled — same
        # structured refusal contract as the REST path in routes/tools.py.
        if not self._tool_enabled(tool):
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"'{tool_name}' is an action tool and is disabled: it mutates real "
                    f"containers. Set {ACTION_TOOLS_ENV}=true to allow "
                    "constitutionally-gated execution."
                ),
                metadata={"error_code": "action_tools_disabled", "gated_by": ACTION_TOOLS_ENV},
            )

        # Validate through Constitutional AI if required
        if tool.requires_approval and self.validator:
            validation_context = {
                "tool_name": tool_name,
                "parameters": parameters,
                "risk_level": tool.risk_level,
                **(context or {}),
            }

            # Check if action is allowed
            report = self.validator.validate(
                action_id=f"tool-{tool_name}-{datetime.utcnow().timestamp()}",
                action_description=f"Execute {tool_name}: {parameters.get('reason', 'No reason provided')}",
                action_type=tool_name,
                confidence=context.get("confidence", 0.8) if context else 0.8,
                context=validation_context,
            )

            if not report.can_proceed and not report.requires_approval:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Constitutional AI blocked: {report.explanation}",
                    metadata={"validation": report.__dict__},
                )

        # Execute the tool
        try:
            if tool.handler:
                result = await tool.handler(parameters, context)
            else:
                result = ToolResult(
                    success=False,
                    data=None,
                    error=f"Tool '{tool_name}' has no handler",
                )
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            result = ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

        result.execution_time_ms = (time.perf_counter() - start_time) * 1000
        return result

    # Tool Handlers

    async def _find_similar(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Find similar incidents from episodic memory."""
        title = params.get("title", "")
        category = params.get("category", "unknown")
        affected_services = params.get("affected_services", [])
        limit = params.get("limit", 5)

        if not self.episode_store:
            # Production: no silent mock fallback — surface the missing dependency.
            return ToolResult(
                success=False,
                data=None,
                error="Episode store unavailable: similarity search requires a connected episode store",
            )

        try:
            from src.memory.episode_store import Episode

            # Create query episode
            query_episode = Episode(
                episode_id="query",
                incident_id=params.get("incident_id", "query"),
                title=title,
                description=title,
                severity="medium",
                category=category,
                detected_at=datetime.utcnow(),
                affected_services=affected_services,
            )

            similar = await self.episode_store.find_similar_episodes(
                query_episode,
                limit=limit,
                min_similarity=0.3,
            )

            results = []
            for episode, score in similar:
                results.append({
                    "incident_id": episode.incident_id,
                    "title": episode.title,
                    "similarity_score": round(score, 3),
                    "root_cause": episode.root_cause,
                    "resolution": episode.successful_actions[0] if episode.successful_actions else None,
                    "resolution_time_minutes": episode.resolution_time_minutes,
                })

            return ToolResult(
                success=True,
                data={
                    "similar_incidents": results,
                    "total_searched": len(self.episode_store._memory_store),
                },
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _get_dependencies(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Get service dependency graph."""
        service_name = params.get("service_name", "")
        direction = params.get("direction", "both")
        depth = params.get("depth", 2)

        if not self.neo4j_client:
            # Production: no silent mock fallback — surface the missing dependency.
            return ToolResult(
                success=False,
                data=None,
                error="Neo4j client unavailable: dependency lookup requires a connected graph store",
            )

        try:
            deps = await self.neo4j_client.get_service_dependencies(
                service_name,
                depth=depth,
            )

            # Organize by direction
            upstream = [d for d in deps if d.get("direction") == "upstream"]
            downstream = [d for d in deps if d.get("direction") == "downstream"]

            result_deps = {}
            if direction in ["upstream", "both"]:
                result_deps["upstream"] = [d["name"] for d in upstream]
            if direction in ["downstream", "both"]:
                result_deps["downstream"] = [d["name"] for d in downstream]

            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "dependencies": result_deps,
                    "depth": depth,
                    "total_dependencies": len(deps),
                },
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _restart_service(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Restart a whitelisted container via the shared real executor.

        Delegates to the same executor as the REST path (container whitelist,
        t3 remote routing, docker restart) so the MCP protocol path can no
        longer fake success. The ``AIOPS_ENABLE_ACTION_TOOLS`` gate and the
        constitutional validation already ran in ``execute_tool``.
        """
        import time

        from src.api.routes.tools import _execute_restart_service

        response = await _execute_restart_service(dict(params), time.time())
        metadata = dict(response.metadata or {})
        if response.error_code:
            metadata["error_code"] = response.error_code
        return ToolResult(
            success=response.success,
            data=response.data,
            error=response.error,
            metadata=metadata,
        )

    async def _scale_service(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Scale a whitelisted compose service via the shared real executor.

        Delegates to the REST path's executor (whitelist + replica clamp 0-5 +
        docker compose scale) instead of the old fake-success mock. Gating and
        validation already ran in ``execute_tool``.
        """
        import time

        from src.api.routes.tools import _execute_scale_service

        response = await _execute_scale_service(dict(params), time.time())
        metadata = dict(response.metadata or {})
        if response.error_code:
            metadata["error_code"] = response.error_code
        return ToolResult(
            success=response.success,
            data=response.data,
            error=response.error,
            metadata=metadata,
        )

    # ------------------------------------------------------------------ #
    # Phase-2 READ-ONLY handlers (appended; existing handlers untouched)  #
    # ------------------------------------------------------------------ #

    async def _query_recent_logs(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Query recent logs via TelemetryCollector.query_logs."""
        service = params.get("service", "")
        time_range = params.get("time_range_minutes", 15)
        limit = params.get("limit", 50)
        query_override = params.get("query")

        if not self.telemetry_collector:
            return ToolResult(
                success=False,
                data=None,
                error="Telemetry collector unavailable: log query requires a connected telemetry collector",
            )

        try:
            from datetime import timedelta

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range)

            logs = await self.telemetry_collector.query_logs(
                service=service,
                start_time=start_time,
                end_time=end_time,
                query=query_override,
                limit=limit,
            )

            entries = []
            for log in logs:
                entries.append({
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "level": log.level,
                    "message": log.message[:300],
                    "service": log.service,
                })

            return ToolResult(
                success=True,
                data={
                    "service": service,
                    "time_range_minutes": time_range,
                    "total_entries": len(entries),
                    "entries": entries,
                },
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _query_metric(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Query Prometheus metrics via TelemetryCollector.query_metrics."""
        service = params.get("service", "")
        time_range = params.get("time_range_minutes", 30)
        metrics_list: Optional[list[str]] = params.get("metrics") or None

        if not self.telemetry_collector:
            return ToolResult(
                success=False,
                data=None,
                error="Telemetry collector unavailable: metrics query requires a connected telemetry collector",
            )

        try:
            from datetime import timedelta

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range)

            metric_points = await self.telemetry_collector.query_metrics(
                service=service,
                start_time=start_time,
                end_time=end_time,
                metrics=metrics_list,
            )

            points = []
            for mp in metric_points:
                points.append({
                    "timestamp": mp.timestamp.isoformat() if mp.timestamp else None,
                    "name": mp.name,
                    "value": mp.value,
                })

            return ToolResult(
                success=True,
                data={
                    "service": service,
                    "time_range_minutes": time_range,
                    "total_points": len(points),
                    "metrics": points,
                },
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _list_containers(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """List Docker containers (read-only). Reuses Docker SDK logic from infrastructure route."""
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

            return ToolResult(
                success=True,
                data={
                    "total": len(containers),
                    "containers": containers,
                    "include_stopped": include_all,
                },
            )

        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="Docker SDK not available",
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _analyze_time_series_anomaly(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Z-score anomaly detection on metric time series via TelemetryCollector.query_metrics."""
        service_name = params.get("service_name", "")
        metric_name: Optional[str] = params.get("metric_name")
        time_range = params.get("time_range_minutes", 60)

        if not self.telemetry_collector:
            return ToolResult(
                success=False,
                data=None,
                error="Telemetry collector unavailable: anomaly detection requires a connected telemetry collector",
            )

        try:
            from datetime import timedelta

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range)

            metrics_filter = [metric_name] if metric_name else None
            metric_points = await self.telemetry_collector.query_metrics(
                service=service_name,
                start_time=start_time,
                end_time=end_time,
                metrics=metrics_filter,
            )

            if not metric_points:
                return ToolResult(
                    success=True,
                    data={
                        "service": service_name,
                        "anomalies_detected": 0,
                        "message": "No metrics data available for anomaly analysis",
                    },
                )

            # Group by metric name
            groups: dict[str, list[float]] = {}
            for mp in metric_points:
                groups.setdefault(mp.name, []).append(mp.value)

            anomalies = []
            for name, values in groups.items():
                if len(values) < 3:
                    continue
                mean_val = sum(values) / len(values)
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                std_val = variance ** 0.5 if variance > 0 else 0
                if std_val > 0:
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

            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "time_range_minutes": time_range,
                    "metrics_analyzed": len(groups),
                    "anomalies_detected": len(anomalies),
                    "anomalies": anomalies[:10],
                },
                metadata={"method": "z_score"},
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # ---- pre-existing _analyze_logs (unchanged below) ---- #

    async def _analyze_logs(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Analyze logs for patterns and anomalies."""
        service_name = params.get("service_name", "")
        time_range = params.get("time_range_minutes", 30)
        log_level = params.get("log_level", "error")
        include_patterns = params.get("include_patterns", True)

        if not self.telemetry_collector:
            # Production: no silent mock fallback — surface the missing dependency
            # like the sibling handlers (A5). Fabricated data must never reach the UI.
            return ToolResult(
                success=False,
                data=None,
                error="Telemetry collector unavailable: log analysis requires a connected telemetry collector",
            )

        try:
            from datetime import timedelta

            # Collect telemetry window
            window = await self.telemetry_collector.collect_window(
                service=service_name,
                duration=timedelta(minutes=time_range),
            )

            # Analyze logs
            error_count = sum(1 for log in window.logs if log.level == "ERROR")
            warning_count = sum(1 for log in window.logs if log.level in ["WARN", "WARNING"])
            info_count = len(window.logs) - error_count - warning_count

            # Extract error patterns
            error_patterns: dict[str, dict] = {}
            for log in window.logs:
                if log.level == "ERROR":
                    # Simple pattern extraction
                    pattern = log.message[:100]
                    if pattern not in error_patterns:
                        error_patterns[pattern] = {
                            "pattern": pattern,
                            "count": 0,
                            "first_seen": log.timestamp.isoformat(),
                            "last_seen": log.timestamp.isoformat(),
                        }
                    error_patterns[pattern]["count"] += 1
                    error_patterns[pattern]["last_seen"] = log.timestamp.isoformat()

            top_errors = sorted(
                error_patterns.values(),
                key=lambda x: x["count"],
                reverse=True,
            )[:10]

            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "time_range_minutes": time_range,
                    "summary": {
                        "total_logs": len(window.logs),
                        "error_count": error_count,
                        "warning_count": warning_count,
                        "info_count": info_count,
                    },
                    "top_errors": top_errors,
                    "anomalies": [],
                    "patterns": [],
                },
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


# MCP Protocol handlers

async def handle_list_tools(server: MCPActionServer) -> dict:
    """Handle MCP list_tools request."""
    return {
        "tools": server.list_tools()
    }


async def handle_call_tool(
    server: MCPActionServer,
    tool_name: str,
    arguments: dict[str, Any],
    context: Optional[dict[str, Any]] = None,
) -> dict:
    """Handle MCP call_tool request."""
    result = await server.execute_tool(tool_name, arguments, context)

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result.data, indent=2) if result.success else result.error,
            }
        ],
        "isError": not result.success,
        "metadata": {
            "execution_time_ms": result.execution_time_ms,
            **result.metadata,
        },
    }


__all__ = [
    "MCPActionServer",
    "ToolDefinition",
    "ToolResult",
    "ToolCategory",
    "handle_list_tools",
    "handle_call_tool",
]
