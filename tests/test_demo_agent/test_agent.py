"""Unit tests for the t3 control agent's PURE helpers (build_commands /
is_authorized).

``demo-agent/agent.py`` lives outside the importable package tree (hyphenated
dir, stdlib-only, meant to be deployed standalone), so we load it by file path
via importlib. We only exercise the pure functions — no server, no docker.
"""

import importlib.util
from pathlib import Path

import pytest


def _load_agent(monkeypatch, token="secret-token"):
    """Import demo-agent/agent.py fresh with a given DEMO_AGENT_TOKEN.

    The token is read at import time into the module-level DEMO_AGENT_TOKEN, so we
    set the env BEFORE loading and load a fresh module object each time.
    """
    monkeypatch.setenv("DEMO_AGENT_TOKEN", token)
    monkeypatch.delenv("NEXTCLOUD_CONTAINER", raising=False)
    monkeypatch.delenv("NEXTCLOUD_DB_CONTAINER", raising=False)
    monkeypatch.delenv("DEMO_AGENT_CONTAINERS", raising=False)

    agent_path = (
        Path(__file__).resolve().parents[2] / "demo-agent" / "agent.py"
    )
    spec = importlib.util.spec_from_file_location("_t3_agent_under_test", agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# is_authorized
# ---------------------------------------------------------------------------

class TestIsAuthorized:
    def test_correct_bearer_token_passes(self, monkeypatch):
        agent = _load_agent(monkeypatch, token="abc123")
        assert agent.is_authorized("Bearer abc123") is True

    def test_wrong_token_fails(self, monkeypatch):
        agent = _load_agent(monkeypatch, token="abc123")
        assert agent.is_authorized("Bearer nope") is False

    def test_missing_header_fails(self, monkeypatch):
        agent = _load_agent(monkeypatch, token="abc123")
        assert agent.is_authorized("") is False
        assert agent.is_authorized(None) is False

    def test_malformed_header_fails(self, monkeypatch):
        agent = _load_agent(monkeypatch, token="abc123")
        assert agent.is_authorized("abc123") is False  # missing "Bearer "
        assert agent.is_authorized("Bearer ") is False  # empty token
        assert agent.is_authorized("Basic abc123") is False

    def test_empty_agent_token_never_authorizes(self, monkeypatch):
        # Even a "Bearer " with empty presented token must fail, and an empty
        # agent token fails closed regardless of what is presented.
        agent = _load_agent(monkeypatch, token="")
        assert agent.is_authorized("Bearer anything") is False


# ---------------------------------------------------------------------------
# build_commands
# ---------------------------------------------------------------------------

class TestBuildCommands:
    def test_unknown_scenario_raises_keyerror(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        with pytest.raises(KeyError):
            agent.build_commands("nope", "start")

    def test_unknown_action_raises_valueerror(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        with pytest.raises(ValueError):
            agent.build_commands("db_down", "pause")

    def test_db_down_start_stops_db(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        assert agent.build_commands("db_down", "start") == [
            ["docker", "stop", "nextcloud-db"]
        ]

    def test_db_down_heal_starts_db(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        assert agent.build_commands("db_down", "heal") == [
            ["docker", "start", "nextcloud-db"]
        ]

    def test_cpu_stress_start_runs_two_loops(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        cmds = agent.build_commands("cpu_stress", "start")
        assert len(cmds) == 2
        for cmd in cmds:
            assert cmd[:4] == ["docker", "exec", "-d", "nextcloud"]
            assert "timeout 90" in cmd[-1]
            assert "while :" in cmd[-1]

    def test_cpu_stress_heal_pkill(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        cmds = agent.build_commands("cpu_stress", "heal")
        assert len(cmds) == 1
        assert "pkill" in cmds[0][-1]
        assert "|| true" in cmds[0][-1]

    def test_mem_stress_start_self_expires(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        cmds = agent.build_commands("mem_stress", "start")
        assert len(cmds) == 1
        assert cmds[0][:4] == ["docker", "exec", "-d", "nextcloud"]
        # Self-expiring via timeout 90, robust against failure with || true.
        assert "timeout 90" in cmds[0][-1]
        assert "|| true" in cmds[0][-1]

    def test_bad_config_toggles_maintenance_mode(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        start = agent.build_commands("bad_config_5xx", "start")[0]
        heal = agent.build_commands("bad_config_5xx", "heal")[0]
        assert start[-3:] == ["maintenance:mode", "--on"] or start[-1] == "--on"
        assert "--on" in start
        assert "--off" in heal
        assert "-u" in start and "www-data" in start

    def test_disk_fill_start_writes_and_logs(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        cmd = agent.build_commands("disk_fill", "start")[0]
        script = cmd[-1]
        assert "chaos_fill.bin" in script
        assert "dd if=/dev/zero" in script
        assert "nextcloud.log" in script

    def test_disk_fill_heal_removes_file(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        cmd = agent.build_commands("disk_fill", "heal")[0]
        assert "rm -f" in cmd[-1]
        assert "chaos_fill.bin" in cmd[-1]
        assert "|| true" in cmd[-1]

    def test_container_names_honor_env_overrides(self, monkeypatch):
        monkeypatch.setenv("NEXTCLOUD_CONTAINER", "nc-app")
        monkeypatch.setenv("NEXTCLOUD_DB_CONTAINER", "nc-db")
        # Reload after setting env so the module-level names pick them up.
        agent = _load_agent(monkeypatch)
        # _load_agent deletes the override envs, so re-set + re-import manually.
        monkeypatch.setenv("NEXTCLOUD_CONTAINER", "nc-app")
        monkeypatch.setenv("NEXTCLOUD_DB_CONTAINER", "nc-db")
        import importlib.util
        from pathlib import Path

        agent_path = Path(agent.__file__)
        spec = importlib.util.spec_from_file_location("_t3_agent_ov", agent_path)
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)

        assert agent.build_commands("db_down", "start") == [
            ["docker", "stop", "nc-db"]
        ]
        assert agent.build_commands("cpu_stress", "start")[0][3] == "nc-app"


# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------

class TestWhitelist:
    def test_default_whitelist_is_the_two_nc_containers(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        assert agent._whitelist() == {"nextcloud", "nextcloud-db"}

    def test_whitelist_env_override(self, monkeypatch):
        agent = _load_agent(monkeypatch)
        monkeypatch.setenv("DEMO_AGENT_CONTAINERS", "alpha, beta ,")
        assert agent._whitelist() == {"alpha", "beta"}
