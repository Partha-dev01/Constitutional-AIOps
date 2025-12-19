"""
Constitutional AIOps - Tools API Routes

Exposes MCP tools through REST API for frontend and external integrations.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


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


class ToolListResponse(BaseModel):
    """Response listing all tools."""
    tools: list[ToolInfo]
    total: int


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
        # Return default tool list for development
        default_tools = [
            ToolInfo(
                name="find_similar",
                description="Find similar incidents from episodic memory",
                category="query",
                parameters={"type": "object", "properties": {}},
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="get_dependencies",
                description="Get service dependency graph",
                category="query",
                parameters={"type": "object", "properties": {}},
                requires_approval=False,
                risk_level="low",
            ),
            ToolInfo(
                name="restart_service",
                description="Restart a service",
                category="action",
                parameters={"type": "object", "properties": {}},
                requires_approval=True,
                risk_level="medium",
            ),
            ToolInfo(
                name="scale_service",
                description="Scale service replicas",
                category="action",
                parameters={"type": "object", "properties": {}},
                requires_approval=True,
                risk_level="medium",
            ),
            ToolInfo(
                name="analyze_logs",
                description="Analyze logs for patterns",
                category="analysis",
                parameters={"type": "object", "properties": {}},
                requires_approval=False,
                risk_level="low",
            ),
        ]
        return ToolListResponse(tools=default_tools, total=len(default_tools))

    tools = mcp_server.list_tools()
    return ToolListResponse(
        tools=[ToolInfo(**t) for t in tools],
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
        # Mock response
        mock_tools = {
            "find_similar": ToolInfo(
                name="find_similar",
                description="Find similar incidents from episodic memory based on symptoms",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "category": {"type": "string"},
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
                description="Get service dependency graph",
                category="query",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["upstream", "downstream", "both"]},
                        "depth": {"type": "integer", "default": 2},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
            "restart_service": ToolInfo(
                name="restart_service",
                description="Restart a service or instance",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string"},
                        "instance_id": {"type": "string"},
                        "graceful": {"type": "boolean", "default": True},
                        "reason": {"type": "string"},
                    },
                    "required": ["service_name", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            "scale_service": ToolInfo(
                name="scale_service",
                description="Scale service replicas",
                category="action",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string"},
                        "target_replicas": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["service_name", "target_replicas", "reason"],
                },
                requires_approval=True,
                risk_level="medium",
            ),
            "analyze_logs": ToolInfo(
                name="analyze_logs",
                description="Analyze logs for patterns and anomalies",
                category="analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "service_name": {"type": "string"},
                        "time_range_minutes": {"type": "integer", "default": 30},
                        "log_level": {"type": "string", "enum": ["all", "error", "warn", "info"]},
                    },
                    "required": ["service_name"],
                },
                requires_approval=False,
                risk_level="low",
            ),
        }

        if tool_name not in mock_tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )
        return mock_tools[tool_name]

    tool = mcp_server.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    return ToolInfo(
        name=tool.name,
        description=tool.description,
        category=tool.category.value,
        parameters=tool.parameters,
        requires_approval=tool.requires_approval,
        risk_level=tool.risk_level,
    )


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
    Execute a tool.

    Tools requiring approval will go through Constitutional AI validation.

    Args:
        tool_call: Tool name, parameters, and context

    Returns:
        Tool execution result
    """
    mcp_server = getattr(request.app.state, "mcp_server", None)

    if mcp_server is None:
        # Mock responses for development
        logger.warning("MCP server not available, using mock responses")

        mock_responses = {
            "find_similar": {
                "success": True,
                "data": {
                    "similar_incidents": [
                        {
                            "incident_id": "INC-2025-0042",
                            "title": "Database connection pool exhausted",
                            "similarity_score": 0.87,
                            "root_cause": "Connection pool misconfiguration",
                            "resolution": "Increased pool size",
                        },
                    ],
                    "total_searched": 150,
                },
                "execution_time_ms": 45.2,
                "metadata": {"source": "mock"},
            },
            "get_dependencies": {
                "success": True,
                "data": {
                    "service": tool_call.parameters.get("service_name", "unknown"),
                    "dependencies": {
                        "upstream": ["load-balancer"],
                        "downstream": ["database", "cache", "queue"],
                    },
                },
                "execution_time_ms": 12.5,
                "metadata": {"source": "mock"},
            },
            "restart_service": {
                "success": True,
                "data": {
                    "service": tool_call.parameters.get("service_name", "unknown"),
                    "action": "restart",
                    "status": "completed",
                    "message": "Service restart initiated successfully",
                },
                "execution_time_ms": 523.1,
                "metadata": {"mock": True},
            },
            "scale_service": {
                "success": True,
                "data": {
                    "service": tool_call.parameters.get("service_name", "unknown"),
                    "action": "scale_up",
                    "target_replicas": tool_call.parameters.get("target_replicas", 3),
                    "status": "completed",
                },
                "execution_time_ms": 312.7,
                "metadata": {"mock": True},
            },
            "analyze_logs": {
                "success": True,
                "data": {
                    "service": tool_call.parameters.get("service_name", "unknown"),
                    "summary": {
                        "total_logs": 1542,
                        "error_count": 87,
                        "warning_count": 234,
                    },
                    "top_errors": [
                        {"pattern": "Connection refused", "count": 45},
                        {"pattern": "Timeout", "count": 28},
                    ],
                },
                "execution_time_ms": 89.3,
                "metadata": {"source": "mock"},
            },
        }

        if tool_call.tool_name not in mock_responses:
            return ToolCallResponse(
                success=False,
                data=None,
                error=f"Tool '{tool_call.tool_name}' not found",
                execution_time_ms=0,
            )

        response = mock_responses[tool_call.tool_name]
        return ToolCallResponse(**response)

    # Execute through MCP server
    result = await mcp_server.execute_tool(
        tool_call.tool_name,
        tool_call.parameters,
        tool_call.context,
    )

    return ToolCallResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
        metadata=result.metadata,
    )


__all__ = ["router"]
