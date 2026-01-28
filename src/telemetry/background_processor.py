"""
Constitutional AIOps - Background Telemetry Processor

Continuously processes telemetry from LGTM stack through the Fast Agent.
Implements the "System 1" continuous scanning described in the research paper.

Key responsibilities:
- Periodically collect telemetry via TelemetryCollector
- Process through Fast Agent for annotation
- Escalate to Reasoning Agent if needs_reasoning=true
- Store annotations and episodes in Neo4j graph

From Research_V6.tex:
"Fast Annotation Agent (System 1): A 4B parameter model optimized for
sub-100ms pattern recognition. It continuously scans OpenTelemetry streams
to tag anomalies."

Architecture (Research_V6.tex Section 4.1):
    LGTM Stack → TelemetryCollector → BackgroundProcessor → Fast Agent
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from src.memory.episode_store import Episode

logger = logging.getLogger(__name__)

# Configuration
PROCESSING_INTERVAL_SECONDS = 30  # How often to process telemetry
TELEMETRY_WINDOW_MINUTES = 5  # How far back to look for telemetry
REASONING_INTERVAL_CYCLES = 10  # Run reasoning every N fast cycles (10 * 30s = 5 min)


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
            processing_interval: Seconds between processing cycles
        """
        self.fast_annotator = fast_annotator
        self.reasoning_agent = reasoning_agent
        self.telemetry_collector = telemetry_collector
        self.episode_store = episode_store
        self.neo4j_client = neo4j_client
        self.processing_interval = processing_interval

        self._running = False
        self._task: Optional[asyncio.Task] = None

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

        # Process through Fast Agent
        try:
            annotation = await self.fast_annotator.process({
                "telemetry_type": "combined",
                "content": telemetry_summary,
                "context": f"Telemetry window: {TELEMETRY_WINDOW_MINUTES}min, Logs: {window.log_count}, Metrics: {len(window.metrics)}, Traces: {len(window.traces)}",
            })

            # Check for anomaly
            metadata = annotation.metadata or {}
            anomaly_detected = metadata.get("anomaly_detected", False)
            needs_reasoning = metadata.get("needs_reasoning", False)
            severity = metadata.get("severity", "info")

            if anomaly_detected:
                self.stats["anomalies_detected"] += 1
                logger.info(f"Anomaly detected: {annotation.content} (severity: {severity})")

                # Store annotation in graph
                await self._store_annotation(annotation, window)

                # Escalate to Reasoning Agent if needed
                if needs_reasoning:
                    self.stats["escalations_to_reasoning"] += 1
                    await self._escalate_to_reasoning(annotation, window)

        except Exception as e:
            logger.warning(f"Fast Agent annotation failed: {e}")
            self.stats["errors"] += 1

        # Phase 5: Periodic routine reasoning (every REASONING_INTERVAL_CYCLES)
        if self._fast_cycle_count >= REASONING_INTERVAL_CYCLES:
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

            # Use reasoning agent for trend analysis
            trend_result = await self.reasoning_agent.analyze_incident({
                "service": "system-wide",
                "description": "Routine trend analysis",
                "severity": "info",
                "context": analysis_prompt,
            })

            logger.info(f"Routine reasoning complete: {trend_result.content[:200] if trend_result.content else 'No insights'}")

            # Store as insight episode if significant patterns found
            if trend_result.content and len(trend_result.content) > 50:
                insight_episode = Episode(
                    episode_id=str(uuid4()),
                    incident_id=str(uuid4()),
                    title=f"Trend Analysis: {trend_result.content[:60]}",
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

        # If no services found, return list of known containers
        if not services:
            # Default to known container names from docker-compose
            services = {'backend', 'frontend', 'neo4j', 'grafana', 'prometheus', 'loki'}

        return list(services) if services else ['unknown']

    async def _store_annotation(self, annotation: Any, window: Any) -> None:
        """Store annotation in Neo4j graph with episode compaction."""
        try:
            metadata = annotation.metadata or {}
            episode_id = str(uuid4())

            # Extract actual service names from telemetry (Phase 1 fix)
            affected_services = self._extract_services_from_window(window)

            # Create proper Episode object for EpisodeStore
            episode = Episode(
                episode_id=episode_id,
                incident_id=episode_id,  # Use same ID for incident
                title=annotation.content[:100] if annotation.content else "Anomaly Detected",
                description=annotation.content or "",
                severity=metadata.get("severity", "info"),
                category=metadata.get("category", "unknown"),
                detected_at=datetime.utcnow(),
                affected_services=affected_services,  # Use extracted services instead of "combined"
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
            rca_result = await self.reasoning_agent.analyze_incident({
                "service": services_str,
                "description": annotation.content,
                "severity": annotation.metadata.get("severity", "warning"),
                "context": context,
            })

            logger.info(f"RCA completed: {rca_result.content[:200]}")

            # Store RCA episode with proper Episode object and compaction
            if self.episode_store:
                rca_episode_id = str(uuid4())
                rca_episode = Episode(
                    episode_id=rca_episode_id,
                    incident_id=rca_episode_id,
                    title=f"RCA: {rca_result.content[:80]}" if rca_result.content else "Root Cause Analysis",
                    description=rca_result.content or "",
                    severity=annotation.metadata.get("severity", "warning"),
                    category="rca",
                    detected_at=datetime.utcnow(),
                    affected_services=affected_services,  # Use extracted services
                    root_cause=rca_result.content[:200] if rca_result.content else "unknown",
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


__all__ = ["BackgroundTelemetryProcessor"]
