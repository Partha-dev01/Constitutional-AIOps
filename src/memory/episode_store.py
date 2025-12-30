"""
Constitutional AIOps - Episode Store

Manages episodic memory for incidents, storing complete incident lifecycles
as "episodes" that can be retrieved for similar situation analysis.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.memory.neo4j_client import Neo4jClient, NEO4J_AVAILABLE

logger = logging.getLogger(__name__)


@dataclass
class Episode:
    """
    An episode represents a complete incident lifecycle.

    Episodes are used for:
    - Learning from past incidents
    - Finding similar situations
    - Improving RCA accuracy
    - Training remediation strategies
    """

    episode_id: str
    incident_id: str
    title: str
    description: str
    severity: str
    category: str

    # Timeline
    detected_at: datetime
    analyzed_at: Optional[datetime] = None
    remediated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Analysis results
    root_cause: Optional[str] = None
    causal_chain: list[str] = field(default_factory=list)
    confidence: float = 0.0

    # Actions taken
    actions: list[dict[str, Any]] = field(default_factory=list)
    successful_actions: list[str] = field(default_factory=list)
    failed_actions: list[str] = field(default_factory=list)

    # Context
    affected_services: list[str] = field(default_factory=list)
    telemetry_summary: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    # Outcome
    outcome: str = "unknown"  # resolved, escalated, recurring
    resolution_notes: Optional[str] = None
    human_feedback: Optional[str] = None

    # Embedding for similarity search (optional)
    embedding: Optional[list[float]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert episode to dictionary."""
        return {
            "episode_id": self.episode_id,
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "remediated_at": self.remediated_at.isoformat() if self.remediated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "root_cause": self.root_cause,
            "causal_chain": self.causal_chain,
            "confidence": self.confidence,
            "actions": self.actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "affected_services": self.affected_services,
            "telemetry_summary": self.telemetry_summary,
            "tags": self.tags,
            "outcome": self.outcome,
            "resolution_notes": self.resolution_notes,
            "human_feedback": self.human_feedback,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Episode":
        """Create episode from dictionary."""
        return cls(
            episode_id=data["episode_id"],
            incident_id=data["incident_id"],
            title=data["title"],
            description=data.get("description", ""),
            severity=data["severity"],
            category=data.get("category", "unknown"),
            detected_at=datetime.fromisoformat(data["detected_at"]) if data.get("detected_at") else datetime.utcnow(),
            analyzed_at=datetime.fromisoformat(data["analyzed_at"]) if data.get("analyzed_at") else None,
            remediated_at=datetime.fromisoformat(data["remediated_at"]) if data.get("remediated_at") else None,
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            root_cause=data.get("root_cause"),
            causal_chain=data.get("causal_chain", []),
            confidence=data.get("confidence", 0.0),
            actions=data.get("actions", []),
            successful_actions=data.get("successful_actions", []),
            failed_actions=data.get("failed_actions", []),
            affected_services=data.get("affected_services", []),
            telemetry_summary=data.get("telemetry_summary"),
            tags=data.get("tags", []),
            outcome=data.get("outcome", "unknown"),
            resolution_notes=data.get("resolution_notes"),
            human_feedback=data.get("human_feedback"),
        )

    def generate_signature(self) -> str:
        """Generate a signature for similarity matching."""
        # Combine key fields for hashing
        signature_data = {
            "category": self.category,
            "services": sorted(self.affected_services),
            "root_cause_type": self._extract_root_cause_type(),
        }
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()

    def _extract_root_cause_type(self) -> str:
        """Extract root cause type from root cause description."""
        if not self.root_cause:
            return "unknown"

        root_cause_lower = self.root_cause.lower()

        # Common root cause categories
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

    def extract_semantic_triplets(self) -> list[dict[str, Any]]:
        """
        Extract semantic triplets (entity, relation, entity) from episode.

        Following AriGraph pattern for knowledge graph construction.
        Returns triplets that can be stored in Neo4j for semantic memory.
        """
        triplets = []

        # Service-to-issue triplets
        root_cause_type = self._extract_root_cause_type()
        for service in self.affected_services:
            if self.root_cause:
                triplets.append({
                    "entity1": service,
                    "relation": "EXPERIENCED",
                    "entity2": root_cause_type,
                    "confidence": self.confidence,
                    "source_episode_id": self.episode_id,
                })

        # Causal chain triplets
        for i in range(len(self.causal_chain) - 1):
            triplets.append({
                "entity1": self.causal_chain[i],
                "relation": "CAUSED",
                "entity2": self.causal_chain[i + 1],
                "confidence": 0.8,
                "source_episode_id": self.episode_id,
            })

        # Service dependency triplets (if multiple services affected)
        if len(self.affected_services) > 1:
            primary_service = self.affected_services[0]
            for dependent in self.affected_services[1:]:
                triplets.append({
                    "entity1": primary_service,
                    "relation": "IMPACTED",
                    "entity2": dependent,
                    "confidence": 0.7,
                    "source_episode_id": self.episode_id,
                })

        # Successful action triplets (for learning)
        for action in self.successful_actions:
            triplets.append({
                "entity1": root_cause_type,
                "relation": "RESOLVED_BY",
                "entity2": action,
                "confidence": 0.9,
                "source_episode_id": self.episode_id,
            })

        return triplets

    def get_embedding_text(self) -> str:
        """
        Generate text for embedding creation.

        Combines key fields into a single text for vector embedding.
        """
        parts = [
            self.title,
            self.description or "",
            f"Category: {self.category}",
            f"Severity: {self.severity}",
        ]

        if self.root_cause:
            parts.append(f"Root Cause: {self.root_cause}")

        if self.affected_services:
            parts.append(f"Services: {', '.join(self.affected_services)}")

        if self.causal_chain:
            parts.append(f"Causal Chain: {' -> '.join(self.causal_chain)}")

        return " ".join(parts)


@dataclass
class SemanticTriplet:
    """
    Represents a semantic triplet (entity, relation, entity).

    Used for building the semantic knowledge graph in Neo4j.
    Following AriGraph's dual-memory architecture.
    """

    entity1: str
    relation: str
    entity2: str
    confidence: float
    source_episode_id: str
    extraction_method: str = "rule"  # "llm" | "rule" | "pattern"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "entity1": self.entity1,
            "relation": self.relation,
            "entity2": self.entity2,
            "confidence": self.confidence,
            "source_episode_id": self.source_episode_id,
            "extraction_method": self.extraction_method,
        }


class EpisodeStore:
    """
    Manages storage and retrieval of incident episodes.

    Uses Neo4j for graph-based storage and similarity search.
    Falls back to in-memory storage if Neo4j is unavailable.
    """

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """
        Initialize episode store.

        Args:
            neo4j_client: Optional Neo4j client instance
        """
        self.neo4j_client = neo4j_client
        self._memory_store: dict[str, Episode] = {}  # Fallback storage
        self._signature_index: dict[str, list[str]] = {}  # Signature -> episode_ids

        logger.info("EpisodeStore initialized")

    async def store_episode(self, episode: Episode) -> str:
        """
        Store an episode in the database.

        Args:
            episode: Episode to store

        Returns:
            Episode ID
        """
        # Always store in memory for fast access
        self._memory_store[episode.episode_id] = episode

        # Index by signature for similarity search
        signature = episode.generate_signature()
        if signature not in self._signature_index:
            self._signature_index[signature] = []
        if episode.episode_id not in self._signature_index[signature]:
            self._signature_index[signature].append(episode.episode_id)

        # Store in Neo4j if available
        if self.neo4j_client and NEO4J_AVAILABLE:
            try:
                await self._store_episode_graph(episode)
            except Exception as e:
                logger.warning(f"Failed to store episode in Neo4j: {e}")

        logger.info(f"Stored episode {episode.episode_id}")
        return episode.episode_id

    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        """
        Retrieve an episode by ID.

        Args:
            episode_id: Episode ID

        Returns:
            Episode or None
        """
        # Check memory first
        if episode_id in self._memory_store:
            return self._memory_store[episode_id]

        # Try Neo4j
        if self.neo4j_client and NEO4J_AVAILABLE:
            try:
                return await self._get_episode_graph(episode_id)
            except Exception as e:
                logger.warning(f"Failed to get episode from Neo4j: {e}")

        return None

    async def find_similar_episodes(
        self,
        episode: Episode,
        limit: int = 5,
        min_similarity: float = 0.3,
    ) -> list[tuple[Episode, float]]:
        """
        Find similar episodes based on characteristics.

        Args:
            episode: Reference episode
            limit: Maximum results
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of (Episode, similarity_score) tuples
        """
        similar = []

        # Method 1: Signature-based matching (fast)
        signature = episode.generate_signature()
        if signature in self._signature_index:
            for ep_id in self._signature_index[signature]:
                if ep_id != episode.episode_id and ep_id in self._memory_store:
                    similar.append((self._memory_store[ep_id], 0.8))  # High similarity for same signature

        # Method 2: Service overlap matching
        for ep_id, stored_episode in self._memory_store.items():
            if ep_id == episode.episode_id:
                continue

            score = self._calculate_similarity(episode, stored_episode)
            if score >= min_similarity:
                # Check if already added via signature
                if not any(s[0].episode_id == ep_id for s in similar):
                    similar.append((stored_episode, score))

        # Sort by similarity and limit
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]

    async def find_by_service(
        self,
        service_name: str,
        limit: int = 10,
    ) -> list[Episode]:
        """
        Find episodes affecting a specific service.

        Args:
            service_name: Service name
            limit: Maximum results

        Returns:
            List of episodes
        """
        results = []

        for episode in self._memory_store.values():
            if service_name in episode.affected_services:
                results.append(episode)

        # Sort by recency
        results.sort(key=lambda e: e.detected_at, reverse=True)
        return results[:limit]

    async def find_by_root_cause_type(
        self,
        root_cause_type: str,
        limit: int = 10,
    ) -> list[Episode]:
        """
        Find episodes with similar root cause type.

        Args:
            root_cause_type: Root cause category
            limit: Maximum results

        Returns:
            List of episodes
        """
        results = []

        for episode in self._memory_store.values():
            if episode._extract_root_cause_type() == root_cause_type:
                results.append(episode)

        results.sort(key=lambda e: e.detected_at, reverse=True)
        return results[:limit]

    async def update_episode(
        self,
        episode_id: str,
        updates: dict[str, Any],
    ) -> Optional[Episode]:
        """
        Update an episode with new information.

        Args:
            episode_id: Episode ID
            updates: Fields to update

        Returns:
            Updated episode or None
        """
        episode = await self.get_episode(episode_id)
        if not episode:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(episode, key):
                setattr(episode, key, value)

        # Re-store with updates
        await self.store_episode(episode)
        return episode

    async def record_action_outcome(
        self,
        episode_id: str,
        action_id: str,
        success: bool,
        action_description: str,
    ) -> None:
        """
        Record the outcome of an action for learning.

        Args:
            episode_id: Episode ID
            action_id: Action ID
            success: Whether action succeeded
            action_description: Description of the action
        """
        episode = await self.get_episode(episode_id)
        if not episode:
            return

        if success:
            if action_description not in episode.successful_actions:
                episode.successful_actions.append(action_description)
        else:
            if action_description not in episode.failed_actions:
                episode.failed_actions.append(action_description)

        await self.store_episode(episode)

    async def get_successful_remediation_patterns(
        self,
        category: str,
        service: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get patterns of successful remediations for learning.

        Args:
            category: Incident category
            service: Optional service filter
            limit: Maximum results

        Returns:
            List of successful remediation patterns
        """
        patterns = []

        for episode in self._memory_store.values():
            if episode.category != category:
                continue
            if service and service not in episode.affected_services:
                continue
            if episode.outcome != "resolved":
                continue
            if not episode.successful_actions:
                continue

            patterns.append({
                "root_cause_type": episode._extract_root_cause_type(),
                "successful_actions": episode.successful_actions,
                "confidence": episode.confidence,
                "resolution_time_minutes": (
                    (episode.resolved_at - episode.detected_at).total_seconds() / 60
                    if episode.resolved_at and episode.detected_at
                    else None
                ),
            })

        # Sort by confidence
        patterns.sort(key=lambda p: p["confidence"], reverse=True)
        return patterns[:limit]

    def _calculate_similarity(self, ep1: Episode, ep2: Episode) -> float:
        """Calculate similarity score between two episodes."""
        score = 0.0
        weights_total = 0.0

        # Category match (weight: 0.3)
        if ep1.category == ep2.category:
            score += 0.3
        weights_total += 0.3

        # Service overlap (weight: 0.4)
        if ep1.affected_services and ep2.affected_services:
            services1 = set(ep1.affected_services)
            services2 = set(ep2.affected_services)
            overlap = len(services1 & services2)
            total = len(services1 | services2)
            if total > 0:
                score += 0.4 * (overlap / total)
        weights_total += 0.4

        # Root cause type match (weight: 0.3)
        if ep1._extract_root_cause_type() == ep2._extract_root_cause_type():
            score += 0.3
        weights_total += 0.3

        return score / weights_total if weights_total > 0 else 0.0

    async def _store_episode_graph(self, episode: Episode) -> None:
        """Store episode in Neo4j graph."""
        if not self.neo4j_client:
            return

        async with self.neo4j_client.session() as session:
            # Create Episode node
            query = """
            MERGE (e:Episode {episode_id: $episode_id})
            SET e.incident_id = $incident_id,
                e.title = $title,
                e.category = $category,
                e.severity = $severity,
                e.root_cause = $root_cause,
                e.outcome = $outcome,
                e.confidence = $confidence,
                e.detected_at = datetime($detected_at)
            """

            await session.run(
                query,
                episode_id=episode.episode_id,
                incident_id=episode.incident_id,
                title=episode.title,
                category=episode.category,
                severity=episode.severity,
                root_cause=episode.root_cause,
                outcome=episode.outcome,
                confidence=episode.confidence,
                detected_at=episode.detected_at.isoformat(),
            )

            # Link to services
            for service in episode.affected_services:
                service_query = """
                MATCH (e:Episode {episode_id: $episode_id})
                MERGE (s:Service {name: $service_name})
                MERGE (e)-[:INVOLVES]->(s)
                """
                await session.run(
                    service_query,
                    episode_id=episode.episode_id,
                    service_name=service,
                )

    async def _get_episode_graph(self, episode_id: str) -> Optional[Episode]:
        """Get episode from Neo4j graph."""
        if not self.neo4j_client:
            return None

        async with self.neo4j_client.session() as session:
            query = """
            MATCH (e:Episode {episode_id: $episode_id})
            OPTIONAL MATCH (e)-[:INVOLVES]->(s:Service)
            RETURN e, collect(s.name) as services
            """

            result = await session.run(query, episode_id=episode_id)
            record = await result.single()

            if not record:
                return None

            ep_data = dict(record["e"])
            ep_data["affected_services"] = record["services"]

            return Episode.from_dict(ep_data)


__all__ = ["Episode", "EpisodeStore", "SemanticTriplet"]
