"""
Constitutional AIOps - Background Telemetry Processor

Continuously processes telemetry from LGTM stack through the Fast Agent.
Implements the "System 1" continuous scanning described in the research paper.

Key responsibilities:
- Periodically collect telemetry via TelemetryCollector
- Process through Fast Agent for annotation
- Escalate to Reasoning Agent if needs_reasoning=true
- Store annotations and episodes in Neo4j graph

From Research_V7.tex:
"Fast Annotation Agent (System 1): A 4B parameter model optimized for
sub-100ms pattern recognition. It continuously scans OpenTelemetry streams
to tag anomalies."

Architecture (Research_V7.tex Section 4.1):
    LGTM Stack → TelemetryCollector → BackgroundProcessor → Fast Agent
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.memory.episode_store import Episode
from src.telemetry.chat_activity import chat_turn_active, wait_for_chat_idle

logger = logging.getLogger(__name__)

# Configuration
PROCESSING_INTERVAL_SECONDS = 30  # How often to process telemetry
TELEMETRY_WINDOW_MINUTES = 5  # How far back to look for telemetry
REASONING_INTERVAL_CYCLES = 10  # Run reasoning every N fast cycles (10 * 30s = 5 min)

# Chat-priority interlock: routine reasoning shares the 14B engine with
# interactive chat. A sweep is skipped while a turn is in flight or within this
# grace of the last one (user mid-conversation); escalations instead WAIT
# bounded by the second constant, since skipping one would lose its RCA.
CHAT_PRIORITY_GRACE_SECONDS = 20.0
ESCALATION_CHAT_WAIT_SECONDS = 60.0

# Services kept when an analysis names NO service explicitly: linking every
# service that merely emitted a log line in the window is what produced the
# 560-edge graph hairball, so unattributed episodes keep at most this many.
MAX_UNATTRIBUTED_SERVICES = 2

# ---------------------------------------------------------------------------
# Episode-quality helpers (session-14 W2)
# ---------------------------------------------------------------------------

# Canonical severity vocabulary written to episodes. Live data previously
# carried raw str(int) blobs like "10" because the LangGraph pipeline scores
# severity 0-10 and the old write path stringified it directly.
_SEVERITY_STR_MAP = {
    "info": "info", "low": "info", "none": "info", "debug": "info",
    "warning": "warning", "warn": "warning", "medium": "warning",
    "error": "error", "high": "error", "err": "error",
    "critical": "critical", "crit": "critical", "fatal": "critical",
}


def normalize_severity(value: Any) -> str:
    """Normalize any severity representation to {info,warning,error,critical}.

    Handles the 0-10 numeric scale from the LangGraph annotate node
    (orchestration/graph.py maps info=2 low=4 medium/warning=6 high=8
    critical=10), numeric strings, and common string aliases.
    """
    if isinstance(value, bool):
        return "info"
    if isinstance(value, (int, float)):
        score = float(value)
    else:
        s = str(value or "").strip().lower()
        if s in _SEVERITY_STR_MAP:
            return _SEVERITY_STR_MAP[s]
        try:
            score = float(s)
        except (TypeError, ValueError):
            return "info"
    if score >= 9:
        return "critical"
    if score >= 7:
        return "error"
    if score >= 4:
        return "warning"
    return "info"


_TITLE_FIELD_RE = re.compile(
    r'"(?:root_cause|summary|title)"\s*:\s*"([^"]+)"'
)


def _humanize_title(raw: str | None, fallback: str = "Anomaly detected",
                    max_len: int = 100) -> str:
    """Turn raw agent output (often a JSON blob) into a clean human title.

    RCA/annotation content is frequently a JSON document like
    ``{"root_cause": "...", "causal_chain": [...]}`` — episode titles built by
    naive slicing leaked truncated JSON into the UI. Prefer the
    root_cause/summary/title field; otherwise use the first plain-text line.
    """
    s = (raw or "").strip()
    if not s:
        return fallback

    # Drop chain-of-thought and code fences before extracting.
    if "</think>" in s:
        s = s.split("</think>")[-1].strip()
    s = s.replace("```json", "```")

    candidate: str | None = None
    if "{" in s:
        start, end = s.find("{"), s.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(s[start:end + 1])
                if isinstance(parsed, dict):
                    for key in ("root_cause", "summary", "title"):
                        value = parsed.get(key)
                        if isinstance(value, str) and value.strip():
                            candidate = value.strip()
                            break
            except (json.JSONDecodeError, ValueError):
                pass
        if candidate is None:
            # Truncated/non-strict JSON: regex out the human field.
            match = _TITLE_FIELD_RE.search(s)
            if match:
                candidate = match.group(1)

    if candidate is None:
        first_line = next((ln.strip() for ln in s.splitlines() if ln.strip()), "")
        candidate = first_line
        if candidate.startswith("{") or not candidate:
            return fallback

    # Strip markdown noise + dangling punctuation from truncation.
    candidate = candidate.replace("**", "").replace("`", "")
    candidate = re.sub(r"^\s*#{1,6}\s*", "", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip().rstrip(" ([{,:;-")
    if not candidate:
        return fallback
    if len(candidate) > max_len:
        candidate = candidate[:max_len].rsplit(" ", 1)[0].rstrip() + "…"
    return candidate


# Marker phrases for annotations/analyses that describe NOTHING happening.
# Storing these as episodes polluted the graph with non-event noise.
_NON_EVENT_MARKERS = (
    "no significant anomal",
    "no anomalies detected",
    "no anomaly detected",
    "no anomalies were detected",
    "no significant issues",
    "no issues detected",
    "no concerning patterns",
    "no recurring root causes",
    "system healthy",
    "system is healthy",
    "operating normally",
)


def _is_non_event(*texts: str | None) -> bool:
    """True when the annotation/analysis says nothing actually happened."""
    for text in texts:
        if not text:
            continue
        lowered = str(text).lower()
        if any(marker in lowered for marker in _NON_EVENT_MARKERS):
            return True
    return False


def _select_affected_services(candidates: list[str], *texts: str | None) -> list[str]:
    """Keep only the genuinely affected services for an episode.

    A service is genuinely affected when the analysis text actually names it.
    When the text names none, fall back to the telemetry-derived candidates
    only if the list is small (<= MAX_UNATTRIBUTED_SERVICES) — otherwise the
    episode is system-wide noise and gets no INVOLVES links at all.
    """
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)

    combined = " ".join(str(t).lower() for t in texts if t)
    mentioned = [c for c in deduped if c.lower() in combined]
    if mentioned:
        return mentioned
    return sorted(deduped) if len(deduped) <= MAX_UNATTRIBUTED_SERVICES else []


class BackgroundTelemetryProcessor:
    """
    Background processor that continuously scans telemetry and annotates anomalies.

    Implements the "System 1 and System 2" cognitive model:
    - Fast Agent (System 1): Continuous pattern recognition
    - Reasoning Agent (System 2): Deep analysis when significant anomalies detected

    Uses TelemetryCollector as the unified interface to LGTM stack.
    """

    def __init__(
        self,
        fast_annotator: Any,
        reasoning_agent: Any,
        telemetry_collector: Any,
        episode_store: Any,
        neo4j_client: Any = None,
        incident_graph: Any = None,
        processing_interval: int = PROCESSING_INTERVAL_SECONDS,
    ):
        """
        Initialize the background processor.

        Args:
            fast_annotator: FastAnnotator instance for annotation
            reasoning_agent: ReasoningAgent instance for deep analysis
            telemetry_collector: TelemetryCollector for LGTM data (required)
            episode_store: EpisodeStore for storing episodes
            neo4j_client: Neo4jClient for graph updates (optional)
            incident_graph: Compiled LangGraph pipeline (REQUIRED)
            processing_interval: Seconds between processing cycles

        Raises:
            ValueError: If incident_graph is not provided
        """
        if incident_graph is None:
            raise ValueError(
                "incident_graph is required. Build it with "
                "build_incident_graph() from src.orchestration.graph"
            )

        self.fast_annotator = fast_annotator
        self.reasoning_agent = reasoning_agent
        self.telemetry_collector = telemetry_collector
        self.episode_store = episode_store
        self.neo4j_client = neo4j_client
        self.incident_graph = incident_graph
        self.processing_interval = processing_interval

        self._running = False
        self._task: asyncio.Task | None = None

        # Statistics
        self.stats = {
            "total_cycles": 0,
            "telemetry_processed": 0,
            "anomalies_detected": 0,
            "escalations_to_reasoning": 0,
            "routine_reasoning_runs": 0,
            "episodes_created": 0,
            "errors": 0,
            "last_run": None,
        }

        # Routine reasoning counter (Phase 5)
        self._fast_cycle_count = 0

        logger.info(f"BackgroundTelemetryProcessor initialized (interval: {processing_interval}s)")

    async def start(self) -> None:
        """Start the background processing loop."""
        if self._running:
            logger.warning("Background processor already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._processing_loop())
        logger.info("Background telemetry processor started")

    async def stop(self) -> None:
        """Stop the background processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background telemetry processor stopped")

    async def _processing_loop(self) -> None:
        """Main processing loop - runs continuously."""
        logger.info("Starting continuous telemetry processing loop...")

        while self._running:
            try:
                await self._process_cycle()
            except Exception as e:
                logger.error(f"Error in processing cycle: {e}")
                self.stats["errors"] += 1

            # Wait before next cycle
            await asyncio.sleep(self.processing_interval)

    async def _process_cycle(self) -> None:
        """
        Single processing cycle using TelemetryCollector.

        1. Collect telemetry via TelemetryCollector.collect_window()
        2. Process through Fast Agent
        3. Escalate if needed
        4. Store in graph
        5. Periodic routine reasoning (every REASONING_INTERVAL_CYCLES)
        """
        self.stats["total_cycles"] += 1
        self.stats["last_run"] = datetime.utcnow().isoformat()
        self._fast_cycle_count += 1

        logger.debug(f"Starting processing cycle #{self.stats['total_cycles']} (reasoning in {REASONING_INTERVAL_CYCLES - self._fast_cycle_count} cycles)")

        # Use TelemetryCollector - the proper architecture interface
        try:
            window = await self.telemetry_collector.collect_window(
                service="all",
                duration_minutes=TELEMETRY_WINDOW_MINUTES,
            )
        except Exception as e:
            logger.warning(f"TelemetryCollector failed: {e}")
            return

        # Skip if no data
        if window.log_count == 0 and len(window.metrics) == 0 and len(window.traces) == 0:
            logger.debug("No telemetry data available")
            return

        self.stats["telemetry_processed"] += 1

        # Build telemetry summary from TelemetryWindow
        telemetry_summary = self._build_window_summary(window)

        # ── LangGraph Orchestrated Pipeline (MANDATORY) ────────────────
        # Full pipeline: annotate -> evaluate -> reasoning -> validate -> plan
        try:
            correlation_id = str(uuid4())[:12]
            graph_result = await self.incident_graph.ainvoke({
                "telemetry_data": {
                    "telemetry_type": "combined",
                    "content": telemetry_summary,
                    "context": f"Telemetry window: {TELEMETRY_WINDOW_MINUTES}min, "
                               f"Logs: {window.log_count}, Metrics: {len(window.metrics)}, "
                               f"Traces: {len(window.traces)}",
                },
                "correlation_id": correlation_id,
                "steps_completed": [],
                "latency_ms": {},
            })

            # Extract results from graph state
            steps = graph_result.get("steps_completed", [])
            severity = graph_result.get("severity", 0)

            if severity > 0:
                self.stats["anomalies_detected"] += 1

            if "reasoning" in steps:
                self.stats["escalations_to_reasoning"] += 1

            # Store episode if annotation detected an anomaly
            annotation_data = graph_result.get("annotation")
            if annotation_data and severity > 0:
                await self._store_graph_result_as_episode(graph_result, window)

            logger.debug(
                f"LangGraph pipeline complete: correlation={correlation_id}, "
                f"steps={steps}, severity={severity}"
            )

        except Exception as e:
            logger.error(f"LangGraph pipeline failed: {e}")
            self.stats["errors"] += 1

        # Phase 5: Periodic routine reasoning (every REASONING_INTERVAL_CYCLES)
        if self._fast_cycle_count >= REASONING_INTERVAL_CYCLES:
            if chat_turn_active(grace_seconds=CHAT_PRIORITY_GRACE_SECONDS):
                # Counter stays >= threshold, so the sweep retries next cycle
                # (30s) instead of contending with the interactive turn.
                logger.info("Chat turn active - deferring routine reasoning to next cycle")
            else:
                self._fast_cycle_count = 0
                await self._routine_reasoning_analysis()

    async def _routine_reasoning_analysis(self) -> None:
        """
        Periodic deep analysis by Reasoning Agent.

        Phase 5: Runs every REASONING_INTERVAL_CYCLES (default: 10 cycles = 5 minutes)
        Analyzes recent episodes for patterns, trends, and systemic issues.
        """
        logger.info("Starting routine reasoning analysis...")
        self.stats["routine_reasoning_runs"] += 1

        try:
            # Query recent episodes (last 5 minutes)
            if not self.episode_store:
                logger.warning("No episode store available for routine reasoning")
                return

            recent_episodes = await self.episode_store.get_recent_episodes(minutes=5)

            if not recent_episodes or len(recent_episodes) == 0:
                logger.info("No recent episodes for routine reasoning - system healthy")
                return

            logger.info(f"Analyzing {len(recent_episodes)} recent episodes for patterns...")

            # Build context for trend analysis
            episodes_summary = []
            for ep in recent_episodes[:10]:  # Limit to 10 most recent
                episodes_summary.append(
                    f"- [{ep.severity}] {ep.title}: {ep.description[:100]}... "
                    f"(services: {', '.join(ep.affected_services)})"
                )

            analysis_prompt = f"""Analyze these {len(recent_episodes)} recent incidents for patterns and trends:

{chr(10).join(episodes_summary)}

Identify:
1. Recurring root causes
2. Service correlation patterns
3. Potential systemic issues
4. Preventive recommendations

Provide a brief summary of system health and any concerning patterns."""

            # Use reasoning agent for trend analysis. NOTE: this previously
            # called the nonexistent ``analyze_incident`` and silently raised
            # AttributeError every cycle — the trend path never produced an
            # episode. analyze_rca() is the real API (thinking disabled: this
            # is a lightweight routine sweep, not a full incident RCA).
            trend_result = await self.reasoning_agent.analyze_rca(
                incident_data={
                    "service": "system-wide",
                    "description": "Routine trend analysis",
                    "severity": "info",
                    "context": analysis_prompt,
                },
                enable_thinking=False,
            )

            logger.info(f"Routine reasoning complete: {trend_result.content[:200] if trend_result.content else 'No insights'}")

            # Store as insight episode if significant patterns found
            if trend_result.content and len(trend_result.content) > 50:
                # W2: a "system healthy / no concerning patterns" sweep is a
                # NON-EVENT — do not store it as an episode.
                if _is_non_event(trend_result.content[:400]):
                    logger.info("Routine reasoning found no concerning patterns - not storing")
                    return

                # W2: parse a clean human title out of the (often JSON) content.
                title = (
                    "Trend Analysis: "
                    + _humanize_title(trend_result.content,
                                      fallback="Recent incident patterns",
                                      max_len=80)
                )
                insight_episode = Episode(
                    episode_id=str(uuid4()),
                    incident_id=str(uuid4()),
                    title=title,
                    description=trend_result.content,
                    severity="info",
                    category="trend_analysis",
                    detected_at=datetime.utcnow(),
                    affected_services=list(set(
                        svc for ep in recent_episodes for svc in ep.affected_services
                    ))[:10],  # Aggregate affected services
                    root_cause="routine_analysis",
                    causal_chain=[],
                    confidence=trend_result.confidence,
                    outcome="insight",
                )
                await self.episode_store.store_episode(insight_episode)
                logger.info(f"Stored trend analysis insight: {insight_episode.episode_id[:8]}...")

        except Exception as e:
            logger.error(f"Routine reasoning analysis failed: {e}")
            self.stats["errors"] += 1

    def _build_window_summary(self, window: Any) -> str:
        """Build a summary of telemetry from TelemetryWindow for the Fast Agent."""
        summary_parts = [f"=== Telemetry Summary (last {TELEMETRY_WINDOW_MINUTES} min) ==="]
        summary_parts.append(f"Time: {window.start_time} to {window.end_time}")

        # Logs summary
        if window.logs:
            summary_parts.append(f"\n--- LOGS ({window.log_count} entries) ---")
            summary_parts.append(f"Errors: {window.error_count}, Warnings: {window.warning_count}")

            # Show sample error logs
            error_logs = [l for l in window.logs if l.level.lower() in ("error", "fatal", "critical")]
            for log in error_logs[:5]:
                msg = log.message[:200] if log.message else ""
                summary_parts.append(f"  [ERROR] {msg}")

            # Show sample warning logs
            warn_logs = [l for l in window.logs if l.level.lower() in ("warn", "warning")]
            for log in warn_logs[:3]:
                msg = log.message[:150] if log.message else ""
                summary_parts.append(f"  [WARN] {msg}")

        # Metrics summary
        if window.metrics:
            summary_parts.append(f"\n--- METRICS ({len(window.metrics)} points) ---")
            # Group by metric name
            metric_names = set(m.name for m in window.metrics)
            for name in list(metric_names)[:5]:
                values = [m.value for m in window.metrics if m.name == name]
                if values:
                    avg = sum(values) / len(values)
                    summary_parts.append(f"  {name}: avg={avg:.2f}")

        # Traces summary
        if window.traces:
            summary_parts.append(f"\n--- TRACES ({len(window.traces)} spans) ---")
            slow_traces = [t for t in window.traces if t.duration_ms > 1000]
            if slow_traces:
                summary_parts.append(f"Slow traces (>1s): {len(slow_traces)}")
                for t in slow_traces[:3]:
                    summary_parts.append(f"  {t.service}/{t.operation}: {t.duration_ms}ms")

        return "\n".join(summary_parts)

    def _extract_services_from_window(self, window: Any) -> list[str]:
        """
        Extract actual service/container names from telemetry window.

        Phase 1: Replace hardcoded "combined" with actual container names.
        Extracts from Loki log labels (container_name) and trace service names.
        """
        services = set()

        # Extract from log labels (Loki includes container_name label)
        for log in window.logs:
            if hasattr(log, 'labels') and log.labels:
                # Try different label names that promtail might use
                container = (
                    log.labels.get('container_name') or
                    log.labels.get('container') or
                    log.labels.get('service') or
                    log.labels.get('job')
                )
                if container and container not in ('containerlogs', 'varlogs'):
                    # Clean up container name (remove aiops- prefix for cleaner display)
                    clean_name = container.replace('aiops-', '')
                    services.add(clean_name)

            # Also check service attribute
            if hasattr(log, 'service') and log.service and log.service != 'all':
                services.add(log.service)

        # Extract from traces (service names)
        for trace in window.traces:
            if hasattr(trace, 'service') and trace.service:
                services.add(trace.service)

        # W2: NO static fallback. The old behaviour defaulted to six known
        # containers when nothing was extracted, which linked every episode to
        # every service and produced the graph hairball. An empty list is the
        # honest answer; _select_affected_services decides what to keep.
        return sorted(services)

    async def _store_graph_result_as_episode(self, graph_result: dict, window: Any) -> None:
        """Store a LangGraph pipeline result as an episode in Neo4j."""
        try:
            annotation_data = graph_result.get("annotation", {}) or {}
            rca_data = graph_result.get("rca_result")
            correlation_id = graph_result.get("correlation_id", str(uuid4()))

            annotation_content = annotation_data.get("content", "") or ""
            rca_content = (rca_data or {}).get("content", "") or ""

            # Determine title and description from the best available data.
            # W2: parse the (frequently JSON) agent output into a clean human
            # title instead of slicing a raw blob.
            if rca_data:
                title = "RCA: " + _humanize_title(
                    rca_content, fallback="Root cause analysis", max_len=90
                )
                description = rca_content
                category = "rca"
                outcome = "analyzed"
            else:
                title = _humanize_title(annotation_content, fallback="Anomaly detected")
                description = annotation_content
                category = (annotation_data.get("metadata") or {}).get("category", "unknown")
                outcome = "open"

            # W2: "No significant anomalies detected" NON-EVENTS must not be
            # stored as episodes at all.
            if _is_non_event(annotation_content[:400], title):
                logger.debug(f"Skipping non-event annotation: {title[:80]}")
                return

            # W2: link only genuinely affected services (text-mentioned, or a
            # small telemetry-derived candidate set) — never the whole stack.
            affected_services = _select_affected_services(
                self._extract_services_from_window(window),
                title, annotation_content, rca_content,
            )

            episode_confidence = graph_result.get("confidence", 0.5)

            # Thread the LLM-extracted semantic triplets from the FastAnnotator
            # annotation into the Episode so the Entity/RELATES graph layer is
            # actually populated. Previously this constructor never set triplets=,
            # so episode_store._store_episode_graph iterated an empty list and the
            # pink Entity layer was permanently empty in production. fast_annotator
            # emits triplets with subject/relation/object but no per-triplet
            # confidence, so stamp the episode confidence on each (documented
            # contract) — this makes the MIN_TRIPLET_CONFIDENCE filter meaningful
            # instead of silently falling back to episode.confidence per triplet.
            raw_triplets = (annotation_data.get("metadata") or {}).get("triplets", []) or []
            triplets: list[dict[str, Any]] = []
            for triplet in raw_triplets:
                if not isinstance(triplet, dict):
                    continue
                triplet = {**triplet}
                triplet.setdefault("confidence", episode_confidence)
                triplets.append(triplet)

            episode = Episode(
                episode_id=correlation_id,
                incident_id=correlation_id,
                title=title,
                description=description,
                # W2: write-time normalization — the pipeline carries a 0-10
                # int; str()-ing it stored severities like "10".
                severity=normalize_severity(graph_result.get("severity", "info")),
                category=category,
                detected_at=datetime.utcnow(),
                affected_services=affected_services,
                root_cause=(
                    _humanize_title(rca_content, fallback="unknown", max_len=200)
                    if rca_data else "unknown"
                ),
                causal_chain=graph_result.get("steps_completed", []),
                confidence=episode_confidence,
                outcome=outcome,
                triplets=triplets,
            )

            if self.episode_store:
                # Episode compaction
                similar = await self.episode_store.find_similar_episodes(
                    episode, limit=1, min_similarity=0.7
                )
                if similar:
                    existing, similarity = similar[0]
                    logger.info(f"Compacting: similar episode {existing.episode_id[:8]}... (sim={similarity:.2f})")
                    await self.episode_store.update_episode(
                        existing.episode_id,
                        {"confidence": max(existing.confidence, episode.confidence)},
                    )
                else:
                    await self.episode_store.store_episode(episode)
                    self.stats["episodes_created"] += 1
                    logger.info(f"Stored episode from LangGraph pipeline: {correlation_id[:8]}...")

        except Exception as e:
            logger.warning(f"Failed to store graph result as episode: {e}")

    async def _store_annotation(self, annotation: Any, window: Any) -> None:
        """Store annotation in Neo4j graph with episode compaction."""
        try:
            metadata = annotation.metadata or {}
            episode_id = str(uuid4())

            annotation_content = annotation.content or ""
            title = _humanize_title(annotation_content, fallback="Anomaly detected")

            # W2: never store "no significant anomalies" non-events.
            if _is_non_event(annotation_content[:400], title):
                logger.debug(f"Skipping non-event annotation: {title[:80]}")
                return

            # W2: only genuinely affected services (text-mentioned or a small
            # telemetry-derived candidate set).
            affected_services = _select_affected_services(
                self._extract_services_from_window(window),
                title, annotation_content,
            )

            # Create proper Episode object for EpisodeStore
            episode = Episode(
                episode_id=episode_id,
                incident_id=episode_id,  # Use same ID for incident
                title=title,
                description=annotation_content,
                severity=normalize_severity(metadata.get("severity", "info")),
                category=metadata.get("category", "unknown"),
                detected_at=datetime.utcnow(),
                affected_services=affected_services,
                root_cause=metadata.get("category", "unknown"),
                causal_chain=metadata.get("key_indicators", []),
                confidence=annotation.confidence,
                outcome="open",  # New episode, not yet resolved
                triplets=metadata.get("triplets", []),  # Phase 2: Store semantic triplets
            )

            # Episode compaction: Check for existing similar episodes
            if self.episode_store:
                similar_episodes = await self.episode_store.find_similar_episodes(
                    episode, limit=1, min_similarity=0.7
                )

                if similar_episodes:
                    # Update existing episode instead of creating new one
                    existing_episode, similarity = similar_episodes[0]
                    logger.info(
                        f"Compacting: Found similar episode {existing_episode.episode_id[:8]}... "
                        f"(similarity: {similarity:.2f}) - skipping duplicate"
                    )
                    # Update the existing episode's timestamp and description
                    await self.episode_store.update_episode(
                        existing_episode.episode_id,
                        {
                            "description": f"{annotation.content}\n---\n{existing_episode.description[:500]}",
                            "confidence": max(existing_episode.confidence, annotation.confidence),
                        }
                    )
                    self.stats["telemetry_processed"] += 1  # Count as processed but not new
                    return  # Don't create duplicate episode

                # No similar episode found - create new one
                await self.episode_store.store_episode(episode)
                self.stats["episodes_created"] += 1
                logger.info(f"Stored NEW episode {episode_id}: {episode.title[:50]}")

            # Create graph nodes for each affected service if Neo4j available
            if self.neo4j_client:
                for service_name in affected_services:
                    query = """
                    MERGE (s:Service {name: $service})
                    CREATE (a:Annotation {
                        id: $id,
                        timestamp: datetime($timestamp),
                        severity: $severity,
                        category: $category,
                        summary: $summary,
                        confidence: $confidence
                    })
                    CREATE (s)-[:HAS_ANNOTATION]->(a)
                    RETURN a.id
                    """
                    async with self.neo4j_client.session() as session:
                        await session.run(
                            query,
                            service=service_name,  # Use actual service name
                            id=episode_id,
                            timestamp=episode.detected_at.isoformat(),
                            severity=episode.severity,
                            category=episode.category,
                            summary=episode.description[:500],
                            confidence=episode.confidence,
                        )
                logger.debug(f"Created graph nodes for annotation {episode_id} (services: {affected_services})")

        except Exception as e:
            logger.warning(f"Failed to store annotation: {e}")

    async def _escalate_to_reasoning(self, annotation: Any, window: Any) -> None:
        """Escalate to Reasoning Agent for deep analysis."""
        logger.info("Escalating to Reasoning Agent for RCA")

        # Chat-priority interlock: escalations are event-driven (skipping loses
        # the RCA), so wait for the interactive turn instead — bounded, so a
        # busy chat can only delay an escalation, never starve it.
        waited = await wait_for_chat_idle(ESCALATION_CHAT_WAIT_SECONDS)
        if waited:
            logger.info(f"RCA escalation deferred {waited:.0f}s for an active chat turn")

        # Extract actual services for context
        affected_services = self._extract_services_from_window(window)
        services_str = ', '.join(affected_services)

        try:
            context = f"""
Fast Agent Assessment: {annotation.content}
Severity: {annotation.metadata.get('severity', 'unknown')}
Category: {annotation.metadata.get('category', 'unknown')}
Affected Services: {services_str}
Telemetry: {window.log_count} logs, {len(window.metrics)} metrics, {len(window.traces)} traces

Please perform root cause analysis and suggest remediation actions.
"""
            # NOTE: previously called the nonexistent ``analyze_incident``
            # (AttributeError swallowed by the except below) — RCA escalation
            # episodes were never stored. analyze_rca() is the real API.
            rca_result = await self.reasoning_agent.analyze_rca(
                incident_data={
                    "service": services_str,
                    "description": annotation.content,
                    "severity": annotation.metadata.get("severity", "warning"),
                    "context": context,
                },
            )

            logger.info(f"RCA completed: {rca_result.content[:200]}")

            # Store RCA episode with proper Episode object and compaction
            if self.episode_store:
                rca_episode_id = str(uuid4())
                rca_title = "RCA: " + _humanize_title(
                    rca_result.content, fallback="Root cause analysis", max_len=90
                )
                rca_episode = Episode(
                    episode_id=rca_episode_id,
                    incident_id=rca_episode_id,
                    title=rca_title,
                    description=rca_result.content or "",
                    severity=normalize_severity(
                        annotation.metadata.get("severity", "warning")
                    ),
                    category="rca",
                    detected_at=datetime.utcnow(),
                    affected_services=_select_affected_services(
                        affected_services, rca_title, rca_result.content,
                    ),
                    root_cause=_humanize_title(
                        rca_result.content, fallback="unknown", max_len=200
                    ),
                    causal_chain=[annotation.content[:100]] if annotation.content else [],
                    confidence=rca_result.confidence,
                    outcome="analyzed",
                )

                # Episode compaction for RCA too
                similar_rcas = await self.episode_store.find_similar_episodes(
                    rca_episode, limit=1, min_similarity=0.7
                )

                if similar_rcas:
                    existing_rca, similarity = similar_rcas[0]
                    logger.info(f"Compacting RCA: Found similar {existing_rca.episode_id[:8]}... - skipping")
                    await self.episode_store.update_episode(
                        existing_rca.episode_id,
                        {"confidence": max(existing_rca.confidence, rca_result.confidence)}
                    )
                else:
                    await self.episode_store.store_episode(rca_episode)
                    logger.info(f"Stored NEW RCA episode {rca_episode_id[:8]}...")

        except Exception as e:
            logger.error(f"Reasoning Agent escalation failed: {e}")

    def get_stats(self) -> dict:
        """Get processor statistics."""
        return {
            **self.stats,
            "running": self._running,
            "processing_interval_seconds": self.processing_interval,
            "telemetry_window_minutes": TELEMETRY_WINDOW_MINUTES,
        }


__all__ = ["BackgroundTelemetryProcessor", "normalize_severity"]
