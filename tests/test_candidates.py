"""
Candidate endpoint tests.
CAND-001 through CAND-008.
"""
import uuid


def create_event(client, headers, payload):
    resp = client.post("/api/v1/events", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def create_vendor(client, headers, payload):
    resp = client.post("/api/v1/vendors", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_list_candidates_empty(client, auth_headers, sample_event):
    """CAND-001: List candidates for event with no shortlisted vendors."""
    event_id = create_event(client, auth_headers, sample_event)

    resp = client.get(f"/api/v1/events/{event_id}/candidates", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []


def test_add_candidate(client, auth_headers, sample_event, sample_vendor):
    """CAND-002: Add vendor to event shortlist returns 201 with candidate+vendor data."""
    event_id = create_event(client, auth_headers, sample_event)
    vendor_id = create_vendor(client, auth_headers, sample_vendor)

    resp = client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["vendorId"] == vendor_id
    assert data["eventId"] == event_id
    assert data["status"] == "shortlisted"
    assert data["vendor"]["name"] == "Test Caterer"


def test_add_candidate_duplicate(client, auth_headers, sample_event, sample_vendor):
    """CAND-003: Adding the same vendor twice returns 409 conflict."""
    event_id = create_event(client, auth_headers, sample_event)
    vendor_id = create_vendor(client, auth_headers, sample_vendor)

    client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_add_candidate_vendor_not_owned(client, auth_headers, auth_headers_b, sample_event, sample_vendor):
    """CAND-004: Adding a vendor owned by a different user returns 404."""
    # user A creates event
    event_id = create_event(client, auth_headers, sample_event)
    # user B creates vendor
    vendor_id = create_vendor(client, auth_headers_b, sample_vendor)

    # user A tries to shortlist user B's vendor
    resp = client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_update_candidate(client, auth_headers, sample_event, sample_vendor):
    """CAND-005: Update candidate quoted_cost and status."""
    event_id = create_event(client, auth_headers, sample_event)
    vendor_id = create_vendor(client, auth_headers, sample_vendor)

    client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )

    resp = client.patch(
        f"/api/v1/events/{event_id}/candidates/{vendor_id}",
        json={"quotedCost": 75, "status": "awaitingConfirmation"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["quotedCost"] == 75
    assert body["data"]["status"] == "awaitingConfirmation"


def test_remove_candidate(client, auth_headers, sample_event, sample_vendor):
    """CAND-006: Remove candidate from shortlist — list is empty afterwards."""
    event_id = create_event(client, auth_headers, sample_event)
    vendor_id = create_vendor(client, auth_headers, sample_vendor)

    client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )

    del_resp = client.delete(
        f"/api/v1/events/{event_id}/candidates/{vendor_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    list_resp = client.get(
        f"/api/v1/events/{event_id}/candidates",
        headers=auth_headers,
    )
    assert list_resp.json()["data"] == []


def test_list_candidates_shows_vendor_data(client, auth_headers, sample_event, sample_vendor):
    """CAND-007: List candidates shows nested vendor object."""
    event_id = create_event(client, auth_headers, sample_event)
    vendor_id = create_vendor(client, auth_headers, sample_vendor)

    client.post(
        f"/api/v1/events/{event_id}/candidates",
        json={"vendorId": vendor_id},
        headers=auth_headers,
    )

    resp = client.get(
        f"/api/v1/events/{event_id}/candidates",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert "vendor" in data[0]
    assert data[0]["vendor"]["id"] == vendor_id
    assert data[0]["vendor"]["name"] == "Test Caterer"


def test_candidates_nonexistent_event(client, auth_headers):
    """CAND-008: Candidates for a non-existent event returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.get(
        f"/api/v1/events/{fake_id}/candidates",
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
