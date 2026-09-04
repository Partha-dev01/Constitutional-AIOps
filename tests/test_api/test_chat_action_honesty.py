"""Constitutional AIOps - chat honesty guard tests.

The reasoning agent cannot execute operational actions; they only ever run
through the gated Approve/Reject proposal flow. These tests cover the
deterministic backstop that strips a false "I performed the action" claim from a
reply when no action was actually queued/executed, and replaces it with an
honest clarifier.

Pure-function tests (no Request / FastAPI DI), matching the direct-call style
used across the chat test suite.
"""

import pytest

from src.api.routes.chat import (
    _contains_action_claim,
    _honest_action_clarifier,
    _scrub_unbacked_action_claims,
)

# The live specimen that motivated the fix (verified on the box, s92): the model
# said this after "Restart the Caddy service." even though action tools are off.
_SPECIMEN = "Proceeding with the restart of the `aiops-caddy` container now."


# ---------------------------------------------------------------------------
# _contains_action_claim: TRUE for first-person / passive execution claims
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        _SPECIMEN,
        "I am restarting the nextcloud container now.",
        "I'm restarting it now.",
        "I've restarted the aiops-backend container.",
        "I have restarted the service.",
        "I just restarted nextcloud-db.",
        "I will restart the container now.",
        "I stopped the service to clear the fault.",
        "I've scaled the backend to 3 replicas.",
        "Going ahead with the restart of aiops-caddy.",
        "I went ahead and restarted it.",
        "The restart has been initiated.",
        "The action was executed successfully.",
    ],
)
def test_contains_action_claim_true(text):
    assert _contains_action_claim(text) is True


# ---------------------------------------------------------------------------
# _contains_action_claim: FALSE for recommendations / neutral prose
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "I recommend restarting the aiops-caddy container to clear the fault.",
        "I suggest you restart the service.",
        "You can restart it with `docker restart aiops-caddy`.",
        "You should restart the container if the pool stays stuck.",
        "Restarting the container would clear the stuck connection pool.",
        "A restart is the usual fix for this symptom.",
        "The container is running and healthy; no restart is needed.",
        "I would restart it, but I cannot run actions myself.",
        "aiops-caddy is up and serving requests normally.",
    ],
)
def test_contains_action_claim_false(text):
    assert _contains_action_claim(text) is False


# ---------------------------------------------------------------------------
# _scrub_unbacked_action_claims
# ---------------------------------------------------------------------------
def test_scrub_replaces_bare_claim_with_clarifier():
    new_content, corrected = _scrub_unbacked_action_claims(
        _SPECIMEN, tools_enabled=False, mode="diagnose"
    )
    assert corrected is True
    assert "Proceeding with the restart" not in new_content
    assert "can't run that action myself" in new_content
    # tools off wins the reason clause
    assert "turned off on this deployment" in new_content


def test_scrub_preserves_preceding_analysis():
    content = (
        "The connection pool for nextcloud-db is exhausted, which is causing the "
        "502s. Proceeding with the restart of the nextcloud-db container now."
    )
    new_content, corrected = _scrub_unbacked_action_claims(
        content, tools_enabled=True, mode="approve"
    )
    assert corrected is True
    # The real analysis survives; only the false claim is removed.
    assert "connection pool for nextcloud-db is exhausted" in new_content
    assert "Proceeding with the restart" not in new_content
    assert "Approve or Reject" in new_content


def test_scrub_noop_when_no_claim():
    content = "I recommend restarting aiops-caddy; a human needs to approve it."
    new_content, corrected = _scrub_unbacked_action_claims(
        content, tools_enabled=False, mode="diagnose"
    )
    assert corrected is False
    assert new_content == content


def test_clarifier_mentions_diagnose_when_tools_enabled_but_diagnose():
    text = _honest_action_clarifier(tools_enabled=True, mode="diagnose")
    assert "diagnose" in text.lower()


def test_clarifier_base_when_enabled_and_active():
    text = _honest_action_clarifier(tools_enabled=True, mode="approve")
    assert "Approve or Reject" in text
    assert "turned off" not in text
