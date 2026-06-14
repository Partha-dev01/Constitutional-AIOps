"""Tests for the genuine composite confidence module (src.agents.confidence).

Covers the documented formula C = 0.4*C_LLM + 0.35*C_hist + 0.25*C_sim,
weight renormalization with missing components, all-None -> None, clamping,
and the historical_success_rate / similarity_confidence helpers.
"""

import math

import pytest

from src.agents.confidence import (
    W_HIST,
    W_LLM,
    W_SIM,
    compute_confidence,
    historical_success_rate,
    similarity_confidence,
)


def _approx(a, b, tol=1e-9):
    return a is not None and b is not None and math.isclose(a, b, abs_tol=tol)


class TestComputeConfidence:
    def test_all_three_present_uses_full_weighted_sum(self):
        # 0.4*0.9 + 0.35*0.8 + 0.25*0.6 = 0.36 + 0.28 + 0.15 = 0.79
        result = compute_confidence(0.9, 0.8, 0.6)
        assert _approx(result, 0.79)

    def test_weights_sum_to_one(self):
        assert _approx(W_LLM + W_HIST + W_SIM, 1.0)

    def test_all_none_returns_none(self):
        assert compute_confidence(None, None, None) is None

    def test_single_component_returns_that_component(self):
        # Only LLM present -> renormalized weight is 1.0 -> returns 0.83.
        assert _approx(compute_confidence(0.83, None, None), 0.83)
        # Only historical present.
        assert _approx(compute_confidence(None, 0.42, None), 0.42)
        # Only similarity present.
        assert _approx(compute_confidence(None, None, 0.71), 0.71)

    def test_two_components_renormalize(self):
        # LLM + hist present: weights 0.40 and 0.35 renormalized over 0.75.
        # (0.40*1.0 + 0.35*0.0) / 0.75 = 0.5333...
        result = compute_confidence(1.0, 0.0, None)
        assert _approx(result, 0.40 / 0.75)

        # LLM + sim present: (0.40*0.8 + 0.25*0.4) / 0.65
        result2 = compute_confidence(0.8, None, 0.4)
        expected2 = (0.40 * 0.8 + 0.25 * 0.4) / (0.40 + 0.25)
        assert _approx(result2, expected2)

    def test_renormalization_keeps_value_in_range_for_equal_components(self):
        # If every present component equals v, the renormalized result is v
        # regardless of which subset is present.
        for combo in [
            (0.7, 0.7, 0.7),
            (0.7, 0.7, None),
            (0.7, None, 0.7),
            (None, 0.7, 0.7),
            (0.7, None, None),
        ]:
            assert _approx(compute_confidence(*combo), 0.7)

    def test_clamps_out_of_range_inputs(self):
        # Inputs above 1 / below 0 are clamped per-component before weighting.
        # LLM=1.5->1.0, hist=-0.2->0.0, sim=0.5 :
        # (0.4*1.0 + 0.35*0.0 + 0.25*0.5) = 0.525
        result = compute_confidence(1.5, -0.2, 0.5)
        assert _approx(result, 0.525)
        assert 0.0 <= result <= 1.0

    def test_result_always_in_unit_interval(self):
        assert compute_confidence(1.0, 1.0, 1.0) == 1.0
        assert compute_confidence(0.0, 0.0, 0.0) == 0.0


class TestHistoricalSuccessRate:
    def test_empty_returns_none(self):
        assert historical_success_rate([]) is None
        assert historical_success_rate(None) is None  # type: ignore[arg-type]

    def test_fraction_of_successful_outcomes(self):
        episodes = [
            {"outcome": "resolved"},
            {"outcome": "failed"},
            {"status": "successful"},
            {"status": "open"},
        ]
        # 2 of 4 successful.
        assert _approx(historical_success_rate(episodes), 0.5)

    def test_all_success_is_one(self):
        episodes = [{"status": "resolved"}, {"outcome": "closed"}]
        assert _approx(historical_success_rate(episodes), 1.0)

    def test_boolean_outcome_supported(self):
        episodes = [{"outcome": True}, {"outcome": False}]
        assert _approx(historical_success_rate(episodes), 0.5)

    def test_missing_outcome_counts_as_failure(self):
        episodes = [{"foo": "bar"}, {"outcome": "resolved"}]
        assert _approx(historical_success_rate(episodes), 0.5)

    def test_object_attribute_outcome(self):
        class _Ep:
            def __init__(self, status):
                self.status = status

        episodes = [_Ep("resolved"), _Ep("failed")]
        assert _approx(historical_success_rate(episodes), 0.5)


class TestSimilarityConfidence:
    def test_empty_returns_none(self):
        assert similarity_confidence([]) is None
        assert similarity_confidence(None) is None  # type: ignore[arg-type]

    def test_uses_max_score(self):
        assert _approx(similarity_confidence([0.3, 0.91, 0.5]), 0.91)

    def test_drops_non_numeric_and_clamps(self):
        # "x"/None dropped; 1.4 clamped to 1.0.
        assert _approx(similarity_confidence([None, "x", 0.2, 1.4]), 1.0)

    def test_all_invalid_returns_none(self):
        assert similarity_confidence([None, "x", True]) is None


class TestIntegrationWithChatPath:
    def test_similarity_only_no_longer_bucketed(self):
        """The headline bug: a real similarity score must produce a value
        outside the old {0.5, 0.65, 0.7, 0.85} bucket set."""
        c_sim = similarity_confidence([0.83])
        result = compute_confidence(None, None, c_sim)
        assert result == 0.83
        assert result not in {0.5, 0.65, 0.7, 0.85}
