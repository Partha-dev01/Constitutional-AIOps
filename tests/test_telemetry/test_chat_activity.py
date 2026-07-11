"""Constitutional AIOps - chat-priority interlock tests.

Pins the contract that keeps background 14B reasoning from contending with an
interactive chat turn on the shared GPU:

  * ``chat_activity`` marker semantics (in-flight count, grace window,
    floor-at-zero release, bounded idle wait);
  * the background processor SKIPS a due routine-reasoning sweep while a chat
    turn is active (counter left armed so it retries next cycle) and runs it
    once chat is idle;
  * an RCA escalation WAITS (bounded) for chat to go idle instead of skipping —
    escalations are event-driven and must not be lost.
"""

import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telemetry import background_processor as bp_module
from src.telemetry import chat_activity
from src.telemetry.background_processor import (
    ESCALATION_CHAT_WAIT_SECONDS,
    REASONING_INTERVAL_CYCLES,
    BackgroundTelemetryProcessor,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_chat_activity():
    """Module-level marker state must not leak between tests."""
    chat_activity._active_turns = 0
    chat_activity._last_turn_finished = 0.0
    yield
    chat_activity._active_turns = 0
    chat_activity._last_turn_finished = 0.0


def _make_processor() -> BackgroundTelemetryProcessor:
    processor = BackgroundTelemetryProcessor(
        fast_annotator=MagicMock(),
        reasoning_agent=MagicMock(),
        telemetry_collector=MagicMock(),
        episode_store=None,
        incident_graph=MagicMock(),
    )
    # Non-empty window so _process_cycle reaches Phase 5 (empty windows
    # early-return before the routine-reasoning check).
    window = SimpleNamespace(log_count=1, logs=[], metrics=[], traces=[])
    processor.telemetry_collector.collect_window = AsyncMock(return_value=window)
    processor._build_window_summary = MagicMock(return_value="summary")
    processor.incident_graph.ainvoke = AsyncMock(return_value={})
    processor._routine_reasoning_analysis = AsyncMock()
    return processor


# ---------------------------------------------------------------------------
# Marker semantics
# ---------------------------------------------------------------------------


def test_turn_marker_tracks_in_flight_turns() -> None:
    assert chat_activity.chat_turn_active() is False
    chat_activity.chat_turn_started()
    assert chat_activity.chat_turn_active() is True
    chat_activity.chat_turn_started()  # concurrent second turn
    chat_activity.chat_turn_finished()
    assert chat_activity.chat_turn_active() is True  # one still in flight
    chat_activity.chat_turn_finished()
    assert chat_activity.chat_turn_active() is False


def test_double_release_floors_at_zero() -> None:
    chat_activity.chat_turn_finished()
    chat_activity.chat_turn_finished()
    assert chat_activity._active_turns == 0
    chat_activity.chat_turn_started()
    assert chat_activity.chat_turn_active() is True


def test_grace_window_counts_recent_turn_as_active() -> None:
    chat_activity.chat_turn_started()
    chat_activity.chat_turn_finished()
    # Just finished: active within grace, idle without it.
    assert chat_activity.chat_turn_active() is False
    assert chat_activity.chat_turn_active(grace_seconds=60.0) is True
    # An old last-finish stamp is outside any reasonable grace.
    chat_activity._last_turn_finished = time.monotonic() - 3600.0
    assert chat_activity.chat_turn_active(grace_seconds=60.0) is False


@pytest.mark.asyncio
async def test_wait_for_chat_idle_is_immediate_when_idle_and_bounded_when_not() -> None:
    assert await chat_activity.wait_for_chat_idle(60.0) == 0.0
    chat_activity.chat_turn_started()
    start = time.monotonic()
    waited = await chat_activity.wait_for_chat_idle(0.0)  # bound hit instantly
    assert time.monotonic() - start < 1.0  # returned without a poll sleep
    assert waited >= 0.0
    assert chat_activity.chat_turn_active() is True  # wait is bounded, not blocking


# ---------------------------------------------------------------------------
# Routine reasoning defers to chat
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_due_routine_reasoning_skipped_while_chat_turn_active() -> None:
    processor = _make_processor()
    processor._fast_cycle_count = REASONING_INTERVAL_CYCLES  # sweep is due
    chat_activity.chat_turn_started()

    await processor._process_cycle()

    processor._routine_reasoning_analysis.assert_not_awaited()
    # Counter NOT reset: stays past the threshold so the next 30s cycle retries.
    assert processor._fast_cycle_count >= REASONING_INTERVAL_CYCLES


@pytest.mark.asyncio
async def test_due_routine_reasoning_runs_when_chat_idle() -> None:
    processor = _make_processor()
    processor._fast_cycle_count = REASONING_INTERVAL_CYCLES - 1  # due after +1

    await processor._process_cycle()

    processor._routine_reasoning_analysis.assert_awaited_once()
    assert processor._fast_cycle_count == 0


# ---------------------------------------------------------------------------
# Escalation waits (bounded) instead of skipping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalation_waits_for_chat_idle_then_runs_rca() -> None:
    processor = _make_processor()
    processor.reasoning_agent.analyze_rca = AsyncMock(
        return_value=SimpleNamespace(content="RCA: disk full", confidence=0.7)
    )
    annotation = SimpleNamespace(
        content="disk full on nextcloud",
        metadata={"severity": "warning", "category": "capacity"},
    )
    window = SimpleNamespace(log_count=3, logs=[], metrics=[], traces=[])

    wait_recorder = AsyncMock(return_value=0.0)
    with patch.object(bp_module, "wait_for_chat_idle", new=wait_recorder):
        await processor._escalate_to_reasoning(annotation, window)

    # The bounded wait ran BEFORE the 14B call, with the module's bound.
    wait_recorder.assert_awaited_once_with(ESCALATION_CHAT_WAIT_SECONDS)
    processor.reasoning_agent.analyze_rca.assert_awaited_once()
