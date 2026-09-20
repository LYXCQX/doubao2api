"""
Integration tests for FastAPI endpoints (using TestClient).
"""
import os
import pytest
from fastapi.testclient import TestClient
from doubao2api.unified_server import create_app


@pytest.fixture
def app_unauthenticated():
    # App created without API key
    return create_app(api_key=None)


@pytest.fixture
def app_authenticated():
    # App created with API key
    return create_app(api_key="sk-testsecretkey")


@pytest.mark.integration
def test_health_endpoints(app_unauthenticated):
    client = TestClient(app_unauthenticated)

    # 1. Liveness check should always succeed
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json() == {"status": "alive"}

    # 2. Readiness check should return 503 since browser is not running
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 503
    assert res_ready.json()["error"]["code"] == 503

    # 3. Legacy composite health endpoint
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["live"] is True
    assert data["ready"] is False
    assert data["status"] == "not_ready"


@pytest.mark.integration
def test_auth_headers_and_query_param_rejection(app_authenticated):
    client = TestClient(app_authenticated)

    # No auth header -> 401
    res_no_auth = client.get("/v1/models")
    assert res_no_auth.status_code == 401

    # Query param ?key=sk-testsecretkey MUST BE REJECTED (P0.3 security requirement)
    res_query_key = client.get("/v1/models?key=sk-testsecretkey")
    assert res_query_key.status_code == 401

    # Bearer token -> 200
    res_bearer = client.get("/v1/models", headers={"Authorization": "Bearer sk-testsecretkey"})
    assert res_bearer.status_code == 200
    assert "data" in res_bearer.json()

    # X-API-Key header -> 200
    res_x_api = client.get("/v1/models", headers={"X-API-Key": "sk-testsecretkey"})
    assert res_x_api.status_code == 200


@pytest.mark.integration
def test_auth_eval_disabled_in_production(app_unauthenticated):
    client = TestClient(app_unauthenticated)
    os.environ["DEV_MODE"] = "false"
    os.environ["DEBUG"] = "false"

    # /auth/eval must return 403 in production
    res = client.post("/auth/eval", json={"js": "1+1"})
    assert res.status_code == 403
    assert "disabled in production" in res.json()["error"]["message"]


@pytest.mark.integration
def test_chat_completions_degraded_when_not_ready(app_unauthenticated):
    client = TestClient(app_unauthenticated)

    # Requesting completions when browser is not ready should yield 503
    res = client.post("/v1/chat/completions", json={
        "model": "doubao",
        "messages": [{"role": "user", "content": "hello"}],
    })
    assert res.status_code == 503
    assert "Browser client failed to start" in res.json()["error"]["message"] or "Not logged in" in res.json()["error"]["message"]
