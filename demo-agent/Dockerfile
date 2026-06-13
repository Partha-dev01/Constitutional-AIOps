# t3 chaos/remediation control agent.
# Base on docker:27-cli so the `docker` CLI is already present (the agent shells
# out to it against the mounted host socket). Add python3 via apk — no pip deps,
# the agent is stdlib-only.
FROM docker:27-cli

RUN apk add --no-cache python3

WORKDIR /app
COPY agent.py /app/agent.py

# 8889 is the agent's HTTP port (override via DEMO_AGENT_PORT + the compose publish).
EXPOSE 8889

CMD ["python3", "-u", "agent.py"]
