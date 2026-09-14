# Changelog — Constitutional AIOps SDKs

Both packages (`constitutional-aiops` on PyPI, `@constitutional-aiops/sdk` on npm)
share a version. Releases are cut by pushing an `sdk-v<version>` tag, which
publishes both tokenlessly via OIDC Trusted Publishing.

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
