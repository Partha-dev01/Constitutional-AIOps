# constitutional-aiops (Python)

Official Python client for the Constitutional AIOps REST API. Pre-release
scaffold, standard library only. See `../README.md` for the full status and the
generated-core plan.

## Install (from source, pre-publish)

```bash
pip install -e sdk/python
```

## Use

```python
from constitutional_aiops import AIOpsClient, ConstitutionalRefusal

client = AIOpsClient("https://your-instance.example.com", token="caiops_pat_...")

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

## Auth note

Personal access tokens are planned (see the developer-platform guide). Until they
ship, run against an instance with `AUTH_REQUIRED` unset, or pass a session token
as `token=`.

## License

AGPL-3.0-or-later, matching the app.
