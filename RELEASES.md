# Release notes

Operator-facing release notes for Constitutional AIOps. This is the summary you
read to decide whether to upgrade. For the full development log see
`docs/CHANGELOG.md`, and for the exact commits see the Git history and the
GitHub Releases page.

Versions follow the `frontend/package.json` version. Dates are the merge date.

## Unreleased

Improvements on `main` since v1.0.0, not yet cut into a tagged release.

### Added
- **Guided first-run product tour and a What's-new banner.** A fresh browser gets
  a short guided tour of the main screens on first sign-in; a returning browser
  gets a dismissible banner listing what changed since it last visited, gated on
  the app version. Both are per-browser and fail-soft, the tour is replayable any
  time from the command palette, and neither opens under browser automation.
- **Two reasoning-tier insight widgets on the Dashboard.** *Capacity forecast*
  fits a linear trend to each utilization series and estimates when it would
  reach a threshold, labelled as an extrapolation rather than a guarantee.
  *Metric correlation* surfaces the series that moved together over the last hour
  by Pearson coefficient, labelled as correlation not causation. Both compute in
  the browser with no LLM and carry the same opt-in, cost-fenced "Explain" button
  as the other insight widgets.
- **Quick-Setup "Safety" step.** The first-run wizard now has a dedicated step to
  pick the remediation mode (diagnose / approve / auto) and keep the audit log
  on, so new operators meet the constitutional safety model during setup instead
  of discovering it later in Settings.
- **Audit Log viewer (admin).** A read-only page over the action trail: every
  constitutional validation, approval, rejection and action, filterable by event
  type and time window. Admin only.
- **Benchmark "Your setup" quick-check.** Run a handful of sample cases through
  the exact agents the app uses, against the LLM endpoint you configured, to see
  a pass rate and latency without committing to a full research run. The
  Benchmark page now separates "evaluate your setup" from "reproduce the paper."
- **Webhook "Send test" button** in Settings and Notifications. Admin only and
  SSRF-guarded (it refuses non-HTTP targets and any host that resolves to a
  loopback, private, link-local or reserved address).
- **Community health docs:** CONTRIBUTING, SECURITY and CODE_OF_CONDUCT.

### Changed
- Marketing statistics now match the camera-ready paper (82.4% overall, root-cause
  analysis framed as the win over Llama-3.3-70B, preliminary vLLM speedup) and the
  hosted demo explains its sleep-when-idle cold start as a feature.
- The System Prompts and Topology Schema editors are hidden from non-admin users,
  who previously saw editors that refused to save.

### Fixed
- The Dashboard learned-runbook widget asked for more action history than the API
  returns in a single page, so the request was rejected and the widget showed
  empty on a live instance. It now requests within the page-size limit and renders
  real remediation history.
- The Dashboard insight widgets that read the last hour of metrics now share one
  request instead of each fetching the same series, so they settle together
  rather than one lagging noticeably behind the others.
- Shared-instance mutation routes (topology, prompts, settings reset, model test)
  are now admin-gated on multi-user instances (SEC-004).
- The audit-trail query no longer raises at month boundaries when reading a
  multi-day window.

## v1.0.0 - 2026-09-04

First open-source release.

### Highlights
- **Licensed AGPL-3.0** and packaged for self-hosting: clone, set a `.env`, and
  bring your own OpenAI-compatible LLM endpoint (one endpoint can serve both the
  fast and reasoning agents for a minimal setup).
- **Lite tier** that runs without a GPU or a full observability stack: read logs
  and live CPU and memory from the local Docker socket when no Loki, Prometheus
  or Tempo is configured.
- **Constitutional safety framework:** every proposed action passes twelve
  principles across three tiers, with a diagnose / approve / auto remediation
  policy and a full audit trail. Actions never execute inside the model loop;
  they queue for an explicit Approve or Reject.
- **Dual-agent architecture** (a fast annotator and a reasoning agent),
  graph-episodic memory for incident correlation, and a guided first-run setup
  wizard.
- **Hosted demo** with no login, plus a hosted app front that sleeps when idle
  and wakes on the first visit to keep running costs near zero.

See `README.md` for setup and `docs/DEPLOYMENT.md` for deployment details.
