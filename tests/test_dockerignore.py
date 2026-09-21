"""Gate: an image built from the repo root must not carry local runtime files.

`docker/Dockerfile.backend` copies the whole `data/` directory so the seeded
benchmark set ships. A local run with no `AIOPS_DATA_DIR` writes `users.db`
and `auth_secret.key` into that same directory, and git ignoring them does not
keep them out of a Docker build context. `.dockerignore` does, so these rules
must stay.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _rules() -> list[str]:
    text = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
    lines = (line.strip() for line in text.splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def test_backend_image_still_copies_data() -> None:
    dockerfile = (REPO_ROOT / "docker/Dockerfile.backend").read_text(encoding="utf-8")
    assert "COPY data/ ./data/" in dockerfile, (
        "Dockerfile.backend no longer copies data/; revisit the data/ rules in .dockerignore"
    )


def test_only_the_benchmark_set_of_data_is_in_the_context() -> None:
    rules = _rules()
    assert "data/*" in rules, "data/ is not excluded, so users.db and auth_secret.key can ship"
    exclude = rules.index("data/*")
    assert "!data/benchmark" in rules[exclude:], "the benchmark set must be re-included after data/*"
    reincluded = [rule for rule in rules if rule.startswith("!data/")]
    assert reincluded == ["!data/benchmark", "!data/benchmark/**"], (
        f"only data/benchmark may be re-included, found {reincluded}"
    )


def test_environment_files_are_excluded() -> None:
    rules = _rules()
    for rule in ("**/.env", "**/.env.*"):
        assert rule in rules, f"{rule} is missing from .dockerignore"
    assert not [rule for rule in rules if rule.startswith("!") and ".env" in rule]
