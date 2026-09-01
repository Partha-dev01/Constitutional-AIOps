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
from src.agents.schemas.rca import RCA_JSON_SCHEMA

logger = logging.getLogger(__name__)

# Maximum activity log entries to keep (prevent memory growth)
MAX_ACTIVITY_LOG_SIZE = 50


def _cfg_reasoning_model() -> Optional[str]:
    """Return the configured reasoning-agent model name (e.g. "qwen3-14b").

    Imported lazily so tests/config reloads pick up the current value.
    """
    from src import config as _cfg_module

    return _cfg_module.config.llm.reasoning_agent_model


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

## Scope & Boundaries
You are a DOMAIN-SCOPED operations assistant for THIS system. You help with infrastructure
operations, observability (logs / metrics / traces), incident response, root-cause
analysis, remediation planning, service dependencies, the monitored services in this
stack, and general SRE / DevOps engineering. The monitored services include: nextcloud,
neo4j, loki, prometheus, grafana, tempo, mimir, promtail, otel-collector, and this app's
own backend and frontend.

DEFAULT TO HELPING. If a request is even plausibly about this system — its services,
infrastructure, incidents, telemetry, dependencies, or operations — ANSWER it fully; do
NOT refuse. For example, you MUST answer requests like: "show similar past incidents for
nextcloud", "what caused the latency spike", "is neo4j healthy?", "show the dependencies
of the backend", "summarize recent errors in loki", "how do I stop this from recurring".
When a request is ambiguous, assume it is in-scope and help.

ONLY refuse when a request is CLEARLY unrelated to IT / operations — e.g. general
knowledge, geography, history, trivia, math or word puzzles, current events,
entertainment, shopping, personal or medical advice, creative writing, or programming
help unrelated to operating this system. For those, decline in ONE brief sentence written
in your own words, do not answer even partially, and never attach a confidence score. Do
NOT use this refusal wording for any request that touches a monitored service, telemetry,
or operations — those you MUST answer.

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

## Tool Use (CRITICAL)
You have real tools that fetch live data (similar past incidents, service
dependencies, log analysis, metrics, container status) and gated action tools.
The system runs the relevant tool(s) for you and gives you their REAL results
below under "Current System State" / tool-result blocks.

- NEVER say "I will use the X tool", "let me run X", "please wait", or promise
  to do something later. There is no async work and no "later" — you cannot
  defer. Either ANSWER the user directly, or answer using the tool results that
  are already present below.
- When a tool result is present, base your answer on its actual data and cite
  the concrete numbers/names it contains.
- When a tool reports it "needs parameter X", do not narrate — ask the user for
  exactly that parameter in one short sentence.
- Do not invent tool output. If no data is present for something, say so plainly.

## Response Guidelines
- Be concise but thorough
- Do NOT state a numeric confidence percentage in your answer text — the UI
  already shows an evidence-based confidence gauge next to every reply, and a
  second number in prose contradicts it
- When an action is risky or uncertain, say so plainly and recommend human approval
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
    
    # Prompt names accepted by set_system_prompt/reset_prompts. The prompts
    # API exposes "reasoning_*" names; internally each maps to a mode.
    PROMPT_NAME_TO_MODE: dict[str, str] = {
        "rca": "rca",
        "reasoning_rca": "rca",
        "chat": "chat",
        "reasoning_chat": "chat",
        "planning": "planning",
        "reasoning_planning": "planning",
    }

    # Literal placeholders a custom prompt MUST keep per mode: the chat path
    # injects live runtime context into "{runtime_context}" (_build_prompt) —
    # an edit that drops it would silently disable runtime grounding.
    REQUIRED_PLACEHOLDERS: dict[str, tuple[str, ...]] = {
        "chat": ("{runtime_context}",),
    }

    def __init__(self, model_router: Optional[ModelRouter] = None):
        """
        Initialize the reasoning agent.

        Args:
            model_router: ModelRouter instance (creates new if not provided)
        """
        super().__init__(AgentRole.REASONING)
        self.model_router = model_router or ModelRouter()

        # Per-mode system prompt overrides (session-14 W4). Empty dict means
        # the baked module constants are used. Populated via set_system_prompt
        # (live push from PUT /prompts/{name} + persisted-override replay at
        # startup); cleared via reset_prompts.
        self._prompt_overrides: dict[str, str] = {}

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

    def set_system_prompt(self, name: str, prompt: str) -> None:
        """
        Override the system prompt for a mode (live, takes effect immediately).

        Args:
            name: Prompt name — "reasoning_rca" | "reasoning_chat" |
                "reasoning_planning" (or the bare mode "rca"/"chat"/"planning").
            prompt: The new system prompt text.

        Raises:
            ValueError: Unknown prompt name, empty prompt, or a required
                placeholder (e.g. ``{runtime_context}`` for chat) is missing.
        """
        mode = self.PROMPT_NAME_TO_MODE.get(name)
        if mode is None:
            raise ValueError(
                f"Unknown reasoning prompt '{name}' "
                f"(expected one of {sorted(self.PROMPT_NAME_TO_MODE)})"
            )
        if not prompt or not prompt.strip():
            raise ValueError("System prompt must not be empty")
        for placeholder in self.REQUIRED_PLACEHOLDERS.get(mode, ()):
            if placeholder not in prompt:
                raise ValueError(
                    f"Prompt '{name}' must contain the literal placeholder "
                    f"{placeholder} — live runtime context is injected there"
                )
        self._prompt_overrides[mode] = prompt
        self.logger.info(f"System prompt override applied for mode '{mode}'")

    def reset_prompts(self, name: Optional[str] = None) -> None:
        """
        Clear prompt overrides, restoring the baked module constants.

        Args:
            name: A specific prompt name to reset, or None to reset all.

        Raises:
            ValueError: Unknown prompt name.
        """
        if name is None:
            self._prompt_overrides.clear()
            self.logger.info("All system prompt overrides cleared")
            return
        mode = self.PROMPT_NAME_TO_MODE.get(name)
        if mode is None:
            raise ValueError(
                f"Unknown reasoning prompt '{name}' "
                f"(expected one of {sorted(self.PROMPT_NAME_TO_MODE)})"
            )
        self._prompt_overrides.pop(mode, None)
        self.logger.info(f"System prompt override cleared for mode '{mode}'")

    def get_system_prompt(self, mode: str = "chat") -> str:
        """
        Get the ACTIVE system prompt for the specified mode: a live override
        when one has been applied, else the baked module constant.

        Args:
            mode: "rca" | "chat" | "planning"
        """
        prompts = {
            "rca": RCA_SYSTEM_PROMPT,
            "chat": CHAT_SYSTEM_PROMPT,
            "planning": PLANNING_SYSTEM_PROMPT,
        }
        effective_mode = mode if mode in prompts else "chat"
        override = self._prompt_overrides.get(effective_mode)
        if override is not None:
            return override
        return prompts[effective_mode]
    
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

        # Mode 2 stable-prefix path (Phase 3): the chat route may supply the
        # fully assembled (user_prompt, system_prompt) pair — see
        # src/agents/prompt_layout.py. Absent (Mode 1 and every existing call
        # site), prompt construction is byte-identical to before.
        override = input_data.get("prompt_override")
        if isinstance(override, (tuple, list)) and len(override) == 2:
            user_prompt, system_prompt = str(override[0]), str(override[1])
        else:
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
                # Phase 5: RCA answers are schema-constrained under Mode 2
                # guided decoding (router gates on the serving profile; Mode 1
                # requests unchanged). Chat/planning stay free-form.
                guided_schema=RCA_JSON_SCHEMA if mode == "rca" else None,
            )

            content = response["choices"][0]["message"]["content"]
            # Capture raw chain-of-thought for audit logging (Phase 4.0a, 2026-05-12).
            # Ollama 0.23.2 emits CoT in message.reasoning regardless of enable_thinking=False.
            # _original_reasoning is set by ModelRouter._fix_thinking_response.
            reasoning_trace = response["choices"][0]["message"].get("_original_reasoning") or ""
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Capture token usage from the model response (A3/C6) when available.
            # ModelRouter passes the raw OpenAI-compatible payload through, which
            # carries usage.completion_tokens.
            usage = response.get("usage") if isinstance(response, dict) else None
            tokens_used = usage.get("completion_tokens") if isinstance(usage, dict) else None

            # Parse based on mode
            if mode in ("rca", "planning"):
                parsed = self._parse_json_response(content)
                # Route the LLM self-report through the documented composite
                # formula so RCA shares the single confidence code path with
                # chat. Historical / similarity evidence is not available in this
                # agent context (it is folded in by the orchestration pipeline's
                # ConfidenceCalculator), so pass them as None — compute_confidence
                # then returns the self-report clamped to [0,1] (weights
                # renormalize over the single present component). _normalize_
                # confidence still coerces percentage/out-of-range self-reports
                # first so e.g. "95" becomes 0.95 before the formula.
                from src.agents.confidence import compute_confidence

                c_llm = self._normalize_confidence(parsed.get("confidence", 0.7))
                confidence = compute_confidence(c_llm, None, None)
                if confidence is None:  # defensive: c_llm is never None here
                    confidence = c_llm
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
                # Chat mode - return as-is. Confidence here is a neutral placeholder;
                # the chat route (chat.py) computes the authoritative evidence-based
                # confidence from the telemetry/tool data it gathered.
                try:
                    model_used = _cfg_reasoning_model()
                except Exception:
                    model_used = None
                result = AgentResponse(
                    content=content,
                    confidence=0.5,  # Neutral placeholder; chat.py recomputes evidence-based
                    confidence_level=self.calculate_confidence_level(0.5),
                    reasoning=None,
                    reasoning_trace=reasoning_trace,
                    suggested_action=None,
                    metadata={
                        "mode": "chat",
                        "model_used": model_used,
                        "tokens_used": tokens_used,
                    },
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
        enable_thinking: bool = False,
    ) -> AgentResponse:
        """
        Handle chat interaction with operator.

        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            runtime_context: Runtime system context (containers, agents, etc.)
            enable_thinking: Enable extended thinking mode (B5: threaded from
                ChatRequest.enable_thinking; defaults to False).

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
            "enable_thinking": enable_thinking,
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
    
    @staticmethod
    def _normalize_confidence(raw: Any) -> float:
        """Coerce a model-supplied confidence to a safe ``[0.0, 1.0]`` float.

        The RCA/planning system prompt asks for ``0.0-1.0``, but models sometimes
        return a percentage (e.g. ``95``) or a ``>1`` value. ``AnalysisResponse``
        pins ``confidence`` to ``ge=0.0, le=1.0`` (api/schemas/chat.py), so an
        un-normalized value 500s the ``/chat/analyze`` endpoint. Normalize values
        ``> 1`` by dividing by 100 (percentage form), then clamp into range. Bad
        types fall back to the neutral ``0.7`` default.
        """
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return 0.7
        if value > 1.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))

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

    def record_activity(
        self,
        activity_type: str,
        input_text: str,
        output_text: str,
        latency_ms: float = 0.0,
        status: str = "success",
    ) -> None:
        """Public, best-effort hook to record an externally-driven activity.

        The API chat tool loop drives the ModelRouter directly (see
        chat.py:_make_chat_completion), so those turns never pass through
        process()/_log_activity. Calling this from the chat route keeps the
        Agents activity feed honest about real interactive work. Never raises.
        """
        try:
            self._log_activity(
                activity_type=activity_type,
                input_text=input_text,
                output_text=output_text,
                latency_ms=latency_ms,
                status=status,
            )
        except Exception:  # noqa: BLE001 - activity logging is best-effort
            self.logger.debug("record_activity failed", exc_info=True)

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
