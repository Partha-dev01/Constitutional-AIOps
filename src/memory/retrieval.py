"""
Constitutional AIOps - Context Retrieval

Retrieves relevant context from episodic memory for LLM prompts.
Implements RAG (Retrieval Augmented Generation) patterns for better RCA.

Hybrid Retrieval Formula (from Research_V5.tex):
    score(e) = α · vector_sim(e) + (1-α) · graph_sim(e)

Where:
    α = 0.6 (default) - weight for vector similarity
    (1-α) = 0.4 - weight for graph-based similarity

This implements the AriGraph-inspired dual-memory architecture combining
semantic (vector) and episodic (graph) retrieval strategies.
"""

import logging

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

# Hybrid Retrieval Configuration (from Research_V5.tex)
RETRIEVAL_ALPHA = 0.6  # Weight for vector_sim in: α·vector_sim + (1-α)·graph_sim

from src.memory.episode_store import Episode, EpisodeStore
from src.memory.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """
    Context retrieved from episodic memory for LLM augmentation.

    Used to enrich prompts with relevant historical information.
    """

    # Similar incidents
    similar_incidents: list[dict[str, Any]]

    # Service context
    service_dependencies: list[dict[str, Any]]
    recent_service_incidents: list[dict[str, Any]]

    # Pattern information
    successful_remediation_patterns: list[dict[str, Any]]
    common_root_causes: list[str]

    # Statistics
    category_stats: dict[str, Any]
    service_reliability: dict[str, float]

    # Metadata
    retrieval_timestamp: datetime
    query_time_ms: float

    def to_prompt_context(self, max_tokens: int = 2000) -> str:
        """
        Convert context to a string for LLM prompt.

        Args:
            max_tokens: Approximate max tokens (rough estimate)

        Returns:
            Formatted context string
        """
        sections = []

        # Similar incidents section
        if self.similar_incidents:
            similar_text = "## Similar Past Incidents\n"
            for i, incident in enumerate(self.similar_incidents[:3], 1):
                similar_text += f"{i}. **{incident.get('title', 'Unknown')}** (Severity: {incident.get('severity', 'N/A')})\n"
                if incident.get('root_cause'):
                    similar_text += f"   Root Cause: {incident['root_cause']}\n"
                if incident.get('successful_actions'):
                    similar_text += f"   Resolution: {', '.join(incident['successful_actions'][:2])}\n"
            sections.append(similar_text)

        # Service dependencies
        if self.service_dependencies:
            deps_text = "## Service Dependencies\n"
            for dep in self.service_dependencies[:5]:
                deps_text += f"- {dep.get('name', 'Unknown')} (distance: {dep.get('distance', 'N/A')})\n"
            sections.append(deps_text)

        # Successful patterns
        if self.successful_remediation_patterns:
            patterns_text = "## Successful Remediation Patterns\n"
            for pattern in self.successful_remediation_patterns[:3]:
                actions = pattern.get('successful_actions', [])
                if actions:
                    patterns_text += f"- {pattern.get('root_cause_type', 'Unknown')}: {', '.join(actions[:2])}\n"
            sections.append(patterns_text)

        # Common root causes
        if self.common_root_causes:
            causes_text = "## Common Root Causes for This Category\n"
            for cause in self.common_root_causes[:5]:
                causes_text += f"- {cause}\n"
            sections.append(causes_text)

        # Combine and truncate if needed
        full_context = "\n".join(sections)

        # Rough token estimate (4 chars per token)
        if len(full_context) > max_tokens * 4:
            full_context = full_context[: max_tokens * 4] + "\n...(truncated)"

        return full_context

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "similar_incidents": self.similar_incidents,
            "service_dependencies": self.service_dependencies,
            "recent_service_incidents": self.recent_service_incidents,
            "successful_remediation_patterns": self.successful_remediation_patterns,
            "common_root_causes": self.common_root_causes,
            "category_stats": self.category_stats,
            "service_reliability": self.service_reliability,
            "retrieval_timestamp": self.retrieval_timestamp.isoformat(),
            "query_time_ms": self.query_time_ms,
        }


class ContextRetriever:
    """
    Retrieves relevant context from episodic memory.

    Implements various retrieval strategies:
    - Similarity-based retrieval
    - Service graph traversal
    - Pattern matching
    - Statistical analysis
    """

    def __init__(
        self,
        episode_store: Optional[EpisodeStore] = None,
        neo4j_client: Optional[Neo4jClient] = None,
    ):
        """
        Initialize context retriever.

        Args:
            episode_store: Episode store instance
            neo4j_client: Neo4j client instance
        """
        self.episode_store = episode_store
        self.neo4j_client = neo4j_client

        # Cache for frequently accessed data
        self._root_cause_cache: dict[str, list[str]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)

        logger.info("ContextRetriever initialized")

    async def retrieve_for_incident(
        self,
        incident: dict[str, Any],
        max_similar: int = 5,
        include_patterns: bool = True,
        include_dependencies: bool = True,
    ) -> RetrievalContext:
        """
        Retrieve all relevant context for an incident.

        Args:
            incident: Incident data dictionary
            max_similar: Maximum similar incidents to retrieve
            include_patterns: Include remediation patterns
            include_dependencies: Include service dependencies

        Returns:
            RetrievalContext with all relevant information
        """
        import time

        start_time = time.perf_counter()

        # Extract incident attributes
        category = incident.get("category", "unknown")
        severity = incident.get("severity", "medium")
        affected_services = self._extract_services(incident)
        title = incident.get("title", "")
        description = incident.get("description", "")

        # Retrieve similar incidents
        similar_incidents = await self._find_similar_incidents(
            category=category,
            services=affected_services,
            title=title,
            limit=max_similar,
        )

        # Retrieve service dependencies
        service_dependencies = []
        recent_service_incidents = []
        if include_dependencies and affected_services:
            for service in affected_services[:3]:  # Limit to first 3 services
                deps = await self._get_service_dependencies(service)
                service_dependencies.extend(deps)

                recent = await self._get_recent_service_incidents(service)
                recent_service_incidents.extend(recent)

        # Retrieve successful remediation patterns
        successful_patterns = []
        if include_patterns:
            successful_patterns = await self._get_successful_patterns(
                category=category,
                services=affected_services,
            )

        # Get common root causes for category
        common_root_causes = await self._get_common_root_causes(category)

        # Get category statistics
        category_stats = await self._get_category_stats(category)

        # Calculate service reliability scores
        service_reliability = {}
        for service in affected_services:
            reliability = await self._calculate_service_reliability(service)
            service_reliability[service] = reliability

        query_time = (time.perf_counter() - start_time) * 1000

        return RetrievalContext(
            similar_incidents=similar_incidents,
            service_dependencies=service_dependencies,
            recent_service_incidents=recent_service_incidents,
            successful_remediation_patterns=successful_patterns,
            common_root_causes=common_root_causes,
            category_stats=category_stats,
            service_reliability=service_reliability,
            retrieval_timestamp=datetime.utcnow(),
            query_time_ms=round(query_time, 2),
        )

    async def retrieve_for_rca(
        self,
        incident: dict[str, Any],
        telemetry_summary: Optional[str] = None,
    ) -> str:
        """
        Retrieve context specifically formatted for RCA prompts.

        Args:
            incident: Incident data
            telemetry_summary: Optional compressed telemetry

        Returns:
            Formatted context string for RCA prompt
        """
        context = await self.retrieve_for_incident(
            incident=incident,
            max_similar=3,
            include_patterns=True,
            include_dependencies=True,
        )

        prompt_context = context.to_prompt_context(max_tokens=1500)

        if telemetry_summary:
            prompt_context = f"## Current Telemetry\n{telemetry_summary}\n\n{prompt_context}"

        return prompt_context

    async def retrieve_for_planning(
        self,
        root_cause: str,
        affected_services: list[str],
        category: str,
    ) -> str:
        """
        Retrieve context for remediation planning.

        Args:
            root_cause: Identified root cause
            affected_services: List of affected services
            category: Incident category

        Returns:
            Formatted context for planning prompt
        """
        sections = []

        # Get successful patterns for this type of root cause
        patterns = await self._get_successful_patterns(
            category=category,
            services=affected_services,
        )

        if patterns:
            sections.append("## Previously Successful Remediations")
            for pattern in patterns[:3]:
                actions = pattern.get('successful_actions', [])
                if actions:
                    sections.append(f"- Root cause type: {pattern.get('root_cause_type', 'Unknown')}")
                    sections.append(f"  Actions: {', '.join(actions)}")
                    if pattern.get('resolution_time_minutes'):
                        sections.append(f"  Resolution time: {pattern['resolution_time_minutes']:.0f} minutes")

        # Get service dependencies for impact assessment
        all_deps = []
        for service in affected_services[:3]:
            deps = await self._get_service_dependencies(service)
            all_deps.extend(deps)

        if all_deps:
            sections.append("\n## Potential Impact (Downstream Services)")
            seen = set()
            for dep in all_deps[:5]:
                name = dep.get('name')
                if name and name not in seen:
                    sections.append(f"- {name}")
                    seen.add(name)

        return "\n".join(sections)

    async def hybrid_retrieve(
        self,
        incident: dict[str, Any],
        alpha: float = 0.6,
        limit: int = 5,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Hybrid retrieval combining graph traversal with similarity search.

        Following AriGraph pattern for combining episodic and semantic memory.

        Args:
            incident: Incident data to find similar episodes for
            alpha: Weight for graph-based score (1-alpha for similarity-based)
            limit: Maximum results

        Returns:
            List of (episode_data, combined_score) tuples
        """
        category = incident.get("category", "unknown")
        affected_services = self._extract_services(incident)
        title = incident.get("title", "")

        combined_results: dict[str, tuple[dict, float]] = {}

        # 1. Graph-based retrieval: find episodes with same root cause type
        if self.neo4j_client:
            try:
                # Get root cause type from incident if available
                root_cause = incident.get("root_cause", "")
                if root_cause:
                    # Infer root cause type using same logic as Episode class
                    root_cause_type = self._infer_root_cause_type(root_cause)
                    graph_results = await self.neo4j_client.find_episodes_by_root_cause_type(
                        root_cause_type,
                        limit=limit * 2,
                    )

                    for result in graph_results:
                        ep_id = result.get("episode_id", "")
                        if ep_id:
                            combined_results[ep_id] = (
                                result,
                                result.get("confidence", 0.5) * (1 - alpha),
                            )
            except Exception as e:
                logger.warning(f"Graph retrieval failed: {e}")

        # 2. Similarity-based retrieval: find similar episodes by category/services
        if self.episode_store:
            try:
                similar = await self._find_similar_incidents(
                    category=category,
                    services=affected_services,
                    title=title,
                    limit=limit * 2,
                )

                for ep_data in similar:
                    ep_id = ep_data.get("incident_id", "")
                    sim_score = ep_data.get("similarity_score", 0.5)

                    if ep_id in combined_results:
                        # Combine scores
                        existing = combined_results[ep_id]
                        new_score = existing[1] + (sim_score * alpha)
                        combined_results[ep_id] = (existing[0], new_score)
                    else:
                        combined_results[ep_id] = (ep_data, sim_score * alpha)

            except Exception as e:
                logger.warning(f"Similarity retrieval failed: {e}")

        # Sort by combined score and return top results
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x[1],
            reverse=True,
        )

        return sorted_results[:limit]

    def _infer_root_cause_type(self, root_cause: str) -> str:
        """Infer root cause type from description (mirrors Episode logic)."""
        if not root_cause:
            return "unknown"

        root_cause_lower = root_cause.lower()

        if any(word in root_cause_lower for word in ["memory", "oom", "heap", "leak"]):
            return "memory"
        elif any(word in root_cause_lower for word in ["cpu", "processor", "compute"]):
            return "cpu"
        elif any(word in root_cause_lower for word in ["disk", "storage", "io"]):
            return "storage"
        elif any(word in root_cause_lower for word in ["network", "connection", "timeout", "latency"]):
            return "network"
        elif any(word in root_cause_lower for word in ["database", "query", "deadlock", "connection pool"]):
            return "database"
        elif any(word in root_cause_lower for word in ["config", "configuration", "setting"]):
            return "configuration"
        elif any(word in root_cause_lower for word in ["deploy", "release", "version"]):
            return "deployment"
        elif any(word in root_cause_lower for word in ["dependency", "upstream", "downstream"]):
            return "dependency"
        else:
            return "other"

    def _extract_services(self, incident: dict[str, Any]) -> list[str]:
        """Extract service names from incident data."""
        services = []

        # From affected_services list
        affected = incident.get("affected_services", [])
        for service in affected:
            if isinstance(service, dict):
                services.append(service.get("name", ""))
            elif isinstance(service, str):
                services.append(service)

        # Filter empty
        return [s for s in services if s]

    async def _find_similar_incidents(
        self,
        category: str,
        services: list[str],
        title: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find similar incidents from episode store."""
        if not self.episode_store:
            return []

        similar = []

        # Create a pseudo-episode for comparison
        pseudo_episode = Episode(
            episode_id="query",
            incident_id="query",
            title=title,
            description="",
            severity="medium",
            category=category,
            detected_at=datetime.utcnow(),
            affected_services=services,
        )

        try:
            results = await self.episode_store.find_similar_episodes(
                pseudo_episode,
                limit=limit,
                min_similarity=0.3,
            )

            for episode, score in results:
                similar.append({
                    "incident_id": episode.incident_id,
                    "title": episode.title,
                    "severity": episode.severity,
                    "category": episode.category,
                    "root_cause": episode.root_cause,
                    "successful_actions": episode.successful_actions,
                    "similarity_score": score,
                })

        except Exception as e:
            logger.warning(f"Failed to find similar incidents: {e}")

        return similar

    async def _get_service_dependencies(
        self,
        service_name: str,
    ) -> list[dict[str, Any]]:
        """Get dependencies for a service."""
        if not self.neo4j_client:
            return []

        try:
            return await self.neo4j_client.get_service_dependencies(
                service_name,
                depth=2,
            )
        except Exception as e:
            logger.warning(f"Failed to get service dependencies: {e}")
            return []

    async def _get_recent_service_incidents(
        self,
        service_name: str,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """Get recent incidents for a service."""
        if not self.episode_store:
            return []

        try:
            episodes = await self.episode_store.find_by_service(
                service_name,
                limit=5,
            )

            # Filter to recent ones
            cutoff = datetime.utcnow() - timedelta(days=days)
            recent = [
                {
                    "incident_id": ep.incident_id,
                    "title": ep.title,
                    "severity": ep.severity,
                    "detected_at": ep.detected_at.isoformat(),
                }
                for ep in episodes
                if ep.detected_at > cutoff
            ]

            return recent

        except Exception as e:
            logger.warning(f"Failed to get recent service incidents: {e}")
            return []

    async def _get_successful_patterns(
        self,
        category: str,
        services: list[str],
    ) -> list[dict[str, Any]]:
        """Get successful remediation patterns."""
        if not self.episode_store:
            return []

        try:
            patterns = await self.episode_store.get_successful_remediation_patterns(
                category=category,
                service=services[0] if services else None,
                limit=5,
            )
            return patterns

        except Exception as e:
            logger.warning(f"Failed to get successful patterns: {e}")
            return []

    async def _get_common_root_causes(self, category: str) -> list[str]:
        """Get common root causes for a category."""
        # Check cache
        if self._cache_timestamp and datetime.utcnow() - self._cache_timestamp < self._cache_ttl:
            if category in self._root_cause_cache:
                return self._root_cause_cache[category]

        if not self.episode_store:
            return self._get_default_root_causes(category)

        try:
            # Count root cause types from episodes
            root_cause_counts: dict[str, int] = {}

            for episode in self.episode_store._memory_store.values():
                if episode.category == category and episode.root_cause:
                    rc_type = episode._extract_root_cause_type()
                    root_cause_counts[rc_type] = root_cause_counts.get(rc_type, 0) + 1

            # Sort by frequency
            sorted_causes = sorted(
                root_cause_counts.keys(),
                key=lambda x: root_cause_counts[x],
                reverse=True,
            )

            # Cache and return
            self._root_cause_cache[category] = sorted_causes
            self._cache_timestamp = datetime.utcnow()

            return sorted_causes if sorted_causes else self._get_default_root_causes(category)

        except Exception as e:
            logger.warning(f"Failed to get common root causes: {e}")
            return self._get_default_root_causes(category)

    def _get_default_root_causes(self, category: str) -> list[str]:
        """Get default root causes by category."""
        defaults = {
            "performance": ["memory leak", "cpu saturation", "network latency", "database slow queries"],
            "error": ["null pointer", "configuration error", "dependency failure", "timeout"],
            "availability": ["instance crash", "health check failure", "resource exhaustion", "network partition"],
            "resource": ["disk full", "memory exhaustion", "connection pool exhaustion", "file descriptor limit"],
            "security": ["authentication failure", "certificate expiry", "unauthorized access", "rate limiting"],
            "configuration": ["misconfiguration", "environment mismatch", "missing secrets", "invalid schema"],
        }
        return defaults.get(category, ["unknown cause"])

    async def _get_category_stats(self, category: str) -> dict[str, Any]:
        """Get statistics for a category."""
        if not self.neo4j_client:
            return {}

        try:
            stats = await self.neo4j_client.get_incident_stats(days=30)
            return stats
        except Exception as e:
            logger.warning(f"Failed to get category stats: {e}")
            return {}

    async def _calculate_service_reliability(
        self,
        service_name: str,
        days: int = 30,
    ) -> float:
        """
        Calculate reliability score for a service.

        Returns:
            Reliability score (0.0-1.0)
        """
        if not self.episode_store:
            return 0.95  # Default high reliability

        try:
            episodes = await self.episode_store.find_by_service(service_name, limit=100)

            cutoff = datetime.utcnow() - timedelta(days=days)
            recent_episodes = [ep for ep in episodes if ep.detected_at > cutoff]

            if not recent_episodes:
                return 0.99  # No incidents = high reliability

            # Calculate based on incident count and severity
            severity_weights = {
                "critical": 0.3,
                "high": 0.2,
                "medium": 0.1,
                "low": 0.05,
                "info": 0.02,
            }

            total_impact = sum(
                severity_weights.get(ep.severity, 0.1)
                for ep in recent_episodes
            )

            # Convert to reliability score (fewer incidents = higher reliability)
            reliability = max(0.0, 1.0 - (total_impact / 10))
            return round(reliability, 2)

        except Exception as e:
            logger.warning(f"Failed to calculate service reliability: {e}")
            return 0.95


__all__ = ["RetrievalContext", "ContextRetriever"]
