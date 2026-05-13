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
                # Semantic memory indexes (AriGraph-inspired)
                "CREATE INDEX episode_id IF NOT EXISTS FOR (e:Episode) ON (e.episode_id)",
                "CREATE INDEX entity_name IF NOT EXISTS FOR (en:Entity) ON (en.name)",
                "CREATE INDEX rootcause_type IF NOT EXISTS FOR (rc:RootCauseType) ON (rc.name)",
            ]

            # Full-text indexes for semantic search (AriGraph-inspired)
            fulltext_indexes = [
                """CREATE FULLTEXT INDEX incident_search IF NOT EXISTS
                   FOR (i:Incident) ON EACH [i.description, i.title]""",
                """CREATE FULLTEXT INDEX episode_search IF NOT EXISTS
                   FOR (e:Episode) ON EACH [e.title, e.root_cause]""",
                """CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
                   FOR (en:Entity) ON EACH [en.name, en.description]""",
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

            for ft_index in fulltext_indexes:
                try:
                    await session.run(ft_index)
                except Exception as e:
                    logger.debug(f"Full-text index may already exist: {e}")

            logger.info("Neo4j schema initialized with full-text indexes")

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

    # --- Semantic Memory Operations (AriGraph-inspired) ---

    async def store_semantic_triplet(
        self,
        triplet: dict[str, Any],
        episode_id: str,
    ) -> None:
        """
        Store a semantic triplet in the knowledge graph.

        Following AriGraph pattern for building semantic memory.

        Args:
            triplet: Dict with entity1, relation, entity2, confidence
            episode_id: Source episode ID for traceability
        """
        if not self._connected:
            return

        query = """
        MATCH (ep:Episode {episode_id: $episode_id})
        MERGE (e1:Entity {name: $entity1})
        MERGE (e2:Entity {name: $entity2})
        MERGE (e1)-[r:RELATES {type: $relation}]->(e2)
        SET r.confidence = $confidence,
            r.source_episode = $episode_id,
            r.updated_at = datetime()
        MERGE (ep)-[:EXTRACTED]->(e1)
        MERGE (ep)-[:EXTRACTED]->(e2)
        """

        async with self.session() as session:
            await session.run(
                query,
                episode_id=episode_id,
                entity1=triplet["entity1"],
                entity2=triplet["entity2"],
                relation=triplet["relation"],
                confidence=triplet.get("confidence", 0.5),
            )

    async def link_episode_to_root_cause_type(
        self,
        episode_id: str,
        root_cause_type: str,
    ) -> None:
        """
        Create episodic-semantic edge linking episode to root cause type.

        Args:
            episode_id: Episode ID
            root_cause_type: Root cause category (e.g., "memory", "network")
        """
        if not self._connected:
            return

        query = """
        MATCH (ep:Episode {episode_id: $episode_id})
        MERGE (rc:RootCauseType {name: $root_cause_type})
        MERGE (ep)-[:CAUSED_BY]->(rc)
        """

        async with self.session() as session:
            await session.run(
                query,
                episode_id=episode_id,
                root_cause_type=root_cause_type,
            )

    async def find_episodes_by_root_cause_type(
        self,
        root_cause_type: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find episodes that share the same root cause type.

        Args:
            root_cause_type: Root cause category
            limit: Maximum results

        Returns:
            List of episode data dictionaries
        """
        if not self._connected:
            return []

        query = """
        MATCH (ep:Episode)-[:CAUSED_BY]->(rc:RootCauseType {name: $root_cause_type})
        RETURN ep.episode_id as episode_id,
               ep.title as title,
               ep.severity as severity,
               ep.outcome as outcome,
               ep.confidence as confidence
        ORDER BY ep.detected_at DESC
        LIMIT $limit
        """

        async with self.session() as session:
            result = await session.run(
                query,
                root_cause_type=root_cause_type,
                limit=limit,
            )
            records = await result.data()
            return records

    async def find_similar_episodes_by_embedding(
        self,
        query_embedding: list[float],
        exclude_id: Optional[str] = None,
        top_k: int = 3,
        min_similarity: float = 0.60,
    ) -> list[dict[str, Any]]:
        """
        Retrieve top-K episodes from Neo4j by cosine similarity to query_embedding.

        Neo4j Community Edition has no vector index, so we fetch all episode
        embeddings and compute cosine similarity in Python (numpy).
        Fine for up to ~500 episodes x 384 dims — sub-millisecond.

        Returns list of dicts: episode_id, title, root_cause, outcome,
        confidence, similarity. embedding field is NOT returned.
        """
        if not self._connected:
            return []

        cypher = """
        MATCH (ep:Episode)
        WHERE ep.has_embedding = true AND ep.embedding IS NOT NULL
        AND ($exclude_id IS NULL OR ep.episode_id <> $exclude_id)
        RETURN ep.episode_id AS episode_id,
               ep.title      AS title,
               ep.root_cause AS root_cause,
               ep.outcome    AS outcome,
               ep.confidence AS confidence,
               ep.embedding  AS embedding
        """

        try:
            async with self.session() as session:
                result = await session.run(cypher, exclude_id=exclude_id)
                records = await result.data()

            if not records:
                return []

            import json as _json
            import numpy as _np

            q = _np.array(query_embedding, dtype=_np.float32)
            q_norm = _np.linalg.norm(q)
            if q_norm == 0:
                return []
            q_unit = q / q_norm

            scored: list[dict[str, Any]] = []
            for rec in records:
                try:
                    raw_emb = rec["embedding"]
                    emb_list = _json.loads(raw_emb) if isinstance(raw_emb, str) else raw_emb
                    e = _np.array(emb_list, dtype=_np.float32)
                    e_norm = _np.linalg.norm(e)
                    if e_norm == 0:
                        continue
                    sim = float(_np.dot(q_unit, e / e_norm))
                    if sim >= min_similarity:
                        scored.append({
                            "episode_id": rec["episode_id"],
                            "title":      rec["title"],
                            "root_cause": rec["root_cause"],
                            "outcome":    rec["outcome"],
                            "confidence": rec["confidence"],
                            "similarity": sim,
                        })
                except Exception:
                    continue

            scored.sort(key=lambda x: x["similarity"], reverse=True)
            return scored[:top_k]

        except Exception as exc:
            logger.warning(f"find_similar_episodes_by_embedding failed: {exc}")
            return []

    async def fulltext_search_incidents(
        self,
        query_text: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search incidents using full-text index.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            List of matching incidents with scores
        """
        if not self._connected:
            return []

        query = """
        CALL db.index.fulltext.queryNodes("incident_search", $query_text)
        YIELD node, score
        RETURN node.id as id,
               node.title as title,
               node.description as description,
               score
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            async with self.session() as session:
                result = await session.run(
                    query,
                    query_text=query_text,
                    limit=limit,
                )
                records = await result.data()
                return records
        except Exception as e:
            logger.warning(f"Full-text search failed: {e}")
            return []

    async def get_successful_remediations_for_cause(
        self,
        root_cause_type: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find successful remediations for a root cause type.

        Uses semantic graph to find what actions resolved similar issues.

        Args:
            root_cause_type: Root cause category
            limit: Maximum results

        Returns:
            List of successful remediation patterns
        """
        if not self._connected:
            return []

        query = """
        MATCH (rc:RootCauseType {name: $root_cause_type})<-[:CAUSED_BY]-(ep:Episode)
        WHERE ep.outcome = 'resolved'
        WITH ep, rc
        MATCH (ep)-[:INVOLVES]->(s:Service)
        RETURN ep.episode_id as episode_id,
               ep.title as title,
               ep.successful_actions as actions,
               ep.confidence as confidence,
               collect(s.name) as services
        ORDER BY ep.confidence DESC
        LIMIT $limit
        """

        async with self.session() as session:
            result = await session.run(
                query,
                root_cause_type=root_cause_type,
                limit=limit,
            )
            records = await result.data()
            return records

    # --- Graph Cleanup Operations ---

    async def cleanup_graph(
        self,
        delete_similar_to: bool = True,
        merge_duplicate_entities: bool = True,
        delete_orphan_entities: bool = True,
        keep_episodes: int = 50,
    ) -> dict[str, int]:
        """
        Clean up the graph to prevent hairball visualization.

        Performs:
        1. Delete all SIMILAR_TO edges (recalculated at query time)
        2. Merge duplicate Entity nodes (case-insensitive)
        3. Delete orphan entities with no relationships
        4. Keep only the most recent N episodes

        Args:
            delete_similar_to: Delete all SIMILAR_TO edges
            merge_duplicate_entities: Merge entities with same name (case-insensitive)
            delete_orphan_entities: Delete entities with no relationships
            keep_episodes: Number of recent episodes to keep (0 = keep all)

        Returns:
            Dict with counts of deleted/merged items
        """
        if not self._connected:
            return {"error": "Not connected"}

        stats = {
            "similar_to_deleted": 0,
            "entities_merged": 0,
            "orphan_entities_deleted": 0,
            "old_episodes_deleted": 0,
        }

        async with self.session() as session:
            # 1. Delete SIMILAR_TO edges
            if delete_similar_to:
                result = await session.run("""
                    MATCH ()-[r:SIMILAR_TO]->()
                    WITH r LIMIT 10000
                    DELETE r
                    RETURN count(r) as deleted
                """)
                record = await result.single()
                stats["similar_to_deleted"] = record["deleted"] if record else 0
                logger.info(f"Deleted {stats['similar_to_deleted']} SIMILAR_TO edges")

            # 2. Merge duplicate entities (case-insensitive)
            # Note: This requires iterating since Neo4j doesn't have native case-insensitive merge
            if merge_duplicate_entities:
                # Find duplicate entity names
                result = await session.run("""
                    MATCH (e:Entity)
                    WITH toLower(e.name) as lower_name, collect(e) as entities
                    WHERE size(entities) > 1
                    RETURN lower_name, entities
                """)
                duplicates = await result.data()

                merged_count = 0
                for dup in duplicates:
                    entities = dup["entities"]
                    if len(entities) > 1:
                        # Keep first entity, merge others into it
                        keep_id = entities[0].element_id if hasattr(entities[0], 'element_id') else entities[0].id
                        for other in entities[1:]:
                            other_id = other.element_id if hasattr(other, 'element_id') else other.id
                            # Transfer relationships and delete duplicate
                            await session.run("""
                                MATCH (keep:Entity) WHERE elementId(keep) = $keep_id
                                MATCH (dup:Entity) WHERE elementId(dup) = $dup_id
                                OPTIONAL MATCH (dup)-[r_out]->(target)
                                OPTIONAL MATCH (source)-[r_in]->(dup)
                                FOREACH (r IN CASE WHEN r_out IS NOT NULL THEN [r_out] ELSE [] END |
                                    MERGE (keep)-[:RELATES]->(target)
                                )
                                FOREACH (r IN CASE WHEN r_in IS NOT NULL THEN [r_in] ELSE [] END |
                                    MERGE (source)-[:RELATES]->(keep)
                                )
                                DETACH DELETE dup
                            """, keep_id=keep_id, dup_id=other_id)
                            merged_count += 1

                stats["entities_merged"] = merged_count
                logger.info(f"Merged {merged_count} duplicate entities")

            # 3. Delete orphan entities
            if delete_orphan_entities:
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE NOT (e)--()
                    WITH e LIMIT 1000
                    DELETE e
                    RETURN count(e) as deleted
                """)
                record = await result.single()
                stats["orphan_entities_deleted"] = record["deleted"] if record else 0
                logger.info(f"Deleted {stats['orphan_entities_deleted']} orphan entities")

            # 4. Keep only recent episodes
            if keep_episodes > 0:
                result = await session.run("""
                    MATCH (ep:Episode)
                    WITH ep ORDER BY ep.detected_at DESC
                    SKIP $keep
                    DETACH DELETE ep
                    RETURN count(ep) as deleted
                """, keep=keep_episodes)
                record = await result.single()
                stats["old_episodes_deleted"] = record["deleted"] if record else 0
                logger.info(f"Deleted {stats['old_episodes_deleted']} old episodes")

        logger.info(f"Graph cleanup complete: {stats}")
        return stats

    async def get_graph_stats(self) -> dict[str, Any]:
        """
        Get current graph statistics for monitoring.

        Returns:
            Dict with node and edge counts by type
        """
        if not self._connected:
            return {"error": "Not connected"}

        async with self.session() as session:
            result = await session.run("""
                MATCH (n)
                WITH labels(n)[0] as label, count(n) as count
                RETURN collect({label: label, count: count}) as nodes
            """)
            nodes_record = await result.single()
            nodes = {item["label"]: item["count"] for item in nodes_record["nodes"]} if nodes_record else {}

            result = await session.run("""
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(r) as count
                RETURN collect({type: rel_type, count: count}) as edges
            """)
            edges_record = await result.single()
            edges = {item["type"]: item["count"] for item in edges_record["edges"]} if edges_record else {}

            return {
                "nodes": nodes,
                "edges": edges,
                "total_nodes": sum(nodes.values()),
                "total_edges": sum(edges.values()),
            }


# Singleton instance (optional)
_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client singleton."""
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client


__all__ = ["Neo4jClient", "get_neo4j_client", "NEO4J_AVAILABLE"]
