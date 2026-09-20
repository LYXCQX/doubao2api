"""
Tests for P0-P2 convenience features:
- Model aliasing and auto-fallback
- SSE keep-alive ping
- Account rename and batch probe
- Recent media gallery
- Port conflict detection
"""
import asyncio
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from doubao2api.account_manager import AccountManager
from doubao2api.unified_server import (
    create_app,
    MODEL_ALIASES,
    CHAT_MODELS,
    ALL_MODELS,
    _is_port_in_use,
    _recent_media,
    _record_recent_media,
)


@pytest.fixture
def temp_accounts_file():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_model_aliases_in_models_list():
    """Verify that common aliases are included in /v1/models list."""
    mock_client = MagicMock()
    mock_client.is_ready = True
    app = create_app(browser_client=mock_client)
    client = TestClient(app)

    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()["data"]
    model_ids = {m["id"] for m in data}

    # Verify native models and key aliases
    assert "doubao-2.1-turbo" in model_ids
    assert "doubao-think" in model_ids
    assert "gpt-4o" in model_ids
    assert "gpt-3.5-turbo" in model_ids
    assert "deepseek-reasoner" in model_ids


def test_model_alias_resolution_and_fallback():
    """Test that chat_completions maps aliases and falls back gracefully on unknown models."""
    mock_client = MagicMock()
    mock_client.is_ready = True
    mock_client.needs_captcha = False
    mock_client.is_captcha_visible = AsyncMock(return_value=False)
    mock_client.extract_conversation_id = MagicMock(return_value="c_123")

    calls = []

    def mock_chat_completion(prompt, use_deep_think=0, **kwargs):
        calls.append((prompt, use_deep_think))
        async def _gen():
            yield {
                "_event": "CHUNK_DELTA",
                "text": f"Response for deep_think={use_deep_think}",
            }
        return _gen()

    mock_client.chat_completion = mock_chat_completion
    mock_client.record_success = MagicMock()

    app = create_app(browser_client=mock_client)
    client = TestClient(app)

    # 1. Standard alias: gpt-4o -> doubao-2.1-turbo (use_deep_think=0)
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "gpt-4o"
    assert calls[-1] == ("hello", 0)

    # 2. Reasoning alias: deepseek-reasoner -> doubao-think (use_deep_think=1)
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "deepseek-reasoner", "messages": [{"role": "user", "content": "reason this"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "deepseek-reasoner"
    assert calls[-1] == ("reason this", 1)

    # 3. Unknown model -> falls back to doubao-2.1-turbo without 400 error!
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "completely-unknown-custom-model", "messages": [{"role": "user", "content": "fallback"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "completely-unknown-custom-model"
    assert calls[-1] == ("fallback", 0)


def test_account_rename_and_probe_all(temp_accounts_file):
    """Test account renaming and batch probe endpoints."""
    mgr = AccountManager(filepath=temp_accounts_file)
    acc = mgr.add_or_update_account("旧名称", {"sessionid": "sess_1234567890abcdef"})

    mock_client = MagicMock()
    mock_client.account_manager = mgr
    mock_client.is_ready = True

    app = create_app(browser_client=mock_client)
    client = TestClient(app)

    # 1. Rename account
    resp = client.post("/admin/api/accounts/rename", json={"account_id": acc.id, "name": "新备注名称"})
    assert resp.status_code == 200
    assert resp.json()["renamed"] is True
    assert mgr.get_account(acc.id).name == "新备注名称"

    # 2. Probe all accounts
    resp = client.post("/admin/api/accounts/probe_all")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == acc.id
    assert results[0]["valid"] is True


def test_recent_media_gallery():
    """Test recent media buffer and API endpoint."""
    _recent_media.clear()
    _record_recent_media("image", "https://example.com/img1.png", "画一只可爱的猫", model="doubao-image")
    _record_recent_media("video", "https://example.com/vid1.mp4", "海浪拍打沙滩", cover_url="https://example.com/cover1.png", model="doubao-video")

    mock_client = MagicMock()
    mock_client.is_ready = True
    app = create_app(browser_client=mock_client)
    client = TestClient(app)

    resp = client.get("/admin/api/media/recent")
    assert resp.status_code == 200
    media_list = resp.json()["media"]
    assert len(media_list) == 2
    assert media_list[0]["type"] == "video"
    assert media_list[0]["prompt"] == "海浪拍打沙滩"
    assert media_list[1]["type"] == "image"


def test_is_port_in_use():
    """Test port in use helper function."""
    import socket
    # Bind a temporary port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.listen(1)

    assert _is_port_in_use(port) is True

    s.close()
    assert _is_port_in_use(port) is False
