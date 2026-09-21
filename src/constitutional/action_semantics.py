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

Scope note: this module deliberately covers **P1.1 and P1.4 only**, the two
principles that used substring matching. P1.2 and P1.3 use exact equality
(`action_type in [...]`), which has its own gap (`restart_service` never matches
`"restart"`, so the active-incident check does not fire). That is tracked
separately as ISS-110 and is intentionally NOT changed here.
"""

import re
from typing import FrozenSet

__all__ = [
    "action_tokens",
    "is_data_destructive",
    "modifies_security_config",
    "DATA_DESTRUCTIVE_VERBS",
    "SECURITY_NOUNS",
    "READ_ONLY_VERBS",
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
# configurations without explicit approval", so a noun alone is not enough:
# reading security state is not modifying it.
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


def is_data_destructive(action_type: str) -> bool:
    """True when the action name says it destroys durable data (P1.1)."""
    return bool(action_tokens(action_type) & DATA_DESTRUCTIVE_VERBS)


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
