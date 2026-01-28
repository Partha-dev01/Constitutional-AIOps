"""
Create demo episodes based on actual Constitutional AIOps architecture.
Each service gets its own episodes with proper relationships.
"""

import asyncio
from datetime import datetime, timedelta
from src.memory.episode_store import EpisodeStore, Episode
from src.memory.neo4j_client import Neo4jClient


async def create_demo_episodes():
    neo4j = Neo4jClient()
    store = EpisodeStore(neo4j_client=neo4j)

    now = datetime.utcnow()

    # Episodes for each service based on actual architecture
    episodes = [
        # Neo4j episodes
        Episode(
            episode_id='ep-neo4j-001',
            incident_id='inc-neo4j-001',
            title='Neo4j High Memory Usage',
            description='Neo4j database exceeded 80% memory threshold causing slow graph queries',
            severity='warning',
            category='performance',
            detected_at=now - timedelta(hours=12),
            analyzed_at=now - timedelta(hours=11, minutes=50),
            remediated_at=now - timedelta(hours=11, minutes=30),
            resolved_at=now - timedelta(hours=11),
            root_cause='Graph query complexity',
            causal_chain=['Complex cypher query', 'Full graph scan', 'Memory pressure'],
            confidence=0.88,
            actions=[{'name': 'optimize_query', 'status': 'completed'}],
            successful_actions=['optimize_query', 'add_index'],
            affected_services=['neo4j', 'backend'],
            outcome='resolved',
            tags=['neo4j', 'memory', 'performance']
        ),

        # Prometheus episodes
        Episode(
            episode_id='ep-prometheus-001',
            incident_id='inc-prometheus-001',
            title='Prometheus Scrape Targets Unreachable',
            description='Multiple scrape targets returning connection refused errors',
            severity='critical',
            category='connectivity',
            detected_at=now - timedelta(hours=8),
            analyzed_at=now - timedelta(hours=7, minutes=45),
            remediated_at=now - timedelta(hours=7, minutes=20),
            resolved_at=now - timedelta(hours=7),
            root_cause='Network policy misconfiguration',
            causal_chain=['Network policy change', 'Blocked metrics port', 'Scrape failures'],
            confidence=0.92,
            actions=[{'name': 'fix_network_policy', 'status': 'completed'}],
            successful_actions=['fix_network_policy'],
            affected_services=['prometheus', 'grafana', 'backend', 'frontend'],
            outcome='resolved',
            tags=['prometheus', 'network', 'metrics']
        ),

        # Grafana episodes
        Episode(
            episode_id='ep-grafana-001',
            incident_id='inc-grafana-001',
            title='Grafana Dashboard Loading Timeout',
            description='Dashboards taking >30s to load due to slow datasource queries',
            severity='warning',
            category='performance',
            detected_at=now - timedelta(hours=6),
            analyzed_at=now - timedelta(hours=5, minutes=50),
            remediated_at=now - timedelta(hours=5, minutes=30),
            resolved_at=now - timedelta(hours=5),
            root_cause='Inefficient PromQL queries',
            causal_chain=['Heavy dashboard', 'Large time range', 'Slow PromQL execution'],
            confidence=0.85,
            actions=[{'name': 'optimize_dashboard', 'status': 'completed'}],
            successful_actions=['optimize_dashboard', 'reduce_time_range'],
            affected_services=['grafana', 'prometheus'],
            outcome='resolved',
            tags=['grafana', 'dashboard', 'performance']
        ),

        # Loki episodes
        Episode(
            episode_id='ep-loki-001',
            incident_id='inc-loki-001',
            title='Loki Log Ingestion Backlog',
            description='Log ingestion queue growing causing delayed log visibility',
            severity='warning',
            category='throughput',
            detected_at=now - timedelta(hours=4),
            analyzed_at=now - timedelta(hours=3, minutes=45),
            remediated_at=now - timedelta(hours=3, minutes=20),
            resolved_at=now - timedelta(hours=3),
            root_cause='High log volume from backend',
            causal_chain=['Debug logging enabled', 'High log volume', 'Ingestion backlog'],
            confidence=0.90,
            actions=[{'name': 'reduce_log_level', 'status': 'completed'}],
            successful_actions=['reduce_log_level', 'scale_ingester'],
            affected_services=['loki', 'backend', 'otel-collector'],
            outcome='resolved',
            tags=['loki', 'logs', 'throughput']
        ),

        # Backend episodes
        Episode(
            episode_id='ep-backend-001',
            incident_id='inc-backend-001',
            title='Backend API Latency Spike',
            description='API response times exceeded 2s threshold on /api/v1/chat endpoint',
            severity='critical',
            category='latency',
            detected_at=now - timedelta(hours=2),
            analyzed_at=now - timedelta(hours=1, minutes=50),
            remediated_at=now - timedelta(hours=1, minutes=30),
            resolved_at=now - timedelta(hours=1),
            root_cause='LLM endpoint timeout',
            causal_chain=['Jarvis Labs endpoint slow', 'Timeout waiting for response', 'API latency spike'],
            confidence=0.95,
            actions=[{'name': 'increase_timeout', 'status': 'completed'}],
            successful_actions=['increase_timeout', 'add_retry'],
            affected_services=['backend', 'frontend'],
            outcome='resolved',
            tags=['backend', 'api', 'latency']
        ),

        # Frontend episodes
        Episode(
            episode_id='ep-frontend-001',
            incident_id='inc-frontend-001',
            title='Frontend React Hydration Error',
            description='React hydration mismatch causing blank page on initial load',
            severity='warning',
            category='error',
            detected_at=now - timedelta(hours=1),
            analyzed_at=now - timedelta(minutes=50),
            remediated_at=now - timedelta(minutes=30),
            resolved_at=now - timedelta(minutes=15),
            root_cause='SSR state mismatch',
            causal_chain=['Cache stale', 'State mismatch', 'Hydration error'],
            confidence=0.82,
            actions=[{'name': 'clear_cache', 'status': 'completed'}],
            successful_actions=['clear_cache', 'rebuild_container'],
            affected_services=['frontend', 'backend'],
            outcome='resolved',
            tags=['frontend', 'react', 'error']
        ),

        # Tempo episodes
        Episode(
            episode_id='ep-tempo-001',
            incident_id='inc-tempo-001',
            title='Tempo Trace Storage Full',
            description='Trace storage reached 90% capacity causing trace drop',
            severity='warning',
            category='storage',
            detected_at=now - timedelta(hours=3),
            analyzed_at=now - timedelta(hours=2, minutes=50),
            remediated_at=now - timedelta(hours=2, minutes=30),
            resolved_at=now - timedelta(hours=2),
            root_cause='Retention policy too long',
            causal_chain=['7-day retention', 'High trace volume', 'Storage full'],
            confidence=0.87,
            actions=[{'name': 'reduce_retention', 'status': 'completed'}],
            successful_actions=['reduce_retention', 'cleanup_old_traces'],
            affected_services=['tempo', 'otel-collector'],
            outcome='resolved',
            tags=['tempo', 'traces', 'storage']
        ),

        # OTEL Collector episodes
        Episode(
            episode_id='ep-otel-001',
            incident_id='inc-otel-001',
            title='OTEL Collector Pipeline Blocked',
            description='Telemetry pipeline blocked due to downstream exporter failure',
            severity='critical',
            category='pipeline',
            detected_at=now - timedelta(hours=5),
            analyzed_at=now - timedelta(hours=4, minutes=50),
            remediated_at=now - timedelta(hours=4, minutes=30),
            resolved_at=now - timedelta(hours=4),
            root_cause='Prometheus exporter connection lost',
            causal_chain=['Network blip', 'Exporter disconnect', 'Pipeline blocked'],
            confidence=0.91,
            actions=[{'name': 'restart_pipeline', 'status': 'completed'}],
            successful_actions=['restart_pipeline'],
            affected_services=['otel-collector', 'prometheus', 'loki', 'tempo'],
            outcome='resolved',
            tags=['otel', 'pipeline', 'telemetry']
        ),
    ]

    # Store each episode
    for ep in episodes:
        await store.store_episode(ep)
        print(f'Created episode: {ep.title}')

    print(f'\nCreated {len(episodes)} episodes for Constitutional AIOps services')


if __name__ == '__main__':
    asyncio.run(create_demo_episodes())
