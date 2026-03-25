"""
Task submission & review note tests.
SUB-001 through SUB-006.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup(client, manager_headers, auth_headers_b, sample_event):
    """Create event + task assigned to employee, walk employee to in_progress."""
    # Invite employee
    token = client.post(
        "/api/v1/invites", json={"email": "emp@sub.com"}, headers=manager_headers
    ).json()["data"]["token"]
    client.post("/api/v1/invites/accept", json={"token": token}, headers=auth_headers_b)

    # Get employee id
    emp_id = client.get("/api/v1/me", headers=auth_headers_b).json()["data"]["id"]

    # Create event + assigned task
    event = client.post("/api/v1/events", json=sample_event, headers=manager_headers).json()["data"]
    task_resp = client.post(
        f"/api/v1/events/{event['id']}/tasks",
        json={"title": "Write report", "assignedTo": emp_id},
        headers=manager_headers,
    ).json()["data"]
    task_id = task_resp["id"]
    event_id = event["id"]

    # Employee accepts → starts working
    client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "accepted"},
        headers=auth_headers_b,
    )
    client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers_b,
    )
    return event_id, task_id


def test_employee_submits_with_note(client, auth_headers, auth_headers_b, sample_event):
    """SUB-001: Employee submits with submission_note → status=submitted, note stored."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "submitted", "submissionNote": "All done, please review."},
        headers=auth_headers_b,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "submitted"
    assert data["submissionNote"] == "All done, please review."


def test_employee_submits_without_note(client, auth_headers, auth_headers_b, sample_event):
    """SUB-002: Employee submits without note → status=submitted, submissionNote=null."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "submitted"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "submitted"
    assert data["submissionNote"] is None


def test_employee_cannot_set_submission_note_on_wrong_status(
    client, auth_headers, auth_headers_b, sample_event
):
    """SUB-003: Employee cannot set submission_note when not transitioning to submitted → 400."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        # Still in_progress; trying to set note without submitting
        json={"submissionNote": "sneaky note"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 400


def test_manager_approves_with_review_note(client, auth_headers, auth_headers_b, sample_event):
    """SUB-004: Manager approves submitted task with review_note → status=approved, note stored."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    # Submit first
    client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "submitted"},
        headers=auth_headers_b,
    )

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "approved", "reviewNote": "Looks great!"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "approved"
    assert data["reviewNote"] == "Looks great!"


def test_manager_requests_revision_with_review_note(
    client, auth_headers, auth_headers_b, sample_event
):
    """SUB-005: Manager requests revision with note → status=revision_required, note stored."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "submitted"},
        headers=auth_headers_b,
    )

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "revision_required", "reviewNote": "Please fix section 2."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "revision_required"
    assert data["reviewNote"] == "Please fix section 2."


def test_employee_cannot_set_review_note(client, auth_headers, auth_headers_b, sample_event):
    """SUB-006: Employee trying to set review_note → 403."""
    event_id, task_id = _setup(client, auth_headers, auth_headers_b, sample_event)

    resp = client.patch(
        f"/api/v1/events/{event_id}/tasks/{task_id}",
        json={"status": "submitted", "reviewNote": "I reviewed myself"},
        headers=auth_headers_b,
    )
    assert resp.status_code == 403
