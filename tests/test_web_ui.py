import pytest
from fastapi.testclient import TestClient
from doubao2api.unified_server import create_app

def test_web_ui_routes():
    app = create_app(api_key=None)
    client = TestClient(app, follow_redirects=False)

    # 1. Root route redirect
    resp = client.get("/")
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin"

    # 2. Auth redirect
    resp = client.get("/auth?key=test1234")
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/admin?key=test1234"

    # 3. Admin dashboard HTML
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Doubao 2API 控制台" in resp.text
    assert "apiBaseUrl" in resp.text
    assert "纯净免窗口扫码登录" in resp.text

    # 4. Health
    resp = client.get("/health")
    assert resp.status_code == 200

    # 5. Models list
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    model_ids = [m["id"] for m in data["data"]]
    assert "doubao-2.1-turbo" in model_ids
    assert "doubao-think" in model_ids

def test_web_ui_with_api_key():
    app = create_app(api_key="secret123")
    client = TestClient(app, follow_redirects=False)

    # Admin dashboard should render (allows entering key in UI)
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert "Doubao 2API 控制台" in resp.text

    # System API without key should be 401
    resp = client.get("/admin/api/system")
    assert resp.status_code == 401

    # System API with query key should be rejected (P0 security requirement)
    resp = client.get("/admin/api/system?key=secret123")
    assert resp.status_code == 401

    # System API with X-API-Key header should succeed
    resp = client.get("/admin/api/system", headers={"X-API-Key": "secret123"})
    assert resp.status_code == 200
    sys_info = resp.json()
    assert "platform" in sys_info
    assert "models" in sys_info

    # System API with Bearer token should succeed
    resp = client.get("/admin/api/system", headers={"Authorization": "Bearer secret123"})
    assert resp.status_code == 200
