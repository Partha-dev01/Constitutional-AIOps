"""
Tests for the self-hoster "evaluate my configured endpoint" quick-check.

  POST /api/v1/benchmark/evaluate-endpoint

The route is a thin wrapper: guard concurrency, clamp the case caps, map a
missing dataset to a 400. The real inference path is exercised by the runner
(and needs a live LLM), so here we stub the runner and test the wiring.
"""

import pytest


class _StubRunner:
    def __init__(self, is_running=False, result=None, raises=None):
        self.is_running = is_running
        self._result = result or {}
        self._raises = raises
        self.calls = []

    async def evaluate_endpoint(self, max_annotation=3, max_rca=2):
        self.calls.append((max_annotation, max_rca))
        if self._raises is not None:
            raise self._raises
        return self._result


class TestEvaluateEndpoint:
    @pytest.mark.asyncio
    async def test_conflict_when_a_run_is_active(self, monkeypatch):
        from fastapi import HTTPException
        import src.api.routes.benchmark as bench_mod
        from src.api.routes.benchmark import evaluate_endpoint, EvaluateEndpointRequest

        monkeypatch.setattr(bench_mod, "get_runner", lambda: _StubRunner(is_running=True))

        with pytest.raises(HTTPException) as exc:
            await evaluate_endpoint(EvaluateEndpointRequest())
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_success_returns_summary(self, monkeypatch):
        import src.api.routes.benchmark as bench_mod
        from src.api.routes.benchmark import evaluate_endpoint, EvaluateEndpointRequest

        summary = {
            "ok": True, "model": "constitutional_aiops", "cases_run": 5,
            "passed": 4, "pass_rate": 80.0,
            "annotation": {"run": 3, "passed": 3}, "rca": {"run": 2, "passed": 1},
            "avg_latency_ms": 700.0, "cases": [], "detail": "ok",
        }
        stub = _StubRunner(result=summary)
        monkeypatch.setattr(bench_mod, "get_runner", lambda: stub)

        res = await evaluate_endpoint(EvaluateEndpointRequest(max_annotation=3, max_rca=2))
        assert res["ok"] is True
        assert res["pass_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_caps_are_clamped(self, monkeypatch):
        import src.api.routes.benchmark as bench_mod
        from src.api.routes.benchmark import evaluate_endpoint, EvaluateEndpointRequest

        stub = _StubRunner(result={"ok": True})
        monkeypatch.setattr(bench_mod, "get_runner", lambda: stub)

        await evaluate_endpoint(EvaluateEndpointRequest(max_annotation=999, max_rca=0))
        # Clamped to [1, 10].
        assert stub.calls == [(10, 1)]

    @pytest.mark.asyncio
    async def test_missing_dataset_maps_to_400(self, monkeypatch):
        from fastapi import HTTPException
        import src.api.routes.benchmark as bench_mod
        from src.api.routes.benchmark import evaluate_endpoint, EvaluateEndpointRequest

        stub = _StubRunner(raises=FileNotFoundError("no dataset"))
        monkeypatch.setattr(bench_mod, "get_runner", lambda: stub)

        with pytest.raises(HTTPException) as exc:
            await evaluate_endpoint(EvaluateEndpointRequest())
        assert exc.value.status_code == 400
