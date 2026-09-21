"""Tier-1 action classification (H1): token matching, not substring matching.

A Tier-1 violation BLOCKS outright and `human_approved` is never consulted for
it, so a misclassification here is not a nuisance prompt, it is either a safe
action that can never run or a destructive one that runs unchallenged. These
tests pin both directions.
"""

import pytest

from src.constitutional.action_semantics import (
    action_tokens,
    is_data_destructive,
    modifies_security_config,
)
from src.constitutional.validator import ConstitutionalValidator
from src.tools.registry import TOOLS


# --------------------------------------------------------------------------
# tokenisation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name,expected",
    [
        ("restart_service", {"restart", "service"}),
        ("restart-service", {"restart", "service"}),
        ("Restart Service", {"restart", "service"}),
        ("deleteTable", {"delete", "table"}),
        ("analyze_oracle_logs", {"analyze", "oracle", "logs"}),
        ("", set()),
    ],
)
def test_tokenisation(name, expected):
    assert action_tokens(name) == frozenset(expected)


def test_camel_and_snake_classify_identically():
    """A plugin author's naming convention must not change the safety verdict."""
    assert is_data_destructive("deleteTable") == is_data_destructive("delete_table")
    assert modifies_security_config("updateFirewall") == modifies_security_config(
        "update_firewall"
    )


# --------------------------------------------------------------------------
# P1.1, data protection
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name",
    ["delete_table", "drop_index", "truncate_logs", "remove_node",
     "purge_index", "wipe_volume", "destroy_cluster", "erase_disk",
     "prune_images", "shred_backups", "decommission_node", "format_disk"],
)
def test_destructive_actions_are_caught(name):
    assert is_data_destructive(name) is True


@pytest.mark.parametrize(
    "name",
    ["undelete_row", "restore_snapshot", "analyze_oracle_logs",
     "list_containers", "query_metric", "get_dependencies"],
)
def test_safe_actions_are_not_flagged_as_destructive(name):
    assert is_data_destructive(name) is False


def test_undelete_is_not_data_loss():
    """The substring bug: 'delete' is inside 'undelete', so a restore was blocked."""
    assert is_data_destructive("undelete") is False
    assert is_data_destructive("delete") is True


@pytest.mark.parametrize("name", ["clear_cache", "flush_dns", "evict_key",
                                  "invalidate_cdn", "reset_connection"])
def test_cache_verbs_are_deliberately_not_destructive(name):
    """Tier 1 has no approval path, so routine cache work must not be blocked.

    If this starts failing because someone widened DATA_DESTRUCTIVE_VERBS, read
    the exclusion note in action_semantics before changing the test.
    """
    assert is_data_destructive(name) is False


# --------------------------------------------------------------------------
# P1.4, security integrity
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name",
    ["firewall_update", "update_iam_policy", "rotate_credentials",
     "set_acl", "disable_tls", "grant_role", "delete_secret"],
)
def test_security_modifications_are_caught(name):
    assert modifies_security_config(name) is True


@pytest.mark.parametrize(
    "name",
    ["query_firewall_rules", "get_certificate_expiry", "list_acl",
     "check_tls_expiry", "audit_permissions", "describe_iam_role"],
)
def test_reading_security_state_is_not_a_modification(name):
    """P1.4 says 'never MODIFY security configurations'. A read is not a change."""
    assert modifies_security_config(name) is False


def test_oracle_does_not_match_acl():
    """The substring bug: 'acl' is inside 'oracle', so log analysis was blocked."""
    assert modifies_security_config("analyze_oracle_logs") is False


def test_unknown_verb_on_security_noun_fails_closed():
    """An unrecognised verb touching security config is treated as a change."""
    assert modifies_security_config("firewall_yolo") is True


# --------------------------------------------------------------------------
# end to end through the validator, and no regression on the real tools
# --------------------------------------------------------------------------

def _validate(action_type: str):
    return ConstitutionalValidator().validate(
        action_id="t1",
        action_description=action_type,
        action_type=action_type,
        confidence=0.95,
        context={},
    )


def test_destructive_action_is_blocked_end_to_end():
    report = _validate("purge_index")
    assert report.tier1_passed is False
    assert report.can_proceed is False
    assert any(v.principle.id == "P1.1" for v in report.violations)


def test_oracle_log_analysis_is_no_longer_blocked_end_to_end():
    report = _validate("analyze_oracle_logs")
    assert report.tier1_passed is True
    assert not any(v.principle.id in ("P1.1", "P1.4") for v in report.violations)


def test_tier1_block_is_not_overridable_by_human_approval():
    """Guard the property the whole gate rests on."""
    report = ConstitutionalValidator().validate(
        action_id="t2",
        action_description="purge",
        action_type="purge_index",
        confidence=0.99,
        context={"human_approved": True},
    )
    assert report.tier1_passed is False
    assert report.can_proceed is False


def test_no_registered_tool_is_blocked_by_tier1():
    """The shipped tool set must remain runnable. Catches an over-wide verb list."""
    for tool in TOOLS:
        report = _validate(tool.name)
        assert report.tier1_passed is True, (
            f"registered tool {tool.name!r} is blocked at Tier 1: "
            f"{[v.principle.id for v in report.violations]}"
        )


def test_no_registered_tool_is_blocked_during_an_approved_remediation():
    """The same pin under the context a real remediation actually carries.

    The previous test validates against an empty context, so it cannot see an
    over-wide P1.2 or P1.3 vocabulary. A live remediation runs with an active
    incident, an operator approval and real resource pressure, which is exactly
    where those two principles evaluate.
    """
    context = {
        "active_incident": True,
        "human_approved": True,
        "telemetry_evidence": True,
        "audit_enabled": True,
        "action_scope": "single",
        "resource_usage": 95,
    }
    for tool in TOOLS:
        report = ConstitutionalValidator().validate(
            action_id="t3",
            action_description=tool.name,
            action_type=tool.name,
            confidence=0.95,
            context=context,
        )
        assert report.tier1_passed is True, (
            f"registered tool {tool.name!r} is blocked at Tier 1 during an "
            f"approved remediation: {[v.principle.id for v in report.violations]}"
        )


# --------------------------------------------------------------------------
# ISS-110: P1.2 and P1.3 matched action names EXACTLY
#
# `action_type in ["restart", ...]` never matches the names the system actually
# uses. Every ActionType value is a compound (`restart_service`, `kill_process`,
# `rollback`), and so is every registered tool name, so the two principles were
# inert for all of them. `scale_down` and `scale_up` happened to match literally,
# which is why the gap stayed invisible: the checks looked alive.
# --------------------------------------------------------------------------

def _p12(action_type: str, **ctx):
    context = {"active_incident": True}
    context.update(ctx)
    return ConstitutionalValidator().validate(
        action_id="p12",
        action_description=action_type,
        action_type=action_type,
        confidence=0.95,
        context=context,
    )


@pytest.mark.parametrize(
    "action_type",
    [
        "restart_service",   # the ActionType value AND the registered tool name
        "restart",           # still matches, the old literal
        "kill_process",
        "rollback",
        "block_ip",
        "scale_down",
        "stop_container",
        "terminate_worker",
        "drain_node",
        "redeploy_api",
        "failover_database",
    ],
)
def test_unapproved_disruptive_action_during_incident_violates_p12(action_type):
    """P1.2 is 'never take destructive actions during active incidents without
    explicit approval'. Before ISS-110 only the bare literals fired."""
    report = _p12(action_type)
    assert report.tier1_passed is False, f"{action_type} did not trigger P1.2"
    assert any(v.principle.id == "P1.2" for v in report.violations)


@pytest.mark.parametrize(
    "action_type",
    [
        "analyze_logs",
        "query_recent_logs",
        "list_containers",
        "get_dependencies",
        "find_similar",
        "query_metric",
        "scale_service",       # direction unknown from the name alone
        "describe_deployment",  # reads a deployment, does not perform one
    ],
)
def test_non_disruptive_action_during_incident_passes_p12(action_type):
    """Reading during an incident is how an incident gets diagnosed. A false
    positive here blocks exactly the tools an operator needs mid-incident."""
    report = _p12(action_type)
    assert report.tier1_passed is True, (
        f"{action_type} was blocked during an incident: "
        f"{[v.principle.id for v in report.violations]}"
    )


def test_approval_still_clears_p12_after_the_widening():
    """The principle's own remedy must keep working for the newly matched names."""
    report = _p12("restart_service", human_approved=True, telemetry_evidence=True,
                  audit_enabled=True, action_scope="single")
    assert report.tier1_passed is True
    assert report.can_proceed is True


@pytest.mark.parametrize(
    "action_type,blocked",
    [
        ("scale_up", True),
        ("spawn_worker", True),
        ("fork_process", True),
        ("provision_replica", True),
        ("replicate_shard", True),
        ("scale_service", False),   # could be scaling DOWN, the name cannot say
        ("scale_down", False),      # relieves pressure, never amplifies it
        ("analyze_logs", False),
        ("deprovision_node", False),  # must not collide with "provision"
    ],
)
def test_p13_resource_amplification(action_type, blocked):
    """P1.3 blocks amplifying an already exhausted system. It has NO approval
    route, so the vocabulary stays narrow and direction-aware."""
    report = ConstitutionalValidator().validate(
        action_id="p13",
        action_description=action_type,
        action_type=action_type,
        confidence=0.95,
        context={"resource_usage": 95},
    )
    violated = any(v.principle.id == "P1.3" for v in report.violations)
    assert violated is blocked, f"{action_type}: P1.3 violated={violated}, expected {blocked}"


def test_p13_does_not_fire_below_the_threshold():
    report = ConstitutionalValidator().validate(
        action_id="p13-low",
        action_description="scale_up",
        action_type="scale_up",
        confidence=0.95,
        context={"resource_usage": 40},
    )
    assert not any(v.principle.id == "P1.3" for v in report.violations)
