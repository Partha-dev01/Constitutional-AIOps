"""
cost-fence-D unit tests: per-user daily LLM token budget.

Isolated like the BYOK suites - AIOPS_DATA_DIR points at a tmp SQLite db and the
two fence env vars are cleared so a host default can't leak into a case.
"""

import pytest

from src.auth import store
from src.cost import fence


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AIOPS_COST_FENCE_ENABLED", raising=False)
    monkeypatch.delenv("AIOPS_COST_FENCE_DAILY_TOKENS", raising=False)
    store.init_db()
    record = store.create_user("tenant-fence", "a-long-enough-password", role="user")
    return record


class TestDefaultOff:
    def test_unlimited_by_default(self, db_env):
        decision = fence.check(db_env.id)
        assert decision.allowed is True
        assert decision.limit == 0
        assert decision.remaining == -1
        assert decision.reason == ""

    def test_config_inactive_by_default(self, db_env):
        cfg = fence.resolve_config(db_env.id)
        assert cfg.enabled is False
        assert cfg.active is False

    def test_empty_user_id_is_safe(self):
        decision = fence.check("")
        assert decision.allowed is True
        assert decision.remaining == -1
        # record + public_view must not raise on an empty id
        fence.record("", 100)
        assert fence.public_view("")["usedToday"] == 0


class TestLedger:
    def test_record_increments_usage(self, db_env):
        fence.record(db_env.id, 120)
        fence.record(db_env.id, 30)
        tokens, requests = store.llm_usage_today(db_env.id)
        assert tokens == 150
        assert requests == 2

    def test_add_usage_coerces_bad_values(self, db_env):
        store.add_llm_usage(db_env.id, -50)  # negative -> 0
        store.add_llm_usage(db_env.id, "not-an-int")  # type: ignore[arg-type]
        tokens, requests = store.llm_usage_today(db_env.id)
        assert tokens == 0
        assert requests == 2  # still counts the request attempts

    def test_usage_is_per_day(self, db_env):
        store.add_llm_usage(db_env.id, 100, day="2026-01-01")
        assert store.llm_usage_today(db_env.id, day="2026-01-01") == (100, 1)
        assert store.llm_usage_today(db_env.id, day="2026-01-02") == (0, 0)


class TestEnvDefault:
    def test_env_enables_and_caps(self, db_env, monkeypatch):
        monkeypatch.setenv("AIOPS_COST_FENCE_ENABLED", "true")
        monkeypatch.setenv("AIOPS_COST_FENCE_DAILY_TOKENS", "200")
        # Under budget: allowed with remaining.
        d1 = fence.check(db_env.id)
        assert d1.allowed is True
        assert d1.limit == 200
        assert d1.remaining == 200
        # Spend up to the cap, then deny.
        fence.record(db_env.id, 200)
        d2 = fence.check(db_env.id)
        assert d2.allowed is False
        assert d2.remaining == 0
        assert "budget" in d2.reason

    def test_env_zero_limit_is_unlimited(self, db_env, monkeypatch):
        monkeypatch.setenv("AIOPS_COST_FENCE_ENABLED", "true")
        monkeypatch.setenv("AIOPS_COST_FENCE_DAILY_TOKENS", "0")
        fence.record(db_env.id, 10_000)
        assert fence.check(db_env.id).allowed is True

    def test_bad_env_limit_is_unlimited(self, db_env, monkeypatch):
        monkeypatch.setenv("AIOPS_COST_FENCE_ENABLED", "true")
        monkeypatch.setenv("AIOPS_COST_FENCE_DAILY_TOKENS", "garbage")
        assert fence.resolve_config(db_env.id).active is False


class TestPerUserOverride:
    def test_user_limit_overrides_unlimited_env(self, db_env):
        fence.set_config(db_env.id, enabled=True, daily_token_limit=50)
        fence.record(db_env.id, 50)
        d = fence.check(db_env.id)
        assert d.allowed is False
        assert d.limit == 50

    def test_user_can_disable_when_env_enabled(self, db_env, monkeypatch):
        monkeypatch.setenv("AIOPS_COST_FENCE_ENABLED", "true")
        monkeypatch.setenv("AIOPS_COST_FENCE_DAILY_TOKENS", "100")
        fence.set_config(db_env.id, enabled=False, daily_token_limit=100)
        fence.record(db_env.id, 500)
        assert fence.check(db_env.id).allowed is True

    def test_set_config_preserves_other_settings(self, db_env):
        store.set_user_settings(db_env.id, {"llm": {"fastAgentUrl": "http://x"}})
        fence.set_config(db_env.id, enabled=True, daily_token_limit=10)
        settings = store.get_user_settings(db_env.id)
        assert settings["llm"]["fastAgentUrl"] == "http://x"
        assert settings["costFence"]["dailyTokenLimit"] == 10


class TestPublicView:
    def test_shape(self, db_env):
        fence.set_config(db_env.id, enabled=True, daily_token_limit=100)
        fence.record(db_env.id, 40)
        view = fence.public_view(db_env.id)
        assert view == {
            "enabled": True,
            "dailyTokenLimit": 100,
            "usedToday": 40,
            "requestsToday": 1,
            "remaining": 60,
        }


class TestEstimate:
    def test_estimate_tokens(self):
        assert fence.estimate_tokens("") == 0
        assert fence.estimate_tokens("abcd") == 1
        assert fence.estimate_tokens("a" * 400) == 100
