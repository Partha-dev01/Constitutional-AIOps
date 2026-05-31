"""
Constitutional AIOps - Chat API Schemas

Pydantic models for chat endpoints.
Supports interactive conversation with the Reasoning Agent (Qwen3-14B).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message."""
    role: ChatRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What caused the spike in CPU usage on prod-api-1?",
                "timestamp": "2025-12-14T10:30:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Continue existing conversation")
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional context (incident data, telemetry, etc.)"
    )
    enable_thinking: bool = Field(
        default=False,
        description="Enable extended thinking mode for complex queries"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Why is the payment service returning 503 errors?",
                "conversation_id": "conv-123",
                "context": {"service": "payment-service", "error_rate": 0.15},
                "enable_thinking": True
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    conversation_id: str = Field(..., description="Conversation identifier")
    message: ChatMessage = Field(..., description="Assistant's response")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Confidence in response; null when the agent declines an off-domain request",
    )
    suggested_actions: Optional[list[str]] = Field(
        default=None,
        description="Suggested follow-up actions"
    )
    related_incidents: Optional[list[str]] = Field(
        default=None,
        description="Related incident IDs from memory"
    )
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-123",
                "message": {
                    "role": "assistant",
                    "content": "The payment service is returning 503 errors due to...",
                    "timestamp": "2025-12-14T10:30:05Z"
                },
                "confidence": 0.85,
                "suggested_actions": ["Scale up payment-service", "Check database connections"],
                "related_incidents": ["INC-2024-001", "INC-2024-012"]
            }
        }


class ConversationHistory(BaseModel):
    """Full conversation history."""
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage]
    context: Optional[dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-123",
                "created_at": "2025-12-14T10:00:00Z",
                "updated_at": "2025-12-14T10:30:05Z",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hello! How can I help?"}
                ]
            }
        }


class AnalysisRequest(BaseModel):
    """Request for RCA or planning analysis."""
    mode: str = Field(
        ...,
        pattern="^(rca|planning)$",
        description="Analysis mode: 'rca' or 'planning'"
    )
    incident_id: Optional[str] = Field(None, description="Incident to analyze")
    data: dict[str, Any] = Field(..., description="Analysis input data")
    enable_thinking: bool = Field(default=True, description="Enable extended thinking")

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "rca",
                "incident_id": "INC-2024-042",
                "data": {
                    "symptoms": ["High latency", "Connection timeouts"],
                    "affected_services": ["api-gateway", "user-service"],
                    "start_time": "2025-12-14T09:00:00Z"
                },
                "enable_thinking": True
            }
        }


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""
    analysis_id: str
    mode: str
    result: dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    requires_approval: bool = Field(
        default=False,
        description="Whether suggested actions require human approval"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "ana-456",
                "mode": "rca",
                "result": {
                    "root_cause": "Database connection pool exhaustion",
                    "confidence": 0.87,
                    "remediation_steps": [
                        {"action": "Increase connection pool size", "risk": "low"}
                    ]
                },
                "confidence": 0.87,
                "processing_time_ms": 1250.5,
                "requires_approval": False
            }
        }


__all__ = [
    "ChatRole",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ConversationHistory",
    "AnalysisRequest",
    "AnalysisResponse",
]
