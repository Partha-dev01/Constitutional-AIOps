# Hostinger DNS Setup — point your domain at the AWS deployment

> **Goal:** make `https://<your-domain>` (plus `grafana.` and `ingest.` subdomains)
> resolve to the AWS VM's Elastic IP so Caddy can serve the app and auto-issue
> Let's Encrypt TLS certificates.
>
> **Target IP (Elastic IP, fixed):** `44.195.172.165`
>
> Do these steps **before** Gate 6 (Domain + TLS). DNS first, then we enable Caddy.

---

## 0. Decide your hostnames

The deployment uses one apex + two subdomains (all pointing at the same IP; Caddy
routes them by hostname):

| Hostname | Serves | Example |
|---|---|---|
| `@` (apex / root) | The app (frontend + API) | `aiops.example.com` |
| `grafana` | Grafana dashboards | `grafana.aiops.example.com` |
| `ingest` | Telemetry intake (logs/metrics/traces from your remote agent) | `ingest.aiops.example.com` |

If you'd rather keep the app on a subdomain (e.g. `app.`) instead of the apex,
that's fine — just tell me the exact names and I'll match the Caddyfile to them.

---

## 1. Open the Hostinger DNS editor

1. Log in to **hPanel** (https://hpanel.hostinger.com).
2. Top menu → **Domains** → click **Manage** on your domain.
3. Left sidebar → **DNS / Nameservers** → **DNS records** tab.

> **Important:** this only works if the domain uses **Hostinger's nameservers**
> (`ns1.dns-parking.com` / `ns2.dns-parking.com`, shown on the *Nameservers* tab).
> If you've pointed the domain at Cloudflare or another DNS provider, add the same
> A-records there instead — Hostinger's editor won't control DNS in that case.

---

## 2. Add the A records

In **DNS records**, add three **A** records (Type = `A`, Points to = `44.195.172.165`):

| Type | Name (Host) | Points to | TTL |
|---|---|---|---|
| A | `@` | `44.195.172.165` | 300 |
| A | `grafana` | `44.195.172.165` | 300 |
| A | `ingest` | `44.195.172.165` | 300 |

Steps for each:
1. Set **Type** = `A`.
2. **Name**: type `@` for the root, or `grafana` / `ingest` for the subdomains
   (Hostinger auto-appends your domain — do **not** type the full
   `grafana.example.com`, just `grafana`).
3. **Points to / Content**: `44.195.172.165`
4. **TTL**: `300` (5 min — keeps changes fast while we set up; you can raise it to
   `3600`+ later).
5. Click **Add Record**. Repeat for all three.

### Clean up conflicts
- If an existing **A record for `@`** already exists (Hostinger parking page), **edit
  it** to `44.195.172.165` rather than adding a duplicate.
- Remove any **AAAA** (IPv6) record for these names — the VM has no IPv6, and a
  stray AAAA makes browsers/Let's Encrypt try IPv6 first and fail.
- A `CNAME` for `www` is optional; if you want `www`, add `CNAME www → @`.

---

## 3. (Optional) www and email

- **www:** add `CNAME` Name=`www`, Target=`@` (or your apex) if you want
  `www.<domain>` to work.
- **Email (MX):** leave any existing **MX** / Hostinger email records **untouched** —
  the A-records above don't affect email.

---

## 4. Wait for propagation, then verify

TTL 300 usually propagates in a few minutes (can take up to ~30 min globally).

Verify from your machine (PowerShell):

```powershell
nslookup aiops.example.com
nslookup grafana.aiops.example.com
nslookup ingest.aiops.example.com
```

Each must return **`44.195.172.165`**. (Replace with your real domain.)

Or check globally: https://dnschecker.org — search your domain, Type `A`, confirm
`44.195.172.165` appears in most regions.

---

## 5. What I do next (Gate 6 — on the AWS side)

Once the three names resolve to `44.195.172.165`, I enable Caddy on the VM. Caddy
then automatically requests Let's Encrypt certificates over the HTTP-01 challenge.

For that challenge to succeed, the VM's security group must allow inbound **80**
and **443** from anywhere (`0.0.0.0/0`). The Gate 5 Terraform / `aws/setup-sg.sh`
change opens exactly those two ports (the model/telemetry ports stay private — they
are reachable only through Caddy on 443). **You don't need to touch AWS** — I handle
the security-group + Caddy side; you only do the DNS records above.

---

## Quick checklist

- [ ] Domain uses Hostinger nameservers (or you'll add these records at your real DNS host)
- [ ] A record `@` → `44.195.172.165`
- [ ] A record `grafana` → `44.195.172.165`
- [ ] A record `ingest` → `44.195.172.165`
- [ ] No stray `AAAA` records on those names
- [ ] `nslookup` returns the EIP for all three
- [ ] Tell me the final domain so I bake it into the Caddyfile + CORS

---

_Once DNS resolves, send me the domain name and I'll wire it into the Caddyfile,
CORS origins, and the remote-monitoring ingest host._
