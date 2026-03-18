"""
Security tests.
SEC-001 through SEC-005.
"""
import uuid


def test_no_auth_token(client):
    """SEC-001: No auth token on protected endpoint returns 401."""
    for path in ["/api/v1/events", "/api/v1/vendors"]:
        resp = client.get(path)
        assert resp.status_code == 401, f"Expected 401 for GET {path}"
        assert resp.json()["success"] is False
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_malformed_token(client):
    """SEC-002: Token without 'Bearer ' prefix returns 401."""
    for path in ["/api/v1/events", "/api/v1/vendors"]:
        resp = client.get(path, headers={"Authorization": "Token somejunk"})
        assert resp.status_code == 401, f"Expected 401 for malformed token on GET {path}"
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_idor_events(client, auth_headers, auth_headers_b):
    """SEC-003: User A cannot read user B's events — IDOR protection."""
    # User A creates an event
    create_resp = client.post(
        "/api/v1/events",
        json={
            "title": "User A Event",
            "date": "2026-06-15",
            "venue": "Venue A",
            "category": "music",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["data"]["id"]

    # User A can access it
    resp_a = client.get(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert resp_a.status_code == 200

    # User B cannot access it (returns 404, not 403 — no information leakage)
    resp_b = client.get(f"/api/v1/events/{event_id}", headers=auth_headers_b)
    assert resp_b.status_code == 404

    # User B's event list is empty (does not include User A's event)
    list_resp_b = client.get("/api/v1/events", headers=auth_headers_b)
    assert list_resp_b.json()["data"]["items"] == []


def test_sql_injection_in_search(client, auth_headers):
    """SEC-004: SQL injection in search param does not crash the server."""
    malicious_inputs = [
        "'; DROP TABLE events; --",
        "1' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "%' AND 1=0 UNION ALL SELECT NULL,NULL,NULL --",
    ]
    for payload in malicious_inputs:
        resp = client.get(
            "/api/v1/events",
            params={"search": payload},
            headers=auth_headers,
        )
        # Should return 200 with empty results, not 500
        assert resp.status_code == 200, f"Got {resp.status_code} for search={payload!r}"
        assert resp.json()["success"] is True


def test_long_title_rejected(client, auth_headers):
    """SEC-005: Event title over 255 chars is rejected with 422."""
    long_title = "A" * 256
    resp = client.post(
        "/api/v1/events",
        json={
            "title": long_title,
            "date": "2026-06-15",
            "category": "music",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert resp.json()["success"] is False
