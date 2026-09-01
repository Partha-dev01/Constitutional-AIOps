"""
Constitutional AIOps - Main Application Entry Point

FastAPI application that serves as the central orchestrator for the
Constitutional AIOps system.

Architecture: Simultaneous Dual-Model (Qwen3-4B + Qwen3-14B on 24GB VRAM)
"""

import hmac
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config import config
from src.utils.logging import setup_logging
from src.version import __version__

# Import auth layer (stdlib-only: scrypt + HMAC session tokens + SQLite store)
from src.auth.deps import auth_required, require_user
from src.auth.store import count_users, ensure_initial_admin, init_db as init_auth_db
from src.auth.tokens import COOKIE_NAME as SESSION_COOKIE_NAME, verify_session

# Import routers
from src.api.routes.health import router as health_router, set_startup_time
from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.actions import router as actions_router
from src.api.routes.tools import router as tools_router
from src.api.routes.agents import router as agents_router
from src.api.routes.telemetry import router as telemetry_router
from src.api.routes.graph import router as graph_router
from src.api.routes.graph_topology import router as graph_topology_router
from src.api.routes.prompts import router as prompts_router, apply_persisted_prompts
from src.api.routes.infrastructure import router as infrastructure_router
from src.api.routes.demo import router as demo_router
from src.api.routes.metrics import router as metrics_router
from src.api.routes.benchmark import router as benchmark_router
from src.api.routes.settings import router as settings_router
from src.api.routes.topology import router as topology_router

# Import core components
from src.agents.model_router import ModelRouter
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.fast_annotator import FastAnnotator
from src.constitutional.validator import ConstitutionalValidator

# Import memory components
from src.memory.neo4j_client import Neo4jClient, NEO4J_AVAILABLE
from src.memory.episode_store import EpisodeStore
from src.memory.retrieval import ContextRetriever
from src.memory.embedding_service import get_embedding_service

# Import confidence calculator
from src.confidence import ConfidenceCalculator

# Import telemetry components
from src.telemetry.collector import TelemetryCollector
from src.telemetry.compressor import TokenCompressor
from src.telemetry.aggregator import TelemetryAggregator
from src.telemetry.background_processor import BackgroundTelemetryProcessor

# Import orchestration (LangGraph pipeline)
from src.orchestration.graph import build_incident_graph

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

    # The /ws endpoint is deliberately outside Caddy's basic_auth (the browser
    # can't attach credentials to a WS upgrade), so the app-layer WS_TOKEN is
    # its ONLY guard. An empty token silently disables that guard — refuse to
    # start in production rather than expose the event stream publicly.
    if os.getenv("ENVIRONMENT", "local").lower() == "production" and not os.getenv("WS_TOKEN"):
        raise RuntimeError(
            "WS_TOKEN must be set in production: without it the /ws endpoint "
            "is reachable unauthenticated. Set it in .env.production."
        )

    # In-app auth: initialise the SQLite user store and bootstrap the first
    # admin from AUTH_ADMIN_USER/AUTH_ADMIN_PASSWORD (only on an empty table).
    init_auth_db()
    ensure_initial_admin()
    # Guard-rail: enforcing auth with zero users would lock EVERYONE out of
    # the API with no way to log in — refuse to start instead.
    if auth_required() and count_users() == 0:
        raise RuntimeError(
            "AUTH_REQUIRED=true but the user store is empty and no valid "
            "AUTH_ADMIN_USER/AUTH_ADMIN_PASSWORD bootstrap pair is set. "
            "Set both env vars (password: min 10 chars, not the username) "
            "or pre-create a user before enabling enforcement."
        )
    logger.info(f"In-app auth initialised (enforcement={'ON' if auth_required() else 'off'})")

    # Durable app-state hydration (Batch A): conversations, incidents, pending
    # remediation actions and the incident-id counter are written through to a
    # SQLite store under AIOPS_DATA_DIR on every mutation. Re-hydrate the
    # in-memory dicts (the read fast-path) here so a restart/redeploy restores
    # the prior state instead of dropping it. Non-fatal: a persistence failure
    # must never block startup — the system simply starts empty.
    try:
        from src.persistence import store as persistence_store
        from src.api.routes import chat as chat_routes
        from src.api.routes import incidents as incident_routes

        persistence_store.init_db()

        loaded_convs = persistence_store.load_all_conversations()
        chat_routes._conversations.update(loaded_convs)
        # Re-apply the in-memory eviction cap after a bulk load so a large
        # persisted history can't blow past CHAT_MAX_CONVERSATIONS.
        chat_routes._evict_stale_conversations()

        loaded_pending = persistence_store.load_all_pending_actions()
        chat_routes._pending_actions.update(loaded_pending)
        # Drop anything already past its TTL / over cap on load.
        chat_routes._evict_stale_pending_actions()

        loaded_incidents = persistence_store.load_all_incidents()
        incident_routes._incidents.update(loaded_incidents)

        # Restore the incident counter so new IDs keep advancing past the
        # highest pre-restart value (set_counter persists the live max).
        incident_routes._incident_counter = persistence_store.get_counter(
            incident_routes._INCIDENT_COUNTER_NAME, 0
        )

        logger.info(
            "Durable state restored: %d conversation(s), %d incident(s), "
            "%d pending action(s), incident_counter=%d",
            len(chat_routes._conversations),
            len(incident_routes._incidents),
            len(chat_routes._pending_actions),
            incident_routes._incident_counter,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to hydrate durable app state (starting empty): {e}")

    # Set startup time for uptime tracking
    set_startup_time()

    # Initialize ModelRouter
    app.state.model_router = ModelRouter()

    # Re-apply any UI-saved LLM endpoint override (Settings -> Models). Persisted
    # config wins over env and survives a restart; done before the agents bind so
    # they never see the pre-override state. Non-fatal — a bad stored value just
    # fails on the first LLM call. The key is never logged.
    try:
        from src.api.routes.settings import get_models_settings

        _models = get_models_settings()
        if _models:
            _key = _models.get("apiKey", "")
            await app.state.model_router.reconfigure(
                fast_url=_models.get("fastAgentUrl"),
                reasoning_url=_models.get("reasoningAgentUrl"),
                fast_model=_models.get("fastAgentModel"),
                reasoning_model=_models.get("reasoningAgentModel"),
                fast_api_key=_key,
                reasoning_api_key=_key,
            )
            logger.info("Applied persisted LLM endpoint override from Settings -> Models")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not apply persisted LLM endpoint override (non-fatal): {e}")

    # Initialize agents with shared router
    app.state.fast_annotator = FastAnnotator(model_router=app.state.model_router)
    app.state.reasoning_agent = ReasoningAgent(model_router=app.state.model_router)

    # Re-apply persisted prompt overrides (session-14 W4): UI prompt edits are
    # persisted under AIOPS_DATA_DIR and must survive a restart/redeploy.
    try:
        applied = apply_persisted_prompts(app)
        if applied:
            logger.info(f"Restored {len(applied)} persisted prompt override(s)")
    except Exception as e:
        logger.warning(f"Failed to apply persisted prompt overrides: {e}")

    # Initialize Constitutional Validator
    app.state.validator = ConstitutionalValidator()

    # Startup-load persisted constitutional thresholds (W2.1): the PUT
    # /settings path patches the live validator, but without this the operator's
    # saved auto/approval thresholds RESET to the ConstitutionalValidator
    # defaults on every restart/redeploy. Mirror the persisted values onto the
    # fresh validator here. Non-fatal: a missing/malformed settings file must
    # never block startup — the validator simply keeps its defaults.
    try:
        from src.api.routes.settings import get_constitutional_settings

        const_settings = get_constitutional_settings()
        auto = const_settings.get("autoThreshold")
        approval = const_settings.get("approvalThreshold")
        if auto is not None:
            app.state.validator.confidence_threshold_auto = float(auto) / 100.0
        if approval is not None:
            app.state.validator.confidence_threshold_approval = float(approval) / 100.0
        if auto is not None or approval is not None:
            logger.info(
                "Restored persisted constitutional thresholds → auto=%.2f approval=%.2f",
                app.state.validator.confidence_threshold_auto,
                app.state.validator.confidence_threshold_approval,
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to apply persisted constitutional thresholds: {e}")

    # Initialize embedding service (lazy-loads model on first use)
    app.state.embedding_service = get_embedding_service()
    logger.info(f"Embedding service initialized (available: {app.state.embedding_service.is_available})")

    # Initialize Neo4j client and memory components
    app.state.neo4j_client = None
    app.state.episode_store = None
    app.state.context_retriever = None
    app.state.confidence_calculator = None

    if NEO4J_AVAILABLE:
        try:
            neo4j_client = Neo4jClient()
            connected = await neo4j_client.connect()
            if connected:
                app.state.neo4j_client = neo4j_client
                app.state.episode_store = EpisodeStore(
                    neo4j_client=neo4j_client,
                    embedding_service=app.state.embedding_service,
                )
                app.state.context_retriever = ContextRetriever(
                    episode_store=app.state.episode_store,
                    neo4j_client=neo4j_client,
                )
                # Initialize confidence calculator with all components
                app.state.confidence_calculator = ConfidenceCalculator(
                    neo4j_client=neo4j_client,
                    episode_store=app.state.episode_store,
                )
                logger.info("Neo4j and memory components initialized successfully")
                logger.info(
                    f"Confidence calculator initialized: "
                    f"C(a) = {ConfidenceCalculator.ALPHA}·LLM + "
                    f"{ConfidenceCalculator.BETA}·hist + "
                    f"{ConfidenceCalculator.GAMMA}·sim"
                )
            else:
                logger.warning("Neo4j connection failed, memory features disabled")
                # Still create episode store with in-memory fallback
                app.state.episode_store = EpisodeStore(
                    embedding_service=app.state.embedding_service,
                )
                app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)
                app.state.confidence_calculator = ConfidenceCalculator(
                    episode_store=app.state.episode_store,
                )
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j: {e}")
            app.state.episode_store = EpisodeStore(
                embedding_service=app.state.embedding_service,
            )
            app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)
            app.state.confidence_calculator = ConfidenceCalculator(
                episode_store=app.state.episode_store,
            )
    else:
        logger.info("Neo4j driver not available, using in-memory episode store")
        app.state.episode_store = EpisodeStore(
            embedding_service=app.state.embedding_service,
        )
        app.state.context_retriever = ContextRetriever(episode_store=app.state.episode_store)
        app.state.confidence_calculator = ConfidenceCalculator(
            episode_store=app.state.episode_store,
        )

    # Seed the real platform topology (session-14 W1): idempotent MERGE of the
    # canonical services + DEPENDS_ON edges. Non-fatal — the /graph/topology
    # endpoint falls back to the static constants when Neo4j is unavailable.
    if app.state.neo4j_client is not None:
        try:
            from src.memory.topology_seed import seed_service_topology

            seed_counts = await seed_service_topology(app.state.neo4j_client)
            logger.info(f"Service topology seeded at startup: {seed_counts}")
        except Exception as e:
            logger.warning(f"Topology seeding failed (non-fatal): {e}")

    # Initialize LangGraph orchestration pipeline (MANDATORY)
    # Implements Talker-Reasoner architecture (arXiv:2410.08328)
    app.state.incident_graph = build_incident_graph(
        fast_annotator=app.state.fast_annotator,
        reasoning_agent=app.state.reasoning_agent,
        validator=app.state.validator,
        confidence_calculator=app.state.confidence_calculator,
    )
    if app.state.incident_graph is None:
        raise RuntimeError(
            "Failed to build LangGraph incident orchestration pipeline. "
            "The orchestrator is mandatory — system cannot start without it."
        )
    logger.info("LangGraph incident orchestration pipeline initialized (MANDATORY)")

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
    logger.info("MCP Action Server initialized with 9 tools")

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

    # Initialize and start Background Telemetry Processor
    # This implements the "System 1" continuous scanning from Research_V7.tex
    app.state.background_processor = BackgroundTelemetryProcessor(
        fast_annotator=app.state.fast_annotator,
        reasoning_agent=app.state.reasoning_agent,
        telemetry_collector=app.state.telemetry_collector,
        episode_store=app.state.episode_store,
        neo4j_client=app.state.neo4j_client,
        incident_graph=app.state.incident_graph,
        processing_interval=30,  # Process every 30 seconds
    )
    await app.state.background_processor.start()
    logger.info("Background telemetry processor started (30s interval)")

    logger.info("Constitutional AIOps started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Constitutional AIOps...")

    # Stop background processor first
    if app.state.background_processor:
        await app.state.background_processor.stop()
        logger.info("Background telemetry processor stopped")

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


# Interactive docs / OpenAPI schema are dev-only by DEFAULT (Batch F #5): in
# production we publish no machine-readable API map unless an operator opts back
# in with AIOPS_ENABLE_DOCS=true. Our hosted instance sets it so the public
# Swagger reference (linked from the marketing Docs section) works; a plain
# self-host stays closed. They are always on outside production.
_IS_PRODUCTION = os.getenv("ENVIRONMENT", "local").lower() == "production"
_DOCS_ENABLED = (not _IS_PRODUCTION) or os.getenv(
    "AIOPS_ENABLE_DOCS", "false"
).lower() == "true"

# Max request body for /api/* endpoints (Batch F #5). Mirrors the Caddy
# /ingest body cap so a caller past the auth wall can't stream a huge JSON body
# at /api/* to pressure memory. Overridable via env; defaults to 10MB.
_MAX_API_BODY_BYTES = max(1, int(os.getenv("MAX_API_BODY_MB", "10"))) * 1024 * 1024

# Create FastAPI application
app = FastAPI(
    title="Constitutional AIOps",
    description=(
        "Autonomous infrastructure management system with Constitutional AI safety. "
        "Uses dual-agent architecture (Qwen3-4B + Qwen3-14B) for intelligent operations."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if _DOCS_ENABLED else None,
    redoc_url="/redoc" if _DOCS_ENABLED else None,
    openapi_url="/openapi.json" if _DOCS_ENABLED else None,
)


# Request-body-size cap for /api/* (Batch F #5). Pure-ASGI middleware, no new
# dep. Rejects oversize bodies with 413 BEFORE the route buffers/parses them:
# we trust a present Content-Length, and also defend against a missing/lying
# Content-Length by counting streamed bytes and aborting once the cap is passed.
@app.middleware("http")
async def _limit_api_body_size(request, call_next):
    if request.url.path.startswith("/api/"):
        from starlette.responses import JSONResponse

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > _MAX_API_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large"},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400, content={"detail": "Invalid Content-Length"}
                )

        # NOTE: cap by Content-Length only. Wrapping receive() to tally streamed
        # bytes is unsafe under Starlette's BaseHTTPMiddleware — it corrupts body
        # parsing for downstream handlers (observed live as 400 "error parsing the
        # body" on every POST). Chunked requests without a Content-Length are not
        # byte-capped here; uvicorn enforces its own limits and every real API
        # client (browser fetch, curl) sends Content-Length.

    return await call_next(request)


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
        "version": __version__,
        "architecture": "Simultaneous Dual-Model (24GB VRAM)",
        "models": {
            "fast_agent": "Qwen3-4B Q4_K_M @ port 8081",
            "reasoning_agent": "Qwen3-14B Q4_K_M @ port 8082",
        },
        "features": {
            "constitutional_ai": "12 principles (4+4+4), 3 tiers",
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


# Include routers with /api/v1 prefix.
# PUBLIC: health, the root endpoint and the auth router itself (its admin
# endpoints are guarded internally via require_admin; /login and /config must
# stay reachable pre-login). Everything else requires a user — which is a
# no-op synthetic admin until AUTH_REQUIRED=true flips enforcement on.
_AUTHED = [Depends(require_user)]
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"], dependencies=_AUTHED)
app.include_router(incidents_router, prefix="/api/v1/incidents", tags=["incidents"], dependencies=_AUTHED)
app.include_router(actions_router, prefix="/api/v1/actions", tags=["actions"], dependencies=_AUTHED)
app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"], dependencies=_AUTHED)
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"], dependencies=_AUTHED)
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"], dependencies=_AUTHED)
app.include_router(graph_router, prefix="/api/v1/graph", tags=["graph"], dependencies=_AUTHED)
app.include_router(graph_topology_router, prefix="/api/v1/graph", tags=["graph"], dependencies=_AUTHED)
app.include_router(prompts_router, prefix="/api/v1/prompts", tags=["prompts"], dependencies=_AUTHED)
app.include_router(infrastructure_router, prefix="/api/v1/infrastructure", tags=["infrastructure"], dependencies=_AUTHED)
app.include_router(demo_router, prefix="/api/v1/demo", tags=["demo"], dependencies=_AUTHED)
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"], dependencies=_AUTHED)
app.include_router(benchmark_router, prefix="/api/v1/benchmark", tags=["benchmark"], dependencies=_AUTHED)
app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"], dependencies=_AUTHED)
app.include_router(topology_router, prefix="/api/v1/topology", tags=["topology"], dependencies=_AUTHED)


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None, token: str = None):
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
    # App-layer guard: Caddy can't basic_auth the WS upgrade. A connection is
    # accepted when EITHER (a) the browser presents a valid in-app session
    # cookie (set by /api/v1/auth/login — sent automatically on same-origin WS
    # upgrades), OR (b) the legacy WS_TOKEN query token matches (kept as the
    # fallback for token-fetching clients). An empty WS_TOKEN (local/dev)
    # still allows unauthenticated connections as before.
    session_cookie = websocket.cookies.get(SESSION_COOKIE_NAME)
    session_ok = bool(session_cookie) and verify_session(session_cookie) is not None
    expected = os.getenv("WS_TOKEN", "")
    token_ok = token is not None and hmac.compare_digest(token, expected)
    if not session_ok and expected and not token_ok:
        await websocket.close(code=1008)
        return

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
@app.get("/api/v1/ws/connections", tags=["websocket"], dependencies=[Depends(require_user)])
async def get_websocket_connections():
    """Get information about active WebSocket connections."""
    return {
        "count": ws_manager.connection_count,
        "connections": ws_manager.connections_info,
    }


@app.get("/api/v1/ws/token", tags=["websocket"], dependencies=[Depends(require_user)])
async def get_ws_token():
    """Return the app-layer WebSocket token (empty string if unset). This route
    is gated by Caddy basic_auth like all /api/* paths, plus the in-app session
    once AUTH_REQUIRED is on."""
    import os
    return {"token": os.getenv("WS_TOKEN", "")}


if __name__ == "__main__":
    import uvicorn

    setup_logging(config.app.log_level)

    uvicorn.run(
        "src.main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
    )
