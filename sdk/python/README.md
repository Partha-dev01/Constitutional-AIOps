# constitutional-aiops (Python)

Official Python client for the Constitutional AIOps REST API. Two layers ship
together: a hand-written ergonomic client (`AIOpsClient`, standard library only)
and an optional generated typed core (`constitutional_aiops_client`, full type
safety over every endpoint) that rides on `httpx` + `attrs`. See `../README.md`
for the full status.

## Install (from source, pre-publish)

```bash
pip install -e sdk/python            # ergonomic client only, zero dependencies
pip install -e "sdk/python[typed]"   # also install the generated typed core
```

## Use — ergonomic client

```python
from constitutional_aiops import AIOpsClient, ConstitutionalRefusal

client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")

# List every critical incident (pagination handled for you).
for incident in client.paginate("/incidents/", severity="critical"):
    print(incident["id"], incident["title"])

# Read one incident and its root-cause analysis.
inc = client.get_incident("INC-2026-0007")
print(inc.get("rca", {}).get("root_cause"))

# Approve a pending action. This still passes the constitutional gate.
try:
    client.approve_action("act-123", approved=True, approved_by="me")
except ConstitutionalRefusal as refusal:
    print("gate held the action:", refusal.error_code)

# Stream a chat turn.
result = client.stream_chat("why is nextcloud slow?", on_delta=lambda t: print(t, end=""))
print("\n", result.get("message", {}).get("content"))
```

## Use — typed core

With the `typed` extra installed, every path, parameter, request body and response
is typed from the API's OpenAPI schema.

```python
from constitutional_aiops_client import AuthenticatedClient
from constitutional_aiops_client.api.incidents import incidents_get_incident

client = AuthenticatedClient(
    base_url="https://your-instance.example.com", token="aiops_pat_..."
)
incident = incidents_get_incident.sync(incident_id="INC-2026-0007", client=client)
print(incident.id, incident.severity)
```

## Regenerating the typed core

`constitutional_aiops_client/` is generated from the committed API snapshot
(`openapi/openapi.json`) by
[`openapi-python-client`](https://github.com/openapi-generators/openapi-python-client).
It is committed so the package installs offline; regenerate it whenever the
snapshot changes:

```bash
pip install "openapi-python-client==0.29.1"
bash sdk/python/scripts/generate.sh
```

## Auth

Create a personal access token in the app (Settings, or `POST /api/v1/auth/tokens`)
and pass it as `token=`; it is sent as `Authorization: Bearer aiops_pat_...` and
resolves to your user even when `AUTH_REQUIRED` is off, so calls are attributed and
cost-fenced. Against a single-user instance with `AUTH_REQUIRED` unset the token is
optional.

## License

AGPL-3.0-or-later, matching the app.
