# Quickstart — operate & test the AIOps deployment

Practical scripts + a testing ladder for the live deployment at
**https://aiops.imaginaerium.in** (AWS g6.xlarge L4, dual vLLM, Caddy TLS + basic-auth).

## Contents

| File | What it does |
|------|--------------|
| `_config.ps1` | Non-secret config (region, instance ID, domain). Sourced by the others. |
| `secrets.example.ps1` | Template for credentials → copy to `secrets.local.ps1` (gitignored). |
| `vm-start.ps1` | Start the GPU VM, wait until the app answers. |
| `vm-stop.ps1` | Stop the VM to save cost. |
| `vm-status.ps1` | Show instance state + app health. |
| `test.ps1` | Run a test layer: `smoke` / `live` / `live-headed` / `backend` / `frontend`. |
| `monitor-client/` | Monitor a container on **another (client) machine** — see its README. |

## One-time setup

```powershell
cd quickstart
Copy-Item secrets.example.ps1 secrets.local.ps1   # then edit in the real passwords
```
The live passwords are on the VM in `/mnt/aiops-repo/.env.production`. `secrets.local.ps1`
is gitignored. (Prereqs: AWS CLI configured, Node/npm for frontend+e2e, Python for backend.)

## Start / stop / check the VM (run from PowerShell)

```powershell
.\vm-start.ps1     # start + wait for health (vLLM warmup ~3-5 min)
.\vm-status.ps1    # state + health any time
.\vm-stop.ps1      # stop to stop billing (~$0.80/hr while running)
```
> Data persists on EBS; the whole stack auto-restarts on the next start. An idle-stop
> alarm also stops the VM after ~30 min of <5% CPU.

---

## The testing ladder (quickest → most thorough)

> Layers **smoke** and **live** need the VM running. **backend** and **frontend** are
> fully mocked — no VM, no GPU.

### 1. Smoke — is the live app healthy? (instant)
```powershell
.\test.ps1 smoke
```
Expect `"status":"healthy"`, `"version":"0.7.0"`, all components `true`. Or just open
https://aiops.imaginaerium.in in a browser (it prompts for the app basic-auth).

### 2. Live end-to-end (Playwright) — the real deployed site
8 tests: SPA + all 7 routes, health, Grafana reachable, auth rejection, and a full
browser→Caddy→backend→vLLM **chat round-trip** (with a thinking-suppression check).
```powershell
.\test.ps1 live          # headless
.\test.ps1 live-headed   # watch it drive a real browser
```
HTML report: `npx playwright show-report ..\frontend\playwright-report-live`.

### 3. Backend tests — mocked LLM/Neo4j, no VM/GPU
```powershell
.\test.ps1 backend       # pytest tests/ -v
```

### 4. Frontend unit + build — no VM/GPU
```powershell
.\test.ps1 frontend      # vitest + tsc/vite build
```

### 5. Edge monitoring — monitor a container on a client box
See **[monitor-client/README.md](monitor-client/README.md)**. One agent on the client
host ships all its containers' telemetry to AWS, tagged `edge=<label>`; verify in
Grafana with `{edge="<label>"}`.

---

## Suggested first run

1. `.\vm-status.ps1` — confirm it's running (start it if not).
2. `.\test.ps1 smoke` — instant confidence the deploy is alive.
3. `.\test.ps1 live-headed` — watch Playwright drive the live chat. Most satisfying proof.
4. When done for the day: `.\vm-stop.ps1`.

## Notes

- `secrets.local.ps1` holds passwords and is gitignored — keep it that way.
- `_config.ps1` contains only non-secret resource identifiers (safe to commit).
- These are operator conveniences; the authoritative test configs live in
  `../frontend/playwright.config.live.ts`, `../pyproject.toml`, and `../frontend/`.
