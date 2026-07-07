"""Serving-mode swap-channel tests (Settings → Mode 1 ⇄ Mode 2 toggle, s29).

The backend never swaps anything itself — it writes ``request.json`` under
``AIOPS_DATA_DIR/mode-swap/`` for the host-side watcher
(scripts/mode-swap-watcher.sh) and reports merged status on GET.
"""

import json

import pytest

from src.auth.deps import User, synthetic_admin


@pytest.fixture
def swap_env(tmp_path, monkeypatch):
    """Fresh AIOPS_DATA_DIR + Mode 1 environment for each test."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AIOPS_MODE", raising=False)
    yield tmp_path / "mode-swap"


@pytest.mark.asyncio
async def test_get_serving_mode_idle(swap_env):
    from src.api.routes.settings import get_serving_mode

    result = await get_serving_mode(user=synthetic_admin())
    assert result.mode == 1
    assert result.single_engine is False
    assert result.swap_status == "idle"
    assert result.requested_mode is None


@pytest.mark.asyncio
async def test_post_writes_request_file_and_reports_pending(swap_env):
    from src.api.routes.settings import ServingModeRequest, request_serving_mode

    result = await request_serving_mode(
        ServingModeRequest(mode=2), user=synthetic_admin()
    )
    assert result.swap_status == "pending"
    assert result.requested_mode == 2
    req = json.loads((swap_env / "request.json").read_text(encoding="utf-8"))
    assert req["requested_mode"] == 2
    assert req["requested_by"]


@pytest.mark.asyncio
async def test_post_same_mode_is_noop(swap_env):
    from src.api.routes.settings import ServingModeRequest, request_serving_mode

    result = await request_serving_mode(
        ServingModeRequest(mode=1), user=synthetic_admin()
    )
    assert result.swap_status == "idle"
    assert not (swap_env / "request.json").exists()


@pytest.mark.asyncio
async def test_post_non_admin_forbidden(swap_env):
    from fastapi import HTTPException

    from src.api.routes.settings import ServingModeRequest, request_serving_mode

    viewer = User(id="real-user-1", username="viewer", role="viewer")
    with pytest.raises(HTTPException) as exc:
        await request_serving_mode(ServingModeRequest(mode=2), user=viewer)
    assert exc.value.status_code == 403
    assert not (swap_env / "request.json").exists()


@pytest.mark.asyncio
async def test_get_reflects_watcher_status_files(swap_env):
    from src.api.routes.settings import get_serving_mode

    swap_env.mkdir(parents=True, exist_ok=True)
    (swap_env / "status.json").write_text(
        json.dumps(
            {
                "state": "swapping",
                "target": 2,
                "detail": "running mode-swap.sh up-mode2",
                "updated_at": "2026-07-07T14:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    result = await get_serving_mode(user=synthetic_admin())
    assert result.swap_status == "swapping"
    assert result.requested_mode == 2

    (swap_env / "status.json").write_text(
        json.dumps({"state": "error", "target": 2, "detail": "boom", "updated_at": "x"}),
        encoding="utf-8",
    )
    result = await get_serving_mode(user=synthetic_admin())
    assert result.swap_status == "error"
    assert result.detail == "boom"


@pytest.mark.asyncio
async def test_second_request_does_not_stack(swap_env):
    from src.api.routes.settings import ServingModeRequest, request_serving_mode

    first = await request_serving_mode(ServingModeRequest(mode=2), user=synthetic_admin())
    assert first.swap_status == "pending"
    # A second request while one is pending reports the in-flight state and
    # leaves the original request file untouched.
    before = (swap_env / "request.json").read_text(encoding="utf-8")
    second = await request_serving_mode(ServingModeRequest(mode=2), user=synthetic_admin())
    assert second.swap_status == "pending"
    assert (swap_env / "request.json").read_text(encoding="utf-8") == before
