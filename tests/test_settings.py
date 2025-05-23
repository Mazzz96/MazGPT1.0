import pytest

def test_settings_unauth(client):
    resp = client.get("/user/settings")
    assert resp.status_code == 401
