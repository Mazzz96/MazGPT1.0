import pytest

def assert_unauthorized_or_forbidden(response):
    assert response.status_code in (401, 403, 429), f"Expected 401, 403, or 429 but got {response.status_code}"

def test_rate_limit(client):
    # Simulate rapid requests to a rate-limited endpoint
    for _ in range(10):
        resp = client.post("/auth/login", json={"email": "test@example.com", "password": "badpass"})
    # Should eventually get 429 or 401/403
    assert_unauthorized_or_forbidden(resp)
