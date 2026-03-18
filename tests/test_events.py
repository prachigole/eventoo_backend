"""
Event endpoint tests.
EVENT-001 through EVENT-013.
"""
import uuid


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_event(client, headers, payload):
    return client.post("/api/v1/events", json=payload, headers=headers)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_list_events_empty(client, auth_headers):
    """EVENT-001: Authenticated user with no events gets empty list."""
    resp = client.get("/api/v1/events", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["data"]["meta"]["total"] == 0


def test_create_event_valid(client, auth_headers, sample_event):
    """EVENT-002: Create event with valid payload returns 201 and event object."""
    resp = create_event(client, auth_headers, sample_event)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["title"] == "Test Concert"
    assert data["category"] == "music"
    assert data["status"] == "upcoming"
    assert "id" in data


def test_create_event_missing_title(client, auth_headers, sample_event):
    """EVENT-003: Create event without title returns 422."""
    payload = {k: v for k, v in sample_event.items() if k != "title"}
    resp = create_event(client, auth_headers, payload)
    assert resp.status_code == 422
    assert resp.json()["success"] is False


def test_create_event_invalid_category(client, auth_headers, sample_event):
    """EVENT-004: Create event with invalid category returns 422."""
    payload = {**sample_event, "category": "invalid_category"}
    resp = create_event(client, auth_headers, payload)
    assert resp.status_code == 422
    assert resp.json()["success"] is False


def test_get_event_by_id(client, auth_headers, sample_event):
    """EVENT-005: Get event by id returns the correct event."""
    create_resp = create_event(client, auth_headers, sample_event)
    event_id = create_resp.json()["data"]["id"]

    resp = client.get(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] == event_id
    assert body["data"]["title"] == "Test Concert"
    # EventDetail includes candidates array
    assert "candidates" in body["data"]


def test_get_nonexistent_event(client, auth_headers):
    """EVENT-006: Get non-existent event returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/events/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_update_event(client, auth_headers, sample_event):
    """EVENT-007: PATCH event updates the specified field."""
    event_id = create_event(client, auth_headers, sample_event).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event_id}",
        json={"title": "Updated Concert", "status": "ongoing"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Updated Concert"
    assert body["data"]["status"] == "ongoing"


def test_update_event_not_owned(client, auth_headers):
    """EVENT-008: PATCH on a non-existent (or not-owned) event returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.patch(
        f"/api/v1/events/{fake_id}",
        json={"title": "Hacked"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_delete_event(client, auth_headers, sample_event):
    """EVENT-009: DELETE event returns 200; subsequent list is empty."""
    event_id = create_event(client, auth_headers, sample_event).json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    list_resp = client.get("/api/v1/events", headers=auth_headers)
    assert list_resp.json()["data"]["items"] == []


def test_list_events_status_filter(client, auth_headers, sample_event):
    """EVENT-010: List events filtered by status."""
    # Create upcoming event
    create_event(client, auth_headers, sample_event)
    # Create past event
    create_event(client, auth_headers, {**sample_event, "title": "Past Gig", "status": "past"})

    resp = client.get("/api/v1/events?status=past", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["status"] == "past"
    assert items[0]["title"] == "Past Gig"


def test_list_events_search_filter(client, auth_headers, sample_event):
    """EVENT-011: List events filtered by search term."""
    create_event(client, auth_headers, sample_event)
    create_event(client, auth_headers, {**sample_event, "title": "Corporate Summit"})

    resp = client.get("/api/v1/events?search=Summit", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Corporate Summit"


def test_no_auth_header(client, sample_event):
    """EVENT-012: Missing auth header returns 401."""
    resp = client.get("/api/v1/events")
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_create_then_list(client, auth_headers, sample_event):
    """EVENT-013: Created event appears in the list."""
    create_event(client, auth_headers, sample_event)
    resp = client.get("/api/v1/events", headers=auth_headers)
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Test Concert"
