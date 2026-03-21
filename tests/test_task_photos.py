"""
Task photo endpoint tests.
PHOTO-001 through PHOTO-005.
"""

# Minimal valid JPEG header (12 bytes) — enough for content-type sniffing
_FAKE_JPEG = bytes([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10,
    0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
])


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_event(client, headers, sample_event):
    return client.post("/api/v1/events", json=sample_event, headers=headers).json()["data"]


def create_task(client, headers, event_id, payload=None):
    payload = payload or {"title": "Setup stage"}
    return client.post(f"/api/v1/events/{event_id}/tasks", json=payload, headers=headers)


def become_employee(client, manager_headers, employee_headers):
    token = client.post(
        "/api/v1/invites", json={"email": "emp@test.com"}, headers=manager_headers
    ).json()["data"]["token"]
    client.post("/api/v1/invites/accept", json={"token": token}, headers=employee_headers)


def upload_photo(client, employee_headers, event_id, task_id):
    return client.post(
        f"/api/v1/events/{event_id}/tasks/{task_id}/photos",
        files={"file": ("photo.jpg", _FAKE_JPEG, "image/jpeg")},
        headers=employee_headers,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_employee_uploads_photo(client, auth_headers, auth_headers_b, sample_event):
    """PHOTO-001: Employee uploads photo → 201, filePath contains task id."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"], {"title": "T", "assignedTo": emp_id}
    ).json()["data"]["id"]

    resp = upload_photo(client, auth_headers_b, event["id"], task_id)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert task_id in data["filePath"]
    assert data["originalName"] == "photo.jpg"


def test_manager_cannot_upload_photo(client, auth_headers, sample_event):
    """PHOTO-002: Manager cannot upload photo → 403."""
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.post(
        f"/api/v1/events/{event['id']}/tasks/{task_id}/photos",
        files={"file": ("photo.jpg", _FAKE_JPEG, "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_employee_cannot_upload_to_unassigned_task(
    client, auth_headers, auth_headers_b, sample_event
):
    """PHOTO-003: Employee cannot upload to task not assigned to them → 404."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = upload_photo(client, auth_headers_b, event["id"], task_id)
    assert resp.status_code == 404


def test_manager_lists_photos(client, auth_headers, auth_headers_b, sample_event):
    """PHOTO-004: Manager lists photos for a task → 200, length matches uploads."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"], {"title": "T", "assignedTo": emp_id}
    ).json()["data"]["id"]

    upload_photo(client, auth_headers_b, event["id"], task_id)
    upload_photo(client, auth_headers_b, event["id"], task_id)

    resp = client.get(
        f"/api/v1/events/{event['id']}/tasks/{task_id}/photos", headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_manager_deletes_photo(client, auth_headers, auth_headers_b, sample_event):
    """PHOTO-005: Manager deletes photo → 200, no longer in list."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"], {"title": "T", "assignedTo": emp_id}
    ).json()["data"]["id"]

    photo_id = upload_photo(
        client, auth_headers_b, event["id"], task_id
    ).json()["data"]["id"]

    resp = client.delete(
        f"/api/v1/events/{event['id']}/tasks/{task_id}/photos/{photo_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200

    photos = client.get(
        f"/api/v1/events/{event['id']}/tasks/{task_id}/photos", headers=auth_headers
    ).json()["data"]
    assert len(photos) == 0
