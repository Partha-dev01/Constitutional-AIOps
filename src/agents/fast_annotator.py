"""
Constitutional AIOps - Fast Annotator Agent

High-throughput telemetry annotation agent using Qwen3-4B Q4_K_M.
Always loaded on port 8081 (TTL: -1, never unload).

Responsibilities:
- Anomaly detection in logs, metrics, traces
- Alert classification (severity, category)
- Confidence scoring for routing decisions
- Token compression for downstream processing

Performance Targets:
- Latency: <50ms (p99)
- Context: 8K tokens
- Throughput: High (batch processing capable)
"""

import json
import logging
from typing import Any, Optional

from src.agents.base_agent import AgentResponse, AgentRole, BaseAgent
from src.agents.model_router import ModelRouter

logger = logging.getLogger(__name__)


# System prompt for fast annotation
FAST_ANNOTATOR_SYSTEM_PROMPT = """You are a fast telemetry annotator for an AIOps system.

Your job is to quickly analyze telemetry data (logs, metrics, traces) and:
1. Detect anomalies or issues
2. Classify the severity (critical, warning, info)
3. Categorize the issue type (performance, error, security, resource)
4. Provide a confidence score (0.0-1.0)
5. Decide if deeper analysis is needed

Respond in JSON format:
{
    "anomaly_detected": true/false,
    "severity": "critical|warning|info",
    "category": "performance|error|security|resource|unknown",
    "confidence": 0.0-1.0,
    "summary": "Brief description",
    "needs_reasoning": true/false,
    "key_indicators": ["indicator1", "indicator2"]
}

Be fast and decisive. When in doubt, set needs_reasoning=true.
"""


class FastAnnotator(BaseAgent):
    """
    Fast annotation agent for high-throughput telemetry processing.
    
    Uses Qwen3-4B Q4_K_M model running on port 8081.
    Optimized for speed over depth - complex issues are routed to reasoning agent.
    """
    
    def __init__(self, model_router: Optional[ModelRouter] = None):
        """
        Initialize the fast annotator.
        
        Args:
            model_router: ModelRouter instance (creates new if not provided)
        """
        super().__init__(AgentRole.FAST_ANNOTATOR)
        self.model_router = model_router or ModelRouter()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for fast annotation."""
        return FAST_ANNOTATOR_SYSTEM_PROMPT
    
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process telemetry data and return annotation.
        
        Args:
            input_data: Dictionary containing:
                - telemetry_type: "log" | "metric" | "trace"
                - content: The telemetry data to analyze
                - context: Optional additional context
                
        Returns:
            AgentResponse with classification and confidence
        """
        # Build prompt
        prompt = self._build_prompt(input_data)
        
        try:
            # Get completion from fast agent
            response = await self.model_router.fast_completion(
                prompt=prompt,
                max_tokens=512,
                temperature=0.1,  # Low temp for consistent classification
            )
            
            # Parse response
            content = response["choices"][0]["message"]["content"]
            annotation = self._parse_annotation(content)
            
            # Build agent response
            confidence = annotation.get("confidence", 0.5)
            return AgentResponse(
                content=annotation.get("summary", "Unknown"),
                confidence=confidence,
                confidence_level=self.calculate_confidence_level(confidence),
                reasoning=None,  # Fast agent doesn't provide detailed reasoning
                suggested_action="escalate" if annotation.get("needs_reasoning") else "monitor",
                metadata={
                    "anomaly_detected": annotation.get("anomaly_detected", False),
                    "severity": annotation.get("severity", "info"),
                    "category": annotation.get("category", "unknown"),
                    "key_indicators": annotation.get("key_indicators", []),
                    "needs_reasoning": annotation.get("needs_reasoning", False),
                },
            )
            
        except Exception as e:
            self.logger.error(f"Fast annotation failed: {e}")
            # Return safe default on error
            return AgentResponse(
                content=f"Annotation failed: {str(e)}",
                confidence=0.0,
                confidence_level=self.calculate_confidence_level(0.0),
                suggested_action="escalate",
                metadata={"error": str(e), "needs_reasoning": True},
            )
    
    def _build_prompt(self, input_data: dict[str, Any]) -> str:
        """Build prompt for the model."""
        telemetry_type = input_data.get("telemetry_type", "unknown")
        content = input_data.get("content", "")
        context = input_data.get("context", "")
        
        prompt = f"""Analyze this {telemetry_type} telemetry:

{content}

"""
        if context:
            prompt += f"Additional context: {context}\n"
        
        prompt += "\nProvide your analysis in JSON format."
        return prompt
    
    def _parse_annotation(self, content: str) -> dict[str, Any]:
        """Parse JSON annotation from model response."""
        try:
            # Try to extract JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse annotation JSON: {content[:100]}...")
            return {
                "anomaly_detected": False,
                "severity": "info",
                "category": "unknown",
                "confidence": 0.3,
                "summary": content[:200],
                "needs_reasoning": True,
            }


__all__ = ["FastAnnotator", "FAST_ANNOTATOR_SYSTEM_PROMPT"]
