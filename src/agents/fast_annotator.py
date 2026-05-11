"""
Constitutional AIOps - Fast Annotator Agent

High-throughput telemetry annotation agent using Qwen3-4B Q4_K_M.
Always loaded on port 8081 (TTL: -1, never unload).

Responsibilities:
- Anomaly detection in logs, metrics, traces
- Alert classification (severity, category)
- Confidence scoring for routing decisions
- Token compression for downstream processing

Performance Targets (from Research_V7.tex):
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

# =============================================================================
# Entity Canonicalization (v0.6.0 - Prevent entity proliferation)
# =============================================================================
# Maps entity variants to canonical forms to reduce node count in graph
# Without this, LLM creates: "api-gateway", "api_gateway", "ApiGateway", "API Gateway" → 4 nodes
# With this: All map to "api_gateway" → 1 node

ENTITY_CANONICALIZATION: dict[str, list[str]] = {
    # Infrastructure services
    "api_gateway": ["api-gateway", "apigateway", "api gateway", "gateway", "apigw"],
    "database": ["db", "postgres", "postgresql", "mysql", "mongodb", "redis_db", "data_store"],
    "cache": ["redis", "memcached", "cache_service", "caching", "redis_cache"],
    "load_balancer": ["lb", "load-balancer", "loadbalancer", "nginx", "haproxy", "elb", "alb"],
    "message_queue": ["mq", "rabbitmq", "kafka", "sqs", "message_broker", "queue", "pubsub"],

    # Error types
    "connection_timeout": ["timeout", "conn_timeout", "request_timeout", "gateway_timeout", "504"],
    "memory_error": ["oom", "out_of_memory", "oom_error", "memory_exhausted", "heap_overflow"],
    "cpu_error": ["cpu_throttle", "cpu_high", "high_cpu", "cpu_saturation"],
    "disk_error": ["disk_full", "disk_space", "no_space", "storage_full", "enospc"],
    "rate_limit": ["throttle", "rate_limited", "429", "too_many_requests"],

    # Common services
    "backend": ["backend_service", "api_server", "app_server", "application"],
    "frontend": ["frontend_service", "web_server", "ui", "client"],
    "auth_service": ["auth", "authentication", "authorization", "oauth", "identity"],
    "payment_service": ["payment", "payments", "billing", "checkout"],
    "notification_service": ["notification", "notifications", "alerting", "email_service"],

    # Observability
    "prometheus": ["prom", "prometheus_server", "metrics_server"],
    "grafana": ["graf", "grafana_server", "dashboard"],
    "loki": ["loki_server", "log_aggregator"],

    # Actions
    "restart": ["restart_service", "restart_pod", "service_restart", "pod_restart"],
    "scale": ["scale_up", "scale_down", "scale_replicas", "horizontal_scale", "autoscale"],
    "rollback": ["rollback_deployment", "revert", "undo_deployment"],
}


def canonicalize_entity(name: str) -> str:
    """
    Map entity variants to canonical form.

    This reduces entity node proliferation in the graph by mapping
    common variants to a single canonical name.

    Args:
        name: Raw entity name from LLM extraction

    Returns:
        Canonical entity name (lowercase, underscores)

    Examples:
        "API Gateway" → "api_gateway"
        "Redis" → "cache"
        "connection timeout" → "connection_timeout"
        "my_custom_service" → "my_custom_service" (unchanged)
    """
    # Normalize: lowercase, replace hyphens/spaces with underscores
    name_lower = name.lower().strip().replace("-", "_").replace(" ", "_")

    # Remove consecutive underscores
    while "__" in name_lower:
        name_lower = name_lower.replace("__", "_")

    # Strip leading/trailing underscores
    name_lower = name_lower.strip("_")

    # Check if it matches a canonical form or any variant
    for canonical, variants in ENTITY_CANONICALIZATION.items():
        if name_lower == canonical or name_lower in variants:
            return canonical

    # Not found - return normalized name as-is
    return name_lower


# System prompt for fast annotation
# Using qwen3:4b-instruct (no thinking mode) - no /no_think prefix needed
FAST_ANNOTATOR_SYSTEM_PROMPT = """You are a fast telemetry annotator for an AIOps system.

Your job is to quickly analyze telemetry data (logs, metrics, traces) and:
1. Detect anomalies or issues
2. Classify the severity (critical, warning, info)
3. Categorize the issue type (performance, error, security, resource)
4. Provide a confidence score (0.0-1.0)
5. Decide if deeper analysis is needed
6. Extract semantic triplets: relationships between entities found in the telemetry

IMPORTANT: You MUST respond with ONLY valid JSON, no additional text or explanation.

{
    "anomaly_detected": true,
    "severity": "critical",
    "category": "error",
    "confidence": 0.85,
    "summary": "Brief description of the issue",
    "needs_reasoning": false,
    "key_indicators": ["indicator1", "indicator2"],
    "triplets": [
        {"subject": "entity1", "relation": "VERB_PHRASE", "object": "entity2"}
    ]
}

TRIPLET EXTRACTION RULES:
- Extract meaningful relationships from the telemetry data
- subject/object: service names, components, resources (e.g., "backend", "database", "memory")
- relation: action verbs in UPPER_CASE (e.g., "EXPERIENCED", "CAUSED", "AFFECTED", "CONNECTED_TO", "DEPENDS_ON", "TRIGGERED", "RESOLVED", "DEGRADED")
- Examples:
  - {"subject": "backend", "relation": "EXPERIENCED", "object": "high_latency"}
  - {"subject": "memory_leak", "relation": "CAUSED", "object": "oom_error"}
  - {"subject": "database", "relation": "AFFECTED", "object": "api_gateway"}
  - {"subject": "prometheus", "relation": "MONITORS", "object": "backend"}
- Extract 1-5 triplets per analysis

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
            # Using qwen3:4b-instruct (no thinking mode) - 2048 tokens is sufficient
            # for direct JSON annotation output without chain-of-thought overhead.
            response = await self.model_router.fast_completion(
                prompt=prompt,
                max_tokens=2048,  # No thinking overhead with instruct model
                temperature=0.0,  # Deterministic classification (greedy decoding)
                system_prompt=self.get_system_prompt(),  # Include system prompt for context
            )

            # Parse response - ModelRouter already fixes thinking mode
            # (moves reasoning to content when content is empty)
            message = response["choices"][0]["message"]
            content = message.get("content", "")
            annotation = self._parse_annotation(content)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Build agent response
            confidence = annotation.get("confidence", 0.5)

            # Extract and validate triplets (Phase 2: Semantic triplet extraction)
            # Uses canonicalize_entity() to map variants to canonical forms
            raw_triplets = annotation.get("triplets", [])
            validated_triplets = []
            for triplet in raw_triplets:
                if isinstance(triplet, dict) and all(k in triplet for k in ["subject", "relation", "object"]):
                    # Canonicalize entities to prevent node proliferation
                    # e.g., "API Gateway", "api-gateway", "apigateway" all → "api_gateway"
                    validated_triplets.append({
                        "subject": canonicalize_entity(str(triplet["subject"])),
                        "relation": str(triplet["relation"]).upper().replace(" ", "_").replace("-", "_"),
                        "object": canonicalize_entity(str(triplet["object"])),
                    })

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
                    "triplets": validated_triplets,  # Phase 2: Include semantic triplets
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
        """Parse JSON annotation from model response.

        Handles Qwen3 thinking mode where chain-of-thought text precedes
        the actual JSON. Searches for the JSON object that contains
        expected annotation keys (anomaly_detected, severity) rather than
        just the first '{' which may be a small object from thinking.
        """
        try:
            # Strip whitespace first
            content = content.strip()

            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Try direct parse first (works when content is clean JSON)
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

            # Find ALL complete JSON objects by brace-matching, then pick the best
            # This handles Qwen3 thinking mode where content contains
            # chain-of-thought text with small JSON objects (triplet examples)
            # before the actual annotation JSON.
            candidates = []
            search_start = 0
            while search_start < len(content):
                start_idx = content.find('{', search_start)
                if start_idx == -1:
                    break
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
                if brace_count == 0:
                    json_str = content[start_idx:end_idx + 1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            candidates.append(parsed)
                    except json.JSONDecodeError:
                        pass
                search_start = end_idx + 1 if brace_count == 0 else start_idx + 1

            if candidates:
                # Prefer the candidate with annotation keys
                for c in candidates:
                    if "anomaly_detected" in c and "severity" in c:
                        return c
                # Fallback: return the largest candidate (most complete)
                return max(candidates, key=lambda c: len(c))

            # No JSON found at all
            self.logger.warning(f"No JSON object found in content ({len(content)} chars)")
            return {
                "anomaly_detected": False,
                "severity": "info",
                "category": "unknown",
                "confidence": 0.3,
                "summary": content[:200] if content else "Parse error",
                "needs_reasoning": True,
            }

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
