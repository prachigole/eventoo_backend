"""
User endpoint tests.
USER-001 through USER-003.
"""


def test_me_returns_manager_role(client, auth_headers):
    """USER-001: GET /me returns 200 with role='manager' for a new user."""
    resp = client.get("/api/v1/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["role"] == "manager"


def test_me_role_field_present(client, auth_headers):
    """USER-002: role key is present and non-null in /me response."""
    resp = client.get("/api/v1/me", headers=auth_headers)
    data = resp.json()["data"]
    assert "role" in data
    assert data["role"] is not None
    assert "id" in data


def test_two_users_both_default_to_manager(client, auth_headers, auth_headers_b):
    """USER-003: Two different users both default to role='manager'."""
    resp_a = client.get("/api/v1/me", headers=auth_headers)
    resp_b = client.get("/api/v1/me", headers=auth_headers_b)
    assert resp_a.json()["data"]["role"] == "manager"
    assert resp_b.json()["data"]["role"] == "manager"
    # Confirm they are different users
    assert resp_a.json()["data"]["id"] != resp_b.json()["data"]["id"]
