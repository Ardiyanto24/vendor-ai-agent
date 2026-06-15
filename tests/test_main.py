import os
import pytest
from fastapi.testclient import TestClient
import main
from main import app

client = TestClient(app)

def test_health_check():
    """
    Test that the health check endpoint returns 200 and has the expected keys.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "supabase" in data
    assert "openrouter" in data
    assert "google" in data
    assert "tavily" in data
    assert "uptime_seconds" in data
    assert "version" in data

def test_middleware_blocks_unauthorized():
    """
    Test that endpoints requiring service token block requests without X-Service-Token header.
    """
    response = client.get("/v1/any-endpoint")
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Invalid service token" in response.json()["detail"]

def test_middleware_allows_excluded_endpoints():
    """
    Test that /health and /v1/chat/stream are excluded from the token check.
    """
    # /health should work without token
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    
    # /v1/chat/stream should bypass auth (and return 501 Not Implemented instead of 401 Unauthorized)
    resp_stream = client.get("/v1/chat/stream")
    assert resp_stream.status_code == 501
    
    # /docs should also bypass auth (and return 200 OK)
    resp_docs = client.get("/docs")
    assert resp_docs.status_code == 200

def test_middleware_allows_authorized():
    """
    Test that sending the correct X-Service-Token header bypasses the auth block.
    """
    # Temporarily set the server-side service token
    original_token = main.SERVICE_TOKEN
    main.SERVICE_TOKEN = "valid-test-token"
    
    try:
        # Request with correct token to a non-existent route should return 404 (Passed Auth), not 401
        headers = {"X-Service-Token": "valid-test-token"}
        response = client.get("/v1/non-existent-route", headers=headers)
        assert response.status_code == 404
    finally:
        # Restore original token
        main.SERVICE_TOKEN = original_token
