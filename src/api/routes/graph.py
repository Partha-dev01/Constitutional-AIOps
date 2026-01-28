"""
Constitutional AIOps - Graph API Routes

Provides endpoints for Neo4j graph queries including:
- Episodic memory graphs (Graphiti-style)
- Root cause correlation
- Action success patterns
- Service impact analysis
- Episode generation via Reasoning Agent

Graph Model (from Research_V6.tex):
- Episodes → CAUSED_BY → RootCauseType
- Episodes → RESOLVED_BY → Action
- Episodes → AFFECTS → Service
- Episodes → SIMILAR_TO → Episode
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter()

# =============================================================================
# Graph Schema Constants (v0.6.0 - Optimized for clean visualization)
# =============================================================================
# These constants prevent the "hairball" graph problem by limiting edge creation

# SIMILAR_TO edge threshold: Only connect highly similar episodes
# Old value: 0.5 (created O(n²) edges) → New value: 0.75
SIMILAR_TO_THRESHOLD = 0.75

# Maximum SIMILAR_TO edges per episode (prevents hub-and-spoke patterns)
MAX_SIMILAR_EDGES_PER_EPISODE = 3

# Minimum confidence for LLM-extracted entity triplets
MIN_TRIPLET_CONFIDENCE = 0.70

# Maximum edges per node for visualization (degree capping)
MAX_EDGES_PER_NODE = 5

# =============================================================================


class ServiceNode(BaseModel):
    """Service node - only shown when affected by episodes."""
    name: str
    type: str = "service"
    status: str = Field(default="healthy", description="Status: healthy, warning, critical")
    incident_count: int = Field(default=0, description="Number of incidents affecting this service")
    last_incident: datetime | None = Field(default=None, description="Last incident timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("last_incident", mode="before")
    @classmethod
    def convert_neo4j_datetime(cls, v):
        """Convert Neo4j DateTime to Python datetime."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if hasattr(v, "to_native"):
            return v.to_native()
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class RootCauseNode(BaseModel):
    """Root cause type node - semantic abstraction of failure patterns."""
    id: str
    name: str  # e.g., "connection_timeout", "memory_leak", "disk_full"
    type: str = "root_cause"
    frequency: int = Field(default=0, description="How many episodes caused by this")
    avg_resolution_time_minutes: float = Field(default=0, description="Average time to resolve")
    success_rate: float = Field(default=0, description="Success rate of resolutions")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionNode(BaseModel):
    """Action node - remediation actions with success patterns."""
    id: str
    name: str  # e.g., "scale_replicas", "restart_pod", "increase_pool_size"
    type: str = "action"
    used_count: int = Field(default=0, description="Times this action was used")
    success_rate: float = Field(default=0, description="Success rate 0-1")
    avg_execution_time_seconds: float = Field(default=0, description="Average execution time")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EpisodeNode(BaseModel):
    """Episode node - a complete incident lifecycle."""
    id: str
    title: str
    type: str = "episode"
    timestamp: datetime
    category: str
    severity: str  # critical, high, medium, low
    status: str = "resolved"  # resolved, active, escalated
    root_cause: str | None = None
    confidence: float = 0
    resolution_time_minutes: float | None = None
    services: list[str] = Field(default_factory=list)
    successful_actions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def convert_neo4j_datetime(cls, v):
        """Convert Neo4j DateTime to Python datetime."""
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            return v
        if hasattr(v, "to_native"):
            return v.to_native()
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class EntityNode(BaseModel):
    """Entity node - LLM-extracted entity from semantic triplets."""
    id: str
    name: str
    type: str = "entity"
    relation_count: int = Field(default=0, description="Number of relations involving this entity")
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Graph edge with relationship type."""
    source: str  # Node ID
    target: str  # Node ID
    relationship: str  # CAUSED_BY, RESOLVED_BY, AFFECTS, SIMILAR_TO
    weight: float = Field(default=1.0, description="Edge weight (e.g., similarity score)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EpisodicGraphData(BaseModel):
    """Complete episodic memory graph for visualization."""
    episodes: list[EpisodeNode]
    root_causes: list[RootCauseNode]
    actions: list[ActionNode]
    services: list[ServiceNode]
    entities: list[EntityNode] = Field(default_factory=list)  # LLM-extracted entities
    edges: list[GraphEdge]
    stats: dict[str, Any] = Field(default_factory=dict)


# Legacy models for backward compatibility
class Episode(BaseModel):
    """Episode from episodic memory (legacy)."""
    id: str
    title: str
    timestamp: datetime
    category: str
    severity: str
    services: list[str]
    root_cause: str | None = None
    resolution: str | None = None
    confidence: float = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def convert_neo4j_datetime(cls, v):
        """Convert Neo4j DateTime to Python datetime."""
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            return v
        if hasattr(v, "to_native"):
            return v.to_native()
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class GraphData(BaseModel):
    """Graph data for visualization (legacy)."""
    services: list[ServiceNode]
    episodes: list[Episode]
    edges: list[dict[str, Any]]


class DependencyGraph(BaseModel):
    """Service dependency graph."""
    service: str
    upstream: list[str]
    downstream: list[str]
    depth: int


class SimilarEpisode(BaseModel):
    """Similar episode from memory search."""
    episode: Episode
    similarity_score: float


class EpisodeListResponse(BaseModel):
    """Response listing episodes."""
    episodes: list[Episode]
    total: int


class GraphStatsResponse(BaseModel):
    """Graph database statistics."""
    connected: bool
    node_count: int
    edge_count: int
    episode_count: int


@router.get(
    "/episodes",
    response_model=EpisodicGraphData,
    summary="Get Episodic Memory Graph",
    description="Get complete episodic memory graph with episodes, root causes, actions, and relationships",
)
async def get_episodes(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    since_hours: int = Query(168, description="Get episodes from last N hours (default 7 days)"),
    # v0.6.0: Filtering parameters to prevent hairball visualization
    min_similarity: float = Query(
        SIMILAR_TO_THRESHOLD,
        ge=0.5,
        le=1.0,
        description="Minimum similarity threshold for SIMILAR_TO edges (default 0.75)",
    ),
    min_confidence: float = Query(
        MIN_TRIPLET_CONFIDENCE,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for entity edges (default 0.70)",
    ),
    include_similar_to: bool = Query(
        True,
        description="Include SIMILAR_TO edges between episodes",
    ),
    include_entities: bool = Query(
        True,
        description="Include LLM-extracted entity nodes and edges",
    ),
    max_edges_per_node: int = Query(
        MAX_EDGES_PER_NODE,
        ge=1,
        le=20,
        description="Maximum edges per node to prevent hairball (default 5)",
    ),
) -> EpisodicGraphData:
    """
    Get episodic memory graph for Graphiti-style visualization.

    Returns:
    - Episodes: Past incidents with full metadata
    - Root Causes: Semantic abstractions (connection_timeout, memory_leak, etc.)
    - Actions: Remediation actions with success rates
    - Services: Only services affected by episodes
    - Edges: CAUSED_BY, RESOLVED_BY, AFFECTS, SIMILAR_TO relationships
    """
    episode_store = getattr(request.app.state, "episode_store", None)
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    episodes: list[EpisodeNode] = []
    root_causes: list[RootCauseNode] = []
    actions: list[ActionNode] = []
    services: list[ServiceNode] = []
    entities: list[EntityNode] = []  # Phase 2: LLM-extracted entities
    edges: list[GraphEdge] = []

    # Track unique nodes
    root_cause_map: dict[str, RootCauseNode] = {}
    action_map: dict[str, ActionNode] = {}
    service_map: dict[str, ServiceNode] = {}
    entity_map: dict[str, EntityNode] = {}  # Phase 2: Track entities

    # Try to get data from Neo4j first
    has_neo4j_data = False
    if neo4j_client is not None:
        try:
            # Query episodes with their relationships
            async with neo4j_client.session() as session:
                result = await session.run(
                    """
                    MATCH (e:Episode)
                    OPTIONAL MATCH (e)-[:INVOLVES]->(s:Service)
                    OPTIONAL MATCH (e)-[:CAUSED_BY]->(rc:RootCauseType)
                    RETURN e, collect(DISTINCT s.name) as services, rc.name as root_cause_type
                    ORDER BY e.detected_at DESC
                    LIMIT $limit
                    """,
                    limit=limit,
                )
                episodes_data = await result.data()

            for row in episodes_data:
                has_neo4j_data = True
                ep = row["e"]
                ep_id = ep.get("episode_id", ep.get("id", ""))
                ep_services = [s for s in row.get("services", []) if s]
                root_cause_type = row.get("root_cause_type")

                episode_node = EpisodeNode(
                    id=ep_id,
                    title=ep.get("title", "Unknown Episode"),
                    timestamp=ep.get("detected_at", datetime.utcnow()),
                    category=ep.get("category", "unknown"),
                    severity=ep.get("severity", "medium"),
                    status=ep.get("outcome", "resolved"),
                    root_cause=ep.get("root_cause"),
                    confidence=ep.get("confidence", 0.0),
                    services=ep_services,
                    successful_actions=ep.get("successful_actions", []),
                )
                episodes.append(episode_node)

                # Add AFFECTS edges to services
                for svc_name in ep_services:
                    edges.append(GraphEdge(
                        source=f"episode-{ep_id}",
                        target=f"service-{svc_name}",
                        relationship="affects",
                    ))

                    # Track service
                    if svc_name not in service_map:
                        service_map[svc_name] = ServiceNode(
                            name=svc_name,
                            status="warning" if episode_node.severity in ("critical", "high") else "healthy",
                            incident_count=1,
                            last_incident=episode_node.timestamp,
                        )
                    else:
                        service_map[svc_name].incident_count += 1

                # Add CAUSED_BY edge to root cause
                if root_cause_type:
                    edges.append(GraphEdge(
                        source=f"episode-{ep_id}",
                        target=f"rootcause-{root_cause_type}",
                        relationship="caused_by",
                    ))

                    # Track root cause
                    if root_cause_type not in root_cause_map:
                        root_cause_map[root_cause_type] = RootCauseNode(
                            id=f"rootcause-{root_cause_type}",
                            name=root_cause_type,
                            frequency=1,
                        )
                    else:
                        root_cause_map[root_cause_type].frequency += 1

                # Add RESOLVED_BY edges to actions
                for action_name in episode_node.successful_actions:
                    action_id = action_name.lower().replace(" ", "_")
                    edges.append(GraphEdge(
                        source=f"episode-{ep_id}",
                        target=f"action-{action_id}",
                        relationship="resolved_by",
                    ))

                    # Track action
                    if action_id not in action_map:
                        action_map[action_id] = ActionNode(
                            id=f"action-{action_id}",
                            name=action_name,
                            used_count=1,
                            success_rate=1.0,
                        )
                    else:
                        action_map[action_id].used_count += 1

            # Phase 2: Query LLM-extracted semantic triplets (Entity nodes with RELATES edges)
            async with neo4j_client.session() as session:
                triplet_result = await session.run(
                    """
                    MATCH (s:Entity)-[r:RELATES]->(o:Entity)
                    RETURN s.name as subject, r.type as relation, o.name as object,
                           r.source_episode as episode_id, r.extraction_method as method
                    ORDER BY r.timestamp DESC
                    LIMIT 100
                    """,
                )
                triplets_data = await triplet_result.data()

            # Add dynamic edges from LLM-extracted triplets
            for triplet in triplets_data:
                subject = triplet.get("subject", "")
                relation = triplet.get("relation", "RELATES")
                obj = triplet.get("object", "")

                if not subject or not obj:
                    continue

                # Track entities
                if subject not in entity_map:
                    entity_map[subject] = EntityNode(
                        id=f"entity-{subject}",
                        name=subject,
                        relation_count=1,
                    )
                else:
                    entity_map[subject].relation_count += 1

                if obj not in entity_map:
                    entity_map[obj] = EntityNode(
                        id=f"entity-{obj}",
                        name=obj,
                        relation_count=1,
                    )
                else:
                    entity_map[obj].relation_count += 1

                # Add dynamic edge with LLM-extracted relation type
                edges.append(GraphEdge(
                    source=f"entity-{subject}",
                    target=f"entity-{obj}",
                    relationship=relation.lower(),  # Dynamic relation from LLM
                    metadata={"extraction_method": triplet.get("method", "llm")},
                ))

        except Exception as e:
            logger.warning(f"Failed to query Neo4j for episodes: {e}")

    # If no Neo4j data, show monitored services (real infrastructure being watched)
    if not has_neo4j_data:
        logger.info("No Neo4j episode data found, showing monitored services")
        # Get real monitored services from infrastructure module
        from src.api.routes.infrastructure import _monitored_containers
        monitored_services = [
            ServiceNode(
                name=name.replace("aiops-", "") if name.startswith("aiops-") else name,
                status="healthy",
                incident_count=0,
                metadata={"monitored": True, "container": name},
            )
            for name in sorted(_monitored_containers)
        ]
        return EpisodicGraphData(
            episodes=[],
            root_causes=[],
            actions=[],
            services=monitored_services,
            entities=[],
            edges=[],
            stats={
                "total_episodes": 0,
                "monitored_services": len(monitored_services),
                "message": "Monitoring active. Graph will populate as incidents are detected by the Fast Agent.",
            },
        )
    else:
        # Convert maps to lists
        root_causes = list(root_cause_map.values())
        actions = list(action_map.values())
        services = list(service_map.values())

        # v0.6.0: Filter entities based on include_entities parameter
        if include_entities:
            entities = list(entity_map.values())
        else:
            entities = []
            # Remove entity edges if entities disabled
            edges = [e for e in edges if not e.relationship.startswith("relates")]

        # v0.6.0: Filter edges by confidence
        edges = [e for e in edges if (e.weight or 1.0) >= min_confidence]

        # v0.6.0: Find similar episodes and add SIMILAR_TO edges (if enabled)
        if include_similar_to:
            similar_edges = _find_similar_episode_edges(
                episodes,
                threshold=min_similarity,
                max_per_episode=MAX_SIMILAR_EDGES_PER_EPISODE,
            )
            edges.extend(similar_edges)

        # v0.6.0: Apply degree capping to prevent hairball
        edges = _prune_edges(edges, max_per_node=max_edges_per_node)

    # Calculate stats
    stats = {
        "total_episodes": len(episodes),
        "total_root_causes": len(root_causes),
        "total_actions": len(actions),
        "total_services": len(services),
        "total_entities": len(entities),
        "total_edges": len(edges),
        "critical_episodes": sum(1 for ep in episodes if ep.severity == "critical"),
        "resolved_episodes": sum(1 for ep in episodes if ep.status == "resolved"),
        "dynamic_edges": sum(1 for e in edges if e.metadata.get("extraction_method") == "llm"),
    }

    return EpisodicGraphData(
        episodes=episodes,
        root_causes=root_causes,
        actions=actions,
        services=services,
        entities=entities,
        edges=edges,
        stats=stats,
    )


def _find_similar_episode_edges(
    episodes: list[EpisodeNode],
    threshold: float = SIMILAR_TO_THRESHOLD,
    max_per_episode: int = MAX_SIMILAR_EDGES_PER_EPISODE,
) -> list[GraphEdge]:
    """
    Find and create SIMILAR_TO edges between highly similar episodes.

    Uses higher threshold (0.75) and limits edges per episode to prevent hairball.

    Args:
        episodes: List of episode nodes
        threshold: Minimum similarity score (default: 0.75)
        max_per_episode: Maximum SIMILAR_TO edges per episode (default: 3)

    Returns:
        List of SIMILAR_TO edges (pruned to prevent O(n²) explosion)
    """
    # Calculate all similarities first, then keep only top-k per episode
    all_similarities: list[tuple[str, str, float]] = []
    seen_pairs = set()

    for i, ep1 in enumerate(episodes):
        for ep2 in episodes[i + 1:]:
            # Skip if already paired
            pair_key = tuple(sorted([ep1.id, ep2.id]))
            if pair_key in seen_pairs:
                continue

            # Calculate similarity
            similarity = 0.0

            # Same category = 0.3
            if ep1.category == ep2.category:
                similarity += 0.3

            # Same root cause = 0.4
            if ep1.root_cause and ep2.root_cause and ep1.root_cause == ep2.root_cause:
                similarity += 0.4

            # Service overlap = 0.3 * overlap ratio
            if ep1.services and ep2.services:
                services1 = set(ep1.services)
                services2 = set(ep2.services)
                overlap = len(services1 & services2)
                total = len(services1 | services2)
                if total > 0:
                    similarity += 0.3 * (overlap / total)

            # Only consider if above threshold (0.75 instead of 0.5)
            if similarity >= threshold:
                seen_pairs.add(pair_key)
                all_similarities.append((ep1.id, ep2.id, similarity))

    # Sort by similarity descending
    all_similarities.sort(key=lambda x: x[2], reverse=True)

    # Limit edges per episode (degree capping)
    episode_edge_count: dict[str, int] = {}
    edges = []

    for ep1_id, ep2_id, similarity in all_similarities:
        count1 = episode_edge_count.get(ep1_id, 0)
        count2 = episode_edge_count.get(ep2_id, 0)

        # Only add if both episodes have room for more edges
        if count1 < max_per_episode and count2 < max_per_episode:
            edges.append(GraphEdge(
                source=f"episode-{ep1_id}",
                target=f"episode-{ep2_id}",
                relationship="similar_to",
                weight=similarity,
            ))
            episode_edge_count[ep1_id] = count1 + 1
            episode_edge_count[ep2_id] = count2 + 1

    logger.debug(f"Created {len(edges)} SIMILAR_TO edges (threshold={threshold}, max_per_episode={max_per_episode})")
    return edges


def _prune_edges(
    edges: list[GraphEdge],
    max_per_node: int = MAX_EDGES_PER_NODE,
) -> list[GraphEdge]:
    """
    Limit edges per node to prevent hairball visualization.

    Uses degree capping: keeps highest-weight edges up to max_per_node per node.

    Args:
        edges: List of graph edges
        max_per_node: Maximum edges per node (default: 5)

    Returns:
        Pruned list of edges
    """
    if not edges:
        return edges

    # Sort by weight descending (keep best edges)
    sorted_edges = sorted(edges, key=lambda e: e.weight or 0, reverse=True)

    node_edge_count: dict[str, int] = {}
    pruned = []

    for edge in sorted_edges:
        source_count = node_edge_count.get(edge.source, 0)
        target_count = node_edge_count.get(edge.target, 0)

        # Only add if both nodes have room for more edges
        if source_count < max_per_node and target_count < max_per_node:
            pruned.append(edge)
            node_edge_count[edge.source] = source_count + 1
            node_edge_count[edge.target] = target_count + 1

    logger.debug(f"Pruned edges: {len(edges)} -> {len(pruned)} (max_per_node={max_per_node})")
    return pruned


@router.get(
    "/services",
    response_model=list[ServiceNode],
    summary="List Services",
    description="Get all services from the graph database",
)
async def list_services(
    request: Request,
    status_filter: str | None = Query(None, description="Filter by status"),
) -> list[ServiceNode]:
    """List all services with their dependencies."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        return []

    try:
        query = """
        MATCH (s:Service)
        OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep:Service)
        OPTIONAL MATCH (upstream:Service)-[:DEPENDS_ON]->(s)
        RETURN s.name as name, s.status as status, s.type as type,
               collect(DISTINCT dep.name) as dependencies,
               collect(DISTINCT upstream.name) as dependents
        """
        if status_filter:
            query = query.replace("MATCH (s:Service)", f"MATCH (s:Service {{status: '{status_filter}'}})")

        async with neo4j_client.session() as session:
            query_result = await session.run(query)
            result = await query_result.data()

        services = []
        for row in result:
            services.append(ServiceNode(
                name=row["name"],
                type=row.get("type", "service"),
                status=row.get("status", "healthy"),
                dependencies=[d for d in row.get("dependencies", []) if d],
                dependents=[d for d in row.get("dependents", []) if d],
            ))

        return services

    except Exception as e:
        logger.warning(f"Failed to list services: {e}")
        return []


@router.get(
    "/services/{name}/dependencies",
    response_model=DependencyGraph,
    summary="Get Service Dependencies",
    description="Get dependency graph for a specific service",
)
async def get_service_dependencies(
    request: Request,
    name: str,
    depth: int = Query(2, ge=1, le=5, description="Depth of dependency traversal"),
) -> DependencyGraph:
    """Get upstream and downstream dependencies for a service."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        return DependencyGraph(service=name, upstream=[], downstream=[], depth=depth)

    try:
        # Get downstream dependencies
        downstream_query = f"""
        MATCH (s:Service {{name: $name}})-[:DEPENDS_ON*1..{depth}]->(dep:Service)
        RETURN DISTINCT dep.name as name
        """
        async with neo4j_client.session() as session:
            result = await session.run(downstream_query, name=name)
            downstream_result = await result.data()
        downstream = [row["name"] for row in downstream_result]

        # Get upstream dependencies
        upstream_query = f"""
        MATCH (upstream:Service)-[:DEPENDS_ON*1..{depth}]->(s:Service {{name: $name}})
        RETURN DISTINCT upstream.name as name
        """
        async with neo4j_client.session() as session:
            result = await session.run(upstream_query, name=name)
            upstream_result = await result.data()
        upstream = [row["name"] for row in upstream_result]

        return DependencyGraph(
            service=name,
            upstream=upstream,
            downstream=downstream,
            depth=depth,
        )

    except Exception as e:
        logger.warning(f"Failed to get dependencies: {e}")
        return DependencyGraph(service=name, upstream=[], downstream=[], depth=depth)


@router.get(
    "/episodes/{episode_id}",
    response_model=Episode,
    summary="Get Episode Details",
    description="Get detailed information about a specific episode",
)
async def get_episode(request: Request, episode_id: str) -> Episode:
    """Get detailed episode information."""
    episode_store = getattr(request.app.state, "episode_store", None)

    if episode_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Episode store not available",
        )

    try:
        ep = episode_store.get_episode(episode_id)
        if ep is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode '{episode_id}' not found",
            )

        return Episode(
            id=ep.id,
            title=ep.title,
            timestamp=ep.timestamp,
            category=ep.category,
            severity=ep.severity,
            services=ep.affected_services,
            root_cause=ep.root_cause,
            resolution=ep.resolution,
            confidence=ep.confidence,
            metadata=ep.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/episodes/{episode_id}/similar",
    response_model=list[SimilarEpisode],
    summary="Find Similar Episodes",
    description="Find episodes similar to the specified one",
)
async def find_similar_episodes(
    request: Request,
    episode_id: str,
    limit: int = Query(5, ge=1, le=20),
) -> list[SimilarEpisode]:
    """Find episodes similar to the given one."""
    context_retriever = getattr(request.app.state, "context_retriever", None)
    episode_store = getattr(request.app.state, "episode_store", None)

    if context_retriever is None or episode_store is None:
        return []

    try:
        # Get the source episode
        source_ep = episode_store.get_episode(episode_id)
        if source_ep is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode '{episode_id}' not found",
            )

        # Find similar episodes
        similar = await context_retriever.find_similar(
            title=source_ep.title,
            category=source_ep.category,
            services=source_ep.affected_services,
            limit=limit + 1,  # +1 to exclude self
        )

        # Filter out the source episode and convert
        result = []
        for ep, score in similar:
            if ep.id != episode_id:
                result.append(SimilarEpisode(
                    episode=Episode(
                        id=ep.id,
                        title=ep.title,
                        timestamp=ep.timestamp,
                        category=ep.category,
                        severity=ep.severity,
                        services=ep.affected_services,
                        root_cause=ep.root_cause,
                        resolution=ep.resolution,
                        confidence=ep.confidence,
                    ),
                    similarity_score=score,
                ))

        return result[:limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to find similar episodes: {e}")
        return []


@router.get(
    "/embedding/status",
    summary="Get Embedding Status",
    description="Get status of the embedding service for vector similarity",
)
async def get_embedding_status(request: Request) -> dict:
    """
    Get embedding service status.

    Returns information about:
    - Model availability
    - Device (CUDA/CPU)
    - Embedding dimensions
    - Similarity threshold

    This implements the semantic similarity from Research_V6.tex:
    - Model: sentence-transformers/all-MiniLM-L6-v2
    - Dimensions: 384
    - Threshold: 0.70 cosine similarity
    """
    embedding_service = getattr(request.app.state, "embedding_service", None)

    if embedding_service is None:
        return {
            "available": False,
            "loaded": False,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": 384,
            "device": None,
            "similarity_threshold": 0.70,
            "error": "Embedding service not initialized",
        }

    return embedding_service.get_status()


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    summary="Graph Stats",
    description="Get statistics about the graph database",
)
async def get_graph_stats(request: Request) -> GraphStatsResponse:
    """Get graph database statistics."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    episode_store = getattr(request.app.state, "episode_store", None)

    connected = neo4j_client is not None
    node_count = 0
    edge_count = 0
    episode_count = 0

    if neo4j_client is not None:
        try:
            async with neo4j_client.session() as session:
                # Get node count
                query_result = await session.run("MATCH (n) RETURN count(n) as count")
                result = await query_result.data()
                node_count = result[0]["count"] if result else 0

                # Get edge count
                query_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                result = await query_result.data()
                edge_count = result[0]["count"] if result else 0

                # Get episode count
                query_result = await session.run("MATCH (e:Episode) RETURN count(e) as count")
                result = await query_result.data()
                episode_count = result[0]["count"] if result else 0

        except Exception as e:
            logger.warning(f"Failed to get graph stats: {e}")

    elif episode_store is not None:
        # Fallback to episode store
        try:
            episode_count = len(episode_store.list_episodes(limit=1000))
        except Exception:
            pass

    return GraphStatsResponse(
        connected=connected,
        node_count=node_count,
        edge_count=edge_count,
        episode_count=episode_count,
    )


class GraphCleanupRequest(BaseModel):
    """Request for graph cleanup operation."""
    delete_similar_to: bool = Field(default=True, description="Delete all SIMILAR_TO edges")
    merge_duplicate_entities: bool = Field(default=True, description="Merge duplicate entities")
    delete_orphan_entities: bool = Field(default=True, description="Delete orphan entities")
    keep_episodes: int = Field(default=50, ge=0, le=500, description="Keep N most recent episodes (0=all)")


class GraphCleanupResponse(BaseModel):
    """Response from graph cleanup operation."""
    success: bool
    similar_to_deleted: int = 0
    entities_merged: int = 0
    orphan_entities_deleted: int = 0
    old_episodes_deleted: int = 0
    message: str = ""


@router.post(
    "/cleanup",
    response_model=GraphCleanupResponse,
    summary="Cleanup Graph",
    description="Clean up the graph to prevent hairball visualization. Deletes SIMILAR_TO edges, merges duplicates, removes orphans.",
)
async def cleanup_graph(
    request: Request,
    cleanup_request: GraphCleanupRequest = GraphCleanupRequest(),
) -> GraphCleanupResponse:
    """
    Clean up the Neo4j graph to establish a clean baseline.

    This is useful when the graph has become too dense with:
    - Too many SIMILAR_TO edges (will be recalculated with proper threshold)
    - Duplicate entity nodes
    - Orphan entities with no relationships
    - Old episodes that are no longer relevant

    Use this endpoint before deploying graph schema changes.
    """
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not available",
        )

    try:
        stats = await neo4j_client.cleanup_graph(
            delete_similar_to=cleanup_request.delete_similar_to,
            merge_duplicate_entities=cleanup_request.merge_duplicate_entities,
            delete_orphan_entities=cleanup_request.delete_orphan_entities,
            keep_episodes=cleanup_request.keep_episodes,
        )

        return GraphCleanupResponse(
            success=True,
            similar_to_deleted=stats.get("similar_to_deleted", 0),
            entities_merged=stats.get("entities_merged", 0),
            orphan_entities_deleted=stats.get("orphan_entities_deleted", 0),
            old_episodes_deleted=stats.get("old_episodes_deleted", 0),
            message=f"Graph cleanup complete. Removed {stats.get('similar_to_deleted', 0)} SIMILAR_TO edges.",
        )

    except Exception as e:
        logger.error(f"Graph cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}",
        )


@router.get(
    "/detailed-stats",
    summary="Detailed Graph Stats",
    description="Get detailed statistics including node/edge counts by type",
)
async def get_detailed_graph_stats(request: Request) -> dict:
    """Get detailed graph statistics by node and edge type."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        return {"error": "Neo4j client not available"}

    try:
        return await neo4j_client.get_graph_stats()
    except Exception as e:
        logger.error(f"Failed to get detailed stats: {e}")
        return {"error": str(e)}


# =============================================================================
# Episode Generation via Reasoning Agent
# =============================================================================

# Template-based schema for service definitions
SERVICE_TEMPLATES = [
    {
        "name": "neo4j",
        "type": "database",
        "port": 7687,
        "description": "Graph database for episodic memory and knowledge storage",
        "health_endpoint": "/",
        "dependencies": ["backend"],
        "common_issues": ["memory_pressure", "connection_pool_exhaustion", "slow_queries"],
    },
    {
        "name": "prometheus",
        "type": "monitoring",
        "port": 9090,
        "description": "Metrics collection, alerting, and time-series database",
        "health_endpoint": "/-/healthy",
        "dependencies": ["otel-collector"],
        "common_issues": ["scrape_target_down", "storage_full", "query_timeout"],
    },
    {
        "name": "grafana",
        "type": "visualization",
        "port": 3001,
        "description": "Dashboard visualization and alerting UI",
        "health_endpoint": "/api/health",
        "dependencies": ["prometheus", "loki", "tempo"],
        "common_issues": ["dashboard_load_timeout", "datasource_error", "auth_failure"],
    },
    {
        "name": "loki",
        "type": "logging",
        "port": 3100,
        "description": "Log aggregation and querying system",
        "health_endpoint": "/ready",
        "dependencies": ["otel-collector"],
        "common_issues": ["ingestion_backlog", "storage_limit", "rate_limiting"],
    },
    {
        "name": "tempo",
        "type": "tracing",
        "port": 3200,
        "description": "Distributed tracing backend for trace storage and querying",
        "health_endpoint": "/ready",
        "dependencies": ["otel-collector"],
        "common_issues": ["trace_storage_full", "span_drop", "query_timeout"],
    },
    {
        "name": "otel-collector",
        "type": "telemetry",
        "port": 4317,
        "description": "OpenTelemetry collector for unified telemetry pipeline",
        "health_endpoint": "/",
        "dependencies": [],
        "common_issues": ["exporter_failure", "pipeline_blocked", "memory_limit"],
    },
    {
        "name": "backend",
        "type": "api",
        "port": 8000,
        "description": "FastAPI backend with dual LLM agents (Qwen3-4B + Qwen3-14B)",
        "health_endpoint": "/api/v1/health",
        "dependencies": ["neo4j", "prometheus", "loki"],
        "common_issues": ["llm_timeout", "api_latency", "database_connection"],
    },
    {
        "name": "frontend",
        "type": "ui",
        "port": 3000,
        "description": "React dashboard for Constitutional AIOps visualization",
        "health_endpoint": "/",
        "dependencies": ["backend"],
        "common_issues": ["api_unreachable", "render_error", "websocket_disconnect"],
    },
]

# Episode generation prompt template
EPISODE_GENERATION_TEMPLATE = """You are an expert SRE analyzing infrastructure for the Constitutional AIOps system.

Generate a realistic, resolved incident episode for the {service_name} service based on:
- Service Type: {service_type}
- Description: {service_description}
- Port: {service_port}
- Dependencies: {dependencies}
- Common Issues: {common_issues}

Connected services in this infrastructure:
{all_services}

Generate a detailed, realistic incident that:
1. Could actually occur with this service type
2. Has a clear root cause
3. Shows proper causal chain
4. Includes remediation actions that worked
5. Affects appropriate dependent services

Return ONLY valid JSON matching this exact schema:
{{
    "title": "Concise incident title (50 chars max)",
    "description": "Detailed technical description of what happened, including metrics and symptoms",
    "severity": "critical|warning|info",
    "category": "performance|connectivity|resource|error|security",
    "root_cause": "The underlying technical cause",
    "causal_chain": ["Initial event", "Cascading effect", "Final symptom"],
    "confidence": 0.85,
    "remediation_actions": ["Action 1 that resolved it", "Action 2"],
    "affected_services": ["{service_name}", "other affected service"],
    "resolution_time_minutes": 30,
    "key_metrics": {{
        "metric_name": "abnormal_value",
        "threshold": "normal_threshold"
    }}
}}"""


class GenerateEpisodesRequest(BaseModel):
    """Request to generate demo episodes via Reasoning Agent."""
    services: list[str] | None = Field(
        default=None,
        description="Specific services to generate episodes for. If None, generates for all."
    )
    count_per_service: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Number of episodes per service (1-3)"
    )
    clear_existing: bool = Field(
        default=True,
        description="Clear existing graph data before generating"
    )


class GenerateEpisodesResponse(BaseModel):
    """Response from episode generation."""
    success: bool
    episodes_created: int
    services_processed: list[str]
    errors: list[str]
    message: str


@router.post(
    "/generate-episodes",
    response_model=GenerateEpisodesResponse,
    summary="Generate Episodes via Reasoning Agent",
    description="Generate realistic demo episodes using Qwen3-14B based on actual service templates",
)
async def generate_episodes(
    request: Request,
    gen_request: GenerateEpisodesRequest = GenerateEpisodesRequest(),
) -> GenerateEpisodesResponse:
    """
    Generate realistic episodes using the Reasoning Agent (Qwen3-14B).

    This uses template-based schemas for each service to create episodes
    that accurately reflect the Constitutional AIOps architecture.
    """
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if reasoning_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning Agent not available. Ensure Jarvis Labs VM is running.",
        )

    if neo4j_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not available.",
        )

    errors: list[str] = []
    episodes_created = 0
    services_processed: list[str] = []

    try:
        # Clear existing data if requested
        if gen_request.clear_existing:
            async with neo4j_client.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing graph data")

        # Determine which services to process
        target_services = gen_request.services or [s["name"] for s in SERVICE_TEMPLATES]
        all_services_text = "\n".join([
            f"- {s['name']} ({s['type']}): {s['description']}"
            for s in SERVICE_TEMPLATES
        ])

        now = datetime.utcnow()

        for service_template in SERVICE_TEMPLATES:
            if service_template["name"] not in target_services:
                continue

            svc_name = service_template["name"]
            services_processed.append(svc_name)

            for i in range(gen_request.count_per_service):
                try:
                    # Build prompt from template
                    prompt = EPISODE_GENERATION_TEMPLATE.format(
                        service_name=svc_name,
                        service_type=service_template["type"],
                        service_description=service_template["description"],
                        service_port=service_template["port"],
                        dependencies=", ".join(service_template["dependencies"]) or "none",
                        common_issues=", ".join(service_template["common_issues"]),
                        all_services=all_services_text,
                    )

                    # Call reasoning agent
                    logger.info(f"Generating episode for {svc_name} ({i+1}/{gen_request.count_per_service})")
                    response = await reasoning_agent.chat(prompt)

                    # Parse JSON from response - AgentResponse has .content attribute
                    response_text = response.content if hasattr(response, 'content') else str(response)

                    # Remove thinking tags if present (Qwen3 sometimes outputs <think>...</think>)
                    if "<think>" in response_text:
                        response_text = response_text.split("</think>")[-1].strip()

                    # Extract JSON from markdown code blocks if present
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0]

                    # Try to find JSON object in response
                    response_text = response_text.strip()
                    if not response_text.startswith("{"):
                        # Find first { and last }
                        start = response_text.find("{")
                        end = response_text.rfind("}") + 1
                        if start != -1 and end > start:
                            response_text = response_text[start:end]

                    episode_data = json.loads(response_text)

                    # Generate IDs
                    episode_id = f"ep-{svc_name}-{uuid4().hex[:6]}"
                    detected_at = now - timedelta(hours=i * 4 + 2)
                    resolved_at = detected_at + timedelta(minutes=episode_data.get("resolution_time_minutes", 30))

                    # Store in Neo4j with full schema
                    async with neo4j_client.session() as session:
                        # Create Service node with full details
                        await session.run("""
                            MERGE (s:Service {name: $name})
                            SET s.type = $type,
                                s.port = $port,
                                s.description = $description,
                                s.health_endpoint = $health,
                                s.status = 'healthy',
                                s.last_checked = $now,
                                s.uptime_percent = 99.9
                        """, {
                            "name": svc_name,
                            "type": service_template["type"],
                            "port": service_template["port"],
                            "description": service_template["description"],
                            "health": service_template["health_endpoint"],
                            "now": now.isoformat(),
                        })

                        # Create Episode node
                        await session.run("""
                            CREATE (e:Episode {
                                episode_id: $eid,
                                title: $title,
                                description: $desc,
                                severity: $severity,
                                category: $category,
                                root_cause: $root_cause,
                                confidence: $confidence,
                                outcome: 'resolved',
                                detected_at: $detected,
                                resolved_at: $resolved,
                                resolution_time_minutes: $resolution_time
                            })
                        """, {
                            "eid": episode_id,
                            "title": episode_data["title"],
                            "desc": episode_data["description"],
                            "severity": episode_data["severity"],
                            "category": episode_data["category"],
                            "root_cause": episode_data["root_cause"],
                            "confidence": episode_data["confidence"],
                            "detected": detected_at.isoformat(),
                            "resolved": resolved_at.isoformat(),
                            "resolution_time": episode_data.get("resolution_time_minutes", 30),
                        })

                        # Create INVOLVES relationship (Episode -> Service)
                        await session.run("""
                            MATCH (e:Episode {episode_id: $eid}), (s:Service {name: $name})
                            MERGE (e)-[:INVOLVES {weight: 1.0}]->(s)
                        """, {"eid": episode_id, "name": svc_name})

                        # Create additional affected services
                        for affected_svc in episode_data.get("affected_services", []):
                            if affected_svc != svc_name:
                                # Find template for affected service
                                affected_template = next(
                                    (t for t in SERVICE_TEMPLATES if t["name"] == affected_svc),
                                    None
                                )
                                if affected_template:
                                    await session.run("""
                                        MERGE (s:Service {name: $name})
                                        SET s.type = $type, s.status = 'healthy'
                                        WITH s
                                        MATCH (e:Episode {episode_id: $eid})
                                        MERGE (e)-[:INVOLVES {weight: 0.5}]->(s)
                                    """, {
                                        "name": affected_svc,
                                        "type": affected_template["type"],
                                        "eid": episode_id,
                                    })

                        # Create RootCauseType node
                        rc_id = episode_data["root_cause"].lower().replace(" ", "_")[:50]
                        await session.run("""
                            MERGE (rc:RootCauseType {id: $id})
                            SET rc.name = $name
                            WITH rc
                            MATCH (e:Episode {episode_id: $eid})
                            MERGE (e)-[:CAUSED_BY {confidence: $conf}]->(rc)
                        """, {
                            "id": rc_id,
                            "name": episode_data["root_cause"],
                            "eid": episode_id,
                            "conf": episode_data["confidence"],
                        })

                        # Create Action nodes
                        for action in episode_data.get("remediation_actions", [])[:3]:
                            action_id = action.lower().replace(" ", "_")[:50]
                            await session.run("""
                                MERGE (a:Action {id: $id})
                                SET a.name = $name, a.success_rate = 0.95
                                WITH a
                                MATCH (e:Episode {episode_id: $eid})
                                MERGE (e)-[:RESOLVED_BY]->(a)
                            """, {"id": action_id, "name": action, "eid": episode_id})

                        # Create causal chain as Entity nodes
                        chain = episode_data.get("causal_chain", [])
                        for j in range(len(chain) - 1):
                            await session.run("""
                                MERGE (e1:Entity {name: $from_name})
                                MERGE (e2:Entity {name: $to_name})
                                MERGE (e1)-[:CAUSED {source_episode: $eid}]->(e2)
                            """, {
                                "from_name": chain[j],
                                "to_name": chain[j + 1],
                                "eid": episode_id,
                            })

                    episodes_created += 1
                    logger.info(f"Created episode: {episode_data['title']}")

                except json.JSONDecodeError as e:
                    errors.append(f"{svc_name}: Invalid JSON response - {str(e)[:50]}")
                    logger.warning(f"JSON parse error for {svc_name}: {e}")
                except Exception as e:
                    errors.append(f"{svc_name}: {str(e)[:50]}")
                    logger.warning(f"Error generating episode for {svc_name}: {e}")

        return GenerateEpisodesResponse(
            success=episodes_created > 0,
            episodes_created=episodes_created,
            services_processed=services_processed,
            errors=errors,
            message=f"Generated {episodes_created} episodes for {len(services_processed)} services via Reasoning Agent (Qwen3-14B)",
        )

    except Exception as e:
        logger.error(f"Episode generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Episode generation failed: {str(e)}",
        )


__all__ = ["router"]
