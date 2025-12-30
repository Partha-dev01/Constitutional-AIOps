"""
Constitutional AIOps - Main Application Entry Point

FastAPI application that serves as the central orchestrator for the
Constitutional AIOps system.

Architecture: Simultaneous Dual-Model (Qwen3-4B + Qwen3-14B on 24GB VRAM)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config import config
from src.utils.logging import setup_logging

# Import routers
from src.api.routes.health import router as health_router, set_startup_time
from src.api.routes.chat import router as chat_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.actions import router as actions_router
from src.api.routes.tools import router as tools_router
from src.api.routes.agents import router as agents_router
from src.api.routes.telemetry import router as telemetry_router
from src.api.routes.graph import router as graph_router
from src.api.routes.prompts import router as prompts_router
from src.api.routes.infrastructure import router as infrastructure_router
from src.api.routes.demo import router as demo_router
from src.api.routes.metrics import router as metrics_router

# Import core components
from src.agents.model_router import ModelRouter
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.fast_annotator import FastAnnotator
from src.constitutional.validator import ConstitutionalValidator

# Import memory components
from src.memory.neo4j_client import Neo4jClient, NEO4J_AVAILABLE
from src.memory.episode_store import EpisodeStore
from src.memory.retrieval import ContextRetriever

# Import telemetry components
from src.telemetry.collector import TelemetryCollector
from src.telemetry.compressor import TokenCompressor
from src.telemetry.aggregator import TelemetryAggregator

# Import MCP components
from src.mcp.server import MCPActionServer

# Import WebSocket manager
from src.utils.websocket import manager as ws_manager, EventType, WebSocketEvent

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize connections to LLM servers, Neo4j, observability stack
    - Shutdown: Gracefully close all connections
    """
    # Startup
    logger.info("Starting Constitutional AIOps...")
    logger.info(f"Fast Agent URL: {config.llm.fast_agent_url}")
    logger.info(f"Reasoning Agent URL: {config.llm.reasoning_agent_url}")

    # Set startup time for uptime tracking
    set_startup_time()

    # Initialize ModelRouter
    app.state.model_router = ModelRouter()

    # Initialize agents with shared router
    app.state.fast_annotator = FastAnnotator(model_router=app.state.model_router)
    app.state.reasoning_agent = ReasoningAgent(model_router=app.state.model_router)

    # Initialize Constitutional Validator
    app.state.validator = ConstitutionalValidator()

    # Initialize Neo4j client and memory components
    app.state.neo4j_client = None
    app.state.episode_store = None
    app.state.context_retriever = None

    if NEO4J_AVAILABLE:
        try:
            neo4j_client = Neo4jClient()
            connected = await neo4j_client.connect()
            if connected:
                app.state.neo4j_client = neo4j_client
                app.state.episode_store = EpisodeStore(neo4j_client=neo4j_client)
                app.state.context_retriever = ContextRetriever(
                    episode_store=app.state.episode_store,
                    neo4j_client=neo4j_client,
                )
                logger.info("Neo4j and memory components initialized successfully")
            else:
                logger.warning("Neo4j connection failed, memory features disabled")
                # Still create episode store with in-memory fallback
                app.state.episode_store = EpisodeStore()
                app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j: {e}")
            app.state.episode_store = EpisodeStore()
            app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)
    else:
        logger.info("Neo4j driver not available, using in-memory episode store")
        app.state.episode_store = EpisodeStore()
        app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)

    # Initialize telemetry components
    app.state.telemetry_collector = TelemetryCollector()
    app.state.token_compressor = TokenCompressor()
    app.state.telemetry_aggregator = TelemetryAggregator()
    logger.info("Telemetry components initialized")

    # Initialize MCP Action Server
    app.state.mcp_server = MCPActionServer(
        episode_store=app.state.episode_store,
        neo4j_client=app.state.neo4j_client,
        telemetry_collector=app.state.telemetry_collector,
        validator=app.state.validator,
    )
    logger.info("MCP Action Server initialized with 5 tools")

    # Initialize WebSocket manager
    app.state.ws_manager = ws_manager
    logger.info("WebSocket manager initialized")

    # Verify LLM server connections
    try:
        health = await app.state.model_router.health_check()
        logger.info(f"LLM Health: Fast Agent={health['fast_agent']}, Reasoning Agent={health['reasoning_agent']}")
    except Exception as e:
        logger.warning(f"LLM health check failed (will retry on requests): {e}")

    # Verify telemetry backends
    try:
        telemetry_health = await app.state.telemetry_collector.health_check()
        logger.info(f"Telemetry Health: Loki={telemetry_health['loki']}, Prometheus={telemetry_health['prometheus']}, Tempo={telemetry_health['tempo']}")
    except Exception as e:
        logger.warning(f"Telemetry health check failed: {e}")

    logger.info("Constitutional AIOps started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Constitutional AIOps...")

    # Close ModelRouter connections
    if app.state.model_router:
        await app.state.model_router.close()

    # Close Neo4j connection
    if app.state.neo4j_client:
        await app.state.neo4j_client.close()

    # Close telemetry collector
    if app.state.telemetry_collector:
        await app.state.telemetry_collector.close()

    logger.info("Constitutional AIOps shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Constitutional AIOps",
    description=(
        "Autonomous infrastructure management system with Constitutional AI safety. "
        "Uses dual-agent architecture (Qwen3-4B + Qwen3-14B) for intelligent operations."
    ),
    version="0.4.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Constitutional AIOps",
        "version": "0.4.0",
        "architecture": "Simultaneous Dual-Model (24GB VRAM)",
        "models": {
            "fast_agent": "Qwen3-4B Q4_K_M @ port 8081",
            "reasoning_agent": "Qwen3-14B Q4_K_M @ port 8082",
        },
        "features": {
            "constitutional_ai": "11 principles, 3 tiers",
            "graph_memory": "Neo4j episodic storage",
            "telemetry": "LGTM stack integration",
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
            "incidents": "/api/v1/incidents",
            "actions": "/api/v1/actions",
            "tools": "/api/v1/tools",
            "metrics": "/api/v1/metrics",
            "websocket": "/ws",
        },
    }


# Include routers with /api/v1 prefix
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(incidents_router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(actions_router, prefix="/api/v1/actions", tags=["actions"])
app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(graph_router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(prompts_router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(infrastructure_router, prefix="/api/v1/infrastructure", tags=["infrastructure"])
app.include_router(demo_router, prefix="/api/v1/demo", tags=["demo"])
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"])


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """
    WebSocket endpoint for real-time event streaming.

    Connect to receive live updates about:
    - Incident creation/updates/resolution
    - Action creation/approval/execution
    - RCA analysis progress
    - System health updates

    Query Parameters:
        client_id: Optional client identifier for tracking

    Message Format (JSON):
        {
            "type": "event_type",
            "payload": {...},
            "timestamp": "ISO8601",
            "correlation_id": "optional"
        }

    Subscription:
        Send: {"type": "subscribe", "payload": {"room": "incident:123"}}
        To subscribe to specific incident updates
    """
    connection_id = await ws_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive and handle messages
            data = await websocket.receive_text()
            await ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)


# WebSocket connections info endpoint
@app.get("/api/v1/ws/connections", tags=["websocket"])
async def get_websocket_connections():
    """Get information about active WebSocket connections."""
    return {
        "count": ws_manager.connection_count,
        "connections": ws_manager.connections_info,
    }


if __name__ == "__main__":
    import uvicorn

    setup_logging(config.app.log_level)

    uvicorn.run(
        "src.main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
    )
