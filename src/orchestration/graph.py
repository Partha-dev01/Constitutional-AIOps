"""
Constitutional AIOps - LangGraph Incident Orchestration Pipeline

Implements the Talker-Reasoner architecture (Christakopoulou et al.,
Google DeepMind, arXiv:2410.08328) using LangGraph StateGraph.

Pipeline:
    START -> annotate (System 1, Qwen3-4B)
          -> evaluate_escalation
          -> [conditional] reasoning (System 2, Qwen3-14B) with CoT context
          -> validate (Constitutional AI)
          -> [conditional] plan (auto) or END (approval/alert)
          -> END

Key design decisions:
- Nodes wrap existing agents (FastAnnotator, ReasoningAgent, ConstitutionalValidator)
- No new LLM code — LangGraph only orchestrates existing components
- IncidentState (TypedDict) carries context across all pipeline stages
- Conditional edges implement severity-based escalation (severity >= 8)
- Prior context from System 1 is passed to System 2 for Chain-of-Thought
"""

import logging
import time
from typing import Any, Optional
from uuid import uuid4

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)

# Severity threshold for escalation to Reasoning Agent (from paper)
ESCALATION_SEVERITY_THRESHOLD = 8


class IncidentState(TypedDict, total=False):
    """
    State that flows through the entire orchestration pipeline.

    Each node reads from and writes to this shared state.
    LangGraph merges node return dicts into the state automatically.
    """

    # ── Input ────────────────────────────────────────────────────
    telemetry_data: dict  # Raw telemetry input
    correlation_id: str  # Unique trace ID for this pipeline run

    # ── Stage 1: Fast Annotation (System 1) ──────────────────────
    annotation: Optional[dict]  # FastAnnotator AgentResponse as dict
    annotation_content: str  # Raw annotation text
    severity: int  # 0-10 severity score from annotation
    needs_reasoning: bool  # Escalation flag from FastAnnotator

    # ── Stage 2: Reasoning RCA (System 2) ────────────────────────
    rca_result: Optional[dict]  # ReasoningAgent AgentResponse as dict
    prior_context: str  # CoT context built from Stage 1

    # ── Stage 3: Constitutional Validation ────────────────────────
    validation_report: Optional[dict]  # ValidationReport as dict
    authorization_level: str  # "automatic" | "approval" | "alert"
    confidence: float  # Composite confidence score

    # ── Stage 4: Remediation Planning ─────────────────────────────
    plan: Optional[dict]  # Remediation plan from ReasoningAgent

    # ── Pipeline Metadata ─────────────────────────────────────────
    steps_completed: list[str]  # Breadcrumb trail of completed stages
    latency_ms: dict[str, float]  # Per-stage latency tracking
    error: Optional[str]  # Error message if pipeline failed


def _make_annotate_node(fast_annotator):
    """
    Create the annotation node (System 1 — Qwen3-4B).

    Wraps FastAnnotator.process() as a LangGraph node function.
    """

    async def annotate_node(state: IncidentState) -> dict:
        """Fast annotation: classify telemetry, detect anomalies, assign severity."""
        start = time.perf_counter()
        correlation_id = state.get("correlation_id", uuid4().hex[:12])

        try:
            telemetry_data = state.get("telemetry_data", {})

            # Call existing FastAnnotator — no new LLM code
            annotation = await fast_annotator.process({
                "telemetry_type": telemetry_data.get("telemetry_type", "combined"),
                "content": telemetry_data.get("content", ""),
                "context": telemetry_data.get("context", ""),
            })

            # Extract metadata from FastAnnotator response
            metadata = annotation.metadata or {}
            severity = metadata.get("severity", 0)
            if isinstance(severity, str):
                # Convert severity strings to numeric
                severity_map = {"info": 2, "low": 4, "medium": 6, "warning": 6, "high": 8, "critical": 10}
                severity = severity_map.get(severity.lower(), 5)

            needs_reasoning = metadata.get("needs_reasoning", False)
            latency = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                f"[{correlation_id}] Annotation complete: severity={severity}, "
                f"needs_reasoning={needs_reasoning}, latency={latency}ms"
            )

            return {
                "annotation": {
                    "content": annotation.content,
                    "confidence": annotation.confidence,
                    "metadata": metadata,
                },
                "annotation_content": annotation.content or "",
                "severity": severity,
                "needs_reasoning": needs_reasoning,
                "confidence": annotation.confidence,
                "steps_completed": state.get("steps_completed", []) + ["annotate"],
                "latency_ms": {**state.get("latency_ms", {}), "annotate": latency},
            }

        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            logger.error(f"[{correlation_id}] Annotation failed: {e}")
            return {
                "severity": 0,
                "needs_reasoning": False,
                "error": f"Annotation failed: {e}",
                "steps_completed": state.get("steps_completed", []) + ["annotate_error"],
                "latency_ms": {**state.get("latency_ms", {}), "annotate": latency},
            }

    return annotate_node


async def evaluate_escalation_node(state: IncidentState) -> dict:
    """
    Evaluate whether the Reasoning Agent (System 2) is needed.

    Implements the paper's escalation rule: severity >= 8 OR needs_reasoning flag.
    This is the conditional gate between System 1 and System 2.
    """
    severity = state.get("severity", 0)
    needs_reasoning = state.get("needs_reasoning", False)

    # Paper-claimed threshold: escalate when severity >= 8
    should_escalate = needs_reasoning or severity >= ESCALATION_SEVERITY_THRESHOLD

    correlation_id = state.get("correlation_id", "unknown")
    logger.info(
        f"[{correlation_id}] Escalation evaluation: severity={severity}, "
        f"needs_reasoning={needs_reasoning}, escalate={should_escalate}"
    )

    return {
        "needs_reasoning": should_escalate,
        "steps_completed": state.get("steps_completed", []) + ["evaluate_escalation"],
    }


def route_escalation(state: IncidentState) -> str:
    """
    Conditional edge: route to reasoning (System 2) or fast-path to END.

    This implements the Talker-Reasoner architecture's key decision point:
    simple cases resolved by System 1 alone, complex cases escalated to System 2.
    """
    if state.get("needs_reasoning", False):
        return "reasoning"
    return END


def _make_reasoning_node(reasoning_agent):
    """
    Create the reasoning node (System 2 — Qwen3-14B).

    KEY: Passes prior_context from System 1 annotation to System 2 for
    Chain-of-Thought reasoning across agents (Layered CoT, arXiv:2501.18645).
    """

    async def reasoning_node(state: IncidentState) -> dict:
        """Deep RCA with CoT context from Fast Agent annotation."""
        start = time.perf_counter()
        correlation_id = state.get("correlation_id", "unknown")

        try:
            telemetry_data = state.get("telemetry_data", {})

            # Build CoT prior context from System 1 annotation
            annotation_content = state.get("annotation_content", "")
            annotation_meta = (state.get("annotation") or {}).get("metadata", {})

            prior_context = (
                f"Severity: {state.get('severity', 'unknown')}\n"
                f"Category: {annotation_meta.get('category', 'unknown')}\n"
                f"Assessment: {annotation_content[:500]}"
            )

            # Call existing ReasoningAgent with CoT prior_context
            rca_response = await reasoning_agent.analyze_rca(
                incident_data=telemetry_data,
                prior_context=prior_context,
                enable_thinking=True,
            )

            latency = round((time.perf_counter() - start) * 1000, 2)
            rca_metadata = rca_response.metadata or {}

            logger.info(
                f"[{correlation_id}] RCA complete: confidence={rca_response.confidence}, "
                f"latency={latency}ms"
            )

            return {
                "rca_result": {
                    "content": rca_response.content,
                    "confidence": rca_response.confidence,
                    "reasoning": rca_response.reasoning,
                    "suggested_action": rca_response.suggested_action,
                    "metadata": rca_metadata,
                },
                "prior_context": prior_context,
                "confidence": rca_response.confidence,
                "steps_completed": state.get("steps_completed", []) + ["reasoning"],
                "latency_ms": {**state.get("latency_ms", {}), "reasoning": latency},
            }

        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            logger.error(f"[{correlation_id}] Reasoning failed: {e}")
            return {
                "confidence": 0.0,
                "error": f"Reasoning failed: {e}",
                "steps_completed": state.get("steps_completed", []) + ["reasoning_error"],
                "latency_ms": {**state.get("latency_ms", {}), "reasoning": latency},
            }

    return reasoning_node


def _make_validate_node(validator):
    """
    Create the constitutional validation node.

    Validates the proposed action against 12 constitutional principles
    across 3 tiers (Safety, Operational, Learning).
    """

    async def validate_node(state: IncidentState) -> dict:
        """Constitutional validation of RCA-suggested action."""
        start = time.perf_counter()
        correlation_id = state.get("correlation_id", "unknown")

        try:
            rca_result = state.get("rca_result") or {}
            confidence = state.get("confidence", 0.0)
            suggested_action = rca_result.get("suggested_action", "monitor")

            # Call existing ConstitutionalValidator
            report = validator.validate(
                action_id=correlation_id,
                action_description=suggested_action or "No action suggested",
                action_type=_classify_action_type(suggested_action),
                confidence=confidence,
                context={
                    "rca": rca_result,
                    "severity": state.get("severity", 0),
                    "source": "langgraph_pipeline",
                },
            )

            latency = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                f"[{correlation_id}] Validation: authorization={report.authorization_level.value}, "
                f"can_proceed={report.can_proceed}, latency={latency}ms"
            )

            return {
                "validation_report": {
                    "authorization_level": report.authorization_level.value,
                    "overall_result": report.overall_result.value,
                    "tier1_passed": report.tier1_passed,
                    "tier2_passed": report.tier2_passed,
                    "can_proceed": report.can_proceed,
                    "requires_approval": report.requires_approval,
                    "explanation": report.explanation,
                },
                "authorization_level": report.authorization_level.value,
                "steps_completed": state.get("steps_completed", []) + ["validate"],
                "latency_ms": {**state.get("latency_ms", {}), "validate": latency},
            }

        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            logger.error(f"[{correlation_id}] Validation failed: {e}")
            return {
                "authorization_level": "alert",
                "error": f"Validation failed: {e}",
                "steps_completed": state.get("steps_completed", []) + ["validate_error"],
                "latency_ms": {**state.get("latency_ms", {}), "validate": latency},
            }

    return validate_node


def route_authorization(state: IncidentState) -> str:
    """
    Conditional edge: route based on constitutional authorization level.

    - AUTOMATIC (confidence >= 0.90): proceed to plan generation
    - APPROVAL_REQUIRED / ALERT_ONLY: end pipeline (human review needed)
    """
    level = state.get("authorization_level", "alert")
    if level == "automatic":
        return "plan"
    return END


def _make_plan_node(reasoning_agent):
    """
    Create the remediation planning node.

    Only reached for auto-approved actions (confidence >= 0.90).
    Generates a step-by-step remediation plan.
    """

    async def plan_node(state: IncidentState) -> dict:
        """Generate remediation plan for auto-approved actions."""
        start = time.perf_counter()
        correlation_id = state.get("correlation_id", "unknown")

        try:
            rca_result = state.get("rca_result") or {}
            root_cause = rca_result.get("content", "Unknown root cause")

            # Call existing ReasoningAgent.create_plan()
            plan_response = await reasoning_agent.create_plan(
                root_cause=root_cause[:500],
                incident_context={
                    "severity": state.get("severity", 0),
                    "telemetry": state.get("telemetry_data", {}),
                    "rca": rca_result,
                },
            )

            latency = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                f"[{correlation_id}] Plan generated: "
                f"confidence={plan_response.confidence}, latency={latency}ms"
            )

            return {
                "plan": {
                    "content": plan_response.content,
                    "confidence": plan_response.confidence,
                    "metadata": plan_response.metadata or {},
                },
                "steps_completed": state.get("steps_completed", []) + ["plan"],
                "latency_ms": {**state.get("latency_ms", {}), "plan": latency},
            }

        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            logger.error(f"[{correlation_id}] Plan generation failed: {e}")
            return {
                "error": f"Plan generation failed: {e}",
                "steps_completed": state.get("steps_completed", []) + ["plan_error"],
                "latency_ms": {**state.get("latency_ms", {}), "plan": latency},
            }

    return plan_node


def _classify_action_type(action: Optional[str]) -> str:
    """Classify an action string into a type for constitutional validation."""
    if not action:
        return "monitor"

    action_lower = action.lower()
    if any(w in action_lower for w in ("restart", "reboot", "reset")):
        return "restart"
    if any(w in action_lower for w in ("scale", "replicas", "resize")):
        return "scale"
    if any(w in action_lower for w in ("delete", "remove", "drop")):
        return "delete"
    if any(w in action_lower for w in ("modify", "update", "change", "config")):
        return "modify"
    return "monitor"


# ═══════════════════════════════════════════════════════════════════
# Graph Builder
# ═══════════════════════════════════════════════════════════════════


def build_incident_graph(
    fast_annotator,
    reasoning_agent,
    validator,
    confidence_calculator=None,
):
    """
    Build the LangGraph incident orchestration pipeline.

    Implements the Talker-Reasoner architecture (arXiv:2410.08328) where:
    - System 1 (Talker/Fast): FastAnnotator for rapid telemetry annotation
    - System 2 (Reasoner/Slow): ReasoningAgent for deep RCA analysis

    The pipeline uses conditional edges for:
    - Severity-based escalation (severity >= 8 triggers System 2)
    - Confidence-gated actions (>= 0.90 auto, 0.70-0.90 approval, < 0.70 alert)

    Args:
        fast_annotator: FastAnnotator instance (System 1)
        reasoning_agent: ReasoningAgent instance (System 2)
        validator: ConstitutionalValidator instance
        confidence_calculator: Optional ConfidenceCalculator instance

    Returns:
        Compiled LangGraph StateGraph ready for .ainvoke()
    """
    graph = StateGraph(IncidentState)

    # Create node functions with agent closures
    annotate = _make_annotate_node(fast_annotator)
    reasoning = _make_reasoning_node(reasoning_agent)
    validate = _make_validate_node(validator)
    plan = _make_plan_node(reasoning_agent)

    # ── Add Nodes ────────────────────────────────────────────────
    graph.add_node("annotate", annotate)
    graph.add_node("evaluate_escalation", evaluate_escalation_node)
    graph.add_node("reasoning", reasoning)
    graph.add_node("validate", validate)
    graph.add_node("plan", plan)

    # ── Add Edges ────────────────────────────────────────────────
    # START -> annotate -> evaluate_escalation
    graph.add_edge(START, "annotate")
    graph.add_edge("annotate", "evaluate_escalation")

    # evaluate_escalation -> [conditional] reasoning OR END (fast path)
    graph.add_conditional_edges(
        "evaluate_escalation",
        route_escalation,
        {"reasoning": "reasoning", END: END},
    )

    # reasoning -> validate
    graph.add_edge("reasoning", "validate")

    # validate -> [conditional] plan (auto) OR END (approval/alert)
    graph.add_conditional_edges(
        "validate",
        route_authorization,
        {"plan": "plan", END: END},
    )

    # plan -> END
    graph.add_edge("plan", END)

    logger.info(
        "LangGraph incident pipeline built: "
        "START -> annotate -> evaluate -> [reasoning -> validate -> [plan]] -> END"
    )

    return graph.compile()


__all__ = [
    "IncidentState",
    "build_incident_graph",
    "ESCALATION_SEVERITY_THRESHOLD",
]
