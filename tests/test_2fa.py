import pytest

def test_2fa_status(client):
    # Should return 401 if not logged in
    resp = client.get("/auth/2fa/status")
    assert resp.status_code == 401

# More 2FA tests (enable, verify, disable) require login/session handling
