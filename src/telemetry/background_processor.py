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
            "episodes_created": 0,
            "errors": 0,
            "last_run": None,
        }

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
        """
        self.stats["total_cycles"] += 1
        self.stats["last_run"] = datetime.utcnow().isoformat()

        logger.debug(f"Starting processing cycle #{self.stats['total_cycles']}")

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

    async def _store_annotation(self, annotation: Any, window: Any) -> None:
        """Store annotation in Neo4j graph with episode compaction."""
        try:
            metadata = annotation.metadata or {}
            episode_id = str(uuid4())

            # Create proper Episode object for EpisodeStore
            episode = Episode(
                episode_id=episode_id,
                incident_id=episode_id,  # Use same ID for incident
                title=annotation.content[:100] if annotation.content else "Anomaly Detected",
                description=annotation.content or "",
                severity=metadata.get("severity", "info"),
                category=metadata.get("category", "unknown"),
                detected_at=datetime.utcnow(),
                affected_services=["combined"],  # Track which services are affected
                root_cause=metadata.get("category", "unknown"),
                causal_chain=metadata.get("key_indicators", []),
                confidence=annotation.confidence,
                outcome="open",  # New episode, not yet resolved
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

            # Create graph node if Neo4j available
            if self.neo4j_client:
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
                        service="combined",
                        id=episode_id,
                        timestamp=episode.detected_at.isoformat(),
                        severity=episode.severity,
                        category=episode.category,
                        summary=episode.description[:500],
                        confidence=episode.confidence,
                    )
                logger.debug(f"Created graph node for annotation {episode_id}")

        except Exception as e:
            logger.warning(f"Failed to store annotation: {e}")

    async def _escalate_to_reasoning(self, annotation: Any, window: Any) -> None:
        """Escalate to Reasoning Agent for deep analysis."""
        logger.info("Escalating to Reasoning Agent for RCA")

        try:
            context = f"""
Fast Agent Assessment: {annotation.content}
Severity: {annotation.metadata.get('severity', 'unknown')}
Category: {annotation.metadata.get('category', 'unknown')}
Telemetry: {window.log_count} logs, {len(window.metrics)} metrics, {len(window.traces)} traces

Please perform root cause analysis and suggest remediation actions.
"""
            rca_result = await self.reasoning_agent.analyze_incident({
                "service": "combined",
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
                    affected_services=["combined"],
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
