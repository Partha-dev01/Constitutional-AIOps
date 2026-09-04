"""Deterministic first-run onboarding generators.

Pure, offline, dependency-light builders used by the Quick-Setup wizard:
turn a plain list of user-described services into (a) a valid platform
topology schema and (b) a base system-prompt draft. Both are the always-
available baseline; the wizard's optional "improve with AI" path layers an
LLM pass on top (see the topology / prompts routes) and falls back to these
when no endpoint is configured or a generation fails.

Kept free of FastAPI / route imports so they unit-test in isolation. The
topology output is a plain ``{"nodes": [...], "edges": [...]}`` dict; the
route runs it through ``src.topology.schema.validate_topology_schema`` so a
generated schema is byte-shape-identical to a hand-edited / Applied one.
"""

from __future__ import annotations

import re
from typing import Any

from src.topology.schema import (
    ALLOWED_NODE_KINDS,
    MAX_EDGES,
    MAX_NODES,
)

# Ordered (kind, keywords): first match wins. Roles and names are matched
# case-insensitively. Multi-word / hyphenated keywords match as substrings;
# single tokens match on word boundaries so e.g. "sandbox" is not mistaken for
# a datastore because it contains "db". ``backend`` is the default, so it needs
# no keyword list.
_KIND_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "gateway",
        (
            "gateway",
            "proxy",
            "reverse proxy",
            "caddy",
            "nginx",
            "ingress",
            "traefik",
            "envoy",
            "load balancer",
            "loadbalancer",
        ),
    ),
    (
        "observability",
        (
            "prometheus",
            "grafana",
            "loki",
            "tempo",
            "jaeger",
            "otel",
            "opentelemetry",
            "telemetry",
            "metrics",
            "logging",
            "monitor",
            "monitoring",
            "observability",
            "tracing",
        ),
    ),
    (
        "datastore",
        (
            "database",
            "postgres",
            "postgresql",
            "mysql",
            "mariadb",
            "mongo",
            "mongodb",
            "redis",
            "neo4j",
            "cassandra",
            "sqlite",
            "elastic",
            "elasticsearch",
            "kafka",
            "rabbitmq",
            "queue",
            "cache",
            "datastore",
            "db",
            "sql",
        ),
    ),
    (
        "llm",
        (
            "llm",
            "vllm",
            "ollama",
            "gpt",
            "qwen",
            "llama",
            "mistral",
            "inference",
            "embedding",
            "embeddings",
            "model server",
            "openai",
        ),
    ),
    (
        "frontend",
        (
            "frontend",
            "front-end",
            "front end",
            "ui",
            "spa",
            "react",
            "vue",
            "angular",
            "svelte",
            "dashboard",
            "web app",
            "webapp",
            "website",
            "client",
        ),
    ),
    (
        "edge",
        (
            "edge",
            "iot",
            "sensor",
            "device",
        ),
    ),
)

# Default tier per kind (0 = entry point, higher = deeper dependency).
_DEFAULT_TIER: dict[str, int] = {
    "gateway": 0,
    "frontend": 1,
    "backend": 2,
    "llm": 3,
    "datastore": 3,
    "observability": 3,
    "edge": 4,
    "edge-host": 4,
}

_MAX_TIER = 20  # mirrors SchemaNode.tier upper bound


def _slugify(name: str) -> str:
    """Turn a service name into a stable, non-empty node id."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")
    return slug or "service"


def _keyword_matches(text: str, keyword: str) -> bool:
    """Word-boundary match for single tokens; substring for multi-word ones."""
    if " " in keyword or "-" in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def infer_kind(name: str, role: str = "") -> str:
    """Map a free-form role / name to one allowed topology node kind.

    An explicit ``role`` that is already a valid kind wins outright; otherwise
    keyword heuristics on ``role`` then ``name`` decide, defaulting to
    ``backend`` (the safe, most common case) when nothing matches.
    """
    role_norm = (role or "").strip().lower()
    if role_norm in ALLOWED_NODE_KINDS:
        return role_norm
    text = f"{role_norm} {str(name).strip().lower()}"
    for kind, keywords in _KIND_KEYWORDS:
        if any(_keyword_matches(text, kw) for kw in keywords):
            return kind
    return "backend"


def _coerce_int(value: Any) -> int | None:
    """Best-effort int coercion (accepts int or a digit string), else None."""
    if isinstance(value, bool):  # bool is an int subclass — reject it explicitly
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


_OBSERVABILITY_KINDS = frozenset({"observability"})
_SENSOR_KINDS = frozenset({"edge", "edge-host"})


def _infer_default_edges(
    nodes: list[dict[str, Any]],
    explicit_sources: set[str],
    existing: set[tuple[str, str]],
    budget: int,
) -> list[dict[str, Any]]:
    """Synthesise a sensible topology for services with no hand-wired deps.

    A services list without ``dependsOn`` would otherwise render as disconnected
    dots, so we derive relationships from the inferred kinds/tiers:
      * DEPENDS_ON down the tier spine (gateway -> frontend -> backend ->
        datastore / llm), skipping the next-tier hop where a tier is empty.
      * SHIPS_TELEMETRY from every service to each observability node (and from
        edge sensors, which never sit in the dependency spine).
    This only supplements: a service the operator already gave dependencies for
    keeps exactly those. Honours the same dedupe + total-edge budget as explicit
    edges, so a huge paste degrades gracefully.
    """
    out: list[dict[str, Any]] = []

    def add(source: str, target: str, relationship: str) -> None:
        if len(out) >= budget or source == target or (source, target) in existing:
            return
        existing.add((source, target))
        out.append(
            {"source": source, "target": target, "relationship": relationship, "kind": "static"}
        )

    obs_ids = [str(n["id"]) for n in nodes if n.get("kind") in _OBSERVABILITY_KINDS]
    sensors = [n for n in nodes if n.get("kind") in _SENSOR_KINDS]
    spine = [
        n
        for n in nodes
        if n.get("kind") not in _OBSERVABILITY_KINDS and n.get("kind") not in _SENSOR_KINDS
    ]

    # Layered DEPENDS_ON along the spine, from each tier to the next deeper one.
    by_tier: dict[int, list[str]] = {}
    for n in spine:
        by_tier.setdefault(int(n["tier"]), []).append(str(n["id"]))
    tiers = sorted(by_tier)
    for lo, hi in zip(tiers, tiers[1:]):
        for src in by_tier[lo]:
            if src in explicit_sources:
                continue  # operator wired this service's deps by hand
            for tgt in by_tier[hi]:
                add(src, tgt, "DEPENDS_ON")

    # Telemetry flows: every service reports to each observability node.
    for obs in obs_ids:
        for n in spine + sensors:
            add(str(n["id"]), obs, "SHIPS_TELEMETRY")
    # Sensors with no observability sink still connect to the app backend.
    if not obs_ids:
        backends = [str(n["id"]) for n in spine if n.get("kind") == "backend"]
        for s in sensors:
            for b in backends:
                add(str(s["id"]), b, "SHIPS_TELEMETRY")

    return out


def build_topology_from_services(
    services: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Deterministically build a topology ``{"nodes","edges"}`` from services.

    Each service dict may carry ``name`` (required), ``role``, ``tier``,
    ``port`` and ``dependsOn`` (a list of other service names or ids). The
    output is guaranteed to satisfy ``validate_topology_schema``: allowed
    kinds, unique node ids, tiers clamped to [0, 20], edges only between known
    nodes. Unknown / self / duplicate dependencies are dropped silently.

    Input is capped at ``MAX_NODES`` services (and edges at ``MAX_EDGES``) so a
    huge paste degrades gracefully instead of tripping the strict size guard.
    """
    nodes: list[dict[str, Any]] = []
    # Map both a service's lowercased name and its slug to the final unique id,
    # so a dependsOn entry can reference either form.
    id_by_input: dict[str, str] = {}
    used_ids: set[str] = set()

    capped = [s for s in services if isinstance(s, dict)][:MAX_NODES]

    for svc in capped:
        name = str(svc.get("name") or "").strip()
        if not name:
            continue
        kind = infer_kind(name, str(svc.get("role") or ""))

        base_id = _slugify(name)
        node_id = base_id
        suffix = 2
        while node_id in used_ids:
            node_id = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(node_id)
        id_by_input.setdefault(name.lower(), node_id)
        id_by_input.setdefault(base_id, node_id)

        tier = _coerce_int(svc.get("tier"))
        if tier is None:
            tier = _DEFAULT_TIER.get(kind, 2)
        tier = max(0, min(_MAX_TIER, tier))

        node: dict[str, Any] = {
            "id": node_id,
            "label": name,
            "kind": kind,
            "tier": tier,
        }
        port = _coerce_int(svc.get("port"))
        if port is not None and 0 <= port <= 65535:
            node["port"] = port
        description = str(svc.get("description") or "").strip()
        if description:
            node["description"] = description
        nodes.append(node)

    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str]] = set()

    for svc in capped:
        name = str(svc.get("name") or "").strip()
        if not name:
            continue
        source = id_by_input.get(name.lower()) or id_by_input.get(_slugify(name))
        if not source:
            continue
        deps = svc.get("dependsOn")
        if deps is None:
            deps = svc.get("depends_on")
        if not isinstance(deps, list):
            continue
        for dep in deps:
            dep_str = str(dep or "").strip()
            if not dep_str:
                continue
            target = id_by_input.get(dep_str.lower()) or id_by_input.get(
                _slugify(dep_str)
            )
            if not target or target == source:
                continue
            key = (source, target)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            if len(edges) >= MAX_EDGES:
                break
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relationship": "DEPENDS_ON",
                    "kind": "static",
                }
            )

    # Without hand-wired deps the graph would be disconnected dots. Synthesise a
    # sensible layered topology so a Quick-Setup run always yields a connected,
    # meaningful graph (explicit dependencies above are always kept as-is).
    if len(edges) < MAX_EDGES:
        explicit_sources = {str(e["source"]) for e in edges}
        edges.extend(
            _infer_default_edges(nodes, explicit_sources, seen_edges, MAX_EDGES - len(edges))
        )

    return {"nodes": nodes, "edges": edges}


def _node_lookup(topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index the topology nodes by id (tolerant of a malformed payload)."""
    out: dict[str, dict[str, Any]] = {}
    nodes = topology.get("nodes") if isinstance(topology, dict) else None
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict) and node.get("id"):
                out[str(node["id"])] = node
    return out


def build_base_prompt(
    services: list[dict[str, Any]],
    topology: dict[str, Any],
) -> str:
    """Build a deterministic base system-prompt describing the platform.

    Uses the (already-generated) topology as the source of truth for kinds /
    tiers / dependencies, falling back to the raw services list for names. The
    result is a ready-to-edit operator-assistant prompt within the prompts
    endpoint's 10..10000 character bounds.
    """
    by_id = _node_lookup(topology)
    node_items = list(by_id.values())
    if not node_items:
        # No topology yet — derive minimal node stand-ins from the services.
        node_items = [
            {"id": _slugify(str(s.get("name"))), "label": str(s.get("name") or "").strip(),
             "kind": infer_kind(str(s.get("name") or ""), str(s.get("role") or "")),
             "tier": None}
            for s in services
            if isinstance(s, dict) and str(s.get("name") or "").strip()
        ]

    lines: list[str] = [
        "You are the AIOps operations assistant for this platform. You help "
        "operators understand incidents, correlate logs, metrics and traces, "
        "reason about root cause, and propose safe, minimal remediation.",
        "",
    ]

    if node_items:
        lines.append("PLATFORM SERVICES:")
        for node in node_items:
            label = str(node.get("label") or node.get("id") or "service").strip()
            kind = str(node.get("kind") or "service").strip()
            tier = node.get("tier")
            descr = str(node.get("description") or "").strip()
            tier_str = f", tier {tier}" if isinstance(tier, int) else ""
            suffix = f" — {descr}" if descr else ""
            lines.append(f"- {label} ({kind}{tier_str}){suffix}")
        lines.append("")

    # Dependency edges (topology is authoritative when present).
    edges = topology.get("edges") if isinstance(topology, dict) else None
    dep_lines: list[str] = []
    if isinstance(edges, list):
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            src = by_id.get(str(edge.get("source")), {})
            tgt = by_id.get(str(edge.get("target")), {})
            src_label = str(src.get("label") or edge.get("source") or "").strip()
            tgt_label = str(tgt.get("label") or edge.get("target") or "").strip()
            if not src_label or not tgt_label:
                continue
            rel = str(edge.get("relationship") or "DEPENDS_ON")
            verb = "ships telemetry to" if rel == "SHIPS_TELEMETRY" else "depends on"
            dep_lines.append(f"- {src_label} {verb} {tgt_label}")
    if dep_lines:
        lines.append("SERVICE DEPENDENCIES:")
        lines.extend(dep_lines)
        lines.append("")

    lines.extend(
        [
            "WHEN AN OPERATOR ASKS FOR HELP:",
            "- Ground every answer in the telemetry and incident data available "
            "to you; cite the specific service, metric or log line when you can.",
            "- Use the service dependencies above to reason about blast radius "
            "and likely upstream causes.",
            "- Give clear, actionable next steps and call out risks explicitly.",
            "- Any change to infrastructure must go through the Constitutional AI "
            "approval process — propose actions, never assume they are executed.",
            "",
            "Be helpful, precise, and safety-conscious.",
        ]
    )

    prompt = "\n".join(lines).strip()
    # Enforce the prompts endpoint bounds (10..10000 chars).
    if len(prompt) < 10:
        prompt = (
            "You are the AIOps operations assistant for this platform. Help "
            "operators diagnose incidents and propose safe remediation."
        )
    return prompt[:10000]


__all__ = [
    "infer_kind",
    "build_topology_from_services",
    "build_base_prompt",
]
