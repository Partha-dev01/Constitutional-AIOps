"""
Tests for src/agents/user_router.py — per-user model routing selection.

Verifies the routing decision (BYOK spec Decision #3) without any network I/O:
  * admin / synthetic  -> the shared global agent,
  * regular user WITH a config -> a distinct per-user agent (cached, rebuilt on
    invalidation),
  * regular user WITHOUT a config -> None (caller surfaces a setup error).

Each test runs its provider calls inside a SINGLE event loop, then closes the
per-user routers in that same loop, so no httpx client outlives its loop.
"""

import asyncio
from types import SimpleNamespace

import pytest

from src.auth import crypto, store, user_llm
from src.auth.deps import SYNTHETIC_USER_ID
from src.agents import user_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-router")
    crypto.reset_cache()
    store.init_db()
    record = store.create_user("tenant2", "a-long-enough-password", role="user")
    global_agent = object()
    global_router = object()
    app = SimpleNamespace(
        state=SimpleNamespace(reasoning_agent=global_agent, model_router=global_router)
    )
    request = SimpleNamespace(app=app)
    yield SimpleNamespace(
        record=record,
        app=app,
        request=request,
        global_agent=global_agent,
        global_router=global_router,
    )
    crypto.reset_cache()


def _user(uid, role):
    return SimpleNamespace(id=uid, role=role)


def _cfg(**over):
    base = dict(
        fast_agent_url="https://api.example.com/v1",
        fast_agent_model="mf",
        reasoning_agent_url="https://api.example.com/v1",
        reasoning_agent_model="mr",
        api_key_plaintext="sk-x",
    )
    base.update(over)
    return base


def test_admin_gets_global(env):
    async def body():
        return await user_router.resolve_reasoning_agent(
            env.request, _user("admin-id", "admin")
        )

    agent, per_user = asyncio.run(body())
    assert agent is env.global_agent
    assert per_user is False


def test_synthetic_gets_global(env):
    async def body():
        return await user_router.resolve_reasoning_agent(
            env.request, _user(SYNTHETIC_USER_ID, "admin")
        )

    agent, per_user = asyncio.run(body())
    assert agent is env.global_agent
    assert per_user is False


def test_regular_without_config_returns_none(env):
    async def body():
        return await user_router.resolve_reasoning_agent(
            env.request, _user(env.record.id, "user")
        )

    agent, per_user = asyncio.run(body())
    assert agent is None
    assert per_user is False


def test_regular_with_config_gets_per_user_and_caches(env):
    user_llm.set_user_llm(env.record.id, **_cfg())

    async def body():
        u = _user(env.record.id, "user")
        a1, p1 = await user_router.resolve_reasoning_agent(env.request, u)
        a2, _ = await user_router.resolve_reasoning_agent(env.request, u)
        await user_router.close_all(env.app)
        return a1, p1, a2

    a1, p1, a2 = asyncio.run(body())
    assert a1 is not None
    assert a1 is not env.global_agent
    assert p1 is True
    assert a2 is a1  # cache hit -> same instance


def test_model_router_matches_agent_router(env):
    user_llm.set_user_llm(env.record.id, **_cfg())

    async def body():
        u = _user(env.record.id, "user")
        agent, _ = await user_router.resolve_reasoning_agent(env.request, u)
        router, per = await user_router.resolve_model_router(env.request, u)
        await user_router.close_all(env.app)
        return agent, router, per

    agent, router, per_user = asyncio.run(body())
    assert per_user is True
    assert router is not env.global_router
    # The per-user reasoning agent is bound to the per-user router.
    assert agent.model_router is router


def test_invalidate_rebuilds(env):
    user_llm.set_user_llm(env.record.id, **_cfg())

    async def body():
        u = _user(env.record.id, "user")
        a1, _ = await user_router.resolve_reasoning_agent(env.request, u)
        await user_router.invalidate_user(env.app, env.record.id)
        a2, _ = await user_router.resolve_reasoning_agent(env.request, u)
        await user_router.close_all(env.app)
        return a1, a2

    a1, a2 = asyncio.run(body())
    assert a1 is not a2  # rebuilt after invalidation


def test_config_change_rebuilds(env):
    user_llm.set_user_llm(env.record.id, **_cfg())

    async def body():
        u = _user(env.record.id, "user")
        a1, _ = await user_router.resolve_reasoning_agent(env.request, u)
        # Change the endpoint -> new fingerprint -> new router on next resolve.
        user_llm.set_user_llm(env.record.id, **_cfg(reasoning_agent_model="mr-2"))
        a2, _ = await user_router.resolve_reasoning_agent(env.request, u)
        await user_router.close_all(env.app)
        return a1, a2

    a1, a2 = asyncio.run(body())
    assert a1 is not a2
