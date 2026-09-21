"""Gate: the published safety docs must match the principles in code.

The 12-principle gate is the project's headline claim, and the published list
had drifted badly from `src/constitutional/principles.py`. Six of the twelve
were wrong, including three of the four Tier-1 safety-critical ones: P1.4 was
published as "All actions reversible within a short window" while the code says
"Never modify security configurations without explicit approval", and P1.2 was
published as "Maintain a minimum of healthy replicas" while the code says
"Never take destructive actions during active incidents without explicit
approval". Nothing compared the two, so nobody noticed.
"""

from pathlib import Path

import pytest

from src.constitutional.principles import ALL_PRINCIPLES

REPO_ROOT = Path(__file__).resolve().parents[1]
SAFETY_PAGE = REPO_ROOT / "docs-site" / "guide" / "safety.md"
README = REPO_ROOT / "README.md"

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
    for path in (SAFETY_PAGE, README):
        assert claim not in path.read_text(encoding="utf-8"), (
            f"{path.name} still carries the retired claim {claim!r}, which "
            "describes a principle the code does not implement"
        )
