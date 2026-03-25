"""
Invite endpoint tests.
INVITE-001 through INVITE-006.
"""
import uuid
from datetime import datetime, timedelta, timezone

from app.models.invite import InviteToken


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_invite(client, headers, email="employee@example.com"):
    return client.post("/api/v1/invites", json={"email": email}, headers=headers)


def accept_invite(client, headers, token):
    return client.post("/api/v1/invites/accept", json={"token": token}, headers=headers)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_manager_can_create_invite(client, auth_headers):
    """INVITE-001: Manager creates invite → 201, returns token and expiresAt."""
    resp = create_invite(client, auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "token" in data
    assert "expiresAt" in data
    assert data["email"] == "employee@example.com"
    # token should be a valid UUID string
    uuid.UUID(data["token"])


def test_employee_cannot_create_invite(client, auth_headers, auth_headers_b):
    """INVITE-002: Employee (user who accepted an invite) cannot create invite → 403."""
    # Manager creates an invite
    invite_resp = create_invite(client, auth_headers)
    token = invite_resp.json()["data"]["token"]

    # user_b accepts the invite → becomes employee
    accept_invite(client, auth_headers_b, token)

    # user_b (now employee) tries to create an invite
    resp = create_invite(client, auth_headers_b, email="another@example.com")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_valid_token_sets_role_to_employee(client, auth_headers, auth_headers_b):
    """INVITE-003: Accepting a valid token → 200, user role becomes employee."""
    invite_resp = create_invite(client, auth_headers)
    token = invite_resp.json()["data"]["token"]

    resp = accept_invite(client, auth_headers_b, token)
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "employee"

    # Confirm /me now returns employee role
    me = client.get("/api/v1/me", headers=auth_headers_b)
    assert me.json()["data"]["role"] == "employee"


def test_expired_token_returns_410(client, auth_headers, auth_headers_b, db_session):
    """INVITE-004: Accepting an expired token → 410."""
    # Create a manager user first (so created_by FK resolves)
    client.get("/api/v1/me", headers=auth_headers)
    from app.database import _uid_to_user_id
    manager_id = _uid_to_user_id.get("test-user-uid-abc123")

    expired_token = uuid.uuid4()
    invite = InviteToken(
        created_by=manager_id,
        email="exp@example.com",
        token=expired_token,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(invite)
    db_session.commit()

    resp = accept_invite(client, auth_headers_b, str(expired_token))
    assert resp.status_code == 410
    assert resp.json()["error"]["code"] == "INVITE_EXPIRED"


def test_already_accepted_token_returns_409(client, auth_headers, auth_headers_b):
    """INVITE-005: Accepting an already-accepted token → 409."""
    invite_resp = create_invite(client, auth_headers)
    token = invite_resp.json()["data"]["token"]

    # First accept succeeds
    accept_invite(client, auth_headers_b, token)

    # Second accept (different user would be realistic, but same user also hits 409)
    resp = accept_invite(client, auth_headers_b, token)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_nonexistent_token_returns_404(client, auth_headers_b):
    """INVITE-006: Accepting a non-existent token → 404."""
    resp = accept_invite(client, auth_headers_b, str(uuid.uuid4()))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
