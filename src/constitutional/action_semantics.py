"""How an action name is classified for the Tier-1 safety principles.

The principles used to do their own string matching, inline and inconsistently:
P1.1 and P1.4 asked `if any(word in action_type.lower() ...)`, a **substring**
test. Two things follow from that, and both are wrong:

* **False positives that hard-block safe reads.** A Tier-1 violation is not an
  approval prompt, it blocks the action outright (see `ConstitutionalValidator.validate`:
  `tier1_passed = False` sets `can_proceed = False` and `human_approved` is never
  consulted). So a collision is not cosmetic. `"acl"` is a substring of
  `"oracle"`, which means a read-only `analyze_oracle_logs` was classified as a
  security configuration change and blocked. `"delete"` is a substring of
  `"undelete"`, so a restore was classified as data loss.
* **False negatives.** The vocabulary was four English words per principle.
  Anything phrased differently, `purge_index` or `wipe_volume`, passed P1.1
  untouched.

Matching on **tokens** fixes both directions at once: `analyze_oracle_logs`
tokenises to `{analyze, oracle, logs}`, which does not contain `acl`, while
`purge_index` tokenises to `{purge, index}`, which does contain a destructive
verb.

**ISS-112 (2026-09-21) brought P1.2 and P1.3 in too.** They matched action names
by exact equality, `action_type in ["restart", "deploy", "scale_down"]`, and
nothing in the system is named that way: every `ActionType` value is a compound
(`restart_service`, `kill_process`, `rollback`) and so is every registered tool
name. `scale_down` and `scale_up` happened to match the literals, which is
precisely why the gap stayed invisible, the checks looked alive. In practice an
unapproved `restart_service` during an active incident passed P1.2 untouched.

The two principles are NOT symmetric and the vocabularies reflect that:

* **P1.2 has an approval route** ("without explicit approval" is in the
  principle text, and the validator implements it), so a slightly generous
  disruptive vocabulary costs an approval prompt, not an outright block.
* **P1.3 has none.** Amplifying an exhausted system is blocked with no appeal,
  the same shape as P1.1, so its vocabulary stays narrow and direction-aware.

Known limit, stated rather than hidden: classification reads the NAME only. A
`scale_service` call is not classified either way because the name cannot say
which direction it scales; the replica count lives in the parameters. Widening
the gate to parameters is a larger change than ISS-112 and is deliberately not
attempted here.
"""

import re
from typing import FrozenSet

__all__ = [
    "action_tokens",
    "is_data_destructive",
    "modifies_security_config",
    "is_service_disruptive",
    "is_resource_amplifying",
    "DATA_DESTRUCTIVE_VERBS",
    "SECURITY_NOUNS",
    "READ_ONLY_VERBS",
    "SERVICE_DISRUPTIVE_VERBS",
    "RESOURCE_AMPLIFYING_VERBS",
]

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def action_tokens(action_type: str) -> FrozenSet[str]:
    """Split an action name into lowercase word tokens.

    Handles the shapes action names actually arrive in: `restart_service`,
    `restart-service`, `restart.service`, `Restart Service`. camelCase is split
    too, so `deleteTable` and `delete_table` classify the same way rather than
    depending on which convention a plugin author used.
    """
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", action_type or "")
    return frozenset(t for t in _TOKEN_SPLIT.split(spaced.lower()) if t)


# Verbs that destroy durable data. P1.1 is "Never execute actions that could
# cause data loss or corruption", and a match here BLOCKS with no approval path,
# so this list is for unambiguous destruction only.
DATA_DESTRUCTIVE_VERBS: FrozenSet[str] = frozenset({
    # the original four
    "delete", "drop", "truncate", "remove",
    # synonyms that were missed entirely and are just as final
    "purge", "wipe", "destroy", "erase", "prune", "obliterate",
    "rm", "rmdir", "unlink", "shred",
    "deprovision", "decommission", "teardown",
    "format", "reformat", "reinitialize",
})

# DELIBERATELY EXCLUDED from DATA_DESTRUCTIVE_VERBS, do not add without reading
# this. These read as destructive in English but name routine, recoverable cache
# and session operations (`clear_cache`, `flush_dns`, `invalidate_cdn`,
# `evict_key`, `reset_connection`). Tier 1 is a hard block with no approval
# route, so including them would make ordinary remediation impossible rather
# than merely gated. If one of these ever names a genuinely destructive tool,
# the right fix is to rename the tool, not to widen this set.
_EXCLUDED_AMBIGUOUS_VERBS: FrozenSet[str] = frozenset({
    "clear", "flush", "evict", "invalidate", "reset", "expire", "rotate",
})

# Nouns that denote security configuration. P1.4 is "Never MODIFY security
# configurations", so a noun alone is not enough: reading security state is
# not modifying it. P1.4 has no approval route (ISS-113), the same shape as
# P1.1 and P1.3.
SECURITY_NOUNS: FrozenSet[str] = frozenset({
    "firewall", "auth", "authn", "authz", "tls", "ssl", "certificate", "cert",
    "acl", "iam", "policy", "permission", "permissions", "role", "roles",
    "credential", "credentials", "secret", "secrets", "token", "tokens",
    "key", "keys", "password", "passwords", "sudo", "privilege", "privileges",
    "securitygroup", "sg", "rbac",
})

# Verbs that only observe. Used as the exemption for P1.4: anything that is not
# clearly a read is treated as a modification when it touches a security noun.
# That direction is deliberate. A new or unrecognised verb against security
# configuration should be gated, not waved through, so the default is closed.
READ_ONLY_VERBS: FrozenSet[str] = frozenset({
    "get", "list", "query", "read", "describe", "show", "fetch", "view",
    "check", "inspect", "analyze", "analyse", "find", "search", "count",
    "audit", "report", "status", "summarize", "summarise", "diff", "validate",
    "verify", "test", "scan", "monitor", "watch", "trace", "explain",
})


# Verbs that interrupt a RUNNING service, as opposed to destroying its data.
# P1.2 reaches these only during an active incident and only when nobody has
# approved, and approval clears it, so the bar is "would an operator want to be
# asked mid-incident", not "is this irreversible".
SERVICE_DISRUPTIVE_VERBS: FrozenSet[str] = frozenset({
    # the original literals
    "restart", "deploy",
    # stopping or removing capacity
    "reboot", "stop", "halt", "kill", "terminate", "shutdown",
    "drain", "cordon", "detach", "unmount", "disable", "disconnect",
    # replacing what is running
    "redeploy", "rollback", "revert", "failover", "migrate", "evacuate",
    # cutting something off
    "block", "quarantine", "isolate", "blackhole",
})

# Verbs that ADD load or capacity. P1.3 blocks these outright when the system is
# already past its resource ceiling, with no approval route, so this set stays
# small and every member is unambiguous about direction.
RESOURCE_AMPLIFYING_VERBS: FrozenSet[str] = frozenset({
    "spawn", "fork", "provision", "replicate", "clone", "duplicate", "expand",
})


def is_data_destructive(action_type: str) -> bool:
    """True when the action name says it destroys durable data (P1.1)."""
    return bool(action_tokens(action_type) & DATA_DESTRUCTIVE_VERBS)


def is_service_disruptive(action_type: str) -> bool:
    """True when the action interrupts a running service (P1.2).

    Anything that destroys data is disruptive too, so P1.1's vocabulary is
    included rather than duplicated. `scale_down` is matched as the PAIR
    {scale, down}: a bare `scale` says nothing about direction, so
    `scale_service` is deliberately not classified here.
    """
    tokens = action_tokens(action_type)
    if tokens & SERVICE_DISRUPTIVE_VERBS or tokens & DATA_DESTRUCTIVE_VERBS:
        return True
    return {"scale", "down"} <= tokens


def is_resource_amplifying(action_type: str) -> bool:
    """True when the action would add load to an already exhausted system (P1.3).

    Same pair rule in the other direction: {scale, up} matches, a bare `scale`
    does not. `deprovision` is a single token and so cannot collide with
    `provision`.
    """
    tokens = action_tokens(action_type)
    if tokens & RESOURCE_AMPLIFYING_VERBS:
        return True
    return {"scale", "up"} <= tokens


def modifies_security_config(action_type: str) -> bool:
    """True when the action appears to CHANGE security configuration (P1.4).

    Requires a security noun AND the absence of a read-only verb. So
    `query_firewall_rules` and `get_certificate_expiry` are reads and pass,
    while `firewall_update`, `rotate_credentials` and an unrecognised
    `firewall_yolo` are all treated as modifications.
    """
    tokens = action_tokens(action_type)
    if not (tokens & SECURITY_NOUNS):
        return False
    return not (tokens & READ_ONLY_VERBS)
