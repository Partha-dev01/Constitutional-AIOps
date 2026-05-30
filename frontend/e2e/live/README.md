# Live e2e suite

Playwright tests that run against the **live AWS deployment**
(`https://aiops.imaginaerium.in`), which is behind Caddy basic-auth + TLS.

These are intentionally separate from any mocked/CI e2e: they hit the real
backend, dual vLLM models, Neo4j, and Grafana through Caddy's path routing.

## Run

Credentials are read from the environment only (never committed). Provide the
Caddy basic-auth pair, then run headless or headed from `frontend/`:

```powershell
# PowerShell (Windows)
$env:E2E_USER = "admin"
$env:E2E_PASS = "<app-basic-auth-pass>"
npm run test:e2e:live          # headless
npm run test:e2e:live:headed   # headed
```

```bash
# bash
E2E_USER=admin E2E_PASS=<app-basic-auth-pass> npm run test:e2e:live
```

Override the target with `E2E_BASE_URL` (defaults to the production domain).

## What it covers

| Spec | Path through the stack |
|------|------------------------|
| `smoke.spec.ts` | SPA loads, all 7 routes render, health footer flips to *System Healthy* |
| `api-health.spec.ts` | `/api/v1/health` + `/ready` healthy, `/grafana` reachable, anon = 401 |
| `chat.spec.ts` | browser → Caddy → backend → ModelRouter → vLLM round-trip, thinking suppressed |

## Artifacts

HTML report → `frontend/playwright-report-live/`; traces/screenshots/video →
`frontend/test-results/live/`. Both are git-ignored.

> If the VM was idle-stopped, start it first:
> `aws ec2 start-instances --instance-ids i-091c4de0e95d63154 --region us-east-1`
> and wait ~3–4 min for vLLM warmup.
