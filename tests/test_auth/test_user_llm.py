"""
Tests for src/auth/user_llm.py — per-user BYOK endpoint config (encrypted).

Pins AUTH_SECRET_KEY + AIOPS_DATA_DIR (tmp) and creates a real users-table row
(the user_settings FK requires it) per test, so no state leaks.
"""

import pytest

from src.auth import crypto, store, user_llm


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-user-llm")
    crypto.reset_cache()
    store.init_db()
    record = store.create_user("tenant1", "a-long-enough-password", role="user")
    yield record
    crypto.reset_cache()


def _cfg(**over):
    base = dict(
        fast_agent_url="https://api.example.com/v1",
        fast_agent_model="m-fast",
        reasoning_agent_url="https://api.example.com/v1",
        reasoning_agent_model="m-reason",
        api_key_plaintext="sk-tenant-key",
    )
    base.update(over)
    return base


class TestSetGet:
    def test_roundtrip_decrypts_key(self, db_env):
        user_llm.set_user_llm(db_env.id, **_cfg())
        got = user_llm.get_user_llm(db_env.id)
        assert got is not None
        assert got["fastAgentUrl"] == "https://api.example.com/v1"
        assert got["reasoningAgentModel"] == "m-reason"
        assert got["apiKey"] == "sk-tenant-key"

    def test_public_hides_key(self, db_env):
        user_llm.set_user_llm(db_env.id, **_cfg())
        pub = user_llm.get_user_llm_public(db_env.id)
        assert pub is not None
        assert pub["apiKeySet"] is True
        assert "apiKey" not in pub

    @pytest.mark.skipif(not crypto.is_available(), reason="cryptography not installed")
    def test_key_encrypted_on_disk(self, db_env):
        user_llm.set_user_llm(db_env.id, **_cfg())
        raw = store.get_user_settings(db_env.id)["llm"]["apiKey"]
        assert raw.startswith("enc::v1::")
        assert "sk-tenant-key" not in raw

    def test_unset_returns_none(self, db_env):
        assert user_llm.get_user_llm(db_env.id) is None
        assert user_llm.user_has_llm(db_env.id) is False
        assert user_llm.get_user_llm_public(db_env.id) is None

    def test_incomplete_config_is_unset_but_public_shows_partial(self, db_env):
        # A block missing a URL must not route (get_user_llm None), but the UI
        # still needs to see the partial values to finish it.
        user_llm.set_user_llm(db_env.id, **_cfg(reasoning_agent_url=""))
        assert user_llm.get_user_llm(db_env.id) is None
        assert user_llm.user_has_llm(db_env.id) is False
        assert user_llm.get_user_llm_public(db_env.id) is not None

    def test_stored_key_kept_across_reads(self, db_env):
        user_llm.set_user_llm(db_env.id, **_cfg())
        assert user_llm.stored_api_key_plaintext(db_env.id) == "sk-tenant-key"


class TestMergePreservesOtherSettings:
    def test_set_llm_preserves_notifications(self, db_env):
        store.set_user_settings(db_env.id, {"notifications": {"emailEnabled": True}})
        user_llm.set_user_llm(db_env.id, **_cfg())
        settings = store.get_user_settings(db_env.id)
        assert settings["notifications"] == {"emailEnabled": True}
        assert "llm" in settings

    def test_clear_preserves_notifications(self, db_env):
        store.set_user_settings(db_env.id, {"notifications": {"emailEnabled": True}})
        user_llm.set_user_llm(db_env.id, **_cfg())
        user_llm.clear_user_llm(db_env.id)
        settings = store.get_user_settings(db_env.id)
        assert "llm" not in settings
        assert settings["notifications"] == {"emailEnabled": True}


class TestFingerprint:
    def test_changes_with_key(self):
        base = {
            "fastAgentUrl": "u",
            "fastAgentModel": "m",
            "reasoningAgentUrl": "u",
            "reasoningAgentModel": "m",
            "apiKey": "k1",
        }
        other = dict(base, apiKey="k2")
        assert user_llm.config_fingerprint(base) != user_llm.config_fingerprint(other)

    def test_stable_for_same_config(self):
        cfg = {
            "fastAgentUrl": "u",
            "fastAgentModel": "m",
            "reasoningAgentUrl": "u",
            "reasoningAgentModel": "m",
            "apiKey": "k",
        }
        assert user_llm.config_fingerprint(cfg) == user_llm.config_fingerprint(dict(cfg))
