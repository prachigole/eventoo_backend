"""
Vendor endpoint tests.
VENDOR-001 through VENDOR-011.
"""
import uuid


def create_vendor(client, headers, payload):
    return client.post("/api/v1/vendors", json=payload, headers=headers)


def test_list_vendors_empty(client, auth_headers):
    """VENDOR-001: Authenticated user with no vendors gets empty list."""
    resp = client.get("/api/v1/vendors", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["items"] == []


def test_create_vendor_valid(client, auth_headers, sample_vendor):
    """VENDOR-002: Create vendor with valid payload returns 201."""
    resp = create_vendor(client, auth_headers, sample_vendor)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["name"] == "Test Caterer"
    assert data["category"] == "catering"
    assert data["rating"] == 4.5
    assert "id" in data


def test_create_vendor_missing_name(client, auth_headers, sample_vendor):
    """VENDOR-003: Create vendor missing required field (name) returns 422."""
    payload = {k: v for k, v in sample_vendor.items() if k != "name"}
    resp = create_vendor(client, auth_headers, payload)
    assert resp.status_code == 422
    assert resp.json()["success"] is False


def test_get_vendor_by_id(client, auth_headers, sample_vendor):
    """VENDOR-004: Get vendor by id returns the correct vendor."""
    vendor_id = create_vendor(client, auth_headers, sample_vendor).json()["data"]["id"]

    resp = client.get(f"/api/v1/vendors/{vendor_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["id"] == vendor_id
    assert body["data"]["name"] == "Test Caterer"
    # VendorDetail includes notes, createdAt, updatedAt
    assert "notes" in body["data"]
    assert "createdAt" in body["data"]


def test_get_nonexistent_vendor(client, auth_headers):
    """VENDOR-005: Get non-existent vendor returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/vendors/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_update_vendor(client, auth_headers, sample_vendor):
    """VENDOR-006: PATCH vendor updates specified field."""
    vendor_id = create_vendor(client, auth_headers, sample_vendor).json()["data"]["id"]

    resp = client.patch(
        f"/api/v1/vendors/{vendor_id}",
        json={"rating": 4.9, "eventsWorked": 15},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["rating"] == 4.9
    assert body["data"]["eventsWorked"] == 15


def test_delete_vendor(client, auth_headers, sample_vendor):
    """VENDOR-007: DELETE vendor then GET returns 404."""
    vendor_id = create_vendor(client, auth_headers, sample_vendor).json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/vendors/{vendor_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    get_resp = client.get(f"/api/v1/vendors/{vendor_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_list_vendors_category_filter(client, auth_headers, sample_vendor):
    """VENDOR-008: List vendors filtered by category."""
    # catering vendor
    create_vendor(client, auth_headers, sample_vendor)
    # photography vendor
    create_vendor(
        client, auth_headers,
        {**sample_vendor, "name": "Photo Pro", "category": "photography"},
    )

    resp = client.get("/api/v1/vendors?category=photography", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Photo Pro"


def test_list_vendors_search(client, auth_headers, sample_vendor):
    """VENDOR-009: List vendors filtered by search term."""
    create_vendor(client, auth_headers, sample_vendor)
    create_vendor(
        client, auth_headers,
        {**sample_vendor, "name": "Royal Lights"},
    )

    resp = client.get("/api/v1/vendors?search=Royal", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Royal Lights"


def test_list_vendors_min_rating(client, auth_headers, sample_vendor):
    """VENDOR-010: List vendors with min_rating filter."""
    # rating 4.5
    create_vendor(client, auth_headers, sample_vendor)
    # low rating vendor
    create_vendor(
        client, auth_headers,
        {**sample_vendor, "name": "Budget Caterer", "rating": 2.0},
    )

    resp = client.get("/api/v1/vendors?min_rating=4.0", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Test Caterer"


def test_vendors_no_auth(client):
    """VENDOR-011: No auth header returns 401."""
    resp = client.get("/api/v1/vendors")
    assert resp.status_code == 401
