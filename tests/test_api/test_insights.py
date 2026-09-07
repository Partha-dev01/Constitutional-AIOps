"""
Track 2 W3 - LLM insight-widget plumbing (src/api/routes/insights.py).

Locks the fail-closed contract of the opt-in, cost-fenced ``/insights/explain``
surface and its preferences store:

  * opt-in gate: no LLM call and no spend until ui.aiWidgets.enabled is on;
  * cost fence: over budget returns a uniform available=false, no LLM call;
  * BYOK: a regular user with no endpoint degrades (no_endpoint), never the
    owner key;
  * success: the fast tier runs, tokens are recorded, the explanation returns
    labelled model_generated;
  * preferences: default off, a PUT toggles + persists WITHOUT wiping the row's
    other blocks (llm / costFence).

Isolated like the BYOK / fence suites: AIOPS_DATA_DIR points at a tmp SQLite db
and the fence env vars are cleared so a host default cannot leak into a case.
"""

from types import SimpleNamespace

import pytest
from fastapi.routing import APIRoute

from src.api.routes import insights
from src.api.routes.insights import (
    _KIND_INSTRUCTIONS,
    ExplainRequest,
    PreferencesUpdate,
    _build_prompt,
    explain,
    get_preferences,
    put_preferences,
)
from src.auth import store
from src.auth.deps import User, require_user, synthetic_admin


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    from src.auth import crypto

    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-insights")
    monkeypatch.delenv("AIOPS_COST_FENCE_ENABLED", raising=False)
    monkeypatch.delenv("AIOPS_COST_FENCE_DAILY_TOKENS", raising=False)
    crypto.reset_cache()
    store.init_db()
    record = store.create_user("tenant-insight", "a-long-enough-password", role="user")
    yield record
    crypto.reset_cache()


def _request(**state) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


class _FakeRouter:
    """A stand-in ModelRouter whose fast_completion returns a canned reply."""

    def __init__(self, content="Likely a cache stampede on the api tier.", usage=None):
        self._content = content
        self._usage = usage
        self.calls: list[dict] = []

    async def fast_completion(self, prompt, max_tokens=None, system_prompt=None, **kwargs):
        return self._record("fast", prompt, max_tokens, system_prompt)

    async def reasoning_completion(self, prompt, max_tokens=None, system_prompt=None, **kwargs):
        return self._record("reasoning", prompt, max_tokens, system_prompt)

    def _record(self, tier, prompt, max_tokens, system_prompt) -> dict:
        self.calls.append(
            {"tier": tier, "prompt": prompt, "max_tokens": max_tokens, "system_prompt": system_prompt}
        )
        result: dict = {"choices": [{"message": {"content": self._content}}]}
        if self._usage is not None:
            result["usage"] = self._usage
        return result


def _enable_widgets(user_id: str) -> None:
    put = PreferencesUpdate(enabled=True)
    insights._write_prefs(user_id, put)


def _patch_router(monkeypatch, value):
    async def _resolver(request, user):
        return value

    monkeypatch.setattr(insights, "resolve_model_router", _resolver)


def _patch_router_forbidden(monkeypatch):
    async def _resolver(request, user):  # pragma: no cover - must never run
        raise AssertionError("resolve_model_router must not be called")

    monkeypatch.setattr(insights, "resolve_model_router", _resolver)


class TestOptInGate:
    @pytest.mark.asyncio
    async def test_disabled_by_default_no_spend_no_llm(self, db_env, monkeypatch):
        _patch_router_forbidden(monkeypatch)  # opt-in check must short-circuit first
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(_request(), ExplainRequest(kind="spike", payload={"v": 9}), user=user)
        assert resp.available is False
        assert resp.reason == "ai_widgets_disabled"
        assert store.llm_usage_today(db_env.id) == (0, 0)


class TestBudgetFence:
    @pytest.mark.asyncio
    async def test_over_budget_returns_uniform_body_no_llm(self, db_env, monkeypatch):
        from src.cost import fence

        _enable_widgets(db_env.id)
        fence.set_config(db_env.id, enabled=True, daily_token_limit=10)
        fence.record(db_env.id, 10)  # exhaust the day
        _patch_router_forbidden(monkeypatch)  # fence check must short-circuit first
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(_request(), ExplainRequest(kind="spike", payload={}), user=user)
        assert resp.available is False
        assert resp.reason == "budget_reached"
        assert resp.remaining == 0


class TestByokDegrade:
    @pytest.mark.asyncio
    async def test_regular_user_without_endpoint_degrades(self, db_env):
        # Real resolver: a regular tenant with no llm block resolves to None, so
        # they degrade to no_endpoint rather than reaching the owner router.
        _enable_widgets(db_env.id)
        user = User(id=db_env.id, username="tenant-insight", role="user")
        request = _request(model_router=object())
        resp = await explain(request, ExplainRequest(kind="spike", payload={}), user=user)
        assert resp.available is False
        assert resp.reason == "no_endpoint"
        assert store.llm_usage_today(db_env.id) == (0, 0)

    @pytest.mark.asyncio
    async def test_none_router_degrades(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        _patch_router(monkeypatch, (None, False))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(_request(), ExplainRequest(payload={}), user=user)
        assert resp.available is False
        assert resp.reason == "no_endpoint"


class TestSuccess:
    @pytest.mark.asyncio
    async def test_explains_and_records_tokens(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        fake = _FakeRouter(usage={"completion_tokens": 40})
        _patch_router(monkeypatch, (fake, True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(
            _request(), ExplainRequest(kind="spike", payload={"cpu": 99}), user=user
        )
        assert resp.available is True
        assert resp.model_generated is True
        assert "cache stampede" in (resp.explanation or "")
        assert resp.tokens_used and resp.tokens_used > 40  # completion + prompt estimate
        # Fast tier was used with the SRE system prompt over a bounded prompt.
        assert len(fake.calls) == 1
        assert fake.calls[0]["system_prompt"] == insights._SYSTEM_PROMPT
        assert "Data:" in fake.calls[0]["prompt"]
        # The spend hit the ledger.
        tokens, requests = store.llm_usage_today(db_env.id)
        assert tokens == resp.tokens_used
        assert requests == 1

    @pytest.mark.asyncio
    async def test_reasoning_tier_routes_to_reasoning_completion(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        fake = _FakeRouter(content="Approve the restart; it is the least invasive step.")
        _patch_router(monkeypatch, (fake, True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(
            _request(),
            ExplainRequest(kind="next_best_action", tier="reasoning", payload={"incidents": []}),
            user=user,
        )
        assert resp.available is True
        # The reasoning tier was used, with its larger bound.
        assert fake.calls[0]["tier"] == "reasoning"
        assert fake.calls[0]["max_tokens"] == insights._MAX_TOKENS_REASONING

    @pytest.mark.asyncio
    async def test_graph_copilot_uses_reasoning_tier(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        fake = _FakeRouter(content="Cache-tier restarts dominate and have worked; watch the db.")
        _patch_router(monkeypatch, (fake, True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(
            _request(),
            ExplainRequest(
                kind="graph_copilot", tier="reasoning",
                payload={"stats": {"episodes": 3}, "topRootCauses": []},
            ),
            user=user,
        )
        assert resp.available is True
        assert fake.calls[0]["tier"] == "reasoning"
        assert fake.calls[0]["max_tokens"] == insights._MAX_TOKENS_REASONING

    @pytest.mark.asyncio
    async def test_default_tier_is_fast(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        fake = _FakeRouter()
        _patch_router(monkeypatch, (fake, True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        await explain(_request(), ExplainRequest(payload={"x": 1}), user=user)
        assert fake.calls[0]["tier"] == "fast"
        assert fake.calls[0]["max_tokens"] == insights._MAX_TOKENS

    @pytest.mark.asyncio
    async def test_empty_content_degrades_but_still_records(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)
        _patch_router(monkeypatch, (_FakeRouter(content=""), True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(_request(), ExplainRequest(payload={"x": 1}), user=user)
        assert resp.available is False
        assert resp.reason == "empty"
        # The request was served, so the ledger still advanced.
        assert store.llm_usage_today(db_env.id)[1] == 1

    @pytest.mark.asyncio
    async def test_router_exception_degrades(self, db_env, monkeypatch):
        _enable_widgets(db_env.id)

        class _Boom:
            async def fast_completion(self, *a, **k):
                raise RuntimeError("endpoint down")

        _patch_router(monkeypatch, (_Boom(), True))
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await explain(_request(), ExplainRequest(payload={}), user=user)
        assert resp.available is False
        assert resp.reason == "error"


class TestPreferences:
    @pytest.mark.asyncio
    async def test_default_off(self, db_env):
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await get_preferences(user=user)
        assert resp.aiWidgets.enabled is False
        assert resp.aiWidgets.autoExplain is False
        assert "usedToday" in resp.budget

    @pytest.mark.asyncio
    async def test_put_toggles_and_preserves_other_blocks(self, db_env):
        # A pre-existing llm block must survive the opt-in write.
        store.set_user_settings(db_env.id, {"llm": {"fastAgentUrl": "http://x"}})
        user = User(id=db_env.id, username="tenant-insight", role="user")
        resp = await put_preferences(
            PreferencesUpdate(enabled=True, autoExplain=True), user=user
        )
        assert resp.aiWidgets.enabled is True
        assert resp.aiWidgets.autoExplain is True
        settings = store.get_user_settings(db_env.id)
        assert settings["llm"]["fastAgentUrl"] == "http://x"
        assert settings["ui"]["aiWidgets"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_put_null_leaf_leaves_field_unchanged(self, db_env):
        user = User(id=db_env.id, username="tenant-insight", role="user")
        await put_preferences(PreferencesUpdate(enabled=True, autoExplain=True), user=user)
        # Patch only enabled -> autoExplain stays True.
        resp = await put_preferences(PreferencesUpdate(enabled=False), user=user)
        assert resp.aiWidgets.enabled is False
        assert resp.aiWidgets.autoExplain is True


class TestPromptBuilder:
    def test_known_kind_uses_its_instruction(self):
        prompt = _build_prompt("anomaly", {"a": 1})
        assert _KIND_INSTRUCTIONS["anomaly"][:20] in prompt
        assert "Data:" in prompt

    def test_graph_copilot_kind_uses_its_instruction(self):
        prompt = _build_prompt("graph_copilot", {"stats": {"episodes": 2}})
        assert _KIND_INSTRUCTIONS["graph_copilot"][:20] in prompt
        assert "Data:" in prompt

    def test_incident_kind_uses_its_instruction(self):
        prompt = _build_prompt("incident", {"title": "API 5xx", "severity": "critical"})
        assert _KIND_INSTRUCTIONS["incident"][:20] in prompt
        assert "Data:" in prompt

    def test_unknown_kind_falls_back_to_generic(self):
        prompt = _build_prompt("does-not-exist", {"a": 1})
        assert _KIND_INSTRUCTIONS["generic"][:20] in prompt

    def test_large_payload_is_truncated(self):
        prompt = _build_prompt("generic", {"blob": "z" * 5000})
        assert "...(truncated)" in prompt
        assert len(prompt) < 5000


class TestRouteContract:
    def test_explain_requires_user(self):
        route = next(
            r for r in insights.router.routes
            if isinstance(r, APIRoute) and r.path == "/explain"
        )
        assert require_user in {dep.call for dep in route.dependant.dependencies}

    @pytest.mark.asyncio
    async def test_admin_synthetic_uses_global_router(self, db_env, monkeypatch):
        # A synthetic/self-host admin with the opt-in on reaches the global router
        # (the real resolver returns app.state.model_router for admins).
        admin = synthetic_admin()
        _enable_widgets(admin.id)
        fake = _FakeRouter()
        request = _request(model_router=fake)
        resp = await explain(request, ExplainRequest(payload={"k": 1}), user=admin)
        assert resp.available is True
        assert len(fake.calls) == 1
