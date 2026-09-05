# Constitutional Safety

Every proposed action passes a constitutional validator before it can run. The
validator scores the action, and an authorization matrix decides what happens
next. This is the core safety property of the system.

## Authorization matrix

| Confidence | Action | Human review |
|------------|--------|--------------|
| Above 90% | Automatic | Audit only |
| 70% to 90% | Approval required | A human must approve |
| Below 70% | Alert only | Notify, do not act |

The two thresholds are configurable with `CONFIDENCE_THRESHOLD_AUTO` (default
0.90) and `CONFIDENCE_THRESHOLD_APPROVAL` (default 0.70). See
[Configuration](/guide/configuration).

## Confidence score

Confidence combines the model's own confidence, the historical success rate of
the action, and its similarity to past incidents:

```
C(a) = 0.4 · C_LLM + 0.35 · C_hist + 0.25 · C_sim
```

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
