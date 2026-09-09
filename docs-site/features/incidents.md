---
title: Incidents and RCA
outline: deep
---

# Incidents and RCA

The Incidents page is the record of what went wrong, what the reasoning agent
concluded, and how sure it was. It is where root-cause analysis lands.

![The incidents view](/screenshots/incidents.png)

## What you see

- **The incident list**, each row carrying a title, severity, status, category,
  the affected services, and tags.
- **A confidence score** on the analysis, shown as a percent. When a score is
  absent or not a number the UI shows `n/a` rather than a broken `NaN%`.
- **Filters** to narrow the list down to what you care about right now.
- **Export**, to take the currently filtered incidents out as CSV or JSON. Nested
  fields like services and tags flatten to a readable joined string.

## How to use it

1. **Filter to the incidents that matter** by severity, status, or category.
2. **Open an incident** to read the root-cause detail: what the reasoning agent
   found, the affected services, and the proposed remediation.
3. **Read the confidence** before acting. A high-confidence analysis with a
   low-risk fix can move quickly. A low-confidence one is a prompt to look
   closer, not to auto-approve.
4. **Export the filtered set** as CSV or JSON for a report or a hand-off.

## How confidence connects to action

The confidence score is not decoration. It feeds the authorization matrix from
[Constitutional Safety](/guide/safety): high-confidence low-risk actions can be
audited and proceed, uncertain ones wait for a human, and low-confidence ones
only raise an alert. So the percent you read on an incident is part of what
decides whether a remediation runs on its own or waits for you.

## Related

- [Graph Explorer](/features/graph-explorer) shows the same incidents as nodes,
  linked to their root causes, actions, and services.
- [Dashboard](/features/dashboard) surfaces the Live Incident Narrative as an
  incident unfolds.
