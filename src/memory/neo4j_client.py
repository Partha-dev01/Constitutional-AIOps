"""
Constitutional AIOps - Neo4j Client

Graph database client for episodic memory storage.
Stores incidents, actions, and their relationships for pattern learning.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

from src.config import config

logger = logging.getLogger(__name__)

# Try to import neo4j, but allow graceful fallback
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncDriver = Any
    AsyncSession = Any
    logger.warning("neo4j package not installed. Graph memory will be disabled.")


class Neo4jClient:
    """
    Async Neo4j client for graph-episodic memory.

    Stores:
    - Incidents and their relationships
    - Actions and outcomes
    - Service dependencies
    - Similar incident patterns
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j bolt URI (default from config)
            user: Neo4j username (default from config)
            password: Neo4j password (default from config)
            database: Neo4j database name (default from config)
        """
        self.uri = uri or config.neo4j.uri
        self.user = user or config.neo4j.user
        self.password = password or config.neo4j.password
        self.database = database or config.neo4j.database

        self._driver: Optional[AsyncDriver] = None
        self._connected = False

        logger.info(f"Neo4jClient initialized (uri: {self.uri})")

    async def connect(self) -> bool:
        """
        Establish connection to Neo4j.

        Returns:
            True if connection successful, False otherwise
        """
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available, skipping connection")
            return False

        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            self._connected = True
            logger.info("Connected to Neo4j successfully")

            # Initialize schema
            await self._initialize_schema()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")

    async def health_check(self) -> bool:
        """
        Check Neo4j connection health.

        Returns:
            True if healthy, False otherwise
        """
        if not self._connected or not self._driver:
            return False

        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a Neo4j session context manager.

        Yields:
            AsyncSession for running queries
        """
        if not self._driver:
            raise RuntimeError("Neo4j client not connected")

        session = self._driver.session(database=self.database)
        try:
            yield session
        finally:
            await session.close()

    async def _initialize_schema(self) -> None:
        """Initialize Neo4j schema with indexes and constraints."""
        if not self._driver:
            return

        async with self.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE",
            ]

            # Create indexes for common queries
            indexes = [
                "CREATE INDEX incident_created IF NOT EXISTS FOR (i:Incident) ON (i.created_at)",
                "CREATE INDEX incident_status IF NOT EXISTS FOR (i:Incident) ON (i.status)",
                "CREATE INDEX incident_severity IF NOT EXISTS FOR (i:Incident) ON (i.severity)",
                "CREATE INDEX action_status IF NOT EXISTS FOR (a:Action) ON (a.status)",
                "CREATE INDEX service_namespace IF NOT EXISTS FOR (s:Service) ON (s.namespace)",
            ]

            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint may already exist: {e}")

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug(f"Index may already exist: {e}")

            logger.info("Neo4j schema initialized")

    # --- Incident Operations ---

    async def create_incident(self, incident: dict[str, Any]) -> str:
        """
        Create an incident node in the graph.

        Args:
            incident: Incident data dictionary

        Returns:
            Incident ID
        """
        if not self._connected:
            logger.warning("Neo4j not connected, incident not persisted")
            return incident.get("id", "")

        query = """
        CREATE (i:Incident {
            id: $id,
            title: $title,
            description: $description,
            severity: $severity,
            status: $status,
            category: $category,
            source: $source,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN i.id as id
        """

        async with self.session() as session:
            result = await session.run(
                query,
                id=incident["id"],
                title=incident["title"],
                description=incident.get("description", ""),
                severity=incident["severity"],
                status=incident["status"],
                category=incident.get("category", "unknown"),
                source=incident.get("source", "manual"),
                created_at=incident["created_at"].isoformat() if isinstance(incident["created_at"], datetime) else incident["created_at"],
                updated_at=incident["updated_at"].isoformat() if isinstance(incident["updated_at"], datetime) else incident["updated_at"],
            )
            record = await result.single()
            return record["id"] if record else incident["id"]

    async def update_incident(self, incident_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an incident node.

        Args:
            incident_id: Incident ID
            updates: Fields to update

        Returns:
            True if updated successfully
        """
        if not self._connected:
            return False

        # Build dynamic SET clause
        set_parts = []
        params = {"id": incident_id}

        for key, value in updates.items():
            if key not in ("id",):
                set_parts.append(f"i.{key} = ${key}")
                if isinstance(value, datetime):
                    params[key] = value.isoformat()
                else:
                    params[key] = value

        if not set_parts:
            return True

        query = f"""
        MATCH (i:Incident {{id: $id}})
        SET {', '.join(set_parts)}
        RETURN i.id as id
        """

        async with self.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record is not None

    async def get_incident(self, incident_id: str) -> Optional[dict[str, Any]]:
        """
        Get an incident by ID.

        Args:
            incident_id: Incident ID

        Returns:
            Incident data or None
        """
        if not self._connected:
            return None

        query = """
        MATCH (i:Incident {id: $id})
        RETURN i
        """

        async with self.session() as session:
            result = await session.run(query, id=incident_id)
            record = await result.single()
            if record:
                return dict(record["i"])
            return None

    async def link_incident_to_service(
        self,
        incident_id: str,
        service_name: str,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Create relationship between incident and affected service.

        Args:
            incident_id: Incident ID
            service_name: Service name
            namespace: Optional service namespace
        """
        if not self._connected:
            return

        query = """
        MATCH (i:Incident {id: $incident_id})
        MERGE (s:Service {name: $service_name})
        ON CREATE SET s.namespace = $namespace
        MERGE (i)-[:AFFECTS]->(s)
        """

        async with self.session() as session:
            await session.run(
                query,
                incident_id=incident_id,
                service_name=service_name,
                namespace=namespace,
            )

    async def find_similar_incidents(
        self,
        incident_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find similar incidents based on affected services and category.

        Args:
            incident_id: Reference incident ID
            limit: Maximum results to return

        Returns:
            List of similar incidents with similarity scores
        """
        if not self._connected:
            return []

        query = """
        MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)<-[:AFFECTS]-(similar:Incident)
        WHERE similar.id <> $incident_id
        WITH similar, COUNT(s) as shared_services
        OPTIONAL MATCH (i:Incident {id: $incident_id})
        WHERE similar.category = i.category
        WITH similar, shared_services,
             CASE WHEN similar.category = i.category THEN 1 ELSE 0 END as same_category
        WITH similar, (shared_services * 0.6 + same_category * 0.4) as score
        ORDER BY score DESC
        LIMIT $limit
        RETURN similar.id as id, similar.title as title, similar.severity as severity,
               similar.status as status, similar.created_at as created_at, score
        """

        async with self.session() as session:
            result = await session.run(query, incident_id=incident_id, limit=limit)
            records = await result.data()
            return records

    # --- Action Operations ---

    async def create_action(self, action: dict[str, Any]) -> str:
        """
        Create an action node in the graph.

        Args:
            action: Action data dictionary

        Returns:
            Action ID
        """
        if not self._connected:
            return action.get("id", "")

        query = """
        CREATE (a:Action {
            id: $id,
            action_type: $action_type,
            description: $description,
            target_service: $target_service,
            status: $status,
            confidence: $confidence,
            created_at: datetime($created_at)
        })
        RETURN a.id as id
        """

        async with self.session() as session:
            result = await session.run(
                query,
                id=action["id"],
                action_type=action["action_type"],
                description=action["description"],
                target_service=action["target_service"],
                status=action["status"],
                confidence=action["confidence"],
                created_at=action["created_at"].isoformat() if isinstance(action["created_at"], datetime) else action["created_at"],
            )
            record = await result.single()
            return record["id"] if record else action["id"]

    async def link_action_to_incident(
        self,
        action_id: str,
        incident_id: str,
    ) -> None:
        """
        Create relationship between action and incident.

        Args:
            action_id: Action ID
            incident_id: Incident ID
        """
        if not self._connected:
            return

        query = """
        MATCH (a:Action {id: $action_id})
        MATCH (i:Incident {id: $incident_id})
        MERGE (a)-[:REMEDIATES]->(i)
        """

        async with self.session() as session:
            await session.run(query, action_id=action_id, incident_id=incident_id)

    async def record_action_outcome(
        self,
        action_id: str,
        success: bool,
        duration_ms: float,
        notes: Optional[str] = None,
    ) -> None:
        """
        Record the outcome of an action for learning.

        Args:
            action_id: Action ID
            success: Whether action succeeded
            duration_ms: Execution duration
            notes: Optional outcome notes
        """
        if not self._connected:
            return

        query = """
        MATCH (a:Action {id: $action_id})
        SET a.success = $success,
            a.duration_ms = $duration_ms,
            a.outcome_notes = $notes,
            a.completed_at = datetime()
        """

        async with self.session() as session:
            await session.run(
                query,
                action_id=action_id,
                success=success,
                duration_ms=duration_ms,
                notes=notes,
            )

    # --- Service Dependency Graph ---

    async def create_service_dependency(
        self,
        from_service: str,
        to_service: str,
        dependency_type: str = "calls",
    ) -> None:
        """
        Create a dependency relationship between services.

        Args:
            from_service: Source service name
            to_service: Target service name
            dependency_type: Type of dependency (calls, uses, etc.)
        """
        if not self._connected:
            return

        query = """
        MERGE (s1:Service {name: $from_service})
        MERGE (s2:Service {name: $to_service})
        MERGE (s1)-[r:DEPENDS_ON {type: $dependency_type}]->(s2)
        """

        async with self.session() as session:
            await session.run(
                query,
                from_service=from_service,
                to_service=to_service,
                dependency_type=dependency_type,
            )

    async def get_service_dependencies(
        self,
        service_name: str,
        depth: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Get dependencies for a service up to specified depth.

        Args:
            service_name: Service name
            depth: Maximum depth to traverse

        Returns:
            List of dependent services
        """
        if not self._connected:
            return []

        query = """
        MATCH path = (s:Service {name: $service_name})-[:DEPENDS_ON*1..$depth]->(dep:Service)
        RETURN dep.name as name, dep.namespace as namespace, length(path) as distance
        ORDER BY distance
        """

        async with self.session() as session:
            result = await session.run(query, service_name=service_name, depth=depth)
            records = await result.data()
            return records

    async def get_affected_by_service(
        self,
        service_name: str,
    ) -> list[dict[str, Any]]:
        """
        Get services that depend on the given service (impact analysis).

        Args:
            service_name: Service name

        Returns:
            List of services that would be affected
        """
        if not self._connected:
            return []

        query = """
        MATCH (dep:Service)-[:DEPENDS_ON*]->(s:Service {name: $service_name})
        RETURN DISTINCT dep.name as name, dep.namespace as namespace
        """

        async with self.session() as session:
            result = await session.run(query, service_name=service_name)
            records = await result.data()
            return records

    # --- Statistics and Analytics ---

    async def get_incident_stats(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get incident statistics for the past N days.

        Args:
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        if not self._connected:
            return {}

        query = """
        MATCH (i:Incident)
        WHERE i.created_at > datetime() - duration({days: $days})
        RETURN
            COUNT(i) as total,
            COUNT(CASE WHEN i.status = 'resolved' THEN 1 END) as resolved,
            COUNT(CASE WHEN i.severity = 'critical' THEN 1 END) as critical,
            AVG(CASE WHEN i.resolved_at IS NOT NULL
                THEN duration.between(i.created_at, i.resolved_at).minutes
                END) as avg_resolution_minutes
        """

        async with self.session() as session:
            result = await session.run(query, days=days)
            record = await result.single()
            if record:
                return dict(record)
            return {}

    async def get_action_success_rate(
        self,
        action_type: Optional[str] = None,
        days: int = 30,
    ) -> float:
        """
        Get action success rate for learning feedback.

        Args:
            action_type: Optional filter by action type
            days: Number of days to analyze

        Returns:
            Success rate (0.0-1.0)
        """
        if not self._connected:
            return 0.0

        query = """
        MATCH (a:Action)
        WHERE a.created_at > datetime() - duration({days: $days})
        AND a.success IS NOT NULL
        """ + ("AND a.action_type = $action_type" if action_type else "") + """
        RETURN
            COUNT(CASE WHEN a.success = true THEN 1 END) as successes,
            COUNT(a) as total
        """

        params = {"days": days}
        if action_type:
            params["action_type"] = action_type

        async with self.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            if record and record["total"] > 0:
                return record["successes"] / record["total"]
            return 0.0


# Singleton instance (optional)
_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client singleton."""
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client


__all__ = ["Neo4jClient", "get_neo4j_client", "NEO4J_AVAILABLE"]
