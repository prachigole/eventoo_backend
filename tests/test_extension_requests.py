"""
Extension request endpoint tests.
EXT-001 through EXT-006.
"""


# ── Helpers (imported pattern from test_tasks) ────────────────────────────────

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


def submit_extension_request(client, employee_headers, event_id, task_id, new_date="2026-07-01"):
    return client.post(
        f"/api/v1/events/{event_id}/tasks/{task_id}/extension-requests",
        json={"newDueDate": new_date, "reason": "Need more time"},
        headers=employee_headers,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_employee_submits_extension_request(client, auth_headers, auth_headers_b, sample_event):
    """EXT-001: Employee submits extension request → 201, status=pending."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"], {"title": "T", "assignedTo": emp_id}
    ).json()["data"]["id"]

    resp = submit_extension_request(client, auth_headers_b, event["id"], task_id)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "pending"
    assert data["newDueDate"] == "2026-07-01"
    assert data["reason"] == "Need more time"


def test_manager_cannot_submit_extension_request(client, auth_headers, sample_event):
    """EXT-002: Manager cannot submit extension request → 403."""
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.post(
        f"/api/v1/events/{event['id']}/tasks/{task_id}/extension-requests",
        json={"newDueDate": "2026-07-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_employee_cannot_request_extension_for_unassigned_task(
    client, auth_headers, auth_headers_b, sample_event
):
    """EXT-003: Employee cannot request extension for a task not assigned to them → 404."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = submit_extension_request(client, auth_headers_b, event["id"], task_id)
    assert resp.status_code == 404


def test_manager_lists_extension_requests(client, auth_headers, auth_headers_b, sample_event):
    """EXT-004: Manager lists extension requests for event → 200, list length matches."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"], {"title": "T", "assignedTo": emp_id}
    ).json()["data"]["id"]

    submit_extension_request(client, auth_headers_b, event["id"], task_id)

    resp = client.get(f"/api/v1/events/{event['id']}/extension-requests", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


def test_manager_approves_extension_request(client, auth_headers, auth_headers_b, sample_event):
    """EXT-005: Manager approves → task due_date updated to requested date."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"],
        {"title": "T", "assignedTo": emp_id, "dueDate": "2026-06-15"},
    ).json()["data"]["id"]

    req_id = submit_extension_request(
        client, auth_headers_b, event["id"], task_id, "2026-07-01"
    ).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event['id']}/extension-requests/{req_id}",
        json={"status": "approved"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "approved"

    # Confirm task due_date was updated
    tasks = client.get(
        f"/api/v1/events/{event['id']}/tasks", headers=auth_headers
    ).json()["data"]
    assert tasks[0]["dueDate"] == "2026-07-01"


def test_manager_rejects_extension_request(client, auth_headers, auth_headers_b, sample_event):
    """EXT-006: Manager rejects → task due_date unchanged."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(
        client, auth_headers, event["id"],
        {"title": "T", "assignedTo": emp_id, "dueDate": "2026-06-15"},
    ).json()["data"]["id"]

    req_id = submit_extension_request(
        client, auth_headers_b, event["id"], task_id, "2026-07-01"
    ).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event['id']}/extension-requests/{req_id}",
        json={"status": "rejected"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "rejected"

    tasks = client.get(
        f"/api/v1/events/{event['id']}/tasks", headers=auth_headers
    ).json()["data"]
    assert tasks[0]["dueDate"] == "2026-06-15"
