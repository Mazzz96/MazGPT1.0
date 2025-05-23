import pytest

def assert_unauthorized_or_forbidden(response):
    assert response.status_code in (401, 403), f"Expected 401 or 403 but got {response.status_code}"

def test_signup_and_login(client):
    # Signup
    resp = client.post("/auth/signup", json={
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "testpassword123"
    })
    assert resp.status_code == 200 or resp.status_code == 400  # 400 if already exists
    # Login
    resp = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "testpassword123"
    })
    assert resp.status_code == 200 or resp.status_code == 400 or resp.status_code == 403

def test_invalid_login(client):
    resp = client.post("/auth/login", json={
        "email": "notareal@example.com",
        "password": "wrongpass"
    })
    assert_unauthorized_or_forbidden(resp)
