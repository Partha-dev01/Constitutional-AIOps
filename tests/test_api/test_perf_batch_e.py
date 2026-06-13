"""
Batch-E backend performance tests.

Covers the three items in W2_E_backend_perf.md:

1. Docker SDK blocking calls wrapped in asyncio.to_thread (infrastructure.py)
2. /health TTL cache — second call within TTL does not re-probe (health.py)
3. _incidents LRU cap + evicted incident still loadable from persistence (incidents.py)
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import time
import types
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Item 1: Docker SDK calls wrapped in asyncio.to_thread
# ---------------------------------------------------------------------------

class TestDockerToThread:
    """infrastructure.py — blocking Docker SDK never runs on the event loop."""

    def test_collect_container_status_is_sync_callable(self) -> None:
        """_collect_container_status must be a plain (non-async) callable."""
        from src.api.routes.infrastructure import _collect_container_status

        assert callable(_collect_container_status)
        assert not asyncio.iscoroutinefunction(_collect_container_status), (
            "_collect_container_status must be sync so asyncio.to_thread can offload it"
        )

    def test_discover_all_containers_is_sync_callable(self) -> None:
        """_discover_all_containers must be a plain (non-async) callable."""
        from src.api.routes.infrastructure import _discover_all_containers

        assert callable(_discover_all_containers)
        assert not asyncio.iscoroutinefunction(_discover_all_containers)

    def test_get_containers_uses_to_thread(self) -> None:
        """get_containers must delegate the blocking work via asyncio.to_thread."""
        import asyncio as _asyncio
        import src.api.routes.infrastructure as infra_mod

        mock_containers: list = []
        mock_healthy = 0
        mock_unhealthy = 0

        to_thread_called = []

        async def fake_to_thread(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
            to_thread_called.append(fn)
            # Run the sync fn synchronously in the test (no real thread needed).
            return fn(*args, **kwargs) if not callable(fn) else (mock_containers, mock_healthy, mock_unhealthy)

        request = MagicMock()

        with patch.object(_asyncio, "to_thread", new=fake_to_thread):
            with patch.object(infra_mod, "_collect_container_status", return_value=([], 0, 0)) as mock_fn:
                result = _asyncio.get_event_loop().run_until_complete(
                    infra_mod.get_containers(request)
                )

        # to_thread must have been awaited with _collect_container_status
        assert len(to_thread_called) >= 1, "asyncio.to_thread was never called"

    def test_discover_containers_uses_to_thread(self) -> None:
        """discover_containers must delegate the blocking work via asyncio.to_thread."""
        import asyncio as _asyncio
        import src.api.routes.infrastructure as infra_mod

        to_thread_called = []

        async def fake_to_thread(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
            to_thread_called.append(fn)
            return []

        with patch.object(_asyncio, "to_thread", new=fake_to_thread):
            with patch.object(infra_mod, "_discover_all_containers", return_value=[]):
                result = _asyncio.get_event_loop().run_until_complete(
                    infra_mod.discover_containers()
                )

        assert len(to_thread_called) >= 1, "asyncio.to_thread was never called for discover_containers"

    def test_get_containers_falls_back_on_exception(self) -> None:
        """get_containers must fall back to static list when to_thread raises."""
        import asyncio as _asyncio
        import src.api.routes.infrastructure as infra_mod

        request = MagicMock()

        async def boom(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("daemon unavailable")

        with patch.object(_asyncio, "to_thread", new=boom):
            response = _asyncio.get_event_loop().run_until_complete(
                infra_mod.get_containers(request)
            )

        # Should not raise — static fallback returns a valid InfrastructureResponse
        assert response is not None
        assert hasattr(response, "containers")


# ---------------------------------------------------------------------------
# Item 2: /health TTL cache
# ---------------------------------------------------------------------------

class TestHealthTTLCache:
    """/health does not re-probe when called within the TTL window."""

    def _make_mock_request(self) -> MagicMock:
        mock_router = MagicMock()
        mock_router.health_check = AsyncMock(return_value={
            "fast_agent": True,
            "reasoning_agent": True,
        })
        mock_neo4j = MagicMock()
        mock_neo4j.health_check = AsyncMock(return_value=True)

        request = MagicMock()
        request.app.state.model_router = mock_router
        request.app.state.neo4j_client = mock_neo4j
        return request

    def _reset_cache(self) -> None:
        import src.api.routes.health as health_mod
        health_mod._health_cache_result = None
        health_mod._health_cache_ts = 0.0

    def test_ttl_constant_exists_and_is_positive(self) -> None:
        from src.api.routes.health import HEALTH_CACHE_TTL_SECONDS
        assert isinstance(HEALTH_CACHE_TTL_SECONDS, (int, float))
        assert HEALTH_CACHE_TTL_SECONDS > 0

    def test_second_call_within_ttl_does_not_re_probe(self) -> None:
        """Model-router health_check must be called exactly once for two rapid polls."""
        import src.api.routes.health as health_mod

        self._reset_cache()
        request = self._make_mock_request()
        loop = asyncio.get_event_loop()

        # First call — fills cache
        loop.run_until_complete(health_mod.health_check(request))
        first_call_count = request.app.state.model_router.health_check.call_count

        # Second call immediately — should use cache, NOT re-probe
        loop.run_until_complete(health_mod.health_check(request))
        second_call_count = request.app.state.model_router.health_check.call_count

        assert second_call_count == first_call_count, (
            f"health_check probe was called {second_call_count} times total; "
            f"expected only {first_call_count} (no re-probe within TTL)"
        )

    def test_call_after_ttl_re_probes(self) -> None:
        """After the TTL expires a new call must re-probe (cache stale)."""
        import src.api.routes.health as health_mod

        self._reset_cache()
        request = self._make_mock_request()
        loop = asyncio.get_event_loop()

        # First call
        loop.run_until_complete(health_mod.health_check(request))
        first_call_count = request.app.state.model_router.health_check.call_count

        # Expire the cache by backdating the timestamp beyond the TTL
        health_mod._health_cache_ts = time.monotonic() - health_mod.HEALTH_CACHE_TTL_SECONDS - 1.0

        # Third call — cache expired, must re-probe
        loop.run_until_complete(health_mod.health_check(request))
        after_expiry_count = request.app.state.model_router.health_check.call_count

        assert after_expiry_count > first_call_count, (
            "Expected re-probe after TTL expiry but call count did not increase"
        )

    def test_health_response_shape_unchanged(self) -> None:
        """Response must still carry status / version / components / uptime_seconds."""
        import src.api.routes.health as health_mod

        self._reset_cache()
        request = self._make_mock_request()
        loop = asyncio.get_event_loop()

        response = loop.run_until_complete(health_mod.health_check(request))

        assert hasattr(response, "status")
        assert hasattr(response, "version")
        assert hasattr(response, "components")
        assert hasattr(response, "uptime_seconds")
        assert isinstance(response.components, list)
        assert len(response.components) > 0


# ---------------------------------------------------------------------------
# Item 3: _incidents LRU cap + persistence-reload
# ---------------------------------------------------------------------------

class TestIncidentsCap:
    """_incidents dict is capped; evicted incidents are loadable from persistence."""

    def _make_incident(self, inc_id: str, resolved: bool = False) -> Any:
        """Create a minimal Incident object with required fields."""
        from src.api.schemas.incident import (
            Incident,
            IncidentCategory,
            IncidentSeverity,
            IncidentStatus,
            ServiceInfo,
        )

        s = IncidentStatus.RESOLVED if resolved else IncidentStatus.DETECTING
        now = datetime.utcnow()
        return Incident(
            id=inc_id,
            title=f"Test incident {inc_id}",
            description="auto-generated test",
            severity=IncidentSeverity.LOW,
            category=IncidentCategory.PERFORMANCE,
            affected_services=[ServiceInfo(name="test-svc", namespace="test")],
            tags=[],
            source="test",
            status=s,
            created_at=now,
            updated_at=now,
            detected_at=now,
        )

    def _clear_incidents(self) -> None:
        import src.api.routes.incidents as inc_mod
        inc_mod._incidents.clear()

    def test_max_incidents_constant_exists(self) -> None:
        import src.api.routes.incidents as inc_mod
        assert hasattr(inc_mod, "_MAX_INCIDENTS")
        assert inc_mod._MAX_INCIDENTS > 0

    def test_evict_stale_incidents_caps_dict(self) -> None:
        """After eviction the dict must not exceed _MAX_INCIDENTS."""
        import src.api.routes.incidents as inc_mod

        self._clear_incidents()
        original_max = inc_mod._MAX_INCIDENTS
        inc_mod._MAX_INCIDENTS = 5

        try:
            for i in range(10):
                inc = self._make_incident(f"INC-TEST-{i:04d}", resolved=(i < 5))
                inc_mod._incidents[inc.id] = inc

            inc_mod._evict_stale_incidents()
            assert len(inc_mod._incidents) <= 5, (
                f"Expected ≤5 incidents after eviction, got {len(inc_mod._incidents)}"
            )
        finally:
            inc_mod._MAX_INCIDENTS = original_max
            self._clear_incidents()

    def test_evicted_incident_loadable_from_persistence(self) -> None:
        """An evicted incident must still be retrievable via the persistence fallback."""
        import src.api.routes.incidents as inc_mod
        from src.persistence import store as ps

        self._clear_incidents()
        original_max = inc_mod._MAX_INCIDENTS
        inc_mod._MAX_INCIDENTS = 3

        try:
            # Create 5 incidents — first 4 are resolved (eviction candidates)
            incidents = [self._make_incident(f"INC-EVICT-{i:04d}", resolved=(i < 4)) for i in range(5)]
            for inc in incidents:
                inc_mod._incidents[inc.id] = inc

            # The incident we want to keep loadable: the oldest resolved one
            target = incidents[0]

            # Build a fake persistence that returns the target incident.
            fake_all = {target.id: target}
            with patch.object(ps, "load_all_incidents", return_value=fake_all):
                inc_mod._evict_stale_incidents()
                assert target.id not in inc_mod._incidents, (
                    "Eviction should have removed the target from in-memory dict"
                )

                # Now try to reload it via _load_incident_from_persistence
                loaded = inc_mod._load_incident_from_persistence(target.id)

            assert loaded is not None, "Evicted incident must be loadable from persistence"
            assert loaded.id == target.id
        finally:
            inc_mod._MAX_INCIDENTS = original_max
            self._clear_incidents()

    def test_evicted_incident_re_enters_cache(self) -> None:
        """After persistence reload the incident must be back in the in-memory dict."""
        import src.api.routes.incidents as inc_mod
        from src.persistence import store as ps

        self._clear_incidents()
        inc = self._make_incident("INC-RELOAD-0001", resolved=True)
        fake_all = {inc.id: inc}

        with patch.object(ps, "load_all_incidents", return_value=fake_all):
            result = inc_mod._load_incident_from_persistence(inc.id)

        assert result is not None
        assert inc.id in inc_mod._incidents, (
            "Persistence-reloaded incident should be back in the in-memory cache"
        )
        self._clear_incidents()

    def test_get_incident_falls_back_to_persistence(self) -> None:
        """GET /{id} must not 404 for an evicted-but-persisted incident."""
        import asyncio as _asyncio
        import src.api.routes.incidents as inc_mod
        from src.persistence import store as ps
        from fastapi import HTTPException

        self._clear_incidents()
        inc = self._make_incident("INC-FALLBACK-0001", resolved=True)
        # Ensure it is NOT in the in-memory cache (simulates eviction)
        inc_mod._incidents.pop(inc.id, None)

        fake_all = {inc.id: inc}
        with patch.object(ps, "load_all_incidents", return_value=fake_all):
            result = _asyncio.get_event_loop().run_until_complete(
                inc_mod.get_incident(inc.id)
            )

        assert result.id == inc.id, "Should have returned the incident from persistence"
        self._clear_incidents()

    def test_get_incident_404_when_not_in_persistence_either(self) -> None:
        """GET /{id} must 404 when the incident is absent from both cache and persistence."""
        import asyncio as _asyncio
        import src.api.routes.incidents as inc_mod
        from src.persistence import store as ps
        from fastapi import HTTPException

        self._clear_incidents()
        with patch.object(ps, "load_all_incidents", return_value={}):
            try:
                _asyncio.get_event_loop().run_until_complete(
                    inc_mod.get_incident("INC-GHOST-9999")
                )
                assert False, "Expected HTTPException 404"
            except HTTPException as exc:
                assert exc.status_code == 404
        self._clear_incidents()
