---
title: Generative UI
outline: deep
---

# Generative UI

Constitutional AIOps has a generative UI layer, but it is built on an honesty
rule that is worth stating up front: **nothing generated or AI-assisted is ever
presented as measured telemetry.** Anything a model produced is labelled as such.
Anything computed from your real data is computed on your machine and shown as a
fact. The two never blur together.

There are two distinct layers, and they behave very differently.

![Event-driven widgets on the dashboard](/screenshots/dashboard.png)

## Layer 1: computed widgets (no LLM)

These widgets live on the [Dashboard](/features/dashboard). They are event
driven and client computed. They read the same real telemetry the rest of the
app uses, derive a view in the browser, and never call a model. That means they
work with no LLM endpoint configured at all, they cost nothing per view, and they
render instantly.

Each one degrades to an honest empty state when it has no data, rather than
showing a plausible-looking placeholder.

- **Blast-Radius Preview**: for a proposed or active change, the services and
  dependencies it could touch. Answers "what does this affect" before an action
  runs.
- **What-Changed Diff**: a compact diff of what moved between two points in
  time, so a shift in state is visible without reading raw logs.
- **Anomaly Scan**: a statistical pass over the current series. It flags points
  by z-score and direction (unusually high or low). This is arithmetic on your
  numbers, not a model opinion.
- **Live Incident Narrative**: a running, plain-language account of an incident
  assembled from the event stream as events arrive.
- **Learned Runbook**: the steps that resolved similar incidents before,
  surfaced from prior activity so a known fix is one glance away.
- **Constitutional Approval Ticker**: the actions currently waiting on a human
  decision, drawn straight from the authorization queue.
- **Recent Activity**: the newest-first log of what the system actually did.

::: info Why "no LLM" matters
These widgets are the reason the app is useful before you connect an endpoint,
and the reason they never surprise you with a bill. They are pure functions over
real data, unit-tested without a network or a model.
:::

## Layer 2: LLM insight widgets (opt-in, cost-fenced)

Some widgets can go one step further and ask a model to explain what they are
showing. This is the only place the UI calls an LLM on your behalf from a widget,
and it is deliberately fenced:

- **It computes first, explains second.** The widget derives its full view
  without a model. The model is only ever asked to explain an already-computed
  result.
- **It is opt-in per user.** The "Explain" button appears only if you turned on
  AI widgets in [Settings](/features/settings). A user who never opts in never
  sees an explain button, and a failed preference fetch degrades to off, so a
  button is never shown that the app cannot back.
- **It never fires on mount.** The model is called only when you click "Explain".
  Nothing is spent just by loading the page.
- **The payload is bounded.** A widget caps what it sends. The Anomaly Scan, for
  example, sends only the strongest few flagged points, so a noisy scan cannot
  drive a huge prompt. The server truncates as well.
- **It defaults to the fast tier** to keep each explanation cheap.
- **It is labelled.** An explanation carries an honesty chip that says it is
  model-generated, not measured telemetry.

### The "Explain" flow

1. Turn on AI widgets in [Settings](/features/settings). This writes a per-user
   preference (`enabled`, and optionally `autoExplain`).
2. On a supported widget, click **Explain**.
3. The widget sends its small, bounded payload to the opt-in `/insights/explain`
   endpoint.
4. You get a short, plain-language reading of the computed result, clearly marked
   as model-generated.

### Degrade contract

The insight layer is designed to never break the computed view underneath it:

- **No endpoint configured**: you keep the rule-based computed view. The explain
  button simply is not offered.
- **Rate limited (429)**: you see a brief notice and stay on the computed view.
  Nothing is lost.
- **Preference fetch fails**: AI widgets resolve to off.

In every failure case the honest, computed widget is still there. The LLM layer
is additive, never load-bearing.

## In-browser local chat (WebLLM)

For a fully client-side option, the app can run a small model entirely in your
browser through WebLLM.

![The assistant](/screenshots/chat.png)

- It loads through a dynamic import, so the large WASM and engine payload never
  enters the main bundle and is fetched only the first time you load a local
  model.
- Inference runs on your own device via WebGPU. Model weights download to your
  browser cache.
- **Nothing is sent to our servers.** This is the most private way to try the
  assistant, at the cost of running a deliberately small model.

Open it from the local-chat route, or from the [Chat](/features/chat) page's
local option. The curated model list is intentionally tiny, ordered
smallest and fastest first, because large models are impractical in a browser
tab.

## Command palette

Press <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>K</kbd> anywhere to open the command
palette. It is a zero-dependency fuzzy quick-nav over the app's own routes: type
a few characters, get a ranked list, press Enter to go. An exact title match
beats a prefix, which beats a substring, which beats a scattered subsequence. An
empty query lists every command in order, so it doubles as a "browse all" view.

## The honesty contract, in one place

| Element | Source | How it is labelled |
| --- | --- | --- |
| Computed widgets | Your real telemetry, in-browser | Shown as fact |
| Anomaly z-scores | Arithmetic on your series | Shown as fact |
| "Explain" output | An LLM, on click, opt-in | Marked model-generated |
| Local chat | A model in your browser | Runs on your device, nothing sent to us |

If you remember one thing: the generative and AI-assisted views are labelled,
opt-in, and never dressed up as measurements.
