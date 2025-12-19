#!/usr/bin/env python3
"""
Constitutional AIOps - Anomaly Injection Script

Injects test anomalies into the system for testing incident detection,
RCA analysis, and remediation workflows.

Usage:
    python scripts/inject_anomaly.py --type cpu_spike --service api-gateway
    python scripts/inject_anomaly.py --type memory_leak --service user-service --duration 300
    python scripts/inject_anomaly.py --type db_connection --service postgres --severity critical
    python scripts/inject_anomaly.py --scenario full_cascade
"""

import argparse
import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


API_BASE_URL = "http://localhost:8080/api/v1"


class AnomalyInjector:
    """Injects test anomalies into the Constitutional AIOps system."""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def create_incident(
        self,
        title: str,
        description: str,
        severity: str,
        category: str,
        affected_services: list[str],
        auto_analyze: bool = True,
    ) -> dict:
        """Create an incident via API."""
        response = await self.client.post(
            f"{self.api_url}/incidents",
            json={
                "title": title,
                "description": description,
                "severity": severity,
                "category": category,
                "affected_services": [{"name": s} for s in affected_services],
                "auto_analyze": auto_analyze,
                "source": "anomaly_injection",
                "tags": ["test", "anomaly-injection"],
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_action(
        self,
        action_type: str,
        description: str,
        target_service: str,
        confidence: float,
        incident_id: Optional[str] = None,
    ) -> dict:
        """Create an action via API."""
        response = await self.client.post(
            f"{self.api_url}/actions",
            json={
                "action_type": action_type,
                "description": description,
                "target_service": target_service,
                "confidence": confidence,
                "incident_id": incident_id,
                "reason": "Anomaly injection test",
            },
        )
        response.raise_for_status()
        return response.json()

    # Anomaly Types

    async def inject_cpu_spike(
        self,
        service: str,
        severity: str = "high",
        duration_seconds: int = 300,
    ) -> dict:
        """Inject a CPU spike anomaly."""
        print(f"Injecting CPU spike on {service}...")

        incident = await self.create_incident(
            title=f"High CPU usage on {service}",
            description=f"CPU usage exceeded 85% threshold on {service}. "
            f"Current usage: {random.randint(85, 98)}%. "
            f"Duration: {duration_seconds}s",
            severity=severity,
            category="performance",
            affected_services=[service],
        )

        print(f"  Created incident: {incident['id']}")

        # Create remediation action
        action = await self.create_action(
            action_type="scale_up",
            description=f"Scale up {service} to handle increased load",
            target_service=service,
            confidence=0.82,
            incident_id=incident["id"],
        )

        print(f"  Created action: {action['id']} (status: {action['status']})")

        return {"incident": incident, "action": action}

    async def inject_memory_leak(
        self,
        service: str,
        severity: str = "high",
        duration_seconds: int = 600,
    ) -> dict:
        """Inject a memory leak anomaly."""
        print(f"Injecting memory leak on {service}...")

        memory_pct = random.randint(88, 97)
        growth_rate = random.uniform(0.5, 2.0)

        incident = await self.create_incident(
            title=f"Memory leak detected on {service}",
            description=f"Memory usage has been growing steadily on {service}. "
            f"Current: {memory_pct}%, growth rate: {growth_rate:.1f}%/hour. "
            f"Potential memory leak in application code.",
            severity=severity,
            category="resource",
            affected_services=[service],
        )

        print(f"  Created incident: {incident['id']}")

        # Create restart action
        action = await self.create_action(
            action_type="restart_service",
            description=f"Restart {service} to clear memory leak",
            target_service=service,
            confidence=0.78,
            incident_id=incident["id"],
        )

        print(f"  Created action: {action['id']} (status: {action['status']})")

        return {"incident": incident, "action": action}

    async def inject_db_connection_issue(
        self,
        service: str,
        severity: str = "critical",
    ) -> dict:
        """Inject a database connection issue."""
        print(f"Injecting database connection issue on {service}...")

        pool_size = random.randint(45, 50)

        incident = await self.create_incident(
            title=f"Database connection pool exhausted on {service}",
            description=f"Connection pool reached maximum capacity ({pool_size}/50). "
            f"New connections are being rejected. "
            f"Likely cause: Connection leak or increased traffic.",
            severity=severity,
            category="resource",
            affected_services=[service, "postgres-primary"],
        )

        print(f"  Created incident: {incident['id']}")

        # Create config modification action
        action = await self.create_action(
            action_type="modify_config",
            description=f"Increase connection pool size for {service}",
            target_service=service,
            confidence=0.85,
            incident_id=incident["id"],
        )

        print(f"  Created action: {action['id']} (status: {action['status']})")

        return {"incident": incident, "action": action}

    async def inject_latency_spike(
        self,
        service: str,
        severity: str = "medium",
    ) -> dict:
        """Inject a latency spike anomaly."""
        print(f"Injecting latency spike on {service}...")

        p99_latency = random.randint(800, 2000)
        baseline = random.randint(100, 200)

        incident = await self.create_incident(
            title=f"Latency spike detected on {service}",
            description=f"P99 latency increased from {baseline}ms to {p99_latency}ms. "
            f"Possible causes: Database slow queries, network issues, or downstream service problems.",
            severity=severity,
            category="performance",
            affected_services=[service],
        )

        print(f"  Created incident: {incident['id']}")

        return {"incident": incident}

    async def inject_error_rate_spike(
        self,
        service: str,
        severity: str = "high",
    ) -> dict:
        """Inject an error rate spike."""
        print(f"Injecting error rate spike on {service}...")

        error_rate = random.uniform(5.0, 15.0)
        baseline = random.uniform(0.1, 0.5)

        incident = await self.create_incident(
            title=f"Error rate spike on {service}",
            description=f"Error rate increased from {baseline:.1f}% to {error_rate:.1f}%. "
            f"Top errors: ConnectionRefusedError (45%), TimeoutError (30%), ValueError (25%).",
            severity=severity,
            category="error",
            affected_services=[service],
        )

        print(f"  Created incident: {incident['id']}")

        # Create rollback action
        action = await self.create_action(
            action_type="rollback",
            description=f"Rollback {service} to previous version",
            target_service=service,
            confidence=0.72,
            incident_id=incident["id"],
        )

        print(f"  Created action: {action['id']} (status: {action['status']})")

        return {"incident": incident, "action": action}

    async def inject_disk_space_warning(
        self,
        service: str,
        severity: str = "medium",
    ) -> dict:
        """Inject a disk space warning."""
        print(f"Injecting disk space warning on {service}...")

        disk_pct = random.randint(85, 95)

        incident = await self.create_incident(
            title=f"Disk space warning on {service}",
            description=f"Disk usage at {disk_pct}% on {service}. "
            f"Consider cleaning up logs or increasing storage.",
            severity=severity,
            category="resource",
            affected_services=[service],
        )

        print(f"  Created incident: {incident['id']}")

        return {"incident": incident}

    # Scenarios

    async def run_cascade_scenario(self) -> dict:
        """
        Run a cascading failure scenario.

        Simulates a typical production cascade:
        1. Database connection issue
        2. API gateway errors
        3. User service failures
        4. Memory pressure from retries
        """
        print("\n=== Running Cascading Failure Scenario ===\n")

        results = []

        # Step 1: Database connection issue (root cause)
        print("Step 1: Database connection pool exhaustion (root cause)")
        db_result = await self.inject_db_connection_issue("postgres-primary", "critical")
        results.append(db_result)
        await asyncio.sleep(1)

        # Step 2: User service starts failing
        print("\nStep 2: User service connection errors")
        user_result = await self.inject_error_rate_spike("user-service", "high")
        results.append(user_result)
        await asyncio.sleep(1)

        # Step 3: API gateway latency spike
        print("\nStep 3: API gateway latency spike")
        api_result = await self.inject_latency_spike("api-gateway", "high")
        results.append(api_result)
        await asyncio.sleep(1)

        # Step 4: Memory pressure from retries
        print("\nStep 4: Memory pressure from retry storms")
        memory_result = await self.inject_memory_leak("api-gateway", "medium")
        results.append(memory_result)

        print("\n=== Cascade Scenario Complete ===")
        print(f"Created {len(results)} related incidents")

        return {"scenario": "cascade", "results": results}

    async def run_load_test_scenario(self, count: int = 5) -> dict:
        """
        Run a load test scenario with multiple random incidents.
        """
        print(f"\n=== Running Load Test Scenario ({count} incidents) ===\n")

        services = ["api-gateway", "user-service", "order-service", "payment-service", "inventory-service"]
        anomaly_types = [
            self.inject_cpu_spike,
            self.inject_memory_leak,
            self.inject_latency_spike,
            self.inject_error_rate_spike,
            self.inject_disk_space_warning,
        ]

        results = []
        for i in range(count):
            service = random.choice(services)
            anomaly_fn = random.choice(anomaly_types)
            print(f"\n[{i+1}/{count}] ", end="")
            result = await anomaly_fn(service)
            results.append(result)
            await asyncio.sleep(0.5)

        print(f"\n=== Load Test Scenario Complete ===")
        print(f"Created {len(results)} incidents")

        return {"scenario": "load_test", "results": results}


async def main():
    parser = argparse.ArgumentParser(description="Inject test anomalies into Constitutional AIOps")
    parser.add_argument("--api-url", default=API_BASE_URL, help="API base URL")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Individual anomaly types
    cpu_parser = subparsers.add_parser("cpu_spike", help="Inject CPU spike")
    cpu_parser.add_argument("--service", required=True, help="Target service")
    cpu_parser.add_argument("--severity", default="high", choices=["low", "medium", "high", "critical"])

    memory_parser = subparsers.add_parser("memory_leak", help="Inject memory leak")
    memory_parser.add_argument("--service", required=True, help="Target service")
    memory_parser.add_argument("--severity", default="high", choices=["low", "medium", "high", "critical"])

    db_parser = subparsers.add_parser("db_connection", help="Inject database connection issue")
    db_parser.add_argument("--service", required=True, help="Target service")
    db_parser.add_argument("--severity", default="critical", choices=["low", "medium", "high", "critical"])

    latency_parser = subparsers.add_parser("latency_spike", help="Inject latency spike")
    latency_parser.add_argument("--service", required=True, help="Target service")
    latency_parser.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])

    error_parser = subparsers.add_parser("error_spike", help="Inject error rate spike")
    error_parser.add_argument("--service", required=True, help="Target service")
    error_parser.add_argument("--severity", default="high", choices=["low", "medium", "high", "critical"])

    disk_parser = subparsers.add_parser("disk_warning", help="Inject disk space warning")
    disk_parser.add_argument("--service", required=True, help="Target service")
    disk_parser.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])

    # Scenarios
    cascade_parser = subparsers.add_parser("cascade", help="Run cascading failure scenario")

    load_parser = subparsers.add_parser("load_test", help="Run load test with random incidents")
    load_parser.add_argument("--count", type=int, default=5, help="Number of incidents to create")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    injector = AnomalyInjector(args.api_url)

    try:
        if args.command == "cpu_spike":
            result = await injector.inject_cpu_spike(args.service, args.severity)
        elif args.command == "memory_leak":
            result = await injector.inject_memory_leak(args.service, args.severity)
        elif args.command == "db_connection":
            result = await injector.inject_db_connection_issue(args.service, args.severity)
        elif args.command == "latency_spike":
            result = await injector.inject_latency_spike(args.service, args.severity)
        elif args.command == "error_spike":
            result = await injector.inject_error_rate_spike(args.service, args.severity)
        elif args.command == "disk_warning":
            result = await injector.inject_disk_space_warning(args.service, args.severity)
        elif args.command == "cascade":
            result = await injector.run_cascade_scenario()
        elif args.command == "load_test":
            result = await injector.run_load_test_scenario(args.count)
        else:
            print(f"Unknown command: {args.command}")
            return

        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))

    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
        print("Make sure the Constitutional AIOps API is running at", args.api_url)
    finally:
        await injector.close()


if __name__ == "__main__":
    asyncio.run(main())
