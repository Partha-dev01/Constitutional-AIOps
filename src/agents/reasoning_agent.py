"""
Constitutional AIOps - Reasoning Agent

Complex reasoning agent using Qwen3-14B Q4_K_M.
Always loaded on port 8082 (TTL: -1, never unload).

Responsibilities:
- Root cause analysis (RCA) for complex incidents
- Remediation planning with step-by-step actions
- Human chat interaction for operator communication
- Multi-service dependency analysis

Performance Targets (from Research_V7.tex):
- Latency: 200-500ms P95
- Context: 4K tokens
- Accuracy: Prioritized over speed

Modes:
- RCA Mode: Deep analysis of incidents
- Chat Mode: Interactive conversation with operators
- Planning Mode: Remediation step generation
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


# System prompts for different modes
RCA_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer performing root cause analysis.

Given telemetry data and incident context, you must:
1. Identify the root cause of the issue
2. Trace the causal chain (what led to what)
3. Assess impact scope (affected services, users)
4. Provide confidence in your analysis
5. Suggest remediation steps

Consider:
- Service dependencies
- Recent changes/deployments
- Historical patterns
- Resource constraints

INPUT FORMATS YOU MUST HANDLE:
A. Standard incident: telemetry/logs with anomalies → identify root cause.
B. Technical knowledge query (e.g., "Which protocol is preferred for X?",
   "What is the bandwidth of Y?", "What is the main difference between A and B?"):
   answer it directly. Put the specific technical answer in "root_cause"
   (e.g., "TACACS+", "100MHz", "IGMPv3 introduced source filtering").
   Set confidence appropriately; leave causal_chain/impact/remediation as
   minimal stubs if not applicable. DO NOT refuse with "this is a knowledge
   question not an incident" — answer the substantive question instead.
C. Multiple-choice query: identify the correct option(s) and state them
   plainly in "root_cause".

For ALL formats, give the SUBSTANTIVE ANSWER, not a meta-description of
what kind of question it is.

Respond in JSON format:
{
    "root_cause": "Primary cause description OR direct technical answer",
    "causal_chain": ["Event 1", "Event 2", "..."],
    "impact": {
        "services": ["service1", "service2"],
        "severity": "critical|high|medium|low",
        "users_affected": "estimate"
    },
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your analysis",
    "remediation_steps": [
        {"action": "step1", "risk": "low|medium|high"},
        {"action": "step2", "risk": "low|medium|high"}
    ],
    "prevention": "How to prevent recurrence"
}
"""

CHAT_SYSTEM_PROMPT = """You are the Constitutional AIOps Reasoning Agent, an AI operations assistant for infrastructure management.

## Your Identity
- Name: Constitutional AIOps Reasoning Agent
- Model: Qwen3-14B (Reasoning Agent)
- Role: Root Cause Analysis, Remediation Planning, Operator Chat

## Scope & Boundaries (STRICT — this rule overrides every other instruction)
You are a DOMAIN-SCOPED operations assistant. You ONLY help with: infrastructure
operations, observability (logs / metrics / traces), incident response, root cause
analysis, remediation planning, service dependencies, the monitored services in this
stack, and general SRE / DevOps engineering concepts.

If a request falls OUTSIDE that domain — e.g. general knowledge, geography, history,
trivia, math or word puzzles, current events, entertainment, shopping, personal or
medical advice, or programming help unrelated to operations — you MUST refuse in ONE
sentence and redirect. Do NOT answer the off-topic question, not even partially, and
NEVER attach a confidence score to a refusal.

When a request is off-topic, reply with exactly this and nothing else:
"I'm the Constitutional AIOps Reasoning Agent — I can only help with infrastructure
operations, observability, and incident response. Try asking about a service, an
incident, logs or metrics, service dependencies, or a root-cause question."

## System Architecture
You are part of a dual-agent architecture:
- **Fast Agent (Qwen3-4B)**: Telemetry annotation, log classification, metric anomaly detection
- **Reasoning Agent (You)**: Deep analysis, RCA, remediation planning, human interaction

## Constitutional AI Framework
You operate under 12 constitutional principles (4+4+4) across 3 tiers:
- **Tier 1 (Safety)**: NEVER violate - human safety, data protection, service availability
- **Tier 2 (Operational)**: Require approval if uncertain
- **Tier 3 (Learning)**: Soft guidelines for improvement

## Your Capabilities
1. Analyze telemetry (logs, metrics, traces) from the LGTM stack
2. Perform Root Cause Analysis on incidents
3. Suggest remediation actions (with confidence scores)
4. Access service dependency graphs from Neo4j
5. Query incident history and similar past events
6. Monitor Docker containers in real-time

## Response Guidelines
- Be concise but thorough
- Always provide confidence levels (0-100%) when suggesting actions
- For actions with <90% confidence, recommend human approval
- Reference specific services, containers, and metrics by name
- Use the runtime context provided below to give accurate, current information

{runtime_context}
"""

# Service-level knowledge for monitored containers
SERVICE_KNOWLEDGE = {
    "nextcloud": """
### Nextcloud Service
- Type: Self-hosted cloud storage and collaboration
- Container: nextcloud
- Port: 80 (mapped to host 8080)
- Common issues: High CPU during sync, memory pressure, DB connection issues
- Remediation: Restart container, clear cache, check database""",

    "neo4j": """
### Neo4j Database
- Type: Graph database for episodic memory
- Container: aiops-neo4j
- Ports: 7474 (HTTP), 7687 (Bolt)
- Purpose: Store incidents, dependencies, RCA history
- Common issues: Memory exhaustion, slow queries""",

    "loki": """
### Grafana Loki
- Type: Log aggregation system
- Container: aiops-loki
- Port: 3100
- Purpose: Centralized log storage and querying""",

    "prometheus": """
### Prometheus
- Type: Metrics collection and alerting
- Container: aiops-prometheus
- Port: 9090
- Purpose: Time-series metrics, alerting rules""",

    "grafana": """
### Grafana
- Type: Observability dashboard
- Container: aiops-grafana
- Port: 3001
- Purpose: Visualization of metrics, logs, traces""",

    "tempo": """
### Grafana Tempo
- Type: Distributed tracing backend
- Container: aiops-tempo
- Port: 3200
- Purpose: Store and query distributed traces""",
}

PLANNING_SYSTEM_PROMPT = """You are a remediation planning specialist.

Given an incident and root cause analysis, create a detailed remediation plan.

Your plan must:
1. Minimize service disruption
2. Be reversible when possible
3. Include validation steps
4. Consider dependencies
5. Estimate time and risk for each step

Respond in JSON format:
{
    "plan_name": "Brief description",
    "total_steps": N,
    "estimated_duration": "X minutes",
    "overall_risk": "low|medium|high",
    "rollback_available": true/false,
    "steps": [
        {
            "order": 1,
            "action": "Description",
            "command": "Actual command or null",
            "duration": "X seconds",
            "risk": "low|medium|high",
            "requires_approval": true/false,
            "validation": "How to verify success"
        }
    ],
    "success_criteria": "How to know the issue is resolved",
    "rollback_plan": "Steps to undo if needed"
}
"""


class ReasoningAgent(BaseAgent):
    """
    Complex reasoning agent for deep analysis and planning.
    
    Uses Qwen3-14B Q4_K_M model running on port 8082.
    Supports multiple modes: RCA, Chat, Planning.
    """
    
    def __init__(self, model_router: Optional[ModelRouter] = None):
        """
        Initialize the reasoning agent.

        Args:
            model_router: ModelRouter instance (creates new if not provided)
        """
        super().__init__(AgentRole.REASONING)
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
    
    def get_system_prompt(self, mode: str = "chat") -> str:
        """
        Get the system prompt for the specified mode.
        
        Args:
            mode: "rca" | "chat" | "planning"
        """
        prompts = {
            "rca": RCA_SYSTEM_PROMPT,
            "chat": CHAT_SYSTEM_PROMPT,
            "planning": PLANNING_SYSTEM_PROMPT,
        }
        return prompts.get(mode, CHAT_SYSTEM_PROMPT)
    
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process input and return reasoned response.

        Args:
            input_data: Dictionary containing:
                - mode: "rca" | "chat" | "planning"
                - query: The question or data to analyze
                - context: Additional context (incident data, etc.)
                - enable_thinking: Whether to use extended thinking

        Returns:
            AgentResponse with analysis and confidence
        """
        mode = input_data.get("mode", "chat")
        query = input_data.get("query", "")
        context = input_data.get("context", "")
        runtime_context = input_data.get("runtime_context")
        enable_thinking = input_data.get("enable_thinking", False)

        # Build prompt with runtime context (returns user_prompt, system_prompt)
        user_prompt, system_prompt = self._build_prompt(mode, query, context, runtime_context)

        # Track timing for activity logging
        start_time = time.perf_counter()

        try:
            # Get completion from reasoning agent
            # Temperature: 0.0 for deterministic RCA/planning, 0.5 for natural chat
            temp = 0.0 if mode in ("rca", "planning") else 0.5
            response = await self.model_router.reasoning_completion(
                prompt=user_prompt,
                max_tokens=2048,
                temperature=temp,
                enable_thinking=enable_thinking,
                system_prompt=system_prompt,
            )

            content = response["choices"][0]["message"]["content"]
            # Capture raw chain-of-thought for audit logging (Phase 4.0a, 2026-05-12).
            # Ollama 0.23.2 emits CoT in message.reasoning regardless of enable_thinking=False.
            # _original_reasoning is set by ModelRouter._fix_thinking_response.
            reasoning_trace = response["choices"][0]["message"].get("_original_reasoning") or ""
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Parse based on mode
            if mode in ("rca", "planning"):
                parsed = self._parse_json_response(content)
                confidence = parsed.get("confidence", 0.7)
                result = AgentResponse(
                    content=content,
                    confidence=confidence,
                    confidence_level=self.calculate_confidence_level(confidence),
                    reasoning=parsed.get("reasoning", ""),
                    reasoning_trace=reasoning_trace,
                    suggested_action=self._extract_action(parsed, mode),
                    metadata=parsed,
                )
            else:
                # Chat mode - return as-is
                result = AgentResponse(
                    content=content,
                    confidence=0.8,  # Default confidence for chat
                    confidence_level=self.calculate_confidence_level(0.8),
                    reasoning=None,
                    reasoning_trace=reasoning_trace,
                    suggested_action=None,
                    metadata={"mode": "chat"},
                )

            # Log successful activity
            self._log_activity(
                activity_type=mode,
                input_text=query,
                output_text=content,
                latency_ms=latency_ms,
                status="success",
            )

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Reasoning failed: {e}")

            # Log failed activity
            self._log_activity(
                activity_type=mode,
                input_text=query,
                output_text=str(e),
                latency_ms=latency_ms,
                status="error",
            )

            return AgentResponse(
                content=f"Analysis failed: {str(e)}",
                confidence=0.0,
                confidence_level=self.calculate_confidence_level(0.0),
                suggested_action="escalate",
                metadata={"error": str(e)},
            )
    
    async def analyze_rca(
        self,
        incident_data: dict[str, Any],
        historical_context: str = "",
        prior_context: str = "",
        enable_thinking: bool = True,
    ) -> AgentResponse:
        """
        Perform root cause analysis on an incident.

        Args:
            incident_data: Incident information and telemetry
            historical_context: Context from episodic memory (similar past incidents)
            prior_context: Chain-of-Thought context from Fast Agent (System 1)
                annotation, passed by the LangGraph orchestration pipeline
            enable_thinking: Enable extended thinking mode

        Returns:
            AgentResponse with RCA results
        """
        # Build context with prior annotation and historical information
        context = json.dumps(incident_data, indent=2)
        if prior_context:
            context = f"## Fast Agent Assessment (System 1)\n{prior_context}\n\n## Current Incident\n{context}"
        if historical_context:
            context = f"## Historical Context (Similar Past Incidents)\n{historical_context}\n\n{context}"

        return await self.process({
            "mode": "rca",
            "query": "Perform root cause analysis",
            "context": context,
            "enable_thinking": enable_thinking,
        })
    
    async def create_plan(
        self,
        root_cause: str,
        incident_context: dict[str, Any],
    ) -> AgentResponse:
        """
        Create a remediation plan based on RCA.
        
        Args:
            root_cause: Identified root cause
            incident_context: Context about the incident
            
        Returns:
            AgentResponse with remediation plan
        """
        return await self.process({
            "mode": "planning",
            "query": f"Create remediation plan for: {root_cause}",
            "context": json.dumps(incident_context, indent=2),
            "enable_thinking": True,
        })
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[list[dict]] = None,
        runtime_context: Optional[str] = None,
    ) -> AgentResponse:
        """
        Handle chat interaction with operator.

        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            runtime_context: Runtime system context (containers, agents, etc.)

        Returns:
            AgentResponse with chat reply
        """
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])

        return await self.process({
            "mode": "chat",
            "query": message,
            "context": context,
            "runtime_context": runtime_context,
            "enable_thinking": False,  # Chat doesn't need thinking mode
        })
    
    def _build_prompt(
        self,
        mode: str,
        query: str,
        context: str,
        runtime_context: Optional[str] = None,
    ) -> tuple[str, str]:
        """Build user prompt and system prompt separately.

        Returns:
            Tuple of (user_prompt, system_prompt) for proper message role separation.
        """
        system_prompt = self.get_system_prompt(mode)

        # Inject runtime context into system prompt (for chat mode)
        if mode == "chat" and runtime_context:
            system_prompt = system_prompt.replace("{runtime_context}", f"## Current System State\n{runtime_context}")
        else:
            system_prompt = system_prompt.replace(
                "{runtime_context}",
                "## Current System State\nNo runtime data currently available. Answer based on your knowledge of the system architecture.",
            )

        user_prompt = f"User Query: {query}"
        if context:
            user_prompt += f"\n\nContext:\n{context}"

        return user_prompt, system_prompt
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from model response with robust brace-matching fallback."""
        try:
            content = content.strip()

            # Step 1: Try markdown code block extraction
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Step 2: Try direct parse first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

            # Step 3: Brace-matching fallback (same technique as FastAnnotator)
            # Handles cases where model outputs extra text around JSON
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
                json_str = content[start_idx:end_idx + 1]
                return json.loads(json_str)

            # No JSON object found
            return {"raw_content": content, "confidence": 0.5}

        except (json.JSONDecodeError, ValueError):
            return {"raw_content": content, "confidence": 0.5}
    
    def _extract_action(self, parsed: dict, mode: str) -> Optional[str]:
        """Extract suggested action from parsed response."""
        if mode == "rca":
            steps = parsed.get("remediation_steps", [])
            if steps:
                return steps[0].get("action")
        elif mode == "planning":
            steps = parsed.get("steps", [])
            if steps:
                return steps[0].get("action")
        return None

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
            activity_type: Type of activity (rca, chat, planning)
            input_text: Input prompt/message
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


__all__ = [
    "ReasoningAgent",
    "RCA_SYSTEM_PROMPT",
    "CHAT_SYSTEM_PROMPT", 
    "PLANNING_SYSTEM_PROMPT",
]
