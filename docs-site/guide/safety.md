# Constitutional Safety

Every proposed action passes a constitutional validator before it can run. The
validator scores the action, and an authorization matrix decides what happens
next. This is the core safety property of the system.

![The Constitutional AI thresholds in Settings](/screenshots/settings.png)

These thresholds live under
[Settings → Constitutional AI](/features/settings#constitutional-ai). The
sliders you see there map directly onto the table below.

## Authorization matrix

| Confidence | Action | Human review |
|------------|--------|--------------|
| Above 90% | Automatic | Audit only |
| 70% to 90% | Approval required | A human must approve |
| Below 70% | Alert only | Notify, do not act |

The two thresholds are configurable with `CONFIDENCE_THRESHOLD_AUTO` (default
0.90) and `CONFIDENCE_THRESHOLD_APPROVAL` (default 0.70). See
[Configuration](/guide/configuration).

## Who may approve and run

The matrix above decides **whether** a human has to approve. Your role decides
**who** that human can be. Approving an action, executing an approved one, and
remediating, deleting or dismissing an incident all require the **admin** role,
not merely a signed-in session. Updating an incident's triage notes or assignee
does not. The full table is under
[Who can do what](/guide/configuration#who-can-do-what).

The approval recorded against an action is taken from the authenticated session,
so the audit trail names the account that actually clicked Approve. A caller
cannot label the approval with someone else's name.

## The gate cannot be waived by the caller

The approval flag the validator reads is derived by the server from a real
approval record. It is not something a client can assert.

This matters because the tool endpoint accepts a `context` object, and callers
may legitimately pass hints through it. Every key the validator itself reads is
stripped from that object before it reaches the validator, so a request that
claims its action was already approved gets the full principle check anyway.
Remediation started from inside the app keeps working, because it builds that
context from the approval record rather than from a request body.

The same holds for an action a model proposes during a chat turn. Nothing on
that path asserts prior approval, so a model steered by adversarial text in your
telemetry still meets the gate rather than going around it.

## Confidence score

Confidence combines the model's own confidence, the historical success rate of
the action, and its similarity to past incidents:

```
C(a) = 0.4 · C_LLM + 0.35 · C_hist + 0.25 · C_sim
```

![Confidence score on an incident](/screenshots/incidents.png)

[Incidents](/features/incidents#how-confidence-connects-to-action) shows this
score in practice: a high-confidence, low-risk analysis can move forward on
its own, and an uncertain one waits for you.

## The twelve principles

Principles are grouped into three tiers by how strictly they are enforced.

### Tier 1, safety-critical (never violate)

- **P1.1 Data protection.** No data deletion without confirmation.
- **P1.2 Active incident safety.** Maintain a minimum of healthy replicas.
- **P1.3 Cascade prevention.** No action that affects too many services at once.
- **P1.4 Security integrity.** All actions reversible within a short window.

### Tier 2, operational (require approval to violate)

- **P2.1 Minimal intervention.** Prefer the smallest effective change.
- **P2.2 Evidence-based actions.** Decisions must be grounded in evidence.
- **P2.3 Audit trail.** Every action is recorded.
- **P2.4 Uncertainty escalation.** Prefer graceful degradation over shutdown.

### Tier 3, learning (soft guidelines)

- **P3.1 Outcome tracking.** Attribute outcomes to the actions that caused them.
- **P3.2 Failure analysis.** Analyze failures systematically.
- **P3.3 Pattern reinforcement.** Reinforce successful patterns.
- **P3.4 Solution diversity.** Keep a diverse set of solutions.

## Remediation is opt-in

Restart and scale remediation is off by default (`AIOPS_ENABLE_ACTION_TOOLS`).
Even when enabled, an action still passes the validator and the authorization
matrix, and uncertain actions queue for human approval rather than running. This
means turning tools on does not turn off the safety gate.

## Related

- [MCP tools](/features/mcp#the-constitutional-gate-over-action-tools) shows
  this gate applied to a real tool call, step by step.
- [Settings](/features/settings#constitutional-ai) is where you tune the
  thresholds and toggles above.
- [Incidents and RCA](/features/incidents) is where the confidence score
  shows up per incident.
