"""Gate: the rate-limit settings must mean the same thing on every surface.

The per-account hourly limits and the proxy hop count are read from the
environment in `src/api/rate_limit.py`. The lite compose file hands the backend
an explicit allow-list of variables, not the whole `.env`, so a variable left
off that list is silently ignored in a Docker deploy. That is how the three
`AIOPS_RATE_*` limits went unforwarded while the published configuration page
listed them as settings. This holds the code defaults, the lite compose
allow-list and the published table to one another.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

VARS = (
    "AIOPS_RATE_CHAT_PER_HOUR",
    "AIOPS_RATE_TOOLS_PER_HOUR",
    "AIOPS_RATE_ACTIONS_PER_HOUR",
    "TRUSTED_PROXY_HOPS",
)

_GETENV = re.compile(r'os\.getenv\("([A-Z_]+)",\s*"(\d+)"\)')


def _getenv_defaults(relative_path: str) -> dict[str, str]:
    source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    return dict(_GETENV.findall(source))


def _code_defaults() -> dict[str, str]:
    found = _getenv_defaults("src/api/rate_limit.py")
    missing = [var for var in VARS if var not in found]
    assert not missing, f"no getenv default in src/api/rate_limit.py for {missing}"
    return {var: found[var] for var in VARS}


def _lite_backend_env() -> dict[str, str]:
    text = (REPO_ROOT / "docker/docker-compose.lite.yml").read_text(encoding="utf-8")
    env = yaml.safe_load(text)["services"]["backend"]["environment"]
    if isinstance(env, dict):
        return {key: str(value) for key, value in env.items()}
    return dict(item.split("=", 1) for item in env)


def test_lite_compose_forwards_every_rate_limit_variable() -> None:
    env = _lite_backend_env()
    defaults = _code_defaults()
    for var in VARS:
        assert var in env, (
            f"{var} is not in the lite backend environment allow-list, "
            "so setting it in .env has no effect"
        )
        expected = f"${{{var}:-{defaults[var]}}}"
        assert env[var] == expected, (
            f"{var}: lite compose passes {env[var]!r}, expected {expected!r}"
        )


def test_published_defaults_match_the_code() -> None:
    table = (REPO_ROOT / "docs-site/guide/configuration.md").read_text(encoding="utf-8")
    defaults = _code_defaults()
    for var in VARS:
        match = re.search(rf"^\|\s*`{var}`\s*\|\s*`([^`]+)`\s*\|", table, re.MULTILINE)
        assert match is not None, f"{var} is missing from the configuration table"
        assert match.group(1) == defaults[var], (
            f"{var}: the docs say {match.group(1)}, the code says {defaults[var]}"
        )


def test_login_throttle_reads_the_same_hop_count() -> None:
    # auth.py keeps its own copy for the per-IP login throttle.
    auth = _getenv_defaults("src/api/routes/auth.py")
    assert auth.get("TRUSTED_PROXY_HOPS") == _code_defaults()["TRUSTED_PROXY_HOPS"]
