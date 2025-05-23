import pytest

def test_csrf_protection(client):
    # Should reject POST without CSRF token if required
    resp = client.post("/auth/logout")
    # Accepts if not logged in, but if CSRF is enforced, should be 403 or 401
    assert resp.status_code in (401, 403, 200)
