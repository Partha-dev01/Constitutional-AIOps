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
                          then 302 the visitor to APP_URL.

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
  APP_URL              (required)  302 target once up, e.g. https://aiops-node.example.com
  HOSTINGER_API_TOKEN  (required)  Bearer token for the Hostinger DNS API
  HOSTINGER_DOMAIN     (required)  the Hostinger-managed zone, e.g. example.com
  DNS_RECORD_NAME      (required)  the subdomain record to keep current, e.g. aiops-node
  DNS_TTL              optional, default 60
  HOLDING_REFRESH_SEC  optional, default 8
  (AWS_REGION is provided by the Lambda runtime.)
"""

import json
import os
import urllib.error
import urllib.request

import boto3

_INSTANCE_ID = os.environ.get("TARGET_INSTANCE_ID", "")
_APP_URL = os.environ.get("APP_URL", "")
_REFRESH = int(os.environ.get("HOLDING_REFRESH_SEC", "8"))

_HOSTINGER_TOKEN = os.environ.get("HOSTINGER_API_TOKEN", "")
_HOSTINGER_DOMAIN = os.environ.get("HOSTINGER_DOMAIN", "")
_DNS_RECORD_NAME = os.environ.get("DNS_RECORD_NAME", "")
_DNS_TTL = int(os.environ.get("DNS_TTL", "60"))

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


def _holding_page(title: str, message: str) -> dict:
    html = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"refresh\" content=\"{_REFRESH}\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title><style>"
        "body{margin:0;min-height:100vh;display:flex;align-items:center;"
        "justify-content:center;font:16px/1.5 system-ui,sans-serif;"
        "background:#0f1115;color:#e6e6e6}.card{max-width:30rem;padding:2rem;"
        "text-align:center}.spin{width:2.5rem;height:2.5rem;margin:0 auto 1.25rem;"
        "border:3px solid #333;border-top-color:#6ea8fe;border-radius:50%;"
        "animation:s 1s linear infinite}@keyframes s{to{transform:rotate(360deg)}}"
        "h1{font-size:1.25rem;margin:.25rem 0}p{color:#9aa4b2}</style></head>"
        f"<body><div class=\"card\"><div class=\"spin\"></div><h1>{title}</h1>"
        f"<p>{message}</p><p style=\"font-size:.85rem\">This page refreshes "
        "automatically.</p></div></body></html>"
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


def _handle_running(instance: dict) -> dict:
    """Box is up: re-point DNS at its current IP, then hand the visitor off."""
    ip = instance.get("PublicIpAddress")
    if not ip:
        # Running but the public IP is not attached yet -> let the page refresh.
        return _holding_page("Waking the app…", "The server is up; assigning its address.")
    if not _sync_dns(ip):
        # DNS not confirmed (transient Hostinger error) -> hold and retry rather
        # than redirect to a possibly-stale address.
        return _holding_page("Waking the app…", "The server is up; finalizing its address.")
    return {
        "statusCode": 302,
        "headers": {"Location": _APP_URL, "Cache-Control": "no-store"},
        "body": "",
    }


def handler(event, context):  # noqa: ARG001 - Lambda signature
    if not _INSTANCE_ID:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "TARGET_INSTANCE_ID not configured"}

    # Only genuine human intent wakes the box. CloudFront routes only /launch
    # here; refuse crawlers/scanners before any EC2 call so bots never wake it.
    if _looks_like_bot(_user_agent(event)):
        return _refuse_bot()

    resp = _ec2.describe_instances(InstanceIds=[_INSTANCE_ID])
    reservations = resp.get("Reservations", [])
    instances = reservations[0]["Instances"] if reservations else []
    if not instances:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "target instance not found"}

    instance = instances[0]
    state = instance["State"]["Name"]

    if state == "running":
        return _handle_running(instance)

    if state == "stopped":
        # Only start from a fully-stopped state (can't start while "stopping").
        # A failure here becomes a holding page, never a 500 in the visitor's face.
        try:
            _ec2.start_instances(InstanceIds=[_INSTANCE_ID])
        except Exception:  # noqa: BLE001
            pass
        return _holding_page("Waking the app…",
                             "The server was asleep to save cost. Starting it now.")

    # pending / stopping / shutting-down / etc. -> wait it out; next refresh acts.
    return _holding_page("Waking the app…", f"The server is {state}. Almost there.")
