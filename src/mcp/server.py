"""
Constitutional AIOps - MCP Action Server

Model Context Protocol server that provides tools for infrastructure management.
All tools are validated through Constitutional AI before execution.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from enum import Enum

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
        """Register all available tools."""

        # 1. Find Similar Incidents
        self._tools["find_similar"] = ToolDefinition(
            name="find_similar",
            description="Find similar incidents from episodic memory based on symptoms, affected services, and error patterns",
            category=ToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "Current incident ID to find similar incidents for"
                    },
                    "title": {
                        "type": "string",
                        "description": "Incident title or description"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["performance", "error", "availability", "resource", "security", "configuration"],
                        "description": "Incident category"
                    },
                    "affected_services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of affected service names"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Maximum number of similar incidents to return"
                    }
                },
                "required": ["title"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._find_similar
        )

        # 2. Get Dependencies
        self._tools["get_dependencies"] = ToolDefinition(
            name="get_dependencies",
            description="Get service dependency graph showing upstream and downstream services",
            category=ToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to get dependencies for"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["upstream", "downstream", "both"],
                        "default": "both",
                        "description": "Direction of dependencies to retrieve"
                    },
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Depth of dependency traversal"
                    }
                },
                "required": ["service_name"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._get_dependencies
        )

        # 3. Restart Service
        self._tools["restart_service"] = ToolDefinition(
            name="restart_service",
            description="Restart a whitelisted service container. Gated by AIOPS_ENABLE_ACTION_TOOLS; every call is validated against the constitutional principles first.",
            category=ToolCategory.ACTION,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to restart — must be on the action container whitelist (default: nextcloud)"
                    },
                    "instance_id": {
                        "type": "string",
                        "description": "Specific instance ID (optional, restarts all if not provided)"
                    },
                    "graceful": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to perform graceful restart"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "default": 60,
                        "minimum": 1,
                        "maximum": 600,
                        "description": "Timeout for restart operation in seconds"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for restart (recorded in the audit trail)"
                    }
                },
                "required": ["service_name", "reason"]
            },
            requires_approval=True,
            risk_level="medium",
            handler=self._restart_service
        )

        # 4. Scale Service
        self._tools["scale_service"] = ToolDefinition(
            name="scale_service",
            description="Scale service replicas up or down (replica count clamped to 0-5). Gated by AIOPS_ENABLE_ACTION_TOOLS; every call is validated against the constitutional principles first.",
            category=ToolCategory.ACTION,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to scale — must be on the action container whitelist (default: nextcloud)"
                    },
                    "target_replicas": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 5,
                        "description": "Target number of replicas (clamped to 0-5 by the executor)"
                    },
                    "current_replicas": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Current number of replicas (for validation)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for scaling (recorded in the audit trail)"
                    }
                },
                "required": ["service_name", "target_replicas", "reason"]
            },
            requires_approval=True,
            risk_level="medium",
            handler=self._scale_service
        )

        # 5. Analyze Logs
        self._tools["analyze_logs"] = ToolDefinition(
            name="analyze_logs",
            description="Analyze logs for a service to identify patterns, anomalies, and error clusters",
            category=ToolCategory.ANALYSIS,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to analyze logs for"
                    },
                    "time_range_minutes": {
                        "type": "integer",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 1440,
                        "description": "Time range in minutes to analyze"
                    },
                    "log_level": {
                        "type": "string",
                        "enum": ["all", "error", "warn", "info"],
                        "default": "error",
                        "description": "Minimum log level to analyze"
                    },
                    "include_patterns": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to include pattern analysis"
                    }
                },
                "required": ["service_name"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._analyze_logs
        )

        # 6. Query Recent Logs — wraps TelemetryCollector.query_logs
        self._tools["query_recent_logs"] = ToolDefinition(
            name="query_recent_logs",
            description="Query recent log entries from Loki for a service within a time window",
            category=ToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name to query logs for (use 'all' for all services)"
                    },
                    "time_range_minutes": {
                        "type": "integer",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 1440,
                        "description": "How many minutes back to query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500,
                        "description": "Maximum number of log entries to return"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional LogQL query override (e.g. '{job=\"containerlogs\"} |= \"error\"')"
                    }
                },
                "required": ["service"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._query_recent_logs
        )

        # 7. Query Metric — wraps TelemetryCollector.query_metrics
        self._tools["query_metric"] = ToolDefinition(
            name="query_metric",
            description="Query Prometheus metrics for a service over a time range",
            category=ToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name to query metrics for"
                    },
                    "time_range_minutes": {
                        "type": "integer",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 1440,
                        "description": "Time range in minutes to query"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific PromQL metric names/queries to fetch (defaults to summary metrics)"
                    }
                },
                "required": ["service"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._query_metric
        )

        # 8. List Containers — read-only Docker container list
        self._tools["list_containers"] = ToolDefinition(
            name="list_containers",
            description="List Docker containers and their status (running, stopped, health)",
            category=ToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {
                    "all_containers": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include stopped containers (default: running only)"
                    },
                    "name_filter": {
                        "type": "string",
                        "description": "Optional substring filter on container name"
                    }
                },
                "required": []
            },
            requires_approval=False,
            risk_level="low",
            handler=self._list_containers
        )

        # 9. Analyze Time Series Anomaly — statistical Z-score analysis
        self._tools["analyze_time_series_anomaly"] = ToolDefinition(
            name="analyze_time_series_anomaly",
            description="Statistical Z-score anomaly detection on Prometheus metric time series for a service",
            category=ToolCategory.ANALYSIS,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Service to analyze metrics for"
                    },
                    "metric_name": {
                        "type": "string",
                        "description": "Specific PromQL metric name to analyze (optional; defaults to all summary metrics)"
                    },
                    "time_range_minutes": {
                        "type": "integer",
                        "default": 60,
                        "minimum": 1,
                        "maximum": 1440,
                        "description": "Time range in minutes for the analysis window"
                    }
                },
                "required": ["service_name"]
            },
            requires_approval=False,
            risk_level="low",
            handler=self._analyze_time_series_anomaly
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
        """Restart a service (mock implementation)."""
        service_name = params.get("service_name", "")
        instance_id = params.get("instance_id")
        graceful = params.get("graceful", True)
        timeout = params.get("timeout_seconds", 60)
        reason = params.get("reason", "No reason provided")

        # Mock implementation - in production, this would call Kubernetes API
        logger.info(f"MOCK: Restarting service {service_name} (instance: {instance_id}, graceful: {graceful})")

        # Simulate restart time
        await asyncio.sleep(0.5)

        return ToolResult(
            success=True,
            data={
                "service": service_name,
                "instance_id": instance_id or "all",
                "action": "restart",
                "graceful": graceful,
                "status": "completed",
                "message": f"Service {service_name} restart initiated",
                "restart_time": datetime.utcnow().isoformat(),
            },
            metadata={
                "reason": reason,
                "timeout": timeout,
                "mock": True,
            },
        )

    async def _scale_service(
        self,
        params: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> ToolResult:
        """Scale a service (mock implementation)."""
        service_name = params.get("service_name", "")
        target_replicas = params.get("target_replicas", 1)
        current_replicas = params.get("current_replicas", 1)
        reason = params.get("reason", "No reason provided")

        # Validate scaling limits
        if target_replicas > 50:
            return ToolResult(
                success=False,
                data=None,
                error="Cannot scale beyond 50 replicas without manual approval",
            )

        if target_replicas == 0:
            return ToolResult(
                success=False,
                data=None,
                error="Cannot scale to 0 replicas - use service disable instead",
            )

        # Mock implementation
        logger.info(f"MOCK: Scaling {service_name} from {current_replicas} to {target_replicas}")

        await asyncio.sleep(0.3)

        scale_direction = "up" if target_replicas > current_replicas else "down"

        return ToolResult(
            success=True,
            data={
                "service": service_name,
                "action": f"scale_{scale_direction}",
                "previous_replicas": current_replicas,
                "target_replicas": target_replicas,
                "status": "completed",
                "message": f"Service {service_name} scaled from {current_replicas} to {target_replicas}",
                "scale_time": datetime.utcnow().isoformat(),
            },
            metadata={
                "reason": reason,
                "mock": True,
            },
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
