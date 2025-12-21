"""
Constitutional AIOps - Graph API Routes

Provides endpoints for Neo4j graph queries including:
- Service dependency graphs
- Episodic memory retrieval
- Incident correlation
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, Query, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceNode(BaseModel):
    """Service node in the dependency graph."""
    name: str
    type: str = "service"
    status: str = Field(..., description="Status: healthy, warning, critical")
    dependencies: list[str] = Field(default_factory=list)
    dependents: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Episode(BaseModel):
    """Episode from episodic memory."""
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
    """Graph data for visualization."""
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
    response_model=GraphData,
    summary="Get Episodes and Services",
    description="Get episodic memory data with service nodes for graph visualization",
)
async def get_episodes(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    since_hours: int = Query(24, description="Get episodes from last N hours"),
) -> GraphData:
    """
    Get episodes and services for graph visualization.

    Returns nodes (services) and edges (relationships) for vis-network.
    """
    episode_store = getattr(request.app.state, "episode_store", None)
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    services = []
    episodes = []
    edges = []

    # Try to get data from Neo4j
    if neo4j_client is not None:
        try:
            # Get services
            service_data = await neo4j_client.query(
                """
                MATCH (s:Service)
                RETURN s.name as name, s.status as status, s.type as type
                LIMIT $limit
                """,
                {"limit": limit},
            )

            for row in service_data:
                services.append(ServiceNode(
                    name=row["name"],
                    type=row.get("type", "service"),
                    status=row.get("status", "healthy"),
                ))

            # Get service dependencies
            deps_data = await neo4j_client.query(
                """
                MATCH (s1:Service)-[r:DEPENDS_ON]->(s2:Service)
                RETURN s1.name as from_service, s2.name as to_service
                """,
                {},
            )

            for row in deps_data:
                edges.append({
                    "from": f"service-{row['from_service']}",
                    "to": f"service-{row['to_service']}",
                    "label": "depends_on",
                })

            # Get recent episodes
            episodes_data = await neo4j_client.query(
                """
                MATCH (e:Episode)
                WHERE e.timestamp > datetime() - duration({hours: $hours})
                RETURN e
                ORDER BY e.timestamp DESC
                LIMIT $limit
                """,
                {"hours": since_hours, "limit": limit},
            )

            for row in episodes_data:
                ep = row["e"]
                episodes.append(Episode(
                    id=ep.get("id", ""),
                    title=ep.get("title", ""),
                    timestamp=ep.get("timestamp", datetime.utcnow()),
                    category=ep.get("category", "unknown"),
                    severity=ep.get("severity", "medium"),
                    services=ep.get("services", []),
                    root_cause=ep.get("root_cause"),
                    resolution=ep.get("resolution"),
                    confidence=ep.get("confidence", 0),
                ))

            # Get episode-service relationships
            ep_svc_data = await neo4j_client.query(
                """
                MATCH (e:Episode)-[r:AFFECTS]->(s:Service)
                RETURN e.id as episode_id, s.name as service_name
                """,
                {},
            )

            for row in ep_svc_data:
                edges.append({
                    "from": f"episode-{row['episode_id']}",
                    "to": f"service-{row['service_name']}",
                    "label": "affects",
                })

        except Exception as e:
            logger.warning(f"Failed to query Neo4j: {e}")

    # Fallback to episode store if no Neo4j data
    if not episodes and episode_store is not None:
        try:
            store_episodes = episode_store.list_episodes(limit=limit)
            for ep in store_episodes:
                episodes.append(Episode(
                    id=ep.id,
                    title=ep.title,
                    timestamp=ep.timestamp,
                    category=ep.category,
                    severity=ep.severity,
                    services=ep.affected_services,
                    root_cause=ep.root_cause,
                    resolution=ep.resolution,
                    confidence=ep.confidence,
                ))

                for svc in ep.affected_services:
                    edges.append({
                        "from": f"episode-{ep.id}",
                        "to": f"service-{svc}",
                        "label": "affects",
                    })
        except Exception as e:
            logger.warning(f"Failed to query episode store: {e}")

    # If no services found, create default services from monitored containers
    if not services:
        from src.api.routes.infrastructure import _monitored_containers

        # Create service nodes from monitored containers
        for container_name in _monitored_containers:
            # Infer service name from container name
            service_name = container_name.replace("aiops-", "")
            services.append(ServiceNode(
                name=service_name,
                type="container",
                status="healthy",
            ))

        # Add default service dependencies
        default_deps = [
            ("frontend", "backend"),
            ("backend", "neo4j"),
            ("backend", "loki"),
            ("backend", "prometheus"),
            ("grafana", "loki"),
            ("grafana", "prometheus"),
            ("grafana", "tempo"),
            ("otel-collector", "loki"),
            ("otel-collector", "prometheus"),
            ("otel-collector", "tempo"),
        ]

        service_names = {s.name for s in services}
        for from_svc, to_svc in default_deps:
            if from_svc in service_names and to_svc in service_names:
                edges.append({
                    "from": f"service-{from_svc}",
                    "to": f"service-{to_svc}",
                    "label": "depends_on",
                })

    return GraphData(services=services, episodes=episodes, edges=edges)


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

        result = await neo4j_client.query(query, {})

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
        downstream_result = await neo4j_client.query(downstream_query, {"name": name})
        downstream = [row["name"] for row in downstream_result]

        # Get upstream dependencies
        upstream_query = f"""
        MATCH (upstream:Service)-[:DEPENDS_ON*1..{depth}]->(s:Service {{name: $name}})
        RETURN DISTINCT upstream.name as name
        """
        upstream_result = await neo4j_client.query(upstream_query, {"name": name})
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
            # Get node count
            result = await neo4j_client.query("MATCH (n) RETURN count(n) as count", {})
            node_count = result[0]["count"] if result else 0

            # Get edge count
            result = await neo4j_client.query("MATCH ()-[r]->() RETURN count(r) as count", {})
            edge_count = result[0]["count"] if result else 0

            # Get episode count
            result = await neo4j_client.query("MATCH (e:Episode) RETURN count(e) as count", {})
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
