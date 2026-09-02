"""
Wake-on-visit Lambda for the Constitutional AIOps LITE tier (5c WS4).

Fronts the sleep-when-idle deployment instance so there is NO fixed public IP /
Elastic IP (the ~$3.60/mo the $2-3 target avoids). Sits behind CloudFront on an
HTTP Function URL that the app domain points at.

Front-door path split (redesign R2): the always-on marketing site is served
statically from S3 as the CloudFront default behavior, and ONLY the `/launch`
behavior routes here. So plain visits and crawlers hitting `/` never reach this
Lambda and never wake the box -- only a deliberate launch does. As defense in
depth, an automated/absent User-Agent is refused here BEFORE StartInstances.

On each (human) /launch request:

  * bot / no UA        -> 403, no wake (never touches EC2).
  * stopped            -> ec2.StartInstances + a 200 auto-refreshing "waking up" page.
  * pending / stopping -> the same holding page (still transitioning).
  * running            -> point the app's DNS name at the box's CURRENT public IP,
                          then serve the holding page so its CLIENT-SIDE readiness
                          probe hands the visitor over ONLY once THIS browser can
                          actually reach the box (never a server-side 302 onto a
                          hostname whose DNS the browser has not refreshed yet).

Why the Lambda owns the DNS update: with no Elastic IP the box's public IPv4
changes on every start, so APP_URL's A record has to be re-pointed each wake.
The box's DNS is on Hostinger, which does NOT allow NS delegation of a subdomain
(so a Route53 dyn-DNS zone can't be reached publicly). Hostinger *does* allow an
A record, so this Lambda UPSERTs it directly via the Hostinger DNS REST API. The
Hostinger token lives in this Lambda's (encrypted-at-rest) environment -- never
on the internet-exposed box. This replaces the earlier box-side dyn-DNS
(aws/dyn-dns.sh), which is retired.

Pairs with aws/idle-check.sh (the "stop when idle" half). Together they give
"always reachable, sleeps when idle".

Environment:
  TARGET_INSTANCE_ID   (required)  e.g. i-0123456789abcdef0
  APP_URL              (required)  the app host the visitor is handed to once up,
                                   e.g. https://aiops-node.example.com
  HOSTINGER_API_TOKEN  (required)  Bearer token for the Hostinger DNS API
  HOSTINGER_DOMAIN     (required)  the Hostinger-managed zone, e.g. example.com
  DNS_RECORD_NAME      (required)  the subdomain record to keep current, e.g. aiops-node
  DNS_TTL              optional, default 30 (kept low so a stale cached IP clears fast)
  HOLDING_REFRESH_SEC  optional, default 8
  HOLDING_GUARANTEED_EXIT_SEC optional, default 120 (client-side last-resort nav)
  (AWS_REGION is provided by the Lambda runtime.)
"""

import json
import os
import socket
import urllib.error
import urllib.request
from urllib.parse import unquote

import boto3

_INSTANCE_ID = os.environ.get("TARGET_INSTANCE_ID", "")
_APP_URL = os.environ.get("APP_URL", "")
_REFRESH = int(os.environ.get("HOLDING_REFRESH_SEC", "8"))

_HOSTINGER_TOKEN = os.environ.get("HOSTINGER_API_TOKEN", "")
_HOSTINGER_DOMAIN = os.environ.get("HOSTINGER_DOMAIN", "")
_DNS_RECORD_NAME = os.environ.get("DNS_RECORD_NAME", "")
# Kept LOW on purpose. The box has no Elastic IP, so its public IP changes on
# every wake and the app's A record is re-pointed each time. A low TTL shrinks
# the window in which a visitor's browser/resolver still holds the previous
# (now-dead) IP -- the exact stale-cache that caused "took too long to respond"
# right after a wake.
_DNS_TTL = int(os.environ.get("DNS_TTL", "30"))
# The box is only handed off to once its web server actually accepts TLS
# connections on this port. EC2 "running" fires ~1-3 min before Caddy binds
# 443, so acting on state alone lands the visitor on a dead socket
# ("refuses to connect"). Overridable; 443 is the Caddy HTTPS listener.
_APP_READY_PORT = int(os.environ.get("APP_READY_PORT", "443"))
_APP_READY_TIMEOUT = float(os.environ.get("APP_READY_TIMEOUT", "2.5"))
# Last-resort client-side navigation. The holding page normally moves on only
# once ITS OWN probe reaches the box (so it never lands on stale DNS). If those
# probes are blocked (a corporate proxy, an ad-blocker eating cross-origin
# requests), navigate anyway once enough time has passed that every cached DNS
# entry has surely expired -- comfortably above _DNS_TTL. Guarantees an exit
# without reintroducing the stale-IP crash.
_GEXIT = int(os.environ.get("HOLDING_GUARANTEED_EXIT_SEC", "120"))

_HOSTINGER_BASE = "https://developers.hostinger.com/api/dns/v1/zones"
_HTTP_TIMEOUT = 10  # seconds per Hostinger call (Lambda timeout is 20s)
# Hostinger's WAF 403s the default "Python-urllib/*" UA, so send an explicit one.
_UA = "constitutional-aiops-wake/1.0"

# Bot / crawler filter. CloudFront routes ONLY the /launch behavior to this
# Lambda (plain marketing paths are served always-on from S3 and never reach
# here), and robots.txt disallows /launch -- but a misbehaving crawler that hits
# /launch anyway must NOT wake the box (cost + abuse control). Any request whose
# User-Agent looks automated (or is absent) is refused BEFORE StartInstances is
# ever called. Real browser clicks -- including the holding page's auto-refresh
# -- carry a normal UA and pass through untouched.
_BOT_UA_MARKERS = (
    "bot", "crawl", "spider", "slurp", "bingpreview", "facebookexternalhit",
    "embedly", "quora link preview", "pinterest", "vkshare", "w3c_validator",
    "semrush", "ahrefs", "mj12", "dotbot", "petalbot", "yandex", "duckduckbot",
    "curl", "wget", "python-requests", "python-urllib", "go-http-client",
    "java/", "okhttp", "headless", "scrapy", "httpclient",
)

_ec2 = boto3.client("ec2")

# Warm-context cache: the last IP we confirmed into DNS. While the execution
# environment is reused, a matching IP means DNS is already correct, so we skip
# the Hostinger calls entirely and just redirect. A cold start resets this to
# None and re-syncs once (idempotent). This keeps Hostinger traffic to just the
# minutes right after a wake, not every request (CloudFront caching is off).
_LAST_IP = None


def _looks_like_bot(user_agent: str) -> bool:
    """True for automated clients (or a missing UA). A genuine human clicking
    the marketing "launch" CTA always sends a normal browser UA."""
    ua = (user_agent or "").lower()
    if not ua:
        return True
    return any(marker in ua for marker in _BOT_UA_MARKERS)


def _refuse_bot() -> dict:
    """Refuse a bot on /launch WITHOUT waking the box."""
    return {
        "statusCode": 403,
        "headers": {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-store",
            "X-Robots-Tag": "noindex, nofollow",
        },
        "body": "This endpoint launches the live demo and is not available to automated clients.",
    }


def _user_agent(event) -> str:
    """Function URL (payload v2.0) lower-cases header names; be defensive anyway."""
    headers = (event or {}).get("headers") or {}
    for key, value in headers.items():
        if key.lower() == "user-agent":
            return value or ""
    return ""


def _safe_next(event) -> str:
    """A validated same-origin path to hand off to AFTER wake (e.g. /launch?next=/docs
    → land on the app's /docs). Only an absolute in-app path is allowed; anything
    with a scheme, a protocol-relative `//`, whitespace or excessive length is
    dropped so this can never become an open redirect."""
    params = (event or {}).get("queryStringParameters") or {}
    raw = params.get("next") or ""
    try:
        raw = unquote(raw)
    except Exception:  # noqa: BLE001
        return ""
    if not raw or not raw.startswith("/") or raw.startswith("//"):
        return ""
    if len(raw) > 256 or any(c in raw for c in " \t\r\n\\"):
        return ""
    return raw


# Branded "waking up" page. Readiness is decided CLIENT-SIDE: two probes (an
# <img> load and a no-cors fetch) hit APP_URL and only hand the visitor over the
# instant the box is genuinely serving AND this browser's DNS resolves to the
# live IP -- so we never land on a stale/dead socket. There is deliberately NO
# server-side 302: with no Elastic IP the app's DNS changes each wake, and a
# server bounce could send the browser to its own still-cached previous IP
# (ERR_CONNECTION_TIMED_OUT -- the reported crash). A slow full reload re-hits
# /launch to keep the DNS record fresh; a guaranteed-exit timer is the last
# resort if both probes are blocked; a <noscript> meta refresh covers no-JS.
# __APP_URL__/__TITLE__/__MSG__/__BACKSTOP__/__GEXIT__ are substituted (never an
# f-string: the CSS/JS is full of literal braces).
_HOLDING_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<noscript><meta http-equiv="refresh" content="10"></noscript>
<title>Waking Constitutional AIOps…</title>
<style>
:root{--bg:#0a0e1a;--bg2:#0d1526;--card:#111c33;--line:#1e2b45;--fg:#e8eefb;--muted:#8b97ab;--brand:#3b82f6;--brand2:#4d9fff}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{min-height:100vh;display:flex;align-items:center;justify-content:center;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);background:radial-gradient(60% 55% at 50% 28%,rgba(59,130,246,.16),transparent 70%),linear-gradient(180deg,var(--bg),var(--bg2));background-attachment:fixed}
.card{width:min(92vw,30rem);padding:2.5rem 2rem;text-align:center;background:linear-gradient(180deg,rgba(17,28,51,.9),rgba(13,21,38,.9));border:1px solid var(--line);border-radius:20px;box-shadow:0 20px 60px -20px rgba(0,0,0,.7)}
.mark{width:76px;height:76px;margin:0 auto .25rem;display:block;filter:drop-shadow(0 0 14px rgba(77,159,255,.55));animation:breathe 3.2s ease-in-out infinite}
@keyframes breathe{0%,100%{transform:scale(1);opacity:.92}50%{transform:scale(1.05);opacity:1}}
.brand{font-size:.95rem;font-weight:700;letter-spacing:.02em;margin:.25rem 0 1.5rem}.brand b{color:var(--brand2)}
.spin{width:2.75rem;height:2.75rem;margin:0 auto 1.25rem;border:3px solid rgba(255,255,255,.10);border-top-color:var(--brand2);border-radius:50%;animation:s .9s linear infinite}
@keyframes s{to{transform:rotate(360deg)}}
h1{font-size:1.35rem;margin:.2rem 0 .5rem;font-weight:650}
.msg{color:var(--muted);margin:0 0 1.25rem}
.bar{height:4px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden;margin:1.25rem 0 1rem}
.bar i{display:block;height:100%;width:35%;border-radius:99px;background:linear-gradient(90deg,transparent,var(--brand),var(--brand2),transparent);animation:slide 1.6s ease-in-out infinite}
@keyframes slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
.meta{font-size:.82rem;color:var(--muted)}.meta b{color:var(--fg);font-variant-numeric:tabular-nums}
.fine{font-size:.78rem;color:#5f6c82;margin-top:1rem}
@media (prefers-reduced-motion:reduce){.mark,.spin,.bar i{animation:none}}
</style></head>
<body><div class="card" role="status" aria-live="polite">
<svg class="mark" viewBox="0 0 64 64" fill="none" aria-hidden="true">
<path d="M32 4 56 12v18c0 15-10.4 24.3-24 30C18.4 54.3 8 45 8 30V12L32 4Z" stroke="#4d9fff" stroke-width="2.4" fill="rgba(59,130,246,.06)"/>
<circle cx="32" cy="29" r="7.5" stroke="#4d9fff" stroke-width="2.2"/>
<path d="M32 14v7M32 37v9M20 24l5 4M44 24l-5 4M18 33h7M46 33h-7" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
<circle cx="32" cy="13" r="1.8" fill="#4d9fff"/><circle cx="18" cy="23" r="1.8" fill="#4d9fff"/><circle cx="46" cy="23" r="1.8" fill="#4d9fff"/><circle cx="17" cy="33" r="1.8" fill="#4d9fff"/><circle cx="47" cy="33" r="1.8" fill="#4d9fff"/>
</svg>
<div class="brand">Constitutional <b>AIOps</b></div>
<div class="spin" aria-hidden="true"></div>
<h1 id="title">__TITLE__</h1>
<p class="msg" id="msg">__MSG__</p>
<div class="bar" aria-hidden="true"><i></i></div>
<p class="meta"><b id="elapsed">0s</b> elapsed · usually ready in 1-2 min</p>
<p class="fine">This page moves on automatically the moment the app is ready. No need to refresh.</p>
</div>
<script>
var APP_URL="__APP_URL__",TARGET="__TARGET__",GEXIT=__GEXIT__,KEY="aiops.wake.start",start;
try{start=Number(sessionStorage.getItem(KEY))||0}catch(e){start=0}
// Reset a stale start left by an abandoned earlier wake (a tab reopened much
// later, when the box may be asleep again) so the guaranteed-exit timer below
// can't fire immediately into a not-yet-woken box.
if(!start||(Date.now()-start)>900000){start=Date.now();try{sessionStorage.setItem(KEY,String(start))}catch(e){}}
var titleEl=document.getElementById("title"),msgEl=document.getElementById("msg"),elEl=document.getElementById("elapsed");
function elapsed(){return Math.max(0,Math.round((Date.now()-start)/1000))}
function tick(){var s=elapsed();elEl.textContent=s+"s";
if(s>=90){titleEl.textContent="Almost ready";msgEl.textContent="Finishing startup and health checks."}
else if(s>=30){titleEl.textContent="Loading services";msgEl.textContent="The server is up; bringing the app online."}}
tick();setInterval(tick,1000);
var done=false;
function go(){if(done)return;done=true;try{sessionStorage.removeItem(KEY)}catch(e){}location.replace(TARGET)}
// Navigate ONLY once THIS browser can actually reach the app host. Both probes
// succeed just when this client resolves the LIVE box (right cert + a listening
// server), so we never bounce onto a stale, cached, now-dead IP.
function probeImg(){if(done)return;var img=new Image();img.onload=go;img.onerror=function(){};img.src=APP_URL+"/favicon.ico?ts="+Date.now()}
function probeFetch(){if(done)return;try{fetch(APP_URL+"/favicon.ico?f="+Date.now(),{mode:"no-cors",cache:"no-store"}).then(go).catch(function(){})}catch(e){}}
function probe(){probeImg();probeFetch()}
probe();setInterval(probe,3000);
// Guaranteed exit: once every cached DNS entry has certainly expired, navigate
// even if the probes were blocked. GEXIT is well above the DNS TTL.
setInterval(function(){if(!done&&elapsed()>=GEXIT)go()},2000);
// Backstop full reload re-hits /launch so the Lambda keeps the DNS record
// current while we wait; it never navigates to the box itself.
setTimeout(function(){if(!done)location.reload()},__BACKSTOP__000);
</script></body></html>"""


def _holding_page(title: str, message: str, next_path: str = "") -> dict:
    html = (
        _HOLDING_TEMPLATE
        .replace("__APP_URL__", _APP_URL)  # base host — the favicon readiness probe
        .replace("__TARGET__", _APP_URL + next_path)  # where the visitor lands
        .replace("__TITLE__", title)
        .replace("__MSG__", message)
        .replace("__GEXIT__", str(_GEXIT))  # client-side last-resort navigation
        # Backstop full reload re-hits /launch to keep DNS current while waiting.
        # Kept well above the 3s probe cadence so it is rare.
        .replace("__BACKSTOP__", str(max(15, _REFRESH * 3)))
    )
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"},
        "body": html,
    }


def _hostinger_upsert_a(ip: str) -> None:
    """UPSERT _DNS_RECORD_NAME A -> ip. overwrite=true replaces only this
    name+type (other records in the shared zone are untouched)."""
    body = json.dumps({
        "overwrite": True,
        "zone": [{
            "name": _DNS_RECORD_NAME,
            "type": "A",
            "ttl": _DNS_TTL,
            "records": [{"content": ip}],
        }],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{_HOSTINGER_BASE}/{_HOSTINGER_DOMAIN}",
        data=body,
        headers={
            "Authorization": f"Bearer {_HOSTINGER_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _UA,
        },
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        resp.read()


def _sync_dns(ip: str) -> bool:
    """Ensure the Hostinger A record points at ip. Returns True when the record
    is (now) set, False on any error. The warm-context cache skips Hostinger
    entirely once an IP is confirmed for this execution context; otherwise a
    single idempotent UPSERT (overwrite) sets it -- no read round-trip."""
    global _LAST_IP
    if ip == _LAST_IP:
        return True
    if not (_HOSTINGER_TOKEN and _HOSTINGER_DOMAIN and _DNS_RECORD_NAME):
        print("dns: Hostinger env not fully configured; skipping DNS sync")
        return False
    try:
        _hostinger_upsert_a(ip)
        _LAST_IP = ip
        print(f"dns: {_DNS_RECORD_NAME}.{_HOSTINGER_DOMAIN} A -> {ip}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"dns: update failed for {_DNS_RECORD_NAME}.{_HOSTINGER_DOMAIN}: {exc}")
        return False


def _app_is_ready(ip: str) -> bool:
    """True once the box's web server accepts connections on _APP_READY_PORT.

    EC2 reaching "running" only means the OS booted; Caddy/the app come up a
    minute or three later. A plain TCP connect is exactly the check that
    distinguishes "nothing is listening yet" (the "refuses to connect" the
    visitor was seeing) from "the front door is serving". Cheap, no TLS, no
    Host/SNI juggling."""
    try:
        with socket.create_connection((ip, _APP_READY_PORT), timeout=_APP_READY_TIMEOUT):
            return True
    except OSError:
        return False


def _handle_running(instance: dict, next_path: str = "") -> dict:
    """Box is up: once it is actually SERVING, re-point DNS at its current IP and
    serve the holding page. We do NOT 302 the browser here.

    Why not 302: the box has no Elastic IP, so its public IP changes each wake and
    the app's A record is re-pointed every time. A server-side 302 fires the moment
    THIS Lambda sees the box ready, but the visitor's browser can still hold the
    PREVIOUS (now-dead) IP in its DNS cache -- so the bounce lands on a dead address
    and times out ("took too long to respond"), the reported crash. Instead we sync
    DNS and let the holding page's own client-side probe navigate the instant this
    browser can genuinely reach the box, which is the only moment it is safe."""
    ip = instance.get("PublicIpAddress")
    if not ip:
        # Running but the public IP is not attached yet -> let the page refresh.
        return _holding_page("Waking the app…", "The server is up; assigning its address.", next_path)
    if not _app_is_ready(ip):
        # OS is up but the app isn't serving on 443 yet -> hold; the client probe
        # will not succeed either, so nobody lands on a not-yet-listening socket.
        return _holding_page("Waking the app…", "The server is up; starting the application.", next_path)
    # Keep the DNS record current so this client's next resolution finds the live
    # box (idempotent; the warm-context cache skips repeat Hostinger calls). Even
    # if it transiently fails, holding is correct -- the client probe gates the nav.
    _sync_dns(ip)
    return _holding_page(
        "Almost ready",
        "The app is online. Connecting you to it now.",
        next_path,
    )


def handler(event, context):  # noqa: ARG001 - Lambda signature
    if not _INSTANCE_ID:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "TARGET_INSTANCE_ID not configured"}

    # Only genuine human intent wakes the box. CloudFront routes only /launch
    # here; refuse crawlers/scanners before any EC2 call so bots never wake it.
    if _looks_like_bot(_user_agent(event)):
        return _refuse_bot()

    # Optional same-origin path to land on after wake (e.g. /launch?next=/docs).
    nxt = _safe_next(event)

    resp = _ec2.describe_instances(InstanceIds=[_INSTANCE_ID])
    reservations = resp.get("Reservations", [])
    instances = reservations[0]["Instances"] if reservations else []
    if not instances:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "target instance not found"}

    instance = instances[0]
    state = instance["State"]["Name"]

    if state == "running":
        return _handle_running(instance, nxt)

    if state == "stopped":
        # Only start from a fully-stopped state (can't start while "stopping").
        # A failure here becomes a holding page, never a 500 in the visitor's face.
        try:
            _ec2.start_instances(InstanceIds=[_INSTANCE_ID])
        except Exception:  # noqa: BLE001
            pass
        return _holding_page("Waking the app…",
                             "The server was asleep to save cost. Starting it now.", nxt)

    # pending / stopping / shutting-down / etc. -> wait it out; next refresh acts.
    return _holding_page("Waking the app…", f"The server is {state}. Almost there.", nxt)
