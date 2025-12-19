# Constitutional AIOps - Mega Prompt Part 2: Backend Implementation

---

## 5. Backend Implementation

### 5.1 Configuration Management

```python
# src/config.py
"""
Configuration management for Constitutional AIOps.
Loads from environment variables with sensible defaults.
Dual-Model Architecture: Qwen3-4B (8081) + Qwen3-14B (8082)
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from enum import Enum


class Environment(str, Enum):
    LOCAL = "local"
    GPU_TESTING = "gpu-testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Environment
    environment: Environment = Field(default=Environment.LOCAL)
    debug: bool = Field(default=False)
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=1)
    
    # Dual-Model LLM Configuration (Simultaneous Loading)
    fast_agent_url: str = Field(
        default="http://localhost:8081",
        description="Qwen3-4B Q4_K_M endpoint for fast annotation"
    )
    reasoning_agent_url: str = Field(
        default="http://localhost:8082",
        description="Qwen3-14B Q4_K_M endpoint for RCA and chat"
    )
    
    # Confidence Thresholds
    confidence_high: float = Field(default=0.9)
    confidence_medium: float = Field(default=0.7)
    
    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password123")
    
    # Telemetry Sources
    loki_url: str = Field(default="http://localhost:3100")
    tempo_url: str = Field(default="http://localhost:3200")
    prometheus_url: str = Field(default="http://localhost:9090")
    
    # InfluxDB
    influxdb_url: str = Field(default="http://localhost:8086")
    influxdb_token: Optional[str] = Field(default=None)
    influxdb_org: str = Field(default="aiops")
    influxdb_bucket: str = Field(default="telemetry")
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
```

### 5.2 Main Application Entry Point

```python
# src/main.py
"""
Constitutional AIOps - Main Application Entry Point
Dual-Model Architecture: Qwen3-4B + Qwen3-14B simultaneous loading
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from loguru import logger

from src.config import settings
from src.api.app import create_app
from src.agents.model_router import ModelRouter
from src.memory.neo4j_client import Neo4jClient
from src.telemetry.collector import TelemetryCollector


# Global instances
model_router: ModelRouter = None
neo4j_client: Neo4jClient = None
telemetry_collector: TelemetryCollector = None


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    global model_router, neo4j_client, telemetry_collector
    
    logger.info("Starting Constitutional AIOps (Dual-Model Architecture)...")
    
    # Initialize components
    try:
        # Neo4j connection
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        await neo4j_client.connect()
        logger.info("Neo4j connected")
        
        # Model router (simultaneous dual-model)
        model_router = ModelRouter(
            fast_agent_url=settings.fast_agent_url,
            reasoning_agent_url=settings.reasoning_agent_url
        )
        await model_router.initialize()
        logger.info("Model router initialized (both models loaded)")
        
        # Telemetry collector
        telemetry_collector = TelemetryCollector(
            loki_url=settings.loki_url,
            tempo_url=settings.tempo_url,
            prometheus_url=settings.prometheus_url
        )
        await telemetry_collector.start()
        logger.info("Telemetry collector started")
        
        # Store in app state
        app.state.model_router = model_router
        app.state.neo4j_client = neo4j_client
        app.state.telemetry_collector = telemetry_collector
        
        # Backward compatibility alias
        app.state.model_manager = model_router
        
        logger.info("Constitutional AIOps started successfully")
        
        yield
        
    finally:
        # Cleanup
        logger.info("Shutting down Constitutional AIOps...")
        
        if telemetry_collector:
            await telemetry_collector.stop()
        if neo4j_client:
            await neo4j_client.close()
        if model_router:
            await model_router.shutdown()
            
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Create app
    app = create_app(lifespan=lifespan)
    
    # Run server
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
```

### 5.3 FastAPI Application

```python
# src/api/app.py
"""
FastAPI application factory.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Callable

from src.api.routes import health, chat, telemetry, incidents, actions, status
from src.api.middleware.logging import LoggingMiddleware


def create_app(lifespan: Callable = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Constitutional AIOps",
        description="Autonomous infrastructure management with Constitutional AI safety",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(telemetry.router, prefix="/api/telemetry", tags=["Telemetry"])
    app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
    app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
    app.include_router(status.router, prefix="/api/status", tags=["Status"])
    
    return app
```

### 5.4 Health Check Route

```python
# src/api/routes/health.py
"""
Health check endpoints.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Health check endpoint.
    Returns status of all system components.
    """
    components = {}
    overall_healthy = True
    
    # Check model manager
    if hasattr(request.app.state, 'model_manager'):
        mm = request.app.state.model_manager
        model_status = await mm.get_status()
        components["model_manager"] = model_status
        if model_status.get("status") != "healthy":
            overall_healthy = False
    else:
        components["model_manager"] = {"status": "not_initialized"}
        overall_healthy = False
    
    # Check Neo4j
    if hasattr(request.app.state, 'neo4j_client'):
        neo4j = request.app.state.neo4j_client
        try:
            await neo4j.verify_connection()
            components["neo4j"] = {"status": "healthy"}
        except Exception as e:
            components["neo4j"] = {"status": "unhealthy", "error": str(e)}
            overall_healthy = False
    else:
        components["neo4j"] = {"status": "not_initialized"}
        overall_healthy = False
    
    # Check telemetry collector
    if hasattr(request.app.state, 'telemetry_collector'):
        tc = request.app.state.telemetry_collector
        tc_status = tc.get_status()
        components["telemetry"] = tc_status
    else:
        components["telemetry"] = {"status": "not_initialized"}
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        components=components
    )


@router.get("/ready")
async def readiness_check(request: Request):
    """Kubernetes readiness probe."""
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}
```

### 5.5 Chat WebSocket Route

```python
# src/api/routes/chat.py
"""
Chat endpoints including WebSocket for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import asyncio

from src.agents.reasoning_agent import ReasoningAgent
from src.agents.prompts.chat import ChatPromptBuilder


router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    thinking: Optional[str] = None  # Thinking process if enabled


class ChatRequest(BaseModel):
    message: str
    enable_thinking: Optional[bool] = None  # None = auto-detect
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    thinking: Optional[str] = None
    model_used: str
    latency_ms: float
    session_id: str


# Store active sessions (use Redis in production)
chat_sessions: dict = {}


class ChatSession:
    """Manages a chat session with history."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
    
    def add_message(self, role: str, content: str, thinking: str = None):
        self.messages.append(ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            thinking=thinking
        ))
        self.last_activity = datetime.utcnow()
    
    def get_context(self, max_messages: int = 20) -> List[dict]:
        """Get recent messages for context."""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Message format (incoming):
    {
        "type": "message",
        "content": "user message",
        "enable_thinking": true/false/null
    }
    
    Message format (outgoing):
    {
        "type": "response" | "thinking" | "error" | "status",
        "content": "...",
        "model": "reasoning-agent",
        "latency_ms": 123.45
    }
    """
    await websocket.accept()
    
    # Get or create session
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id)
    session = chat_sessions[session_id]
    
    # Get model manager from app state
    model_manager = websocket.app.state.model_manager
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "status",
            "content": "connected",
            "session_id": session_id
        })
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                user_message = data.get("content", "")
                enable_thinking = data.get("enable_thinking")  # None = auto
                
                # Add user message to history
                session.add_message("user", user_message)
                
                # Record activity (keeps 14B loaded)
                await model_manager.record_activity("chat")
                
                # Send typing indicator
                await websocket.send_json({
                    "type": "status",
                    "content": "thinking"
                })
                
                start_time = datetime.utcnow()
                
                try:
                    # Get response from reasoning agent
                    reasoning_agent = ReasoningAgent(
                        model_manager=model_manager,
                        mode="chat"
                    )
                    
                    response = await reasoning_agent.generate(
                        message=user_message,
                        context=session.get_context(),
                        enable_thinking=enable_thinking
                    )
                    
                    latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    # Send thinking process if available
                    if response.thinking:
                        await websocket.send_json({
                            "type": "thinking",
                            "content": response.thinking
                        })
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "content": response.content,
                        "model": response.model_used,
                        "latency_ms": latency_ms
                    })
                    
                    # Add to history
                    session.add_message(
                        "assistant", 
                        response.content,
                        thinking=response.thinking
                    )
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Error generating response: {str(e)}"
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
        except:
            pass


@router.post("/", response_model=ChatResponse)
async def chat_http(request: Request, chat_request: ChatRequest):
    """
    HTTP endpoint for chat (alternative to WebSocket).
    """
    model_manager = request.app.state.model_manager
    
    # Get or create session
    session_id = chat_request.session_id or f"http-{datetime.utcnow().timestamp()}"
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id)
    session = chat_sessions[session_id]
    
    # Add user message
    session.add_message("user", chat_request.message)
    
    # Record activity
    await model_manager.record_activity("chat")
    
    start_time = datetime.utcnow()
    
    # Generate response
    reasoning_agent = ReasoningAgent(
        model_manager=model_manager,
        mode="chat"
    )
    
    response = await reasoning_agent.generate(
        message=chat_request.message,
        context=session.get_context(),
        enable_thinking=chat_request.enable_thinking
    )
    
    latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Add to history
    session.add_message("assistant", response.content, thinking=response.thinking)
    
    return ChatResponse(
        message=response.content,
        thinking=response.thinking,
        model_used=response.model_used,
        latency_ms=latency_ms,
        session_id=session_id
    )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "message_count": len(session.messages),
        "messages": [m.dict() for m in session.messages]
    }
```

### 5.6 Status Route

```python
# src/api/routes/status.py
"""
System status endpoint showing model state and metrics.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


router = APIRouter()


class ModelStatus(BaseModel):
    name: str
    loaded: bool
    vram_mb: Optional[float]
    last_used: Optional[str]


class SystemStatus(BaseModel):
    timestamp: str
    environment: str
    active_model: str
    model_timeout_seconds: int
    seconds_until_swap: Optional[int]
    models: dict
    telemetry: dict
    memory: dict


@router.get("/", response_model=SystemStatus)
async def get_status(request: Request):
    """
    Get comprehensive system status.
    """
    model_manager = request.app.state.model_manager
    status = await model_manager.get_status()
    
    # Get telemetry status
    telemetry_status = {}
    if hasattr(request.app.state, 'telemetry_collector'):
        telemetry_status = request.app.state.telemetry_collector.get_status()
    
    # Get memory status
    memory_status = {}
    if hasattr(request.app.state, 'neo4j_client'):
        try:
            memory_status = await request.app.state.neo4j_client.get_stats()
        except:
            memory_status = {"status": "error"}
    
    return SystemStatus(
        timestamp=datetime.utcnow().isoformat(),
        environment=request.app.state.model_manager.environment if hasattr(request.app.state.model_manager, 'environment') else "unknown",
        active_model=status.get("active_model", "unknown"),
        model_timeout_seconds=status.get("timeout_seconds", 60),
        seconds_until_swap=status.get("seconds_until_swap"),
        models=status.get("models", {}),
        telemetry=telemetry_status,
        memory=memory_status
    )


@router.get("/models")
async def get_model_status(request: Request):
    """Get detailed model status."""
    model_manager = request.app.state.model_manager
    return await model_manager.get_status()


@router.post("/models/swap")
async def force_model_swap(request: Request, target_model: str):
    """Force swap to a specific model (for testing)."""
    model_manager = request.app.state.model_manager
    await model_manager.ensure_model(target_model)
    return {"status": "swapped", "model": target_model}
```

---

## 6. Agent Framework

### 6.1 Base Agent Class

```python
# src/agents/base.py
"""
Base agent class for LLM interactions.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import httpx
from loguru import logger


class AgentResponse(BaseModel):
    """Standard response from an agent."""
    content: str
    thinking: Optional[str] = None
    confidence: Optional[float] = None
    model_used: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        model_manager,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.model_manager = model_manager
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(timeout=120.0)
    
    @abstractmethod
    async def generate(self, **kwargs) -> AgentResponse:
        """Generate a response. Must be implemented by subclasses."""
        pass
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a call to the LLM via OpenAI-compatible API.
        """
        # Ensure correct model is loaded
        await self.model_manager.ensure_model(self.model_name)
        
        # Build request
        api_base = self.model_manager.api_base
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        try:
            response = await self.client.post(
                f"{api_base}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"LLM API error: {e}")
            raise
    
    def _extract_thinking(self, content: str) -> tuple[str, Optional[str]]:
        """
        Extract thinking process from response if present.
        Returns (clean_content, thinking)
        """
        if "<think>" in content and "</think>" in content:
            import re
            think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
            if think_match:
                thinking = think_match.group(1).strip()
                clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                return clean, thinking
        
        return content, None
```

### 6.2 Model Manager

```python
# src/agents/model_router.py
"""
Model Router for Dual-Model Architecture.
Routes requests to always-loaded Fast (4B) or Reasoning (14B) agents.
No hot-swapping needed - both models run simultaneously on 24GB VRAM.
"""

import asyncio
from typing import Optional, Dict, Any
import httpx
from loguru import logger


class ModelRouter:
    """
    Routes LLM requests to appropriate always-loaded model endpoints.
    
    Architecture: Qwen3-4B + Qwen3-14B running simultaneously on 24GB VRAM.
    - Port 8081: Fast Agent (Qwen3-4B Q4_K_M) - Annotation, anomaly detection
    - Port 8082: Reasoning Agent (Qwen3-14B Q4_K_M) - RCA, chat, remediation
    
    Benefits over hot-swap:
    - Zero latency model switching
    - Simpler codebase (no timeout management)
    - Both models always ready for requests
    """
    
    def __init__(
        self,
        fast_agent_url: str = "http://localhost:8081",
        reasoning_agent_url: str = "http://localhost:8082",
        timeout: float = 30.0
    ):
        self.fast_agent_url = fast_agent_url
        self.reasoning_agent_url = reasoning_agent_url
        
        # Separate clients for each endpoint
        self._fast_client = httpx.AsyncClient(
            base_url=fast_agent_url,
            timeout=timeout
        )
        self._reasoning_client = httpx.AsyncClient(
            base_url=reasoning_agent_url,
            timeout=timeout
        )
        
        # Request counters for observability
        self._request_counts = {
            "fast": 0,
            "reasoning": 0
        }
    
    async def initialize(self):
        """Initialize router and verify both endpoints are healthy."""
        logger.info("Initializing dual-model router...")
        
        # Check fast agent
        try:
            response = await self._fast_client.get("/health")
            if response.status_code == 200:
                logger.info("✓ Fast Agent (Qwen3-4B) is healthy")
            else:
                logger.warning(f"Fast Agent health check returned {response.status_code}")
        except Exception as e:
            logger.error(f"Fast Agent not reachable: {e}")
            raise RuntimeError(f"Fast Agent unavailable: {e}")
        
        # Check reasoning agent
        try:
            response = await self._reasoning_client.get("/health")
            if response.status_code == 200:
                logger.info("✓ Reasoning Agent (Qwen3-14B) is healthy")
            else:
                logger.warning(f"Reasoning Agent health check returned {response.status_code}")
        except Exception as e:
            logger.error(f"Reasoning Agent not reachable: {e}")
            raise RuntimeError(f"Reasoning Agent unavailable: {e}")
        
        logger.info("Dual-model router initialized successfully")
    
    async def shutdown(self):
        """Close HTTP clients."""
        await self._fast_client.aclose()
        await self._reasoning_client.aclose()
    
    def get_fast_client(self) -> httpx.AsyncClient:
        """Get client for fast agent requests."""
        return self._fast_client
    
    def get_reasoning_client(self) -> httpx.AsyncClient:
        """Get client for reasoning agent requests."""
        return self._reasoning_client
    
    async def fast_completion(
        self,
        messages: list,
        max_tokens: int = 512,
        temperature: float = 0.1,
        **kwargs
    ) -> dict:
        """
        Send completion request to Fast Agent (Qwen3-4B).
        Use for: Telemetry annotation, anomaly classification, quick scoring.
        """
        self._request_counts["fast"] += 1
        
        payload = {
            "model": "fast-agent",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        response = await self._fast_client.post(
            "/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def reasoning_completion(
        self,
        messages: list,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        **kwargs
    ) -> dict:
        """
        Send completion request to Reasoning Agent (Qwen3-14B).
        Use for: Root cause analysis, remediation planning, chat interactions.
        """
        self._request_counts["reasoning"] += 1
        
        payload = {
            "model": "reasoning-agent",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        response = await self._reasoning_client.post(
            "/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of both model endpoints."""
        fast_healthy = False
        reasoning_healthy = False
        
        try:
            response = await self._fast_client.get("/health")
            fast_healthy = response.status_code == 200
        except:
            pass
        
        try:
            response = await self._reasoning_client.get("/health")
            reasoning_healthy = response.status_code == 200
        except:
            pass
        
        return {
            "status": "healthy" if (fast_healthy and reasoning_healthy) else "degraded",
            "architecture": "simultaneous_dual_model",
            "vram_allocation": "~15GB / 24GB",
            "models": {
                "fast_agent": {
                    "model": "Qwen3-4B Q4_K_M",
                    "url": self.fast_agent_url,
                    "port": 8081,
                    "healthy": fast_healthy,
                    "purpose": "annotation, anomaly_detection",
                    "request_count": self._request_counts["fast"]
                },
                "reasoning_agent": {
                    "model": "Qwen3-14B Q4_K_M",
                    "url": self.reasoning_agent_url,
                    "port": 8082,
                    "healthy": reasoning_healthy,
                    "purpose": "rca, chat, remediation",
                    "request_count": self._request_counts["reasoning"]
                }
            }
        }


# Backward compatibility alias
ModelManager = ModelRouter
```

### 6.3 Fast Annotator Agent

```python
# src/agents/fast_annotator.py
"""
Fast Annotator Agent using Qwen3-4B (Q4_K_M quantization).
Handles telemetry annotation, anomaly detection, and confidence scoring.
Always loaded on port 8081 for instant response (<50ms latency).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from src.agents.base import BaseAgent, AgentResponse
from src.agents.prompts.annotation import AnnotationPromptBuilder


class AnnotationResult(BaseModel):
    """Result of telemetry annotation."""
    anomaly_detected: bool
    anomaly_type: Optional[str]
    severity: str  # "critical", "warning", "info"
    affected_services: List[str]
    confidence: float
    summary: str
    requires_reasoning: bool
    recommended_actions: List[str]
    raw_analysis: str


class FastAnnotator(BaseAgent):
    """
    Fast annotation agent for telemetry processing.
    
    Responsibilities:
    - Detect anomalies in telemetry data
    - Classify severity
    - Calculate confidence score
    - Decide if reasoning agent is needed
    """
    
    def __init__(self, model_manager):
        super().__init__(
            model_manager=model_manager,
            model_name="fast-agent",
            temperature=0.3,  # Lower temperature for consistent analysis
            max_tokens=1024
        )
        self.prompt_builder = AnnotationPromptBuilder()
    
    async def generate(
        self,
        telemetry_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AnnotationResult:
        """
        Analyze telemetry data and generate annotation.
        
        Args:
            telemetry_data: Dictionary containing logs, metrics, traces
            context: Optional context about the system state
            
        Returns:
            AnnotationResult with analysis details
        """
        start_time = datetime.utcnow()
        
        # Build prompt
        messages = self.prompt_builder.build(telemetry_data, context)
        
        # Call LLM
        response = await self._call_llm(messages)
        
        # Parse response
        content = response["choices"][0]["message"]["content"]
        
        # Extract structured data
        result = self._parse_annotation(content)
        
        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return result
    
    def _parse_annotation(self, content: str) -> AnnotationResult:
        """Parse LLM response into structured annotation."""
        
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
                data = json.loads(json_str)
            elif "{" in content:
                # Try to find JSON object
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found")
            else:
                raise ValueError("No JSON found")
            
            return AnnotationResult(
                anomaly_detected=data.get("anomaly_detected", False),
                anomaly_type=data.get("anomaly_type"),
                severity=data.get("severity", "info"),
                affected_services=data.get("affected_services", []),
                confidence=float(data.get("confidence", 0.5)),
                summary=data.get("summary", ""),
                requires_reasoning=data.get("requires_reasoning", False),
                recommended_actions=data.get("recommended_actions", []),
                raw_analysis=content
            )
            
        except Exception as e:
            # Fallback: create result from unstructured content
            return AnnotationResult(
                anomaly_detected="anomaly" in content.lower(),
                anomaly_type=None,
                severity="warning",
                affected_services=[],
                confidence=0.5,
                summary=content[:200],
                requires_reasoning=True,  # Default to needing reasoning
                recommended_actions=[],
                raw_analysis=content
            )
```

### 6.4 Reasoning Agent

```python
# src/agents/reasoning_agent.py
"""
Reasoning Agent using Qwen3-14B.
Handles complex RCA and human chat interactions.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import re

from src.agents.base import BaseAgent, AgentResponse
from src.agents.prompts.rca import RCAPromptBuilder
from src.agents.prompts.chat import ChatPromptBuilder


class ReasoningMode(str, Enum):
    RCA = "rca"
    CHAT = "chat"


class ThinkingModeDetector:
    """
    Determines whether to enable thinking mode based on query complexity.
    """
    
    COMPLEX_PATTERNS = [
        r"root cause",
        r"why.*fail",
        r"cascade",
        r"correlat",
        r"multiple.*service",
        r"dependency",
        r"explain.*step",
        r"how.*work",
        r"what.*happen.*if",
        r"compare",
        r"trade.?off",
        r"plan",
        r"strategy",
        r"recommend.*approach",
        r"best.*way",
        r"debug",
        r"troubleshoot",
        r"analyze",
    ]
    
    SIMPLE_PATTERNS = [
        r"^(what|who|when|where)\s+is\b",
        r"^status",
        r"^list",
        r"^show",
        r"^restart",
        r"^current",
        r"^check",
    ]
    
    @classmethod
    def should_think(
        cls,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Determine if thinking mode should be enabled."""
        
        query_lower = query.lower()
        
        # Explicit override
        if "/think" in query:
            return True
        if "/no_think" in query:
            return False
        
        # Check simple patterns first
        for pattern in cls.SIMPLE_PATTERNS:
            if re.search(pattern, query_lower):
                return False
        
        # Check complex patterns
        for pattern in cls.COMPLEX_PATTERNS:
            if re.search(pattern, query_lower):
                return True
        
        # Context-based decision
        if context:
            if context.get("affected_services", 0) > 3:
                return True
            if context.get("incident_severity") == "critical":
                return True
        
        # Default: no thinking for faster response
        return False


class ReasoningAgent(BaseAgent):
    """
    Reasoning agent for complex analysis and human chat.
    
    Supports two modes:
    - RCA: Root cause analysis triggered by fast annotator
    - Chat: Human conversation interface
    
    Features:
    - Automatic thinking mode toggle based on complexity
    - Context-aware responses
    - Structured output for RCA mode
    """
    
    def __init__(
        self,
        model_manager,
        mode: ReasoningMode = ReasoningMode.CHAT
    ):
        super().__init__(
            model_manager=model_manager,
            model_name="reasoning-agent",
            temperature=0.7,
            max_tokens=4096
        )
        self.mode = mode
        self.rca_prompt_builder = RCAPromptBuilder()
        self.chat_prompt_builder = ChatPromptBuilder()
        self.thinking_detector = ThinkingModeDetector()
    
    async def generate(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        enable_thinking: Optional[bool] = None,
        telemetry_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Generate a response based on mode.
        
        Args:
            message: User message or RCA request
            context: Conversation history for chat mode
            enable_thinking: Override automatic thinking detection
            telemetry_context: Telemetry data for RCA mode
            
        Returns:
            AgentResponse with content and optional thinking
        """
        from datetime import datetime
        start_time = datetime.utcnow()
        
        # Determine thinking mode
        if enable_thinking is None:
            enable_thinking = self.thinking_detector.should_think(
                message,
                telemetry_context
            )
        
        # Build messages based on mode
        if self.mode == ReasoningMode.RCA:
            messages = self.rca_prompt_builder.build(
                annotation_summary=message,
                telemetry_data=telemetry_context,
                enable_thinking=enable_thinking
            )
        else:
            messages = self.chat_prompt_builder.build(
                user_message=message,
                conversation_history=context or [],
                enable_thinking=enable_thinking
            )
        
        # Call LLM
        response = await self._call_llm(messages)
        
        # Extract content
        content = response["choices"][0]["message"]["content"]
        
        # Parse thinking if present
        clean_content, thinking = self._extract_thinking(content)
        
        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AgentResponse(
            content=clean_content,
            thinking=thinking,
            model_used="reasoning-agent",
            latency_ms=latency_ms
        )
```

### 6.5 Prompt Templates

```python
# src/agents/prompts/annotation.py
"""
Prompt templates for Fast Annotator.
"""

from typing import Dict, Any, List, Optional
import json


class AnnotationPromptBuilder:
    """Builds prompts for telemetry annotation."""
    
    SYSTEM_PROMPT = """You are a fast telemetry annotation agent for infrastructure monitoring.
Your job is to quickly analyze incoming telemetry data and:
1. Detect anomalies
2. Classify severity (critical, warning, info)
3. Identify affected services
4. Calculate confidence score (0.0-1.0)
5. Decide if complex reasoning is needed

Respond in JSON format:
```json
{
    "anomaly_detected": true/false,
    "anomaly_type": "string or null",
    "severity": "critical/warning/info",
    "affected_services": ["service1", "service2"],
    "confidence": 0.0-1.0,
    "summary": "Brief description",
    "requires_reasoning": true/false,
    "recommended_actions": ["action1", "action2"]
}
```

Rules:
- Be concise and fast
- Set requires_reasoning=true if:
  - Multiple services affected
  - Root cause unclear
  - Confidence < 0.7
  - Cascade failure suspected
- Set confidence based on data quality and pattern clarity"""

    def build(
        self,
        telemetry_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Build annotation prompt messages."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # Add context if available
        if context:
            messages.append({
                "role": "system",
                "content": f"Current system context:\n{json.dumps(context, indent=2)}"
            })
        
        # Add telemetry data
        user_content = f"""Analyze this telemetry data:

LOGS:
{json.dumps(telemetry_data.get('logs', [])[:10], indent=2)}

METRICS:
{json.dumps(telemetry_data.get('metrics', {}), indent=2)}

TRACES:
{json.dumps(telemetry_data.get('traces', [])[:5], indent=2)}

Provide your analysis in JSON format."""
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
```

```python
# src/agents/prompts/chat.py
"""
Prompt templates for Human Chat.
"""

from typing import Dict, Any, List


class ChatPromptBuilder:
    """Builds prompts for human chat interactions."""
    
    SYSTEM_PROMPT = """You are an AI operations assistant for infrastructure management.
You help operators understand system state, investigate incidents, and make informed decisions.

Your capabilities:
- Explain infrastructure concepts
- Analyze incidents and suggest solutions
- Answer questions about system state
- Guide troubleshooting processes
- Provide recommendations based on best practices

Guidelines:
- Be clear and concise
- Explain technical concepts when needed
- Ask clarifying questions if the request is ambiguous
- Recommend safe, reversible actions
- Highlight risks and trade-offs

When thinking mode is enabled (/think), show your reasoning process.
When thinking mode is disabled (/no_think), respond directly."""

    def build(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        enable_thinking: bool = False,
        system_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Build chat prompt messages."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # Add system state context if available
        if system_state:
            import json
            messages.append({
                "role": "system",
                "content": f"Current system state:\n{json.dumps(system_state, indent=2)}"
            })
        
        # Add conversation history
        for msg in conversation_history[-20:]:  # Last 20 messages
            messages.append(msg)
        
        # Add thinking directive
        if enable_thinking:
            user_message = f"/think\n{user_message}"
        else:
            user_message = f"/no_think\n{user_message}"
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
```

```python
# src/agents/prompts/rca.py
"""
Prompt templates for Root Cause Analysis.
"""

from typing import Dict, Any, List, Optional
import json


class RCAPromptBuilder:
    """Builds prompts for root cause analysis."""
    
    SYSTEM_PROMPT = """You are an expert root cause analysis agent for infrastructure incidents.
Your job is to:
1. Analyze anomaly annotations from the fast agent
2. Correlate with telemetry data
3. Identify root cause
4. Recommend remediation actions
5. Assess confidence in analysis

You must follow Constitutional AI principles:
- SAFETY: Never recommend actions that could cause data loss or cascade failures
- EVIDENCE: Base conclusions on telemetry data, not assumptions
- MINIMAL: Recommend smallest effective intervention
- REVERSIBLE: Prefer actions that can be rolled back

Output format:
```json
{
    "root_cause": {
        "summary": "Brief description",
        "details": "Detailed analysis",
        "confidence": 0.0-1.0
    },
    "contributing_factors": ["factor1", "factor2"],
    "affected_services": ["service1", "service2"],
    "recommended_actions": [
        {
            "action": "action description",
            "priority": 1-5,
            "risk": "low/medium/high",
            "reversible": true/false
        }
    ],
    "requires_human_approval": true/false
}
```"""

    def build(
        self,
        annotation_summary: str,
        telemetry_data: Optional[Dict[str, Any]] = None,
        enable_thinking: bool = True
    ) -> List[Dict[str, str]]:
        """Build RCA prompt messages."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # Build user message
        user_content = f"""Perform root cause analysis for this incident:

ANNOTATION SUMMARY:
{annotation_summary}
"""
        
        if telemetry_data:
            user_content += f"""
TELEMETRY DATA:
{json.dumps(telemetry_data, indent=2)}
"""
        
        # Add thinking directive
        if enable_thinking:
            user_content = f"/think\n{user_content}"
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
```

---

*Continued in Part 3...*
