"""
Tests for Img2Img (image edits) and Img2Video (video generations with reference image).
"""
import base64
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from doubao2api.unified_server import create_app


@pytest.fixture
def mock_browser_client():
    client = MagicMock()
    client.is_ready = True
    client.needs_captcha = False
    client.consecutive_failures = 0
    client.last_error_code = None
    client.headless = True
    client.browser_name = "chromium"

    client.is_alive = AsyncMock(return_value=True)
    client.upload_image = AsyncMock(return_value={
        "uri": "tos-cn-i-mock/ref_image_123.png",
        "cdn_url": "https://tos.mock.com/ref_image_123.png",
        "name": "ref_image.png",
        "format": "png",
    })
    client.generate_image = AsyncMock(return_value={
        "images": [{"url": "https://tos.mock.com/generated_img.png"}],
    })
    client.generate_video = AsyncMock(return_value={
        "videos": [{"video_url": "https://tos.mock.com/generated_vid.mp4", "duration": 5}],
    })
    return client


@pytest.fixture
def test_app(mock_browser_client):
    app = create_app(browser_client=mock_browser_client)
    yield app, mock_browser_client


def test_images_generations_with_tos_key(test_app):
    app, mock_client = test_app
    with patch.dict(app.extra if hasattr(app, "extra") else {}, {}):
        # Inject client into app closure
        from doubao2api import unified_server
        client = TestClient(app)
        
        # Test images/generations with direct ref_image_key
        resp = client.post(
            "/v1/images/generations",
            json={
                "prompt": "一只戴墨镜的猫",
                "ref_image_key": "tos-cn-i-mock/original.png",
                "size": "1024x1024",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["url"] == "https://tos.mock.com/generated_img.png"
        mock_client.generate_image.assert_called_with(
            prompt="一只戴墨镜的猫",
            ratio="1:1",
            ref_image_key="tos-cn-i-mock/original.png",
        )


def test_images_generations_with_base64_data_uri(test_app):
    app, mock_client = test_app
    client = TestClient(app)

    # 1x1 transparent png in base64
    b64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    resp = client.post(
        "/v1/images/generations",
        json={
            "prompt": "生成相似图片",
            "image": b64_png,
            "size": "1792x1024",
        },
    )
    assert resp.status_code == 200
    mock_client.upload_image.assert_called_once()
    mock_client.generate_image.assert_called_with(
        prompt="生成相似图片",
        ratio="16:9",
        ref_image_key="tos-cn-i-mock/ref_image_123.png",
    )


def test_images_edits_endpoint_json(test_app):
    app, mock_client = test_app
    client = TestClient(app)

    resp = client.post(
        "/v1/images/edits",
        json={
            "prompt": "变成赛博朋克风格",
            "image": "tos-cn-i-mock/city.png",
            "size": "1024x1024",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"][0]["revised_prompt"] == "变成赛博朋克风格"
    mock_client.generate_image.assert_called_with(
        prompt="变成赛博朋克风格",
        ratio="1:1",
        ref_image_key="tos-cn-i-mock/city.png",
    )


def test_images_edits_endpoint_multipart(test_app):
    app, mock_client = test_app
    client = TestClient(app)

    file_content = b"fake-png-data"
    resp = client.post(
        "/v1/images/edits",
        data={"prompt": "水彩画风格", "size": "1024x1024"},
        files={"image": ("test.png", file_content, "image/png")},
    )
    assert resp.status_code == 200
    mock_client.upload_image.assert_called_once()
    mock_client.generate_image.assert_called_with(
        prompt="水彩画风格",
        ratio="1:1",
        ref_image_key="tos-cn-i-mock/ref_image_123.png",
    )


def test_video_generations_with_reference_image(test_app):
    app, mock_client = test_app
    client = TestClient(app)

    resp = client.post(
        "/v1/video/generations",
        json={
            "prompt": "让镜头向前推进，树叶随风飘落",
            "ratio": "16:9",
            "ref_image_key": "tos-cn-i-mock/autumn_forest.png",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["video_url"] == "https://tos.mock.com/generated_vid.mp4"
    mock_client.generate_video.assert_called_with(
        prompt="让镜头向前推进，树叶随风飘落",
        ratio="16:9",
        ref_image_key="tos-cn-i-mock/autumn_forest.png",
    )


def test_ssrf_blocked_in_image_resolution(test_app):
    app, mock_client = test_app
    client = TestClient(app)

    # Private IP should be blocked
    resp = client.post(
        "/v1/images/generations",
        json={
            "prompt": "测试内网拦截",
            "image": "http://127.0.0.1:8080/secret.png",
        },
    )
    assert resp.status_code == 400
    assert "SSRF" in resp.json()["error"]["message"]
