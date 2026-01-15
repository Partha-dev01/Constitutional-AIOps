"""
Constitutional AIOps - Graph API Routes

Provides endpoints for Neo4j graph queries including:
- Episodic memory graphs (Graphiti-style)
- Root cause correlation
- Action success patterns
- Service impact analysis

Graph Model (from Research_V6.tex):
- Episodes → CAUSED_BY → RootCauseType
- Episodes → RESOLVED_BY → Action
- Episodes → AFFECTS → Service
- Episodes → SIMILAR_TO → Episode
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter()


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
            return datetime.now()
        if isinstance(v, datetime):
            return v
        # Handle Neo4j DateTime object
        if hasattr(v, "to_native"):
            return v.to_native()
        # Try to convert from ISO string
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


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
    edges: list[GraphEdge] = []

    # Track unique nodes
    root_cause_map: dict[str, RootCauseNode] = {}
    action_map: dict[str, ActionNode] = {}
    service_map: dict[str, ServiceNode] = {}

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

        # Find similar episodes and add SIMILAR_TO edges
        edges.extend(_find_similar_episode_edges(episodes))

    # Calculate stats
    stats = {
        "total_episodes": len(episodes),
        "total_root_causes": len(root_causes),
        "total_actions": len(actions),
        "total_services": len(services),
        "total_edges": len(edges),
        "critical_episodes": sum(1 for ep in episodes if ep.severity == "critical"),
        "resolved_episodes": sum(1 for ep in episodes if ep.status == "resolved"),
    }

    return EpisodicGraphData(
        episodes=episodes,
        root_causes=root_causes,
        actions=actions,
        services=services,
        edges=edges,
        stats=stats,
    )


def _find_similar_episode_edges(episodes: list[EpisodeNode]) -> list[GraphEdge]:
    """Find and create SIMILAR_TO edges between episodes with same root cause or services."""
    edges = []
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

            # Add edge if similarity > 0.5
            if similarity >= 0.5:
                seen_pairs.add(pair_key)
                edges.append(GraphEdge(
                    source=f"episode-{ep1.id}",
                    target=f"episode-{ep2.id}",
                    relationship="similar_to",
                    weight=similarity,
                ))

    return edges


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


__all__ = ["router"]
