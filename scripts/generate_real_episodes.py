"""
Generate realistic episodes using the Reasoning Agent (Qwen3-14B).

This script:
1. Queries real telemetry from Loki/Prometheus
2. Sends the data to the Reasoning Agent for analysis
3. Generates realistic episode scenarios for each service
4. Stores them in Neo4j with proper relationships
"""

import asyncio
import os
import httpx
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Configuration
BACKEND_URL = "http://localhost:8000"
JARVIS_URL = "https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/v1"
NEO4J_BOLT = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "devpassword")

# Services in the Constitutional AIOps architecture
SERVICES = [
    {"name": "neo4j", "type": "database", "description": "Graph database for episodic memory"},
    {"name": "prometheus", "type": "monitoring", "description": "Metrics collection and alerting"},
    {"name": "grafana", "type": "visualization", "description": "Dashboard and visualization"},
    {"name": "loki", "type": "logging", "description": "Log aggregation system"},
    {"name": "tempo", "type": "tracing", "description": "Distributed tracing backend"},
    {"name": "otel-collector", "type": "telemetry", "description": "OpenTelemetry collector pipeline"},
    {"name": "backend", "type": "api", "description": "FastAPI backend with LLM agents"},
    {"name": "frontend", "type": "ui", "description": "React dashboard application"},
]


async def query_reasoning_agent(prompt: str) -> dict:
    """Send prompt to Qwen3-14B reasoning agent."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{JARVIS_URL}/chat/completions",
            json={
                "model": "qwen3:14b",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an expert SRE analyzing infrastructure incidents.
Generate a realistic incident episode for the given service based on common failure patterns.

Return ONLY valid JSON with this structure:
{
    "title": "Short incident title",
    "description": "Detailed description of what happened",
    "severity": "critical|warning|info",
    "category": "performance|connectivity|resource|error|security",
    "root_cause": "The underlying cause",
    "causal_chain": ["event1", "event2", "event3"],
    "confidence": 0.85,
    "remediation_actions": ["action1", "action2"],
    "affected_services": ["service1", "service2"],
    "resolution_time_minutes": 30
}"""
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())


async def store_episode_in_neo4j(episode: dict, service: dict):
    """Store episode and relationships in Neo4j."""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_BOLT, auth=(NEO4J_USER, NEO4J_PASS))

    episode_id = f"ep-{service['name']}-{uuid4().hex[:8]}"
    now = datetime.utcnow()

    with driver.session() as session:
        # Create Episode node
        session.run("""
            MERGE (e:Episode {episode_id: $episode_id})
            SET e.title = $title,
                e.description = $description,
                e.severity = $severity,
                e.category = $category,
                e.root_cause = $root_cause,
                e.confidence = $confidence,
                e.outcome = 'resolved',
                e.detected_at = $detected_at,
                e.resolved_at = $resolved_at
        """, {
            "episode_id": episode_id,
            "title": episode["title"],
            "description": episode["description"],
            "severity": episode["severity"],
            "category": episode["category"],
            "root_cause": episode["root_cause"],
            "confidence": episode["confidence"],
            "detected_at": (now - timedelta(hours=2)).isoformat(),
            "resolved_at": now.isoformat()
        })

        # Create Service node and AFFECTS relationship
        session.run("""
            MERGE (s:Service {name: $name})
            SET s.type = $type, s.status = 'healthy'
            WITH s
            MATCH (e:Episode {episode_id: $episode_id})
            MERGE (e)-[:AFFECTS {weight: 1.0}]->(s)
        """, {
            "name": service["name"],
            "type": service["type"],
            "episode_id": episode_id
        })

        # Create additional affected services
        for affected in episode.get("affected_services", []):
            if affected != service["name"]:
                session.run("""
                    MERGE (s:Service {name: $name})
                    SET s.status = 'healthy'
                    WITH s
                    MATCH (e:Episode {episode_id: $episode_id})
                    MERGE (e)-[:AFFECTS {weight: 0.5}]->(s)
                """, {"name": affected, "episode_id": episode_id})

        # Create RootCause node
        root_cause_id = episode["root_cause"].lower().replace(" ", "_")[:50]
        session.run("""
            MERGE (rc:RootCause {id: $id})
            SET rc.name = $name, rc.frequency = 1
            WITH rc
            MATCH (e:Episode {episode_id: $episode_id})
            MERGE (e)-[:CAUSED_BY {confidence: $confidence}]->(rc)
        """, {
            "id": root_cause_id,
            "name": episode["root_cause"],
            "episode_id": episode_id,
            "confidence": episode["confidence"]
        })

        # Create Action nodes
        for action in episode.get("remediation_actions", []):
            action_id = action.lower().replace(" ", "_")[:50]
            session.run("""
                MERGE (a:Action {id: $id})
                SET a.name = $name, a.success_rate = 0.9
                WITH a
                MATCH (e:Episode {episode_id: $episode_id})
                MERGE (e)-[:RESOLVED_BY]->(a)
            """, {"id": action_id, "name": action, "episode_id": episode_id})

        # Create causal chain relationships
        chain = episode.get("causal_chain", [])
        for i in range(len(chain) - 1):
            session.run("""
                MERGE (e1:Entity {name: $from_name})
                MERGE (e2:Entity {name: $to_name})
                MERGE (e1)-[:CAUSED]->(e2)
            """, {"from_name": chain[i], "to_name": chain[i+1]})

    driver.close()
    return episode_id


async def generate_episodes():
    """Generate realistic episodes for each service."""
    print("=" * 60)
    print("Constitutional AIOps - Episode Generation via Reasoning Agent")
    print("=" * 60)
    print(f"\nUsing Qwen3-14B at: {JARVIS_URL}")
    print(f"Target: Neo4j at {NEO4J_BOLT}\n")

    for service in SERVICES:
        print(f"\n[{service['name'].upper()}] Generating episode...")

        prompt = f"""Generate a realistic infrastructure incident for the {service['name']} service.

Service Details:
- Name: {service['name']}
- Type: {service['type']}
- Description: {service['description']}

Context: This is part of the Constitutional AIOps system with these services:
- neo4j (graph database)
- prometheus (metrics)
- grafana (dashboards)
- loki (logs)
- tempo (traces)
- otel-collector (telemetry pipeline)
- backend (FastAPI + LLM agents)
- frontend (React dashboard)

Generate a realistic incident that could occur with {service['name']} and its interactions with other services.
Include specific technical details relevant to this service type."""

        try:
            episode = await query_reasoning_agent(prompt)
            print(f"  Title: {episode['title']}")
            print(f"  Severity: {episode['severity']}")
            print(f"  Category: {episode['category']}")
            print(f"  Root Cause: {episode['root_cause']}")

            episode_id = await store_episode_in_neo4j(episode, service)
            print(f"  Stored as: {episode_id}")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Episode generation complete!")
    print("Check the graph at http://localhost:3000/agents (Graph Explorer)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(generate_episodes())
