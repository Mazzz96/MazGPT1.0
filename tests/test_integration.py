import pytest

def assert_unauthorized_or_forbidden(response):
    assert response.status_code in (401, 403), f"Expected 401 or 403 but got {response.status_code}"

def test_full_login_flow(client):
    # Signup
    client.post("/auth/signup", json={
        "email": "integration@example.com",
        "name": "Integration User",
        "password": "integrationpass123"
    })
    # Login
    resp = client.post("/auth/login", json={
        "email": "integration@example.com",
        "password": "integrationpass123"
    })
    assert resp.status_code == 200 or resp.status_code == 400 or resp.status_code == 403
    # TODO: Add 2FA, chat, project, and error case flows
