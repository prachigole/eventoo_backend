"""
Task endpoint tests.
TASK-001 through TASK-012.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_event(client, headers, sample_event):
    return client.post("/api/v1/events", json=sample_event, headers=headers).json()["data"]


def create_task(client, headers, event_id, payload=None):
    payload = payload or {"title": "Setup stage"}
    return client.post(f"/api/v1/events/{event_id}/tasks", json=payload, headers=headers)


def become_employee(client, manager_headers, employee_headers):
    """Manager invites, employee accepts → employee role set."""
    token = client.post(
        "/api/v1/invites", json={"email": "emp@test.com"}, headers=manager_headers
    ).json()["data"]["token"]
    client.post("/api/v1/invites/accept", json={"token": token}, headers=employee_headers)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_manager_creates_root_task(client, auth_headers, sample_event):
    """TASK-001: Manager creates root task → 201, status=draft."""
    event = create_event(client, auth_headers, sample_event)
    resp = create_task(client, auth_headers, event["id"])
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "Setup stage"
    assert data["status"] == "draft"
    assert data["parentTaskId"] is None


def test_manager_creates_subtask(client, auth_headers, sample_event):
    """TASK-002: Manager creates sub-task with parent_task_id → 201."""
    event = create_event(client, auth_headers, sample_event)
    parent = create_task(client, auth_headers, event["id"]).json()["data"]

    resp = create_task(
        client, auth_headers, event["id"],
        {"title": "Subtask A", "parentTaskId": parent["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["parentTaskId"] == parent["id"]


def test_employee_cannot_create_task(client, auth_headers, auth_headers_b, sample_event):
    """TASK-003: Employee cannot create a task → 403."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    resp = create_task(client, auth_headers_b, event["id"])
    assert resp.status_code == 403


def test_manager_lists_all_tasks(client, auth_headers, sample_event):
    """TASK-004: Manager sees all tasks for their event."""
    event = create_event(client, auth_headers, sample_event)
    create_task(client, auth_headers, event["id"], {"title": "Task A"})
    create_task(client, auth_headers, event["id"], {"title": "Task B"})

    resp = client.get(f"/api/v1/events/{event['id']}/tasks", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_employee_sees_only_assigned_tasks(client, auth_headers, auth_headers_b, sample_event):
    """TASK-005: Employee sees only tasks assigned to them."""
    become_employee(client, auth_headers, auth_headers_b)

    # Get employee's user ID
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)

    # Create one assigned to employee, one unassigned
    create_task(client, auth_headers, event["id"], {"title": "For emp", "assignedTo": emp_id})
    create_task(client, auth_headers, event["id"], {"title": "Unassigned"})

    resp = client.get(f"/api/v1/events/{event['id']}/tasks", headers=auth_headers_b)
    tasks = resp.json()["data"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "For emp"


def test_unassigned_employee_gets_empty_list(client, auth_headers, auth_headers_b, sample_event):
    """TASK-006: Employee with no assigned tasks gets empty list, not 403."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    create_task(client, auth_headers, event["id"])

    resp = client.get(f"/api/v1/events/{event['id']}/tasks", headers=auth_headers_b)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_manager_patches_task(client, auth_headers, sample_event):
    """TASK-007: Manager PATCHes task title and priority → 200, fields updated."""
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event['id']}/tasks/{task_id}",
        json={"title": "Updated title", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "Updated title"
    assert data["priority"] == "high"


def test_employee_accepts_assigned_task(client, auth_headers, auth_headers_b, sample_event):
    """TASK-008: Employee accepts assigned task (status: assigned → accepted)."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]
    event = create_event(client, auth_headers, sample_event)

    task_id = create_task(
        client, auth_headers, event["id"], {"title": "AV Setup", "assignedTo": emp_id}
    ).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event['id']}/tasks/{task_id}",
        json={"status": "accepted"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "accepted"


def test_employee_cannot_patch_unassigned_task(client, auth_headers, auth_headers_b, sample_event):
    """TASK-009: Employee cannot PATCH a task not assigned to them → 404."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/events/{event['id']}/tasks/{task_id}",
        json={"status": "accepted"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 404


def test_employee_my_tasks(client, auth_headers, auth_headers_b, sample_event):
    """TASK-010: GET /my-tasks returns employee's tasks across events."""
    become_employee(client, auth_headers, auth_headers_b)
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]

    event = create_event(client, auth_headers, sample_event)
    create_task(client, auth_headers, event["id"], {"title": "My task", "assignedTo": emp_id})
    create_task(client, auth_headers, event["id"], {"title": "Not mine"})

    resp = client.get("/api/v1/my-tasks", headers=auth_headers_b)
    assert resp.status_code == 200
    tasks = resp.json()["data"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "My task"


def test_manager_deletes_task(client, auth_headers, sample_event):
    """TASK-011: Manager deletes task → 200."""
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.delete(
        f"/api/v1/events/{event['id']}/tasks/{task_id}", headers=auth_headers
    )
    assert resp.status_code == 200

    # Confirm gone
    tasks = client.get(f"/api/v1/events/{event['id']}/tasks", headers=auth_headers).json()["data"]
    assert len(tasks) == 0


def test_employee_cannot_delete_task(client, auth_headers, auth_headers_b, sample_event):
    """TASK-012: Employee cannot delete a task → 403."""
    become_employee(client, auth_headers, auth_headers_b)
    event = create_event(client, auth_headers, sample_event)
    task_id = create_task(client, auth_headers, event["id"]).json()["data"]["id"]

    resp = client.delete(
        f"/api/v1/events/{event['id']}/tasks/{task_id}", headers=auth_headers_b
    )
    assert resp.status_code == 403
