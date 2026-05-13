"""
Constitutional AIOps - Base Agent Class

Abstract base class for all LLM agents in the system.
Provides common interface for telemetry processing and decision making.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the system."""
    FAST_ANNOTATOR = "fast_annotator"
    REASONING = "reasoning"
    CHAT = "chat"


class ConfidenceLevel(Enum):
    """Confidence levels for agent decisions."""
    HIGH = "high"      # >90% - automatic action
    MEDIUM = "medium"  # 70-90% - requires approval
    LOW = "low"        # <70% - alert only


@dataclass
class AgentResponse:
    """Standard response format from agents."""
    content: str
    confidence: float
    confidence_level: ConfidenceLevel
    reasoning: Optional[str] = None  # JSON-parsed self-reported reasoning from model output
    reasoning_trace: Optional[str] = None  # Raw chain-of-thought from message.reasoning (Phase 4.0a, 2026-05-12)
    suggested_action: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    
    @property
    def requires_approval(self) -> bool:
        """Check if this response requires human approval."""
        return self.confidence_level == ConfidenceLevel.MEDIUM
    
    @property
    def is_automatic(self) -> bool:
        """Check if this response can trigger automatic action."""
        return self.confidence_level == ConfidenceLevel.HIGH


class BaseAgent(ABC):
    """
    Abstract base class for Constitutional AIOps agents.
    
    All agents must implement:
    - process(): Main processing method
    - get_system_prompt(): System prompt for the agent
    """
    
    def __init__(self, role: AgentRole):
        """
        Initialize the agent.
        
        Args:
            role: The role this agent plays in the system
        """
        self.role = role
        self.logger = logging.getLogger(f"{__name__}.{role.value}")
    
    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process input data and return a response.
        
        Args:
            input_data: Dictionary containing input to process
            
        Returns:
            AgentResponse with decision and confidence
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            System prompt string
        """
        pass
    
    def calculate_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Calculate confidence level from numeric confidence.
        
        Args:
            confidence: Numeric confidence score (0.0-1.0)
            
        Returns:
            ConfidenceLevel enum value
        """
        if confidence >= 0.90:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


__all__ = [
    "AgentRole",
    "ConfidenceLevel", 
    "AgentResponse",
    "BaseAgent",
]
