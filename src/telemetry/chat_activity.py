"""Chat-priority interlock shared between the API layer and background jobs.

The chat endpoints mark a reasoning turn in flight; the background processor
consults the marker and defers its own reasoning-engine (14B) sweeps so
interactive turns don't contend with routine analysis for GPU decode. All
callers run on the same asyncio event loop, so plain module state suffices.
"""

import asyncio
import time

_active_turns = 0
_last_turn_finished = 0.0


def chat_turn_started() -> None:
    """Mark one interactive chat turn as holding the reasoning engine."""
    global _active_turns
    _active_turns += 1


def chat_turn_finished() -> None:
    """Release one turn (floored at zero so a double release can't wedge)."""
    global _active_turns, _last_turn_finished
    _active_turns = max(0, _active_turns - 1)
    _last_turn_finished = time.monotonic()


def chat_turn_active(grace_seconds: float = 0.0) -> bool:
    """True while a turn is in flight, or within ``grace_seconds`` of the last.

    The grace window treats a user mid-conversation (turn just ended, next
    message likely coming) as still active, so periodic background reasoning
    doesn't start a long GPU call between their messages.
    """
    if _active_turns > 0:
        return True
    return (
        grace_seconds > 0
        and (time.monotonic() - _last_turn_finished) < grace_seconds
    )


async def wait_for_chat_idle(max_wait_seconds: float) -> float:
    """Wait (bounded) for interactive chat to go idle; return seconds waited.

    Bounded so a wedged marker can never starve the caller forever.
    """
    if not chat_turn_active():
        return 0.0
    start = time.monotonic()
    while chat_turn_active() and (time.monotonic() - start) < max_wait_seconds:
        await asyncio.sleep(1.0)
    return time.monotonic() - start
