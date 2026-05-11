"""
ARCHIVED: Pre-Orchestrator Fallback Code
=========================================

This file contains the backward-compatible fallback logic that was removed
when the LangGraph orchestration pipeline was made MANDATORY.

Before: If incident_graph was None, the system fell back to direct agent calls.
After:  The orchestrator is required. System raises errors without it.

Archived on: 2026-03-01
Reason: Orchestrator is now mandatory — no fallback path needed.
Files affected:
  - src/telemetry/background_processor.py (removed from _process_cycle)
  - src/api/routes/incidents.py (removed from _trigger_analysis)

This code is preserved for reference only. Do NOT import or use it.
"""


# ═══════════════════════════════════════════════════════════════════
# FROM: src/telemetry/background_processor.py — _process_cycle()
# Was the `else` branch when incident_graph was None
# ═══════════════════════════════════════════════════════════════════

async def _process_cycle_fallback(self, telemetry_summary, window):
    """
    ARCHIVED: Original manual annotation + escalation logic.
    Replaced by LangGraph pipeline in _process_cycle().
    """
    try:
        annotation = await self.fast_annotator.process({
            "telemetry_type": "combined",
            "content": telemetry_summary,
            "context": (
                f"Telemetry window: {5}min, "
                f"Logs: {window.log_count}, "
                f"Metrics: {len(window.metrics)}, "
                f"Traces: {len(window.traces)}"
            ),
        })

        # Check for anomaly
        metadata = annotation.metadata or {}
        anomaly_detected = metadata.get("anomaly_detected", False)
        needs_reasoning = metadata.get("needs_reasoning", False)
        severity = metadata.get("severity", "info")

        if anomaly_detected:
            self.stats["anomalies_detected"] += 1

            # Store annotation in graph
            await self._store_annotation(annotation, window)

            # Escalate to Reasoning Agent if needed
            if needs_reasoning:
                self.stats["escalations_to_reasoning"] += 1
                await self._escalate_to_reasoning(annotation, window)

    except Exception as e:
        self.stats["errors"] += 1


# ═══════════════════════════════════════════════════════════════════
# FROM: src/api/routes/incidents.py — _trigger_analysis()
# Was the fallback when incident_graph was None
# ═══════════════════════════════════════════════════════════════════

async def _trigger_analysis_fallback(request, incident, enable_thinking=True):
    """
    ARCHIVED: Direct reasoning agent call without orchestration.
    Replaced by LangGraph pipeline in _trigger_analysis().
    """
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        return

    incident_data = {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity.value,
        "category": incident.category.value,
        "affected_services": [s.model_dump() for s in incident.affected_services],
        "telemetry": incident.telemetry.model_dump() if incident.telemetry else None,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
    }

    try:
        agent_response = await reasoning_agent.analyze_rca(
            incident_data=incident_data,
            enable_thinking=enable_thinking,
        )

        # Update incident with RCA results
        if agent_response.metadata:
            from src.api.schemas.incident import RCAResult

            incident.rca = RCAResult(
                root_cause=agent_response.metadata.get("root_cause", "Unknown"),
                causal_chain=agent_response.metadata.get("causal_chain", []),
                confidence=agent_response.confidence,
                reasoning=agent_response.metadata.get("reasoning"),
                similar_incidents=agent_response.metadata.get("similar_incidents"),
            )

        # Update status based on confidence
        if agent_response.confidence >= 0.9:
            from src.api.schemas.incident import IncidentStatus
            incident.status = IncidentStatus.REMEDIATING
        elif agent_response.confidence >= 0.7:
            from src.api.schemas.incident import IncidentStatus
            incident.status = IncidentStatus.PENDING_APPROVAL
        else:
            from src.api.schemas.incident import IncidentStatus
            incident.status = IncidentStatus.ANALYZING

    except Exception as e:
        pass  # Original code just logged and continued
