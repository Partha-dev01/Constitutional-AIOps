"""
Constitutional AIOps - MCP Action Server

Model Context Protocol server that provides tools for infrastructure management.
All tools are validated through Constitutional AI before execution.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


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
            description="Restart a service or specific instance. Requires Constitutional AI approval for production services.",
            category=ToolCategory.ACTION,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to restart"
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
                        "description": "Timeout for restart operation"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for restart (required for audit)"
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
            description="Scale service replicas up or down. Requires Constitutional AI approval.",
            category=ToolCategory.ACTION,
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to scale"
                    },
                    "target_replicas": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Target number of replicas"
                    },
                    "current_replicas": {
                        "type": "integer",
                        "description": "Current number of replicas (for validation)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for scaling (required for audit)"
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

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools with their definitions."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "parameters": tool.parameters,
                "requires_approval": tool.requires_approval,
                "risk_level": tool.risk_level,
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
            # Return mock data for development
            return ToolResult(
                success=True,
                data={
                    "similar_incidents": [
                        {
                            "incident_id": "INC-2025-0042",
                            "title": "Database connection timeout",
                            "similarity_score": 0.87,
                            "root_cause": "Connection pool exhaustion",
                            "resolution": "Increased pool size from 10 to 50",
                            "resolution_time_minutes": 15,
                        },
                        {
                            "incident_id": "INC-2025-0038",
                            "title": "API latency spike",
                            "similarity_score": 0.72,
                            "root_cause": "Database slow queries",
                            "resolution": "Added missing index on user_id column",
                            "resolution_time_minutes": 25,
                        },
                    ],
                    "total_searched": 150,
                    "query_time_ms": 45.2,
                },
                metadata={"source": "mock"},
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
            # Return mock data for development
            mock_deps = {
                "api-gateway": {
                    "upstream": ["load-balancer", "cdn"],
                    "downstream": ["user-service", "order-service", "payment-service"],
                },
                "user-service": {
                    "upstream": ["api-gateway"],
                    "downstream": ["postgres-primary", "redis-cache"],
                },
                "order-service": {
                    "upstream": ["api-gateway"],
                    "downstream": ["postgres-primary", "payment-service", "inventory-service"],
                },
                "payment-service": {
                    "upstream": ["api-gateway", "order-service"],
                    "downstream": ["stripe-gateway", "postgres-primary"],
                },
            }

            service_deps = mock_deps.get(service_name, {
                "upstream": [],
                "downstream": ["database", "cache"],
            })

            result_deps = {}
            if direction in ["upstream", "both"]:
                result_deps["upstream"] = service_deps.get("upstream", [])
            if direction in ["downstream", "both"]:
                result_deps["downstream"] = service_deps.get("downstream", [])

            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "dependencies": result_deps,
                    "depth": depth,
                    "total_dependencies": sum(len(v) for v in result_deps.values()),
                },
                metadata={"source": "mock"},
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
            # Return mock analysis
            return ToolResult(
                success=True,
                data={
                    "service": service_name,
                    "time_range_minutes": time_range,
                    "summary": {
                        "total_logs": 1542,
                        "error_count": 87,
                        "warning_count": 234,
                        "info_count": 1221,
                    },
                    "top_errors": [
                        {
                            "pattern": "Connection refused to database:5432",
                            "count": 45,
                            "first_seen": "2025-12-15T10:23:00Z",
                            "last_seen": "2025-12-15T10:45:00Z",
                        },
                        {
                            "pattern": "Timeout waiting for response",
                            "count": 28,
                            "first_seen": "2025-12-15T10:25:00Z",
                            "last_seen": "2025-12-15T10:48:00Z",
                        },
                        {
                            "pattern": "Out of memory error",
                            "count": 14,
                            "first_seen": "2025-12-15T10:30:00Z",
                            "last_seen": "2025-12-15T10:42:00Z",
                        },
                    ],
                    "anomalies": [
                        {
                            "type": "spike",
                            "metric": "error_rate",
                            "timestamp": "2025-12-15T10:35:00Z",
                            "value": 15.5,
                            "baseline": 2.1,
                            "severity": "high",
                        },
                    ],
                    "patterns": [
                        {
                            "name": "cascading_failure",
                            "confidence": 0.85,
                            "description": "Database connection errors leading to service timeouts",
                        },
                    ] if include_patterns else [],
                },
                metadata={"source": "mock"},
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
