# Configuration

All configuration is environment-driven. Copy `.env.example` to `.env` and set
what you need. The most important values are the LLM endpoint (see
[Bring Your Own Endpoint](/guide/bring-your-own-endpoint)).

![The settings page](/screenshots/settings.png)

Most of the values below are also editable live in the running app under
**Settings**. This page is the environment-variable source of truth used at
boot. Settings is the day-to-day way to change the same values afterward,
usually with no restart needed. The screenshot above shows the Constitutional
AI tab, where `CONFIDENCE_THRESHOLD_AUTO` and `CONFIDENCE_THRESHOLD_APPROVAL`
below become the Automatic Action Threshold and Approval Required Threshold
sliders.

## Environment reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_AGENT_URL` | `http://localhost:8000/v1` | Fast-agent OpenAI-compatible base |
| `REASONING_AGENT_URL` | `http://localhost:8001/v1` | Reasoning-agent base (may equal the fast URL) |
| `FAST_AGENT_MODEL` | `qwen3-4b` | Fast-agent model name |
| `REASONING_AGENT_MODEL` | `qwen3-14b` | Reasoning-agent model name |
| `LLM_API_KEY` | unset | Shared bearer token for a secured endpoint. Empty means no `Authorization` header |
| `FAST_AGENT_API_KEY` | falls back to `LLM_API_KEY` | Per-agent bearer override for the fast endpoint |
| `REASONING_AGENT_API_KEY` | falls back to `LLM_API_KEY` | Per-agent bearer override for the reasoning endpoint |
| `AUTH_REQUIRED` | `false` | Gate the app behind the built-in session login |
| `WS_TOKEN` | unset | Required when `ENVIRONMENT=production`. Guards the `/ws` websocket |
| `APP_DOMAIN` | unset | Domain for the Caddy `edge` profile |
| `ACME_EMAIL` | `admin@example.com` | Let's Encrypt contact for the `edge` profile |
| `PUBLIC_API_URL` | `http://localhost:8000/api/v1` | SPA build-time API base. Set to `/api/v1` for same-origin edge |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI (full stack only; lite falls back to in-memory) |
| `NEO4J_PASSWORD` | required in production | Neo4j password (a dummy is fine on lite, no server runs) |
| `CONFIDENCE_THRESHOLD_AUTO` | `0.90` | Auto-approve threshold |
| `CONFIDENCE_THRESHOLD_APPROVAL` | `0.70` | Require-approval threshold |

## Configuration and the UI

Most rows in the table above have a live counterpart in
[Settings](/features/settings): thresholds, remediation mode, notification
channels, and the LLM endpoint itself are all editable there, and most
changes apply without a restart.

One thing has no environment variable at all: the per-user AI-widgets
opt-in. The [Dashboard](/features/dashboard) ships with computed widgets
(Blast-Radius Preview, Anomaly Scan, and others) that read your real
telemetry in the browser and never call a model. A separate, opt-in layer
lets a widget ask an LLM to explain a result it already computed. That layer
is cost-fenced and always labelled as model-generated, never shown as
measured telemetry. The opt-in toggle lives under **Settings, Account**, per
user, not in `.env`. See [Generative UI](/features/generative-ui) for the
full explanation of both layers and [Settings](/features/settings) for where
to toggle it.

## Authentication

Set `AUTH_REQUIRED=true` to gate the app behind the built-in session login, then
set `AUTH_ADMIN_USER`, `AUTH_ADMIN_PASSWORD`, and `AUTH_SECRET_KEY`. When
`ENVIRONMENT=production` you must also set `WS_TOKEN`, which guards the
websocket. The admin credentials seed only on an empty users table.

## Action tools (remediation)

Restart and scale remediation is off by default and fail-closed. Turn it on only
when you understand the blast radius.

| Variable | Default | Description |
|----------|---------|-------------|
| `AIOPS_ENABLE_ACTION_TOOLS` | `false` | Master kill-switch for restart and scale |
| `AIOPS_ACTION_CONTAINER_WHITELIST` | empty | Extra containers beyond the default whitelist |

Even with tools enabled, actions pass the constitutional gate and the
authorization matrix before anything runs. See
[Constitutional Safety](/guide/safety). [MCP tools](/features/mcp) lists
these same two tools and shows the gate they pass through, live.

## Public self-service signup (hosted demo only)

Off by default. A self-host deployment keeps user creation admin-only. Turn this
on only on a hosted demo instance. The abuse controls (captcha, email
verification) are all optional. With none set, signup still enforces the
password policy and a per-IP rate limit.

| Variable | Default | Description |
|----------|---------|-------------|
| `AIOPS_ENABLE_PUBLIC_SIGNUP` | `false` | Master flag. When true, the signup route creates `role=user` accounts. Leave false for self-host |
| `SIGNUP_CAPTCHA_PROVIDER` | unset | `turnstile` or `hcaptcha`. Unset disables captcha |
| `SIGNUP_CAPTCHA_SITE_KEY` | unset | Public site key rendered by the SPA widget |
| `SIGNUP_CAPTCHA_SECRET` | unset | Server secret for siteverify. If a provider is set but this is empty, signup fails closed |
| `SIGNUP_SMTP_HOST` / `SIGNUP_SMTP_PORT` | unset / `587` | SMTP relay for the verification email. Unset means the link is logged, not mailed |
| `SIGNUP_EMAIL_FROM` | `no-reply@localhost` | From address on the verification email |
| `PUBLIC_BASE_URL` | unset | Base URL used to build the verification link |
