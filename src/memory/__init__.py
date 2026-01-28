"""Constitutional AIOps - Graph-episodic memory."""

from src.memory.neo4j_client import Neo4jClient, get_neo4j_client, NEO4J_AVAILABLE
from src.memory.episode_store import Episode, EpisodeStore
from src.memory.retrieval import RetrievalContext, ContextRetriever
from src.memory.embedding_service import (
    EmbeddingService,
    get_embedding_service,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    SIMILARITY_THRESHOLD,
)

__all__ = [
    # Neo4j
    "Neo4jClient",
    "get_neo4j_client",
    "NEO4J_AVAILABLE",
    # Episodes
    "Episode",
    "EpisodeStore",
    # Retrieval
    "RetrievalContext",
    "ContextRetriever",
    # Embeddings
    "EmbeddingService",
    "get_embedding_service",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    "SIMILARITY_THRESHOLD",
]
