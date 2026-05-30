"""Constitutional AIOps - MCP tools.

The MCP tools are implemented as handlers on :class:`src.mcp.server.MCPActionServer`.
For the current (v1) deployment only the two read-only QUERY tools are
production-wired against live stores:

- ``find_similar``      -> episodic-memory similarity search (needs an episode store)
- ``get_dependencies``  -> Neo4j service dependency graph (needs the Neo4j client)

When their backing store is absent these tools now return ``success=False`` rather
than mock data — there is no silent fallback in production.

The ACTION / ANALYSIS tools (``restart_service``, ``scale_service``, ``analyze_logs``)
are intentionally deferred to v2 and still return mock / no-op results; do not rely
on them in production.
"""

# Tools that are production-ready in v1 (live-store backed, no mock fallback).
ACTIVE_QUERY_TOOLS: tuple[str, ...] = ("find_similar", "get_dependencies")

# Tools registered but deferred to v2 (mock / no-op implementations).
DEFERRED_V2_TOOLS: tuple[str, ...] = ("restart_service", "scale_service", "analyze_logs")

__all__ = ["ACTIVE_QUERY_TOOLS", "DEFERRED_V2_TOOLS"]
