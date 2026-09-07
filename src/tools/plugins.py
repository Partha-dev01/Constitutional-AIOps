"""Constitutional AIOps - optional tool-plugin discovery (Track 3-F Phase 3).

Third-party packages may contribute extra platform tools without editing this
repo, discovered through Python packaging **entry points** in the group
``constitutional_aiops.tools``. Discovery is DEFAULT-OFF and fail-closed:

* Nothing loads unless the operator sets ``AIOPS_ENABLE_PLUGINS=true``. With the
  env unset (production / GPU default) ``discover_plugins`` is never called by
  the runtime, so the plugin surface does not exist and the stack is
  byte-identical to a build with no plugin code at all.
* A plugin only *contributes* a tool; it can never *bypass* safety. A plugin
  action tool is registered exactly like the built-in restart/scale — it routes
  through ``_run_action_tool`` -> the constitutional gate -> the validator — and
  a non-container plugin action always requires human approval (see the gate).
* Discovery swallows and logs any error from a misbehaving entry point and skips
  it, rather than letting one bad plugin break the whole tool surface.

This module does DISCOVERY only (find + load + validate entry points into
``PluginTool`` descriptors). The actual wiring into the live registries lives in
``src/api/routes/tools.py`` (``register_plugin_tools``), which is where the
dispatch table, the action-executor map, and the gate are — keeping this module
free of any dependency on the route layer (no import cycle).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from src.tools.registry import ToolMeta

logger = logging.getLogger(__name__)

# Entry-point group third-party distributions advertise their tools under.
PLUGIN_ENTRY_POINT_GROUP = "constitutional_aiops.tools"

# Master switch for the whole plugin surface (fail-closed, default OFF).
PLUGINS_ENV = "AIOPS_ENABLE_PLUGINS"


def plugins_enabled() -> bool:
    """True only when the operator has explicitly enabled plugins via env."""
    return os.getenv(PLUGINS_ENV, "").lower() in ("1", "true", "yes")


@dataclass
class PluginTool:
    """One tool contributed by a plugin.

    ``meta`` is the canonical :class:`ToolMeta` (so the tool goes through the
    same registry, listing, gate, and validator as a built-in). A read/analysis
    plugin supplies ``handler`` — an ``async (ctx, params, start_time) ->
    ToolCallResponse`` that may read app.state components off ``ctx``. An action
    plugin (``meta.category == "action"``) supplies ``executor`` — an
    ``async (params, start_time) -> ToolCallResponse`` invoked only AFTER the
    constitutional gate authorizes the call.
    """

    meta: ToolMeta
    handler: Callable[..., Any] | None = None
    executor: Callable[..., Any] | None = None


def _coerce_to_plugin_tools(loaded: Any) -> list[PluginTool]:
    """Normalize what an entry point loaded into a list of PluginTool.

    Accepts a bare ``PluginTool``, an iterable of them, or a zero-arg factory
    returning either. Anything else yields an empty list (the caller logs+skips).
    """
    obj = loaded
    if callable(obj) and not isinstance(obj, PluginTool):
        obj = obj()  # a factory: call it once to build the tool(s)
    if isinstance(obj, PluginTool):
        return [obj]
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
        items = list(obj)
        if all(isinstance(it, PluginTool) for it in items):
            return items
    return []


def _is_valid(pt: PluginTool) -> bool:
    """A well-formed descriptor: a real ToolMeta with a name, and the right
    callable for its category (executor for actions, handler otherwise)."""
    if not isinstance(pt.meta, ToolMeta) or not isinstance(pt.meta.name, str) or not pt.meta.name:
        return False
    if pt.meta.is_action:
        return callable(pt.executor)
    return callable(pt.handler)


def discover_plugins(
    group: str = PLUGIN_ENTRY_POINT_GROUP,
    entry_points_fn: Callable[..., Iterable[Any]] | None = None,
) -> list[PluginTool]:
    """Discover and validate plugin tools from entry points in ``group``.

    ``entry_points_fn`` is injectable for tests; it defaults to
    ``importlib.metadata.entry_points``. Never raises — a bad entry point is
    logged and skipped so one broken plugin cannot take out the tool surface.
    """
    if entry_points_fn is None:
        import importlib.metadata as importlib_metadata

        entry_points_fn = importlib_metadata.entry_points

    try:
        eps = list(entry_points_fn(group=group))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Plugin entry-point enumeration failed: %s", exc)
        return []

    discovered: list[PluginTool] = []
    for ep in eps:
        ep_name = getattr(ep, "name", "<unknown>")
        try:
            tools = _coerce_to_plugin_tools(ep.load())
        except Exception as exc:
            logger.warning("Plugin entry point %r failed to load: %s", ep_name, exc)
            continue
        if not tools:
            logger.warning(
                "Plugin entry point %r did not resolve to a PluginTool (skipped)", ep_name
            )
            continue
        for pt in tools:
            if _is_valid(pt):
                discovered.append(pt)
            else:
                logger.warning(
                    "Plugin entry point %r yielded an invalid tool descriptor (skipped)", ep_name
                )
    return discovered


__all__ = [
    "PLUGIN_ENTRY_POINT_GROUP",
    "PLUGINS_ENV",
    "PluginTool",
    "plugins_enabled",
    "discover_plugins",
]
