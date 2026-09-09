---
title: Infrastructure
outline: deep
---

# Infrastructure

The Infrastructure page shows the Docker containers this stack can see, lets
you pick which ones to monitor, and walks you through wiring up a remote
Linux host so its containers show up here too.

![The infrastructure page](/screenshots/infrastructure.png)

## What you see

- **Container stats**: total, healthy, and unhealthy counts across whatever is
  currently monitored.
- **Docker Containers list**, split into two groups: platform containers (the
  `aiops-*` stack itself: frontend, backend, Neo4j, Loki, Prometheus, Tempo,
  Grafana, the OTel collector) and other local containers (anything else on
  the host, including `nextcloud` if it is running). Each row shows health,
  status, port, and image, and you can select rows with a checkbox.
- **Monitored remote hosts**, a list of any Linux host running a Grafana
  Alloy edge agent that ships telemetry here. Each entry shows up/down/unknown
  status, how many Prometheus scrape targets are up, recent log line count
  over the last 15 minutes, and when it was last seen.
- **Monitor a Remote Host**, a guided onboarding block: ingest endpoint URLs
  (Loki push, Prometheus remote-write, OTLP), an agent configuration form
  (edge label, ingest user, ingest password), a generated `.env` block you can
  copy, a Docker Compose quickstart for the remote host, and a verify step
  that checks whether telemetry tagged with your edge label has arrived.
- **Demo / Chaos** panel, only shown when the backend's demo agent is
  reachable and enabled: fault-injection scenarios you can start and heal
  against a demo target, plus a field to set that target's URL.

## How to use it

1. **Select containers** in the Docker Containers list, then click **Start
   Monitoring**. This adds them to the backend's monitored set and (if the
   Fast Agent is available) processes their recent log lines through it.
2. **Stop monitoring** a container from its row's `X` button next to the
   "Monitoring" badge.
3. **Refresh** to re-pull both the container list and remote hosts from the
   backend.
4. **Onboard a remote host**: set a domain if the default (your current
   origin) is wrong, fill in an edge label and ingest credentials, copy the
   generated `.env`, and run the quickstart commands on the remote Linux
   host.
5. **Verify telemetry arrived** with the Check Now button, which queries
   `/api/v1/telemetry/logs` filtered by your edge label. You can also open
   Grafana directly and run the LogQL/PromQL checks shown.
6. **Dismiss a remote host** you no longer want listed with its trash-can
   button. This does not delete telemetry: it only hides the label until you
   restore it, and it reappears if the host keeps shipping data.

## The remote-host list is derived, not managed

Monitored remote hosts are not something you register by hand. The backend
queries Prometheus for `count by (edge) (up)` and Loki for recent log volume
per `edge` label, and any label it finds becomes a row. Dismissing a host
adds its label to a persisted denylist rather than touching telemetry, so a
host that keeps sending data resurfaces once you restore it.

## Local vs remote containers

The Docker Containers list only shows what the backend's own Docker socket
can see: this stack's platform containers, plus anything else running on the
same host. It cannot see containers on a different machine. That is what the
remote-host onboarding flow is for: it is Linux-only (the agent bind-mounts
the Docker socket), so a Windows laptop cannot host it.

::: info Docker socket required
If the backend has no access to a Docker socket, the containers list comes
back empty rather than showing a fabricated roster of services that may not
even be deployed.
:::

## Demo / Chaos

This panel injects and heals faults against a separate demo target (a
`nextcloud` / `nextcloud-db` pair by default) so you can watch the AI
diagnose and remediate something concrete. It needs a reachable demo agent
and is disabled outright on lite and bring-your-own-endpoint deployments,
where the backend returns 403 and the panel does not render at all.

## Related

- [MCP tools](/features/mcp) lists `list_containers`, `restart_service`, and
  `scale_service` as callable tools with the same constitutional gate.
- [Metrics](/features/metrics) and [Telemetry](/features/telemetry) show what
  a monitored container or remote host actually reports.
- [Guide: Self-hosting](/guide/self-hosting) covers running this stack
  yourself, including the Docker socket mount this page depends on.
