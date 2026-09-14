---
title: SDK Cookbook
outline: deep
---

# SDK Cookbook

Task-shaped recipes for the Python and TypeScript clients. Each one is small and
runnable. For the full surface, see the [SDK Reference](/guide/sdk).

Every recipe assumes a client:

```python
from constitutional_aiops import AIOpsClient
client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")
```

```ts
import { AIOpsClient } from '@constitutional-aiops/sdk'
const client = new AIOpsClient({ baseUrl: 'https://your-instance.example.com', token: 'aiops_pat_...' })
```

Create the token in the app under Settings, or with `POST /api/v1/auth/tokens`.

## Triage the critical incidents

Walk every critical incident (pagination handled for you) and read one's
root-cause analysis.

```python
for inc in client.paginate("/incidents/", severity="critical"):
    print(inc["id"], inc["title"])

detail = client.get_incident("INC-2026-0007")
print(detail.get("rca", {}).get("root_cause"))
```

```ts
for await (const inc of client.paginate('/incidents/', { severity: 'critical' })) {
  console.log(inc.id, inc.title)
}

const detail = await client.getIncident('INC-2026-0007')
console.log((detail.rca as any)?.root_cause)
```

## Approve an action through the gate

Approving does not bypass the constitutional validator. Handle the refusal.

```python
from constitutional_aiops import ConstitutionalRefusal

for action in client.pending_actions().get("items", []):
    try:
        client.approve_action(action["id"], approved=True, approved_by="me")
        print("approved", action["id"])
    except ConstitutionalRefusal as r:
        print("gate held", action["id"], r.error_code)
```

```ts
import { ConstitutionalRefusal } from '@constitutional-aiops/sdk'

const pending = await client.pendingActions()
for (const action of (pending.items as any[]) ?? []) {
  try {
    await client.approveAction(action.id, { approved: true, approvedBy: 'me' })
    console.log('approved', action.id)
  } catch (e) {
    if (e instanceof ConstitutionalRefusal) console.log('gate held', action.id, e.errorCode)
    else throw e
  }
}
```

## Stream a chat turn

```python
result = client.stream_chat(
    "why is nextcloud slow?",
    on_delta=lambda t: print(t, end="", flush=True),
)
print("\n---\n", result["message"]["content"])
```

```ts
const result = await client.streamChat('why is nextcloud slow?', {
  onDelta: (t) => process.stdout.write(t),
})
console.log('\n---\n', (result.message as any)?.content)
```

## Explain a dashboard anomaly

The generative-UI `explain` endpoint takes a widget's already-computed summary and
returns a short, labelled hypothesis. It is opt-in per user and cost-fenced, and
it always returns a uniform body — so opt in once, then render whatever comes
back.

```python
# 1. Opt in (once per user).
client.set_insight_preferences(enabled=True)

# 2. Send the small computed summary the widget already shows.
payload = {"count": 3, "top": [
    {"series": "cpu_seconds", "value": 0.97, "z": 4.2, "direction": "high"},
]}
res = client.explain("anomaly", payload)          # tier defaults to "fast"

# 3. Render. `available` is false for every non-spend outcome.
if res["available"]:
    print(res["explanation"])   # model_generated hypothesis, not measured telemetry
else:
    print("no explanation:", res["reason"])   # e.g. no_endpoint, budget_reached
```

```ts
await client.setInsightPreferences({ enabled: true })

const payload = {
  count: 3,
  top: [{ series: 'cpu_seconds', value: 0.97, z: 4.2, direction: 'high' }],
}
const res = await client.explain('anomaly', payload)
if (res.available) console.log(res.explanation)
else console.log('no explanation:', res.reason)
```

The heavier reads (a whole incident, the episodic graph) use the reasoning tier:

```python
res = client.explain("incident", incident_summary, tier="reasoning")
```

See the [reference](/guide/sdk#generative-ui) for every `kind`, tier, and
`reason`, and the [Generative UI feature page](/features/generative-ui) for the
honesty contract.

## Resolve a chat-proposed remediation

When a chat turn proposes an action (approve/auto mode), it returns a
`proposed_action`. Resolve it with `decide_chat_action` — distinct from the
`/actions` queue, and still gated.

```python
reply = client.chat("nextcloud is throwing 500s, can you fix it?")
proposed = reply.get("proposed_action")
if proposed:
    outcome = client.decide_chat_action(proposed["id"], approved=True, comment="go ahead")
    print(outcome["status"])   # executed | refused | rejected
```

```ts
const reply = await client.chat('nextcloud is throwing 500s, can you fix it?')
const proposed = reply.proposed_action as any
if (proposed) {
  const outcome = await client.decideChatAction(proposed.id, { approved: true, comment: 'go ahead' })
  console.log(outcome.status)
}
```

## Inspect and call a tool

```python
for t in client.tools().get("tools", []):
    print(t["name"], t["category"], "enabled" if t["enabled"] else f"gated by {t['gated_by']}")

res = client.call_tool("find_similar", {"title": "database connection timeout", "limit": 5})
if res["success"]:
    print(res["data"]["similar_incidents"])
else:
    print("refused:", res["error_code"])   # e.g. action_tools_disabled, approval_required
```

```ts
const listing = await client.tools()
for (const t of (listing.tools as any[]) ?? []) console.log(t.name, t.category)

const res = await client.callTool('find_similar', { title: 'database connection timeout', limit: 5 })
if (res.success) console.log((res.data as any).similar_incidents)
else console.log('refused:', res.error_code)
```

## Filter and paginate anything

`paginate` works with any list endpoint on the standard envelope; extra keyword /
object filters pass straight through as query parameters.

```python
recent = client.audit_events(limit=20, event_type="action.executed")
for event in client.paginate("/actions/", status="pending"):
    ...
```

```ts
const recent = await client.auditEvents({ limit: 20, event_type: 'action.executed' })
for await (const action of client.paginate('/actions/', { status: 'pending' })) {
  // ...
}
```

## Make transient failures self-heal

Opt into retries. A `429` is retried on any method; `5xx` and network errors are
retried on GET only, so a write is never silently resent. `Retry-After` is honored.

```python
client = AIOpsClient(url, token=tok, max_retries=3, backoff=0.5)
```

```ts
const client = new AIOpsClient({ baseUrl: url, token: tok, maxRetries: 3, backoffMs: 500 })
```

## Drop to the typed core

When you want full types over a path the ergonomic client does not wrap:

```python
from constitutional_aiops_client import AuthenticatedClient
from constitutional_aiops_client.api.insights import insights_explain
# install with: pip install "constitutional-aiops[typed]"
```

```ts
import { createTypedClient } from '@constitutional-aiops/sdk'

const api = createTypedClient({ baseUrl: url, token: tok })
const { data } = await api.POST('/api/v1/insights/explain', {
  body: { kind: 'anomaly', tier: 'fast', payload: { count: 1 } },
})
```

Or use the generic escape hatch on the ergonomic client:
`client.request("GET", "/telemetry/traces", params={"service": "backend"})`.
