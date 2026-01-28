"""
Constitutional AIOps - Confidence Calculator

Implements the composite confidence formula from Research_V6.tex:
C(a) = α·C_LLM + β·C_hist + γ·C_sim

This module computes a weighted confidence score combining:
- C_LLM: Raw LLM confidence from the reasoning agent
- C_hist: Historical success rate for this action type
- C_sim: Similarity score to past successfully resolved incidents
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.memory.neo4j_client import Neo4jClient
    from src.memory.episode_store import EpisodeStore

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceBreakdown:
    """Breakdown of composite confidence calculation."""

    composite: float
    c_llm: float
    c_hist: float
    c_sim: float
    alpha: float
    beta: float
    gamma: float
    historical_data_available: bool
    similar_episodes_found: int
    fallback_used: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "composite_confidence": round(self.composite, 4),
            "components": {
                "c_llm": round(self.c_llm, 4),
                "c_hist": round(self.c_hist, 4),
                "c_sim": round(self.c_sim, 4),
            },
            "weights": {
                "alpha": self.alpha,
                "beta": self.beta,
                "gamma": self.gamma,
            },
            "metadata": {
                "historical_data_available": self.historical_data_available,
                "similar_episodes_found": self.similar_episodes_found,
                "fallback_used": self.fallback_used,
            },
        }


class ConfidenceCalculator:
    """
    Calculates composite confidence for action authorization.

    Formula from Research_V6.tex:
    C(a) = α·C_LLM + β·C_hist + γ·C_sim

    Where:
      α = 0.40 (LLM confidence weight)
      β = 0.35 (Historical success rate weight)
      γ = 0.25 (Similarity to past incidents weight)

    This weighted approach ensures:
    - LLM reasoning is the primary signal
    - Historical patterns improve accuracy over time
    - Similar incident context provides additional validation
    """

    # Weights from Research_V6.tex
    ALPHA = 0.40  # LLM confidence weight
    BETA = 0.35   # Historical success rate weight
    GAMMA = 0.25  # Similarity score weight

    # Default values when data unavailable (neutral contribution)
    DEFAULT_HISTORICAL = 0.5
    DEFAULT_SIMILARITY = 0.5

    def __init__(
        self,
        neo4j_client: Optional["Neo4jClient"] = None,
        episode_store: Optional["EpisodeStore"] = None,
    ):
        """
        Initialize confidence calculator.

        Args:
            neo4j_client: Neo4j client for historical success rates
            episode_store: Episode store for similarity lookups
        """
        self.neo4j_client = neo4j_client
        self.episode_store = episode_store

        logger.info(
            f"ConfidenceCalculator initialized with weights: "
            f"α={self.ALPHA}, β={self.BETA}, γ={self.GAMMA}"
        )

    async def calculate_composite(
        self,
        llm_confidence: float,
        action_type: str,
        incident_context: Optional[dict[str, Any]] = None,
    ) -> tuple[float, ConfidenceBreakdown]:
        """
        Calculate composite confidence score.

        Args:
            llm_confidence: Raw confidence from LLM (0.0-1.0)
            action_type: Type of action (restart, scale_up, etc.)
            incident_context: Optional context for similarity lookup
                - incident_id: Related incident ID
                - affected_services: List of affected services
                - category: Incident category
                - description: Incident description

        Returns:
            Tuple of (composite_confidence, breakdown)
        """
        c_llm = max(0.0, min(1.0, llm_confidence))  # Clamp to [0, 1]

        # Get historical success rate
        c_hist, hist_available = await self._get_historical_success_rate(action_type)

        # Get similarity score
        c_sim, similar_count = await self._get_similarity_score(incident_context)

        # Check if fallback was used
        fallback_used = not hist_available and similar_count == 0

        # Calculate composite: C(a) = α·C_LLM + β·C_hist + γ·C_sim
        composite = (
            self.ALPHA * c_llm +
            self.BETA * c_hist +
            self.GAMMA * c_sim
        )

        # Clamp final result
        composite = max(0.0, min(1.0, composite))

        breakdown = ConfidenceBreakdown(
            composite=composite,
            c_llm=c_llm,
            c_hist=c_hist,
            c_sim=c_sim,
            alpha=self.ALPHA,
            beta=self.BETA,
            gamma=self.GAMMA,
            historical_data_available=hist_available,
            similar_episodes_found=similar_count,
            fallback_used=fallback_used,
        )

        logger.debug(
            f"Composite confidence: {composite:.4f} "
            f"(LLM={c_llm:.2f}, hist={c_hist:.2f}, sim={c_sim:.2f})"
        )

        return composite, breakdown

    async def _get_historical_success_rate(
        self,
        action_type: str,
    ) -> tuple[float, bool]:
        """
        Get historical success rate for action type.

        Args:
            action_type: Type of action

        Returns:
            Tuple of (success_rate, data_available)
        """
        if not self.neo4j_client:
            logger.debug("Neo4j client not available, using default historical rate")
            return self.DEFAULT_HISTORICAL, False

        try:
            success_rate = await self.neo4j_client.get_action_success_rate(
                action_type=action_type,
                days=30,  # Look at last 30 days
            )

            # If no data, success_rate will be 0.0, use default
            if success_rate == 0.0:
                # Check if there's actually no data vs all failures
                # For now, assume no data means use default
                return self.DEFAULT_HISTORICAL, False

            return success_rate, True

        except Exception as e:
            logger.warning(f"Failed to get historical success rate: {e}")
            return self.DEFAULT_HISTORICAL, False

    async def _get_similarity_score(
        self,
        incident_context: Optional[dict[str, Any]],
    ) -> tuple[float, int]:
        """
        Get similarity score based on past incidents.

        Uses episode store to find similar past incidents and
        returns weighted average similarity of successfully resolved ones.

        Args:
            incident_context: Context for similarity lookup

        Returns:
            Tuple of (similarity_score, episodes_found)
        """
        if not self.episode_store or not incident_context:
            logger.debug("Episode store or context not available, using default similarity")
            return self.DEFAULT_SIMILARITY, 0

        try:
            from src.memory.episode_store import Episode
            from datetime import datetime

            # Create a temporary episode for similarity matching
            temp_episode = Episode(
                episode_id="temp",
                incident_id=incident_context.get("incident_id", "temp"),
                title=incident_context.get("title", ""),
                description=incident_context.get("description", ""),
                severity=incident_context.get("severity", "medium"),
                category=incident_context.get("category", "unknown"),
                detected_at=datetime.utcnow(),
                affected_services=incident_context.get("affected_services", []),
            )

            # Find similar episodes
            similar_episodes = await self.episode_store.find_similar_episodes(
                episode=temp_episode,
                limit=5,
                min_similarity=0.3,
            )

            if not similar_episodes:
                return self.DEFAULT_SIMILARITY, 0

            # Weight by similarity and resolution success
            total_weight = 0.0
            weighted_score = 0.0

            for episode, similarity in similar_episodes:
                weight = similarity
                total_weight += weight

                # Boost score for successfully resolved episodes
                if episode.outcome == "resolved":
                    weighted_score += weight * 1.0
                elif episode.outcome == "escalated":
                    weighted_score += weight * 0.5
                else:
                    weighted_score += weight * 0.3

            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = self.DEFAULT_SIMILARITY

            return final_score, len(similar_episodes)

        except Exception as e:
            logger.warning(f"Failed to get similarity score: {e}")
            return self.DEFAULT_SIMILARITY, 0

    @classmethod
    def get_weights(cls) -> dict[str, float]:
        """Get the confidence formula weights."""
        return {
            "alpha": cls.ALPHA,
            "beta": cls.BETA,
            "gamma": cls.GAMMA,
        }

    @classmethod
    def get_formula_description(cls) -> str:
        """Get human-readable formula description."""
        return (
            f"C(a) = {cls.ALPHA}·C_LLM + {cls.BETA}·C_hist + {cls.GAMMA}·C_sim\n"
            f"Where:\n"
            f"  C_LLM  = LLM confidence (reasoning agent output)\n"
            f"  C_hist = Historical success rate for action type\n"
            f"  C_sim  = Similarity to past resolved incidents"
        )


__all__ = ["ConfidenceCalculator", "ConfidenceBreakdown"]
