# constitutional-aiops (Python)

[![PyPI](https://img.shields.io/pypi/v/constitutional-aiops?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/constitutional-aiops/)
[![Python versions](https://img.shields.io/pypi/pyversions/constitutional-aiops?logo=python&logoColor=white)](https://pypi.org/project/constitutional-aiops/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://github.com/Partha-dev01/Constitutional-AIOps/blob/main/LICENSE)

Official Python client for the Constitutional AIOps REST API. Two layers ship
together: a hand-written ergonomic client (`AIOpsClient`, standard library only)
and an optional generated typed core (`constitutional_aiops_client`, full type
safety over every endpoint) that rides on `httpx` + `attrs`. See the
[SDK overview](https://github.com/Partha-dev01/Constitutional-AIOps/tree/main/sdk)
for the full status. Using JavaScript or TypeScript? See the sibling package
[`@constitutional-aiops/sdk`](https://www.npmjs.com/package/@constitutional-aiops/sdk).

Published to PyPI from CI with [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/),
no long-lived token.

## Install

```bash
pip install constitutional-aiops            # ergonomic client only, zero dependencies
pip install "constitutional-aiops[typed]"   # also install the generated typed core
```

Or from a source checkout (development):

```bash
pip install -e sdk/python
pip install -e "sdk/python[typed]"
```

## Use — ergonomic client

```python
from constitutional_aiops import AIOpsClient, ConstitutionalRefusal

client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")

# List every critical incident (pagination handled for you).
for incident in client.paginate("/incidents/", severity="critical"):
    print(incident["id"], incident["title"])

# Read one incident and its root-cause analysis.
inc = client.get_incident("INC-2026-0007")
print(inc.get("rca", {}).get("root_cause"))

# Approve a pending action. This still passes the constitutional gate.
try:
    client.approve_action("act-123", approved=True, approved_by="me")
except ConstitutionalRefusal as refusal:
    print("gate held the action:", refusal.error_code)

# Stream a chat turn.
result = client.stream_chat("why is nextcloud slow?", on_delta=lambda t: print(t, end=""))
print("\n", result.get("message", {}).get("content"))
```

## What you can call (ergonomic client, 0.3.0)

Every method returns plain decoded JSON. Constructor:
`AIOpsClient(base_url, token=None, timeout=90.0, max_retries=0, backoff=0.5)`;
`with AIOpsClient(...) as client:` is supported.

- **Incidents:** `list_incidents`, `paginate("/incidents/")`, `get_incident`, `incident_stats`, `create_incident`, `update_incident`, `similar_incidents`
- **Actions** (each still passes the constitutional gate): `list_actions`, `get_action`, `pending_actions`, `create_action`, `approve_action`, `execute_action`, `cancel_action`, `action_stats`, `confidence_formula`
- **Agents:** `fast_agent_stats`, `fast_agent_activity`, `reasoning_agent_stats`, `reasoning_agent_activity`
- **Episodic graph:** `graph_stats`, `topology`, `services`, `episodes`, `get_episode`, `similar_episodes`
- **Audit:** `audit_events`, `audit_event_types`
- **Tokens (self-service PAT):** `list_tokens`, `create_token`, `revoke_token`
- **Notifications:** `notifications`, `unread_count`, `mark_read`, `clear_notifications`
- **Benchmark:** `evaluate_endpoint`, `benchmark_status`, `benchmark_results`
- **Metrics:** `metrics`, `metrics_history`, `metrics_latency`
- **Chat:** `chat`, `stream_chat`, `analyze`, `list_conversations`, `get_conversation`, `delete_conversation`, `decide_chat_action`
- **Generative UI** (opt-in, cost-fenced insight widgets): `explain`, `insight_preferences`, `set_insight_preferences` (plus the exported `INSIGHT_KINDS`, `INSIGHT_TIERS`, `INSIGHT_UNAVAILABLE_REASONS`)
- **Tools** (the MCP registry the copilots and agentic loop share): `tools`, `get_tool`, `call_tool`

Anything not wrapped here is reachable through the typed core (below) or the
generic escape hatch `client.request(method, path, params=..., body=...)`.

### Generative UI (the "Explain" surface)

`explain` powers the dashboard "Explain" buttons: it sends a widget's already
computed summary and gets back a short, labelled, model-generated hypothesis. It
is opt-in per user and cost-fenced, and it always returns a uniform result you can
render without special-casing status codes.

```python
client.set_insight_preferences(enabled=True)  # opt in once

res = client.explain("anomaly", {"count": 3, "top": [{"series": "cpu", "z": 4.1}]})
if res["available"]:
    print(res["explanation"])          # model_generated == True; a hypothesis, not a measurement
else:
    print("no explanation:", res["reason"])   # e.g. no_endpoint, budget_reached
```

**Opt-in retries.** `AIOpsClient(url, max_retries=2)` retries a 429 on any method
and 5xx or network failures on GET only, with exponential backoff that honors a
`Retry-After` header. The default (`max_retries=0`) never retries.

## Use — typed core

With the `typed` extra installed, every path, parameter, request body and response
is typed from the API's OpenAPI schema.

```python
from constitutional_aiops_client import AuthenticatedClient
from constitutional_aiops_client.api.incidents import incidents_get_incident

client = AuthenticatedClient(
    base_url="https://your-instance.example.com", token="aiops_pat_..."
)
incident = incidents_get_incident.sync(incident_id="INC-2026-0007", client=client)
print(incident.id, incident.severity)
```

## Regenerating the typed core

`constitutional_aiops_client/` is generated from the committed API snapshot
(`openapi/openapi.json`) by
[`openapi-python-client`](https://github.com/openapi-generators/openapi-python-client).
It is committed so the package installs offline; regenerate it whenever the
snapshot changes:

```bash
pip install "openapi-python-client==0.29.1"
bash sdk/python/scripts/generate.sh
```

## Auth

Create a personal access token in the app (Settings, or `POST /api/v1/auth/tokens`)
and pass it as `token=`; it is sent as `Authorization: Bearer aiops_pat_...` and
resolves to your user even when `AUTH_REQUIRED` is off, so calls are attributed and
cost-fenced. Against a single-user instance with `AUTH_REQUIRED` unset the token is
optional.

## License

AGPL-3.0-or-later, matching the app.
