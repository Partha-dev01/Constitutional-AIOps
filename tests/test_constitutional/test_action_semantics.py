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
