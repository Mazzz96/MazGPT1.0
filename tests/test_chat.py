import pytest

def assert_unauthorized_or_forbidden(response):
    assert response.status_code in (401, 403), f"Expected 401 or 403 but got {response.status_code}"

def test_chat_send_unauth(client):
    resp = client.post("/chat/send", json={"project_id": "default", "message": "Hello"})
    assert_unauthorized_or_forbidden(resp)
