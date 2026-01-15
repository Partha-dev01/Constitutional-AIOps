"""
Constitutional AIOps - Fast Annotator Agent

High-throughput telemetry annotation agent using Qwen3-4B Q4_K_M.
Always loaded on port 8081 (TTL: -1, never unload).

Responsibilities:
- Anomaly detection in logs, metrics, traces
- Alert classification (severity, category)
- Confidence scoring for routing decisions
- Token compression for downstream processing

Performance Targets (from Research_V6.tex):
- Latency: <100ms P95
- Context: 8K tokens
- Throughput: High (batch processing capable)
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Optional

from src.agents.base_agent import AgentResponse, AgentRole, BaseAgent
from src.agents.model_router import ModelRouter

logger = logging.getLogger(__name__)

# Maximum activity log entries to keep (prevent memory growth)
MAX_ACTIVITY_LOG_SIZE = 50


# System prompt for fast annotation
# /no_think disables Qwen3 thinking mode for faster, direct responses
FAST_ANNOTATOR_SYSTEM_PROMPT = """/no_think
You are a fast telemetry annotator for an AIOps system.

Your job is to quickly analyze telemetry data (logs, metrics, traces) and:
1. Detect anomalies or issues
2. Classify the severity (critical, warning, info)
3. Categorize the issue type (performance, error, security, resource)
4. Provide a confidence score (0.0-1.0)
5. Decide if deeper analysis is needed

IMPORTANT: You MUST respond with ONLY valid JSON, no additional text or explanation.

{
    "anomaly_detected": true,
    "severity": "critical",
    "category": "error",
    "confidence": 0.85,
    "summary": "Brief description of the issue",
    "needs_reasoning": false,
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

        # Activity logging for API visibility
        self.activity_log: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_latency_ms": 0.0,
            "requests_per_minute": 0.0,
            "_latency_sum": 0.0,
            "_first_request_time": None,
        }
    
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
        telemetry_type = input_data.get("telemetry_type", "unknown")
        input_content = input_data.get("content", "")

        # Track timing for activity logging
        start_time = time.perf_counter()

        try:
            # Get completion from fast agent with system prompt for JSON format
            # Qwen3 uses thinking mode which consumes tokens, so we need more
            # Fast Agent has 8K context per CLAUDE.md spec
            response = await self.model_router.fast_completion(
                prompt=prompt,
                max_tokens=2048,  # Qwen3 thinking overhead needs more tokens
                temperature=0.0,  # Deterministic classification (greedy decoding)
                system_prompt=self.get_system_prompt(),  # Include system prompt for context
            )

            # Parse response - Qwen3 may put content in reasoning field if thinking mode is on
            message = response["choices"][0]["message"]
            content = message.get("content", "")

            # If content is empty, try to extract from reasoning field (Qwen3 thinking mode)
            if not content and "reasoning" in message:
                reasoning = message["reasoning"]
                # Look for JSON in the reasoning output
                if "{" in reasoning:
                    start_idx = reasoning.find("{")
                    end_idx = reasoning.rfind("}")
                    if end_idx > start_idx:
                        content = reasoning[start_idx:end_idx + 1]
                        self.logger.info(f"Extracted JSON from Qwen3 reasoning field")
            annotation = self._parse_annotation(content)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Build agent response
            confidence = annotation.get("confidence", 0.5)
            result = AgentResponse(
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

            # Log successful activity
            self._log_activity(
                activity_type=f"annotation:{telemetry_type}",
                input_text=input_content,
                output_text=content,
                latency_ms=latency_ms,
                status="success",
            )

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Fast annotation failed: {e}")

            # Log failed activity
            self._log_activity(
                activity_type=f"annotation:{telemetry_type}",
                input_text=input_content,
                output_text=str(e),
                latency_ms=latency_ms,
                status="error",
            )

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
            # Strip whitespace first
            content = content.strip()

            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Find the first complete JSON object by counting braces
            start_idx = content.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(content[start_idx:], start=start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break
                content = content[start_idx:end_idx + 1]

            return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse annotation JSON: {content[:100]}... Error: {e}")
            return {
                "anomaly_detected": False,
                "severity": "info",
                "category": "unknown",
                "confidence": 0.3,
                "summary": content[:200] if content else "Parse error",
                "needs_reasoning": True,
            }

    def _log_activity(
        self,
        activity_type: str,
        input_text: str,
        output_text: str,
        latency_ms: float,
        status: str = "success",
    ) -> None:
        """
        Log an activity entry for API visibility.

        Args:
            activity_type: Type of activity (annotation:log, annotation:metric, etc.)
            input_text: Input telemetry data
            output_text: Output response
            latency_ms: Request latency in milliseconds
            status: Status of the request (success/error)
        """
        # Create activity entry
        entry = {
            "timestamp": datetime.utcnow(),
            "type": activity_type,
            "input": input_text[:500] if input_text else "",  # Truncate for storage
            "output": output_text[:1000] if output_text else "",
            "latency_ms": round(latency_ms, 2),
            "status": status,
        }

        # Add to log (maintain max size)
        self.activity_log.append(entry)
        if len(self.activity_log) > MAX_ACTIVITY_LOG_SIZE:
            self.activity_log = self.activity_log[-MAX_ACTIVITY_LOG_SIZE:]

        # Update stats
        self.stats["total_requests"] += 1
        if status == "success":
            self.stats["success_count"] += 1
        else:
            self.stats["error_count"] += 1

        self.stats["_latency_sum"] += latency_ms
        self.stats["avg_latency_ms"] = (
            self.stats["_latency_sum"] / self.stats["total_requests"]
        )

        # Calculate requests per minute
        if self.stats["_first_request_time"] is None:
            self.stats["_first_request_time"] = datetime.utcnow()
        else:
            elapsed = (datetime.utcnow() - self.stats["_first_request_time"]).total_seconds()
            if elapsed > 0:
                self.stats["requests_per_minute"] = (
                    self.stats["total_requests"] / elapsed * 60
                )


__all__ = ["FastAnnotator", "FAST_ANNOTATOR_SYSTEM_PROMPT"]
