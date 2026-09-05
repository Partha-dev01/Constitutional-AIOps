"""Minimal end-to-end example for the Constitutional AIOps Python client.

Run against an instance you can reach. With ``AUTH_REQUIRED`` unset you can omit
the token; otherwise pass one via ``AIOPS_TOKEN``.

    AIOPS_URL=https://your-instance.example.com AIOPS_TOKEN=... python quickstart.py
"""

import os

from constitutional_aiops import AIOpsClient, ConstitutionalRefusal


def main() -> None:
    client = AIOpsClient(
        os.environ.get("AIOPS_URL", "http://localhost:8000"),
        token=os.environ.get("AIOPS_TOKEN"),
    )

    print("Recent incidents:")
    for incident in client.paginate("/incidents/", page_size=25):
        print(f"  {incident['id']:<16} {incident.get('severity','?'):<9} {incident.get('title','')}")

    pending = client.pending_actions()
    print(f"\nPending actions: {pending.get('count', 0)}")

    print("\nChat:")
    try:
        result = client.stream_chat(
            "Summarize the current state of the system.",
            on_delta=lambda token: print(token, end="", flush=True),
        )
        print("\n---")
        print(result.get("message", {}).get("content", ""))
    except ConstitutionalRefusal as refusal:
        print("gate refusal:", refusal.error_code)


if __name__ == "__main__":
    main()
