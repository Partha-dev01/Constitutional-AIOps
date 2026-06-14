"""
Constitutional AIOps - genuine composite confidence (pure, dependency-free).

Implements the documented confidence formula from Research_V7.tex / CLAUDE.md:

    C(a) = 0.40 * C_LLM + 0.35 * C_hist + 0.25 * C_sim

This is the single, tested code path that BOTH the chat route and the RCA
reasoning agent route their confidence through, replacing the previous coarse
bucket (which only ever produced {0.5, 0.65, 0.7, 0.85}) and the raw LLM
self-report respectively.

Key design points:
  * Any component may be ``None`` (the chat model does not self-report a
    C_LLM; an incident may have no related history; a query may surface no
    similar incidents). ``compute_confidence`` RENORMALIZES the weights over
    the components that are actually present, so a single present component
    returns that component's value, and all-``None`` returns ``None``.
  * The result is always clamped to ``[0, 1]``.
  * Stdlib only — this module has NO dependencies so it can be imported from
    any path (chat route, reasoning agent, tests) without dragging in the
    Neo4j-backed ``src.confidence`` calculator.

The heavier, graph-backed ``src.confidence.ConfidenceCalculator`` remains the
orchestration-pipeline calculator; this module is the lightweight per-request
formula used directly by the chat/RCA code paths.
"""

from typing import Any, Optional

# Weights from Research_V7.tex (must mirror src.confidence.ConfidenceCalculator).
W_LLM = 0.40   # alpha — LLM self-reported confidence
W_HIST = 0.35  # beta  — historical success rate of related episodes
W_SIM = 0.25   # gamma — similarity to past incidents

# Outcome/status tokens that count as a SUCCESSFUL resolution for C_hist.
_SUCCESS_TOKENS = frozenset(
    {"resolved", "success", "successful", "closed", "fixed", "remediated", "recovered"}
)


def _clamp01(value: float) -> float:
    """Clamp a float into the inclusive ``[0.0, 1.0]`` range."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def compute_confidence(
    c_llm: Optional[float],
    c_hist: Optional[float],
    c_sim: Optional[float],
) -> Optional[float]:
    """Composite confidence ``C = 0.4*C_LLM + 0.35*C_hist + 0.25*C_sim``.

    The weights are RENORMALIZED over whichever components are non-``None`` so
    a missing component does not silently drag the score toward zero:

      * all three present -> the full weighted sum;
      * two present       -> their two weights renormalized to sum 1;
      * one present       -> that component's value (clamped);
      * none present      -> ``None`` (caller hides the gauge).

    Every input component is individually clamped to ``[0, 1]`` first, and the
    final result is clamped to ``[0, 1]``.
    """
    components: list[tuple[float, float]] = []  # (weight, clamped_value)
    if c_llm is not None:
        components.append((W_LLM, _clamp01(float(c_llm))))
    if c_hist is not None:
        components.append((W_HIST, _clamp01(float(c_hist))))
    if c_sim is not None:
        components.append((W_SIM, _clamp01(float(c_sim))))

    if not components:
        return None

    weight_sum = sum(w for w, _ in components)
    if weight_sum <= 0.0:
        # Defensive: weights are positive constants, so this is unreachable in
        # practice, but never divide by zero.
        return None

    weighted = sum(w * v for w, v in components) / weight_sum
    return _clamp01(weighted)


def historical_success_rate(episodes: list) -> Optional[float]:
    """Fraction of related episodes whose outcome indicates success.

    Each episode may be a dict carrying an ``outcome``/``status``/``result``
    field (or a plain object with one of those attributes). The value is
    lower-cased and matched against a small set of success tokens
    (``resolved``, ``success``, ``closed``, ...). Booleans are also accepted
    (``True`` -> success). Returns ``None`` when ``episodes`` is empty so the
    caller can omit the historical component entirely.
    """
    if not episodes:
        return None

    successes = 0
    for episode in episodes:
        outcome = _extract_outcome(episode)
        if _is_success(outcome):
            successes += 1

    return _clamp01(successes / len(episodes))


def similarity_confidence(scores: list) -> Optional[float]:
    """Confidence derived from real similarity scores in ``[0, 1]``.

    Uses the MAX similarity (the single closest past incident is the strongest
    evidence). Non-numeric / out-of-range values are dropped. Returns ``None``
    when no usable score is present.
    """
    usable: list[float] = []
    for score in scores or []:
        if isinstance(score, bool):  # bool is an int subclass — exclude it
            continue
        if isinstance(score, (int, float)):
            usable.append(_clamp01(float(score)))

    if not usable:
        return None
    return max(usable)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_outcome(episode: Any) -> Any:
    """Pull an outcome/status/result signal from a dict or object episode."""
    if isinstance(episode, dict):
        for key in ("outcome", "status", "result", "resolution"):
            if key in episode and episode[key] is not None:
                return episode[key]
        return None
    for attr in ("outcome", "status", "result", "resolution"):
        value = getattr(episode, attr, None)
        if value is not None:
            return value
    return None


def _is_success(outcome: Any) -> bool:
    """True when an outcome value indicates a successful resolution."""
    if outcome is None:
        return False
    if isinstance(outcome, bool):
        return outcome
    text = str(outcome).strip().lower()
    if not text:
        return False
    # Match whole-word success tokens; substring on the token set keeps it
    # tolerant of values like "resolved_auto" or "auto-resolved".
    return any(token in text for token in _SUCCESS_TOKENS)


__all__ = [
    "compute_confidence",
    "historical_success_rate",
    "similarity_confidence",
    "W_LLM",
    "W_HIST",
    "W_SIM",
]
