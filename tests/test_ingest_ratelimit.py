"""ENH-005: hold the rate-limited Caddyfile variant to its base file.

Why this gate exists: `docker/configs/Caddyfile.ingest-ratelimit` is a full copy of
`docker/configs/Caddyfile` plus one documented insert. Two near-identical edge configs
are exactly the shape that drifts silently, and the one that drifts is the one nobody
reads until an incident. When two surfaces must agree, write the gate.

The base file must stay parseable by STOCK Caddy, so the `rate_limit` directive may
never appear in it: the frozen production stack pins `caddy:2.8-alpine`, and a config
it cannot parse takes the whole edge down on restart.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = REPO_ROOT / "docker" / "configs" / "Caddyfile"
VARIANT = REPO_ROOT / "docker" / "configs" / "Caddyfile.ingest-ratelimit"
DOCKERFILE = REPO_ROOT / "docker" / "Dockerfile.caddy"
OVERLAY = REPO_ROOT / "docker" / "docker-compose.ingest-ratelimit.yml"
PRODUCTION = REPO_ROOT / "docker" / "docker-compose.production.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_all_enh005_files_exist() -> None:
    for path in (BASE, VARIANT, DOCKERFILE, OVERLAY):
        assert path.is_file(), f"missing {path.relative_to(REPO_ROOT)}"


def test_base_caddyfile_stays_stock_parseable() -> None:
    """The frozen stack's Caddyfile must never gain a plugin-only directive."""
    base = _read(BASE)
    assert not re.search(r"^\s*rate_limit\s*\{", base, re.MULTILINE), (
        "docker/configs/Caddyfile gained a `rate_limit` block. Stock caddy:2.8-alpine "
        "cannot parse it and the production edge would fail to start. The rate limit "
        "belongs in Caddyfile.ingest-ratelimit, used via the opt-in overlay."
    )


def test_variant_carries_the_rate_limit_zone() -> None:
    variant = _read(VARIANT)
    assert re.search(r"^\s*rate_limit\s*\{", variant, re.MULTILINE)
    assert re.search(r"^\s*zone ingest\s*\{", variant, re.MULTILINE)
    # Keyed on the TCP peer, never a forgeable header.
    assert "key    {remote_host}" in variant
    assert "{$INGEST_RATE_EVENTS:600}" in variant
    assert "{$INGEST_RATE_WINDOW:1m}" in variant


def test_variant_is_the_base_plus_only_the_documented_insert() -> None:
    """Strip the header and the inserted block; what is left must equal the base.

    This is the actual anti-drift check. A change to the base Caddyfile that is not
    mirrored into the variant fails here, naming the first differing line.
    """
    base = _read(BASE)
    variant = _read(VARIANT)

    # 1. drop the generated-file header, everything before the base's first line
    first_base_line = base.split("\n", 1)[0]
    assert first_base_line in variant, "variant no longer contains the base's opening line"
    body = variant[variant.index(first_base_line):]

    # 2. swap the whole inserted region (rate_limit comment, the block, and the
    #    reworded body-cap comment) back for the base file's original comment.
    #    Both regions end at the same anchor, the `request_body` directive.
    start = body.index("\t\t# Per-source request rate limit (ENH-005).")
    end = body.index("\t\trequest_body {")
    reconstructed = body[:start] + _BASE_COMMENT + body[end:]

    if reconstructed != base:
        base_lines = base.split("\n")
        recon_lines = reconstructed.split("\n")
        for i, (a, b) in enumerate(zip(base_lines, recon_lines), start=1):
            if a != b:
                raise AssertionError(
                    "Caddyfile.ingest-ratelimit has drifted from Caddyfile at line "
                    f"{i}.\n  base:    {a!r}\n  variant: {b!r}\n"
                    "Regenerate the variant from the base rather than hand-editing it."
                )
        raise AssertionError(
            "Caddyfile.ingest-ratelimit differs from Caddyfile in length: "
            f"base {len(base_lines)} lines, reconstructed {len(recon_lines)}."
        )


_BASE_COMMENT = """\t\t# Body cap (Batch F #3): keep the 10MB ceiling on telemetry pushes.
\t\t# RATE-LIMITING FOLLOW-UP: stock Caddy has NO `rate_limit` directive, so
\t\t# we deliberately do NOT add one here (a fake/broken directive would fail
\t\t# `caddy validate`). Per-source request rate-limiting on /ingest/* needs a
\t\t# CUSTOM Caddy build that bundles the community ratelimit plugin, e.g.:
\t\t#   xcaddy build --with github.com/mholt/caddy-ratelimit
\t\t# Once that image is in use, add a `rate_limit` block inside this handle.
\t\t# Until then the 10MB body cap below is the only ingest-side throttle.
"""


def test_overlay_pins_the_same_caddy_version_as_production() -> None:
    """Adopting the overlay must not silently become a Caddy upgrade."""
    production = _read(PRODUCTION)
    overlay = _read(OVERLAY)
    dockerfile = _read(DOCKERFILE)

    match = re.search(r"image:\s*caddy:([0-9.]+)-alpine", production)
    assert match, "could not find the pinned caddy image in the production compose"
    pinned = match.group(1)

    assert f'CADDY_VERSION: "{pinned}"' in overlay, (
        f"overlay must build CADDY_VERSION {pinned} to match the production pin"
    )
    assert f"ARG CADDY_VERSION={pinned}" in dockerfile


def test_plugin_version_is_pinned_not_floating() -> None:
    dockerfile = _read(DOCKERFILE)
    match = re.search(r"ARG RATELIMIT_VERSION=(\S+)", dockerfile)
    assert match, "Dockerfile.caddy must declare RATELIMIT_VERSION"
    assert re.fullmatch(r"v\d+\.\d+\.\d+", match.group(1)), (
        "pin the rate-limit module to an exact release; this binary terminates TLS"
    )
    assert "caddy-ratelimit@${RATELIMIT_VERSION}" in dockerfile, (
        "the xcaddy build must consume the pin rather than tracking latest"
    )


def test_frozen_compose_files_do_not_reference_the_overlay() -> None:
    """The opt-in must stay opt-in: nothing frozen may pull this in by default."""
    for path in (
        REPO_ROOT / "docker-compose.yml",
        PRODUCTION,
        REPO_ROOT / "docker" / "docker-compose.gpu.yml",
        REPO_ROOT / "docker" / "docker-compose.lite.yml",
    ):
        if not path.is_file():
            continue
        text = _read(path)
        assert "ingest-ratelimit" not in text, (
            f"{path.name} references the opt-in overlay; it must remain opt-in"
        )
