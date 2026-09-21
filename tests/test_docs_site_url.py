"""Gate: every surface that links to the published docs site must use one URL.

The in-app guide (frontend) and the marketing site both offer a "read the full
documentation" link. They are separate trees with separate build configs, so
nothing stops one from being repointed and the other quietly left behind. That
is the same drift class as the version surfaces in `test_version.py`: two
things that must agree, with nothing checking that they do.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Matches the committed default in either tree:
#   export const DOCS_SITE_URL: string =\n  import.meta.env.VITE_DOCS_SITE_URL ??\n  'https://...'
#   const DOCS_SITE_URL =\n  (import.meta.env.VITE_DOCS_SITE_URL as string | undefined) ??\n  'https://...'
_DEFAULT = re.compile(
    r"DOCS_SITE_URL\b.*?VITE_DOCS_SITE_URL.*?\?\?\s*'([^']+)'",
    re.DOTALL,
)


def _default_docs_url(relative_path: str) -> str:
    source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    match = _DEFAULT.search(source)
    assert match is not None, f"no DOCS_SITE_URL default found in {relative_path}"
    return match.group(1)


def test_marketing_and_app_agree_on_the_docs_url() -> None:
    marketing = _default_docs_url("marketing/src/config.ts")
    app = _default_docs_url("frontend/src/pages/Docs.tsx")
    assert marketing == app, (
        "the marketing site and the in-app guide link to different docs sites: "
        f"{marketing!r} vs {app!r}"
    )


def test_docs_url_is_the_published_site() -> None:
    url = _default_docs_url("marketing/src/config.ts")
    assert url.startswith("https://"), url
    assert url.endswith("/"), "trailing slash keeps VitePress from redirecting"
