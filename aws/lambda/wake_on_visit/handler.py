"""
Wake-on-visit Lambda for the Constitutional AIOps LITE tier (5c WS4).

Fronts the sleep-when-idle deployment instance so there is NO fixed public IP /
Elastic IP (the ~$3.60/mo the $2-3 target avoids). Wired to an HTTP Function URL
that the app domain points at. On each request:

  * stopped   -> ec2.StartInstances + a 200 auto-refreshing "waking up" page.
  * pending / stopping -> the same holding page (still transitioning).
  * running   -> hand the visitor off to the app (see _handle_running / HANDOFF).

Pairs with aws/idle-check.sh (the "stop when idle" half). Together they give
"always reachable, sleeps when idle".

Environment:
  TARGET_INSTANCE_ID   (required)  e.g. i-0123456789abcdef0
  APP_URL              (required for the running handoff) e.g. https://aiops.example.com
  HOLDING_REFRESH_SEC  optional, default 8
  (AWS_REGION is provided by the Lambda runtime.)

--------------------------------------------------------------------------------
OPEN LIVE-DESIGN DECISIONS (settle in the Chunk-B live session, not guessed here):
  1. Running-state handoff. With NO Elastic IP the instance's public address
     changes on every start, and a TLS cert for APP_URL won't match the raw ec2
     DNS name. Options:
       (A) 302 redirect to APP_URL, where a stable low-TTL record already
           resolves to the box once up (e.g. the box self-updates an A record on
           boot). Implemented below by default.
       (B) Full reverse-proxy through the Lambda (fetch from the instance, return
           the response). Simplest DNS, but the Lambda then carries all traffic
           (cost/latency) and needs extra work for WebSockets. Slots into
           _handle_running() without touching the wake logic.
  2. Custom domain on a Function URL. Function URLs expose *.lambda-url.<region>.
     on.aws with their OWN cert; a branded APP_DOMAIN in front needs CloudFront
     (or API Gateway) for a matching cert. Decide the fronting in the live wiring.
--------------------------------------------------------------------------------
"""

import os

import boto3

_INSTANCE_ID = os.environ.get("TARGET_INSTANCE_ID", "")
_APP_URL = os.environ.get("APP_URL", "")
_REFRESH = int(os.environ.get("HOLDING_REFRESH_SEC", "8"))

_ec2 = boto3.client("ec2")


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


def _handle_running() -> dict:
    """Option (A): redirect to the stable app URL (see module docstring)."""
    return {
        "statusCode": 302,
        "headers": {"Location": _APP_URL, "Cache-Control": "no-store"},
        "body": "",
    }


def handler(event, context):  # noqa: ARG001 - Lambda signature
    if not _INSTANCE_ID:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "TARGET_INSTANCE_ID not configured"}

    resp = _ec2.describe_instances(InstanceIds=[_INSTANCE_ID])
    reservations = resp.get("Reservations", [])
    instances = reservations[0]["Instances"] if reservations else []
    if not instances:
        return {"statusCode": 500, "headers": {"Content-Type": "text/plain"},
                "body": "target instance not found"}

    state = instances[0]["State"]["Name"]

    if state == "running":
        return _handle_running()

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
