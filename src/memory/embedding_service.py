"""
Constitutional AIOps - Embedding Service

Provides semantic embeddings for episodes using sentence-transformers.
Implements the vector similarity component from Research_V7.tex.

Model: all-MiniLM-L6-v2 (384 dimensions)
- Optimized for semantic similarity
- ~22M parameters, fast inference
- Works well on both CPU and GPU

CUDA Support:
- Automatically uses GPU if available (NVIDIA GTX 1650+)
- Falls back to CPU if no GPU detected
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# Constants from Research_V7.tex
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
SIMILARITY_THRESHOLD = 0.70  # Minimum cosine similarity for matching


class EmbeddingService:
    """
    Singleton service for generating and comparing semantic embeddings.

    Uses sentence-transformers/all-MiniLM-L6-v2 model.
    Supports GPU acceleration with CUDA for NVIDIA GPUs.
    """

    _instance: Optional["EmbeddingService"] = None
    _initialized: bool = False

    def __new__(cls) -> "EmbeddingService":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize embedding service with lazy model loading."""
        if self._initialized:
            return

        self._model = None
        self._device = None
        self._model_name = EMBEDDING_MODEL
        self._dimensions = EMBEDDING_DIMENSIONS
        self._is_available = False

        # Decide availability WITHOUT importing sentence-transformers here. That
        # import pulls in torch + transformers (tens of seconds on a cold start),
        # and because EmbeddingService is constructed during app startup it blocked
        # uvicorn from serving for that whole window. importlib.util.find_spec only
        # checks the package is installed (no heavy import); the real import is
        # deferred to _load_model, which runs on first embed, after we are serving.
        try:
            import importlib.util
            self._is_available = importlib.util.find_spec("sentence_transformers") is not None
        except (ImportError, ValueError):
            self._is_available = False

        if self._is_available:
            logger.info("Sentence-transformers available, will lazy-load model on first use")
        else:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers torch"
            )

        self._initialized = True

    def _load_model(self) -> bool:
        """
        Lazy-load the embedding model.

        Returns:
            True if model loaded successfully
        """
        if self._model is not None:
            return True

        if not self._is_available:
            return False

        try:
            import torch
            from sentence_transformers import SentenceTransformer

            # Check for CUDA availability
            if torch.cuda.is_available():
                self._device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA available, using GPU: {gpu_name}")
            else:
                self._device = "cpu"
                logger.info("CUDA not available, using CPU")

            # Load model. This is the first heavy sentence-transformers import; it
            # lives here (not __init__) so it never blocks app startup.
            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
            logger.info(f"Embedding model loaded on {self._device}")
            return True

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._model = None
            return False

    @property
    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self._is_available

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    @property
    def device(self) -> Optional[str]:
        """Get the device being used (cuda/cpu)."""
        return self._device

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    def encode(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding for text.

        Args:
            text: Input text to encode

        Returns:
            384-dimensional embedding as list, or None if unavailable
        """
        if not text or not text.strip():
            return None

        if not self._load_model():
            return None

        try:
            # Generate embedding
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalize for cosine similarity
            )
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def encode_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embeddings (None for failed texts)
        """
        if not texts:
            return []

        if not self._load_model():
            return [None] * len(texts)

        try:
            # Filter out empty texts and track indices
            valid_indices = []
            valid_texts = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_indices.append(i)
                    valid_texts.append(text)

            if not valid_texts:
                return [None] * len(texts)

            # Batch encode
            embeddings = self._model.encode(
                valid_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False,
            )

            # Map back to original indices
            results: list[Optional[list[float]]] = [None] * len(texts)
            for i, idx in enumerate(valid_indices):
                results[idx] = embeddings[i].tolist()

            return results

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)

    def cosine_similarity(
        self,
        vec1: list[float],
        vec2: list[float],
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if not vec1 or not vec2:
            return 0.0

        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0

        try:
            a = np.array(vec1, dtype=np.float32)
            b = np.array(vec2, dtype=np.float32)

            # Compute cosine similarity
            dot = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = float(dot / (norm_a * norm_b))

            # Clamp to [0, 1] (normalized vectors should already be in this range)
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error(f"Failed to compute cosine similarity: {e}")
            return 0.0

    def find_most_similar(
        self,
        query_embedding: list[float],
        candidate_embeddings: list[tuple[str, list[float]]],
        top_k: int = 5,
        min_similarity: float = SIMILARITY_THRESHOLD,
    ) -> list[tuple[str, float]]:
        """
        Find most similar embeddings from candidates.

        Args:
            query_embedding: Query vector
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (id, similarity) tuples, sorted by similarity descending
        """
        if not query_embedding or not candidate_embeddings:
            return []

        results = []

        for item_id, embedding in candidate_embeddings:
            if not embedding:
                continue

            similarity = self.cosine_similarity(query_embedding, embedding)

            if similarity >= min_similarity:
                results.append((item_id, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_status(self) -> dict:
        """Get embedding service status."""
        return {
            "available": self._is_available,
            "loaded": self._model is not None,
            "model": self._model_name,
            "dimensions": self._dimensions,
            "device": self._device,
            "similarity_threshold": SIMILARITY_THRESHOLD,
        }


# Module-level singleton accessor
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    "SIMILARITY_THRESHOLD",
]
