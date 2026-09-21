"""Gate: the published safety docs must match the principles in code.

The 12-principle gate is the project's headline claim, and the published list
had drifted badly from `src/constitutional/principles.py`. Six of the twelve
were wrong, including three of the four Tier-1 safety-critical ones: P1.4 was
published as "All actions reversible within a short window" while the code said
"Never modify security configurations without explicit approval", and P1.2 was
published as "Maintain a minimum of healthy replicas" while the code says
"Never take destructive actions during active incidents without explicit
approval". Nothing compared the two, so nobody noticed.

The marketing site carried the same retired list on its landing page and its
Safety page, and neither was checked either. Both are held to the code here now,
as is `configs/constitutional-principles.yaml`, which had lost P3.4 entirely.

ISS-113: P1.4's text ended "without explicit approval" like P1.2's, but the gate
never offered P1.4 an approval route. The text was the thing that was wrong, so
it lost the clause, and a Tier-1 principle may now only name approval if it is
in APPROVAL_ROUTABLE_TIER1.
"""

import re
from pathlib import Path

import pytest
import yaml

from src.constitutional.principles import (
    ALL_PRINCIPLES,
    APPROVAL_ROUTABLE_TIER1,
    TIER_1_PRINCIPLES,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAFETY_PAGE = REPO_ROOT / "docs-site" / "guide" / "safety.md"
README = REPO_ROOT / "README.md"
PRINCIPLES_YAML = REPO_ROOT / "configs" / "constitutional-principles.yaml"
MARKETING_LISTS = [
    REPO_ROOT / "marketing" / "src" / "components" / "landing" / "ConstitutionSection.tsx",
    REPO_ROOT / "marketing" / "src" / "pages" / "Safety.tsx",
]
# Everything public that talks about the principles, checked for retired wording.
PUBLISHED_SURFACES = [
    SAFETY_PAGE,
    README,
    PRINCIPLES_YAML,
    *MARKETING_LISTS,
    REPO_ROOT / "marketing" / "src" / "pages" / "Faq.tsx",
    REPO_ROOT / "frontend" / "src" / "lib" / "demo" / "fixtures.ts",
]

# Phrasing from the old, wrong published list. If any of these come back, the
# docs have been reverted to text that describes principles the code does not
# implement.
RETIRED_CLAIMS = [
    "minimum of healthy replicas",
    "reversible within 60 seconds",
    "reversible within a short window",
    "check historical precedent",
    "Pattern reinforcement",
    "Failure analysis",
    "healthy replicas",
    "reversible within 60s",
    "more than five services",
    "reinforce patterns that worked",
    "analyze failures systematically",
    "analyze every failure systematically",
    "graceful degradation over shutdown",
    "degrade gracefully rather than shut down",
]


@pytest.mark.parametrize("principle", ALL_PRINCIPLES, ids=lambda p: p.id)
def test_safety_page_states_each_principle_verbatim(principle) -> None:
    page = SAFETY_PAGE.read_text(encoding="utf-8")
    expected = f"- **{principle.id} {principle.name}.** {principle.description}."
    assert expected in page, (
        f"{principle.id} is missing or reworded on the published safety page.\n"
        f"expected: {expected}"
    )


def test_safety_page_lists_exactly_twelve_principles() -> None:
    """An extra or dropped bullet means the page and the code disagree on count."""
    page = SAFETY_PAGE.read_text(encoding="utf-8")
    found = sum(1 for p in ALL_PRINCIPLES if f"**{p.id} " in page)
    assert found == len(ALL_PRINCIPLES) == 12, f"{found} of 12 principles on the page"


@pytest.mark.parametrize("claim", RETIRED_CLAIMS)
def test_retired_principle_wording_is_gone(claim: str) -> None:
    for path in PUBLISHED_SURFACES:
        assert claim.lower() not in path.read_text(encoding="utf-8").lower(), (
            f"{path.name} still carries the retired claim {claim!r}, which "
            "describes a principle the code does not implement"
        )


@pytest.mark.parametrize("path", MARKETING_LISTS, ids=lambda p: p.name)
def test_marketing_lists_state_each_principle_verbatim(path: Path) -> None:
    """The landing page and the Safety page each list all twelve, word for word."""
    listed = re.findall(r"^\s*'([^']+)',$", path.read_text(encoding="utf-8"), re.M)
    missing = [p.id for p in ALL_PRINCIPLES if p.description not in listed]
    assert not missing, f"{path.name} does not state {missing} as the code does"
    assert len(listed) == 12, f"{path.name} lists {len(listed)} principles, not 12"


def test_only_approval_routable_tier1_principles_mention_approval() -> None:
    """ISS-113. A Tier-1 violation is final unless the gate offers a way through.

    The text must not promise an approval the gate cannot give, and a principle
    the gate CAN approve must say so. APPROVAL_ROUTABLE_TIER1 is the set the
    action route consults, so text and behaviour are pinned to one list.
    """
    naming = {p.id for p in TIER_1_PRINCIPLES if "approval" in p.description.lower()}
    assert naming == set(APPROVAL_ROUTABLE_TIER1)


def _yaml_principles() -> dict[str, dict]:
    data = yaml.safe_load(PRINCIPLES_YAML.read_text(encoding="utf-8"))
    tiers = ("tier_1_safety", "tier_2_operational", "tier_3_learning")
    return {p["id"]: p for tier in tiers for p in data[tier]}


def test_yaml_reference_lists_exactly_the_code_principles() -> None:
    assert sorted(_yaml_principles()) == sorted(p.id for p in ALL_PRINCIPLES)


@pytest.mark.parametrize("principle", ALL_PRINCIPLES, ids=lambda p: p.id)
def test_yaml_reference_matches_code(principle) -> None:
    entry = _yaml_principles()[principle.id]
    assert entry["name"] == principle.name
    assert entry["description"] == principle.description
    assert entry["violation_action"] == principle.violation_action


def test_yaml_reference_flags_approval_only_where_the_gate_offers_it() -> None:
    flagged = {
        pid
        for pid, entry in _yaml_principles().items()
        if pid.startswith("P1.") and entry.get("requires_explicit_approval")
    }
    assert flagged == set(APPROVAL_ROUTABLE_TIER1)
