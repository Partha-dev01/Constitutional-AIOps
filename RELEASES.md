# Release notes

Operator-facing release notes for Constitutional AIOps. This is the summary you
read to decide whether to upgrade. For the exact commits see the Git history and
the GitHub Releases page.

Versions follow the `frontend/package.json` version. Dates are the merge date.

## Unreleased

Maintenance, plus a correctness fix to the Tier-1 safety gate. Six places where
two things were supposed to agree and nothing checked that they did.

### Security

- **The Tier-1 safety gate matched action names by substring, and now matches by
  word.** A Tier-1 violation blocks an action outright, with no approval path,
  so a mis-match was consequential in both directions. `"acl"` is a substring of
  `"oracle"`, so a read-only `analyze_oracle_logs` was blocked as a security
  configuration change; `"delete"` is a substring of `"undelete"`, so a restore
  was blocked as data loss. In the other direction the vocabulary was four
  English words per principle, so `purge_index` or `wipe_volume` were not
  recognised as destructive at all. Classification now happens once, on word
  tokens, in `src/constitutional/action_semantics.py`.
- **Reading security configuration is no longer treated as changing it.** P1.4
  is "never *modify* security configurations", but any name containing a
  security word matched, so `get_certificate_expiry` was blocked. A violation
  now needs a security term **and** a verb that is not a known read. Unknown
  verbs still count as modifications, so the default stays closed.
- **Two more Tier-1 principles were inert on every real action name.** P1.2
  (active incident safety) and P1.3 (cascade prevention) compared the action
  name for *exact equality* against `["restart", "deploy", "scale_down"]` and
  `["scale_up", "spawn", "fork"]`. Nothing in the system is named that way: every
  action type and every tool name is a compound, so an unapproved
  `restart_service`, `kill_process`, `rollback` or `block_ip` during an active
  incident passed the check untouched. `scale_down` and `scale_up` matched the
  literals, which is why the checks looked alive. Both principles now use the
  same word-token classification as P1.1 and P1.4.
- **Breaking, and the reason the above is safe to ship: a destructive action
  proposed during an active incident is now queued for approval instead of
  being rejected.** P1.2's own text ends "without explicit approval", and the
  gate has always cleared it for an approved remediation. But a newly proposed
  action has no approval yet by definition, so P1.2 fired, Tier 1 failed, and
  the action was marked REJECTED, which the approval endpoint refuses to act on.
  The approval the principle asked for was unreachable. `POST /actions` now
  routes a violation that is **only** P1.2 to `awaiting_approval`. Every other
  Tier-1 violation, and any combination involving one, still blocks outright.
  If you have tooling that treats `rejected` as the terminal state for incident
  remediations, it will now see `awaiting_approval` instead.
- None of the nine shipped tools change behaviour; two tests assert that, one
  against an empty context and one against the context a live approved
  remediation actually carries.

### Added

- **The published safety documentation now matches the code.** Six of the twelve
  constitutional principles were described wrongly on the docs site and in this
  repository's README, including three of the four Tier-1 safety-critical ones.
  P1.4 was published as "all actions reversible within a short window" when the
  implemented principle is "never modify security configurations without
  explicit approval". `tests/test_principles_docs.py` now fails if the published
  list drifts from `src/constitutional/principles.py` again.
- **The in-app guide links to the full documentation.** `Help & Docs` inside the
  app is a condensed mirror, and it offered no way through to the published
  documentation site, so a reader who wanted the complete guides, tutorials,
  configuration reference or SDK docs had to go and find them. There is now a
  link to them at the top of the page. The marketing site and the app read the
  same URL, and a test holds the two to each other.

### Fixed

- **The documentation site advertised v1.0.0 through the whole v1.1.0 release.**
  The version label in the docs navigation was the one version surface not tied
  to `src/version.py`, so the release bump passed it by. `tests/test_version.py`
  now covers it, along with the OpenAPI snapshot's `info.version` and the app's
  what's-new marker, which were also unguarded.
- **`RateLimited` now tells you when to retry.** v1.1.0 added per-caller hourly
  windows that answer `429` with a `Retry-After` header, but both SDKs read that
  header only for their own optional backoff and dropped it before raising. It
  is now on the error as `retry_after` / `retryAfter`, in seconds.
- **`CONSTITUTIONAL_CODES` is exported from the Python SDK**, matching
  TypeScript, so a caller can test a refusal against the canonical list instead
  of hardcoding the string. The Python `execute_action` docstring now also
  states the admin requirement its TypeScript twin already documented.

### Changed

- **The wake Lambda can read its Hostinger API token from AWS SSM.** Set
  `HOSTINGER_TOKEN_SSM_PARAM` to the name of a SecureString parameter and the
  token is fetched from there, decrypted, and cached for the life of the
  execution context, instead of sitting in plaintext in the function's
  environment. `HOSTINGER_API_TOKEN` still works and is used when the parameter
  is unset or unreadable, so this changes nothing for an existing deployment
  until you opt in. If neither is available the DNS sync is skipped and logged,
  exactly as before, rather than failing the wake.
- **The two SDK clients are now held to each other in CI.** `sdk-drift` checked
  each generated core against the API schema, but nothing compared the two
  hand-written clients, and only the Python one has a test suite. A new `parity`
  job reads both with real parsers and fails if a method, an error class or a
  shared server vocabulary list reaches one client and not the other.
- **The documentation site builds on VitePress 2 and Vite 8**, matching the app
  and marketing trees. VitePress 1 pins Vite 5, which is end-of-life, so four
  build-time advisories had no upgrade path while it stayed. None of them ever
  affected the published site, which is static HTML; they applied to the local
  development server. The publish workflow also installs from the lockfile now,
  so what reaches the site is the resolution CI approved.

## v1.1.0 - 2026-09-20

A security release. The headline is that the action and incident routes now
check who you are, not just that you are signed in, and that the constitutional
gate can no longer be waived by the caller it exists to constrain. It also picks
up the interface work that had accumulated on `main` since v1.0.0.

### Security

> **Breaking for API callers.** Approving, executing, remediating, deleting and
> dismissing now require an **admin** session. Any integration that performed
> those calls with a non-admin account will start receiving `403`. Grant the
> account the admin role, or move the call to an admin one. Single-user
> installs are unaffected, because the only account is already an admin.

- **The constitutional validator can no longer be overridden by the caller.**
  `POST /tools/call` accepted a request body whose `context` was merged into the
  validator's own context, so a client could send `"human_approved": true` and
  skip the approval gate entirely. The HTTP entry point now strips every key the
  validator reads before the merge. Remediation started from inside the app is
  unaffected, because it derives those values from a real approval record rather
  than from a request body.
- **Approve, execute, remediate, delete and dismiss now require an admin.** These
  five routes previously checked only that you were signed in, never who you
  were, so any account could approve and run a remediation. They are now gated on
  the admin role, consistent with the rest of the app.
- **The approver is recorded from your session.** `approved_by` in the approval
  body was free text written straight into the audit trail, so the trail could be
  made to name anyone. The field is now accepted and ignored, and the audit entry
  names the authenticated user. Both SDKs still accept the argument so existing
  code keeps working.
- **Self-service LLM endpoints are checked before they are stored.** A non-admin
  setting their own endpoint under Bring your own endpoint could point the server
  at an internal address, including cloud instance metadata. Those URLs now pass
  the same guard the webhook targets already use, which rejects loopback,
  private, link-local and reserved addresses. An **admin** setting the
  instance-wide endpoint is deliberately still allowed to use a private address,
  because a self-hosted Ollama or vLLM on localhost or a LAN is a supported
  deployment.
- **The websocket no longer carries a token in its URL.** When in-app auth is on,
  `GET /ws/token` returns an empty string and the socket accepts the session
  cookie only, so the shared secret stops appearing in query strings and proxy
  logs. With auth off, the token behaves as before, since it is the only gate
  available there.

### Added
- **Rate limits on the endpoints that cost money or change infrastructure.**
  Chat, tool calls and the action group each get a per-caller sliding window:
  120 chat requests an hour, 120 tool calls an hour, and 60 action requests an
  hour. Exceeding one returns `429` with a `Retry-After` header. The limit is
  keyed on the signed-in user where there is one and on the address otherwise,
  so a single abusive session cannot throttle everyone behind the same NAT. All
  three ceilings are tunable, see
  [Configuration](https://partha-dev01.github.io/Constitutional-AIOps/guide/configuration).
  Chat is the one that matters most on a hosted instance, since it is billed per
  token and previously had no ceiling at all.
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
- **Python dependency floors raised off versions with known advisories.** `torch`
  to 2.6.0, `transformers` to 5.10.0, `cryptography` to 48.0.1, `python-dotenv`
  to 1.2.2, and `langgraph` to 1.0.10. The `fastapi` floor disagreed between
  `pyproject.toml` and `requirements.txt` and both now say 0.109.1. Two entries
  were removed outright: `orjson`, which is never imported, and `asyncio`, which
  is the pre-3.4 standard-library backport rather than the standard library and
  would shadow it if a resolver ever picked it up.
- **Dependabot now watches all six dependency trees.** It covered three, which is
  why the frontend sat on a current toolchain while `marketing`, `docs-site` and
  `sdk/typescript` drifted.
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

See `README.md` for setup and the published
[Self-hosting](https://partha-dev01.github.io/Constitutional-AIOps/guide/self-hosting)
guide for deployment details.
