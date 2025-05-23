import pytest

def assert_unauthorized_or_forbidden(response):
    assert response.status_code in (401, 403), f"Expected 401 or 403 but got {response.status_code}"

def test_project_list_unauth(client):
    resp = client.get("/project/list/")
    assert_unauthorized_or_forbidden(resp)
