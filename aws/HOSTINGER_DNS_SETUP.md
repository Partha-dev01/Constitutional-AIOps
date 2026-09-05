# Hostinger DNS Setup — point example.com at the AWS deployment

> **Goal:** make `https://aiops.example.com` resolve to the AWS VM's Elastic IP
> so Caddy can serve the app and auto-issue a Let's Encrypt TLS certificate.
>
> **Domain:** `example.com` (Hostinger)
> **App hostname:** `aiops.example.com` (single subdomain, **path-based** routing)
> **Target IP (Elastic IP, fixed):** `203.0.113.10`
>
> Do this step **before** Gate 6 (Domain + TLS). DNS first, then we enable Caddy.

---

## 0. Topology (decided 2026-05-30)

The AIOps app lives on **one** subdomain. Caddy routes everything by **path** on that
single host, so there is only **one DNS record** and **one TLS certificate**:

| URL | Serves |
|---|---|
| `https://aiops.example.com/` | App UI (frontend) |
| `https://aiops.example.com/api/…` | Backend API |
| `https://aiops.example.com/grafana/` | Grafana (served from sub-path) |
| `https://aiops.example.com/ingest/…` | Telemetry intake from the remote edge agent (basic-auth) |

The apex (`@`), `www`, and your existing service records are **left untouched** —
the AIOps app is fully contained under the `aiops` subdomain.

---

## 1. Open the Hostinger DNS editor

1. Log in to **hPanel** (https://hpanel.hostinger.com).
2. Top menu → **Domains** → click **Manage** on `example.com`.
3. Left sidebar → **DNS / Nameservers** → **DNS records** tab.

> **Important:** this only works if `example.com` uses **Hostinger's nameservers**
> (`ns1.dns-parking.com` / `ns2.dns-parking.com`, shown on the *Nameservers* tab).
> If the domain is pointed at Cloudflare or another DNS provider, add the same
> A-record there instead — Hostinger's editor won't control DNS in that case.

---

## 2. Add ONE A record

Add a single **A** record:

| Type | Name (Host) | Points to / Content | TTL |
|---|---|---|---|
| A | `aiops` | `203.0.113.10` | 300 |

Steps:
1. **Type** = `A`.
2. **Name** = `aiops` (just the label — Hostinger auto-appends `.example.com`;
   do **not** type the full `aiops.example.com`).
3. **Points to / Content** = `203.0.113.10`
4. **TTL** = `300` (5 min — keeps changes fast during setup; raise to `3600`+ later).
5. Click **Add Record**.

That is the **only** record you add.

---

## 3. Do NOT touch your existing records

Your current zone already has these — **leave them all as-is** (none collide with `aiops`):

| Type | Name | Content | Why it stays |
|---|---|---|---|
| A | `@` | `203.0.113.30` | Your main site apex |
| CNAME | `www` | `example.com` | Main site www |
| A | `auditrail` | `203.0.113.20` | A different existing service (different IP) |
| CNAME | `autisense` | `d250wxbvstxrnq.cloudfront.net` | CloudFront-fronted service |
| CNAME | `_769463226f6d485c2bf375eeee3ac2be` | `…acm-validations.aws` | ACM cert validation — required, keep it |

### Only clean up if present
- Any **AAAA** (IPv6) record **named `aiops`** → delete it (the VM is IPv4-only; a
  stray AAAA makes browsers/Let's Encrypt try IPv6 first and fail).
- There is **no** existing `aiops` record, so there's nothing to overwrite — just add.

---

## 4. Wait for propagation, then verify

TTL 300 usually propagates in a few minutes (up to ~30 min globally).

Verify from your machine (PowerShell):

```powershell
nslookup aiops.example.com
```

Must return **`203.0.113.10`**.

Or check globally: https://dnschecker.org — search `aiops.example.com`, Type `A`,
confirm `203.0.113.10` appears in most regions.

---

## 5. What I do next (Gate 6 — on the AWS side)

Once `aiops.example.com` resolves to `203.0.113.10`, I enable Caddy on the VM.
Caddy then automatically requests a Let's Encrypt certificate over the HTTP-01
challenge and serves all four paths above from the one host.

For the challenge to succeed, the VM's security group must allow inbound **80** and
**443** from anywhere (`0.0.0.0/0`). The Gate 5 Terraform / SG change opens exactly
those two ports (the model ports 8000/8001 and the LGTM stores stay private — reachable
only *through* Caddy on 443). **You don't need to touch AWS** — I handle the
security-group + Caddy side; you only do the one DNS record above.

The values I'll bake into the server config at Gate 6 (for reference):

```
APP_DOMAIN     = aiops.example.com
PUBLIC_API_URL = https://aiops.example.com
CORS_ORIGINS   = https://aiops.example.com
```

And the remote edge agent (Gate 7) will push telemetry to:

```
https://aiops.example.com/ingest/loki/...    (logs)
https://aiops.example.com/ingest/prom/...    (metrics, remote-write)
https://aiops.example.com/ingest/otlp/...    (traces)
```
…all behind Caddy basic-auth + TLS.

---

## Quick checklist

- [ ] `example.com` uses Hostinger nameservers (or add the record at your real DNS host)
- [ ] A record `aiops` → `203.0.113.10` (TTL 300) added
- [ ] No stray `AAAA` record named `aiops`
- [ ] Existing records (`@`, `www`, `auditrail`, `autisense`, ACM CNAME) left untouched
- [ ] `nslookup aiops.example.com` returns `203.0.113.10`

---

_Once `aiops.example.com` resolves, tell me and I'll wire it into the Caddyfile
(path-based, Grafana sub-path), CORS origins, and the remote-monitoring ingest host
at Gate 6/7._
