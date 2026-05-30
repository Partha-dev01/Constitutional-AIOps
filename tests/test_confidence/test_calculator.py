"""Tests for the composite confidence calculator.

C(a) = alpha*C_LLM + beta*C_hist + gamma*C_sim   (alpha=.40, beta=.35, gamma=.25)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.confidence.calculator import ConfidenceBreakdown, ConfidenceCalculator

# --- weights / formula metadata ------------------------------------------

def test_weights_sum_to_one():
    w = ConfidenceCalculator.get_weights()
    assert w == {"alpha": 0.40, "beta": 0.35, "gamma": 0.25}
    assert pytest.approx(sum(w.values())) == 1.0


def test_formula_description_mentions_components():
    desc = ConfidenceCalculator.get_formula_description()
    assert "C_LLM" in desc and "C_hist" in desc and "C_sim" in desc


# --- calculate_composite (no stores -> neutral defaults) ------------------

@pytest.mark.asyncio
async def test_composite_with_no_stores_uses_defaults():
    calc = ConfidenceCalculator()
    composite, breakdown = await calc.calculate_composite(0.8, "restart_service")

    # 0.40*0.8 + 0.35*0.5 + 0.25*0.5 = 0.32 + 0.175 + 0.125 = 0.62
    assert composite == pytest.approx(0.62)
    assert isinstance(breakdown, ConfidenceBreakdown)
    assert breakdown.c_llm == 0.8
    assert breakdown.c_hist == ConfidenceCalculator.DEFAULT_HISTORICAL
    assert breakdown.c_sim == ConfidenceCalculator.DEFAULT_SIMILARITY
    assert breakdown.historical_data_available is False
    assert breakdown.similar_episodes_found == 0
    assert breakdown.fallback_used is True


@pytest.mark.asyncio
async def test_llm_confidence_is_clamped():
    calc = ConfidenceCalculator()

    _, hi = await calc.calculate_composite(1.5, "scale_up")
    assert hi.c_llm == 1.0

    _, lo = await calc.calculate_composite(-0.3, "scale_up")
    assert lo.c_llm == 0.0


@pytest.mark.asyncio
async def test_composite_is_clamped_to_unit_interval():
    calc = ConfidenceCalculator()
    composite, _ = await calc.calculate_composite(1.0, "restart_service")
    assert 0.0 <= composite <= 1.0


# --- historical success rate ---------------------------------------------

@pytest.mark.asyncio
async def test_historical_rate_from_neo4j():
    neo4j = MagicMock()
    neo4j.get_action_success_rate = AsyncMock(return_value=0.9)
    calc = ConfidenceCalculator(neo4j_client=neo4j)

    rate, available = await calc._get_historical_success_rate("restart_service")
    assert rate == 0.9
    assert available is True
    neo4j.get_action_success_rate.assert_awaited_once()


@pytest.mark.asyncio
async def test_historical_rate_zero_falls_back_to_default():
    neo4j = MagicMock()
    neo4j.get_action_success_rate = AsyncMock(return_value=0.0)
    calc = ConfidenceCalculator(neo4j_client=neo4j)

    rate, available = await calc._get_historical_success_rate("restart_service")
    assert rate == ConfidenceCalculator.DEFAULT_HISTORICAL
    assert available is False


@pytest.mark.asyncio
async def test_historical_rate_handles_exception():
    neo4j = MagicMock()
    neo4j.get_action_success_rate = AsyncMock(side_effect=RuntimeError("db down"))
    calc = ConfidenceCalculator(neo4j_client=neo4j)

    rate, available = await calc._get_historical_success_rate("restart_service")
    assert rate == ConfidenceCalculator.DEFAULT_HISTORICAL
    assert available is False


# --- similarity score -----------------------------------------------------

@pytest.mark.asyncio
async def test_similarity_weights_resolved_episodes_highest():
    resolved = MagicMock()
    resolved.outcome = "resolved"
    store = MagicMock()
    store.find_similar_episodes = AsyncMock(return_value=[(resolved, 0.8)])
    calc = ConfidenceCalculator(episode_store=store)

    score, count = await calc._get_similarity_score({"title": "db timeout"})
    # single resolved episode: weighted_score/total = (0.8*1.0)/0.8 = 1.0
    assert score == pytest.approx(1.0)
    assert count == 1


@pytest.mark.asyncio
async def test_similarity_outcome_tiers():
    escalated = MagicMock()
    escalated.outcome = "escalated"
    store = MagicMock()
    store.find_similar_episodes = AsyncMock(return_value=[(escalated, 1.0)])
    calc = ConfidenceCalculator(episode_store=store)

    score, count = await calc._get_similarity_score({"title": "x"})
    # escalated -> 0.5 multiplier: (1.0*0.5)/1.0 = 0.5
    assert score == pytest.approx(0.5)
    assert count == 1


@pytest.mark.asyncio
async def test_similarity_no_episodes_uses_default():
    store = MagicMock()
    store.find_similar_episodes = AsyncMock(return_value=[])
    calc = ConfidenceCalculator(episode_store=store)

    score, count = await calc._get_similarity_score({"title": "x"})
    assert score == ConfidenceCalculator.DEFAULT_SIMILARITY
    assert count == 0


@pytest.mark.asyncio
async def test_similarity_no_context_uses_default():
    store = MagicMock()
    calc = ConfidenceCalculator(episode_store=store)
    score, count = await calc._get_similarity_score(None)
    assert score == ConfidenceCalculator.DEFAULT_SIMILARITY
    assert count == 0


# --- breakdown serialization ---------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_to_dict_shape():
    calc = ConfidenceCalculator()
    _, breakdown = await calc.calculate_composite(0.7, "restart_service")
    d = breakdown.to_dict()

    assert set(d.keys()) == {"composite_confidence", "components", "weights", "metadata"}
    assert set(d["components"].keys()) == {"c_llm", "c_hist", "c_sim"}
    assert d["weights"] == {"alpha": 0.40, "beta": 0.35, "gamma": 0.25}
    assert d["metadata"]["fallback_used"] is True
