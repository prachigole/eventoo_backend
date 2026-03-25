"""
Client portal endpoint tests.
CLIENT-001 through CLIENT-007.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_event(client, headers, sample_event):
    return client.post("/api/v1/events", json=sample_event, headers=headers).json()["data"]


def _create_invite(client, manager_headers, event_id):
    """Manager creates a client invite token; returns the raw token string."""
    resp = client.post(
        f"/api/v1/events/{event_id}/client-invite", headers=manager_headers
    )
    assert resp.status_code == 201
    return resp.json()["data"]["token"]


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_manager_creates_client_invite(client, auth_headers, sample_event):
    """CLIENT-001: Manager creates invite → 201, token returned."""
    event = _create_event(client, auth_headers, sample_event)
    resp = client.post(
        f"/api/v1/events/{event['id']}/client-invite", headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "token" in data
    assert len(data["token"]) > 20
    assert data["eventId"] == event["id"]


def test_employee_cannot_create_client_invite(client, auth_headers, auth_headers_b, sample_event):
    """CLIENT-002: Employee cannot create a client invite → 403."""
    # Make auth_headers_b an employee via invite
    token = client.post(
        "/api/v1/invites", json={"email": "emp@c.com"}, headers=auth_headers
    ).json()["data"]["token"]
    client.post("/api/v1/invites/accept", json={"token": token}, headers=auth_headers_b)

    event = _create_event(client, auth_headers, sample_event)
    resp = client.post(
        f"/api/v1/events/{event['id']}/client-invite", headers=auth_headers_b
    )
    assert resp.status_code == 403


def test_client_accepts_invite(client, auth_headers, auth_headers_b, sample_event):
    """CLIENT-003: Client redeems token → role=client, linked to event."""
    event = _create_event(client, auth_headers, sample_event)
    token = _create_invite(client, auth_headers, event["id"])

    resp = client.post(
        "/api/v1/client-invites/accept", json={"token": token}, headers=auth_headers_b
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["eventId"] == event["id"]

    # Verify role changed
    me = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]
    assert me["role"] == "client"


def test_invite_cannot_be_reused(client, auth_headers, auth_headers_b, sample_event):
    """CLIENT-004: Same token used twice → 400."""
    event = _create_event(client, auth_headers, sample_event)
    token = _create_invite(client, auth_headers, event["id"])

    client.post(
        "/api/v1/client-invites/accept", json={"token": token}, headers=auth_headers_b
    )
    resp = client.post(
        "/api/v1/client-invites/accept", json={"token": token}, headers=auth_headers_b
    )
    assert resp.status_code == 400


def test_client_portal_data(client, auth_headers, auth_headers_b, sample_event):
    """CLIENT-005: Client sees event + task summary + approved tasks."""
    event = _create_event(client, auth_headers, sample_event)

    # Create two tasks — approve one
    t1 = client.post(
        f"/api/v1/events/{event['id']}/tasks",
        json={"title": "Stage setup"},
        headers=auth_headers,
    ).json()["data"]
    client.patch(
        f"/api/v1/events/{event['id']}/tasks/{t1['id']}",
        json={"status": "approved"},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/events/{event['id']}/tasks",
        json={"title": "Catering"},
        headers=auth_headers,
    )

    # Client accepts invite
    token = _create_invite(client, auth_headers, event["id"])
    client.post(
        "/api/v1/client-invites/accept", json={"token": token}, headers=auth_headers_b
    )

    resp = client.get("/api/v1/my-client-event", headers=auth_headers_b)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["event"]["title"] == sample_event["title"]
    assert data["taskSummary"]["total"] == 2
    assert data["taskSummary"]["approved"] == 1
    assert len(data["approvedTasks"]) == 1
    assert data["approvedTasks"][0]["title"] == "Stage setup"


def test_manager_cannot_access_client_portal(client, auth_headers, sample_event):
    """CLIENT-006: Manager calling /my-client-event → 403."""
    resp = client.get("/api/v1/my-client-event", headers=auth_headers)
    assert resp.status_code == 403


def test_invalid_token_rejected(client, auth_headers_b):
    """CLIENT-007: Invalid token → 404."""
    resp = client.post(
        "/api/v1/client-invites/accept",
        json={"token": "totally-fake-token"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 404
