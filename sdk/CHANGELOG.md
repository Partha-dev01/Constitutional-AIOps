# Changelog — Constitutional AIOps SDKs

Both packages (`constitutional-aiops` on PyPI, `@constitutional-aiops/sdk` on npm)
share a version. Releases are cut by pushing an `sdk-v<version>` tag, which
publishes both tokenlessly via OIDC Trusted Publishing.

## Unreleased

Tracks a server-side behaviour change. No SDK version has been cut for it yet.

- **`approve_action` / `approveAction` and `execute_action` / `executeAction` now
  require an admin session.** The server gained a role check on these routes, so
  a non-admin token gets `403` where it previously succeeded. Nothing in the SDK
  changed to cause this; the note is here because it changes what your existing
  code can do.
- **The approver is recorded from the session, not the request body.**
  `approved_by` / `approvedBy` is still accepted and is ignored by the server.
  In TypeScript the field is now **optional** rather than required, matching
  Python, so `approveAction(id, { approved: true })` type-checks. Passing it
  still compiles and still works, it simply has no effect.
- **A new `429` is reachable** on chat, tool and action calls once a per-caller
  hourly window fills. The response carries a `Retry-After` header. The SDK
  surfaces it as an ordinary HTTP error, so retry logic is yours to add.

## 0.3.0

Generative UI reaches the SDK, the tool and chat surface grows, and the generated
typed core is resynced with the API. Same shape in Python and TypeScript. No
breaking changes; existing methods are unchanged.

Added to the ergonomic client (both languages):

- **Generative UI (opt-in, cost-fenced insight widgets).** `explain(kind, payload, tier=)`
  is the surface behind the dashboard "Explain" buttons: it returns a uniform
  `ExplainResponse` (check `available`, then `explanation` or `reason`) and never
  throws for a disabled or over-budget widget. `insight_preferences` /
  `set_insight_preferences` read and write the per-user opt-in. The exported
  `INSIGHT_KINDS`, `INSIGHT_TIERS` and `INSIGHT_UNAVAILABLE_REASONS` mirror the
  server vocabulary.
- **Tool registry.** `tools`, `get_tool`, `call_tool` — the same MCP tools the
  copilots and the agentic chat loop use. An action tool still passes the
  constitutional gate; the uniform `ToolCallResponse` carries the verdict.
- **Chat decisions.** `decide_chat_action` resolves the approve-to-run card a chat
  turn proposes (distinct from `approve_action` on the `/actions` queue), and
  `delete_conversation` removes a conversation.

Also:

- **Typed core resynced.** Both generated cores (`constitutional_aiops_client`,
  `schema.d.ts`) are regenerated from the current OpenAPI snapshot, so the full
  typed surface now includes the `insights` (generative UI) endpoints that were
  missing, plus the current codegen output for every other tag.
- **Deterministic regeneration + a real drift gate.** `sdk/python/scripts/generate.sh`
  now applies a pinned, isolated `ruff format` step (openapi-python-client with
  `--meta none` skips its own formatter), so local and CI regeneration are
  byte-identical. A new `sdk-drift` CI workflow regenerates both cores and the
  OpenAPI snapshot and fails on any drift, so the cores can no longer silently
  lag the API.
- Extended stdlib `unittest` smoke tests for the new methods and the exported
  insight vocabulary.

## 0.2.0

A real feature release: the ergonomic `AIOpsClient` grows from a starter set to
cover the high-value tags an operator or script actually reaches. Same shape in
Python and TypeScript. No breaking changes; existing methods are unchanged.

Added (both languages):

- **Incidents:** `incident_stats`, `create_incident`, `update_incident`, `similar_incidents`.
- **Actions** (each still passes the constitutional gate): `list_actions`, `get_action`, `create_action`, `execute_action`, `cancel_action`, `action_stats`, `confidence_formula`.
- **Agents:** `fast_agent_stats`, `fast_agent_activity`, `reasoning_agent_stats`, `reasoning_agent_activity`.
- **Episodic graph:** `graph_stats`, `topology`, `services`, `episodes`, `get_episode`, `similar_episodes`.
- **Audit:** `audit_events`, `audit_event_types`.
- **Personal access tokens (self-service):** `list_tokens`, `create_token`, `revoke_token`.
- **Notifications:** `notifications`, `unread_count`, `mark_read`, `clear_notifications`.
- **Benchmark:** `evaluate_endpoint`, `benchmark_status`, `benchmark_results`.
- **Metrics:** `metrics`, `metrics_history`, `metrics_latency`.
- **Chat:** `chat` (non-streaming), `analyze`, `list_conversations`, `get_conversation`.

Also:

- **Opt-in retries.** `AIOpsClient(url, max_retries=2)` (Python) / `{ maxRetries: 2 }`
  (TypeScript). A 429 is retried on any method; 5xx and network errors are retried
  only for GET, so a POST is never silently resent. Exponential backoff honors a
  `Retry-After` header. Default is 0 (no retries), so behavior is unchanged unless
  opted in.
- **Python context manager.** `with AIOpsClient(...) as client:` is supported.
- **Version single-source (fix).** The Python `__version__` now reads the installed
  distribution version, ending the 0.1.x drift where the literal lagged the manifest.
- Stdlib `unittest` smoke tests for the Python client (URL/param/body construction,
  the typed-error mapping, and the retry policy).

The long tail of the 127-path API stays available through the generated typed core
(`constitutional_aiops_client` with the `typed` extra; `createTypedClient` in
TypeScript) and the generic `request(method, path, ...)` escape hatch.

## 0.1.1

Verification release confirming the tokenless OIDC publish pipeline on both
registries (migrated off the first-publish 2FA token). No client changes.

## 0.1.0

First public release. Ergonomic `AIOpsClient` (incidents list/get, actions
pending/approve, chat streaming, typed errors including `ConstitutionalRefusal`)
plus the generated typed core. Published to PyPI and npm.
