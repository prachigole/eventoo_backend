import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import AppException, Conflict, Forbidden, NotFound
from ..models.invite import InviteToken
from ..schemas.common import ok
from ..schemas.invite import InviteAccept, InviteCreate, InviteOut

router = APIRouter(tags=["Invites"])


# ── POST /invites ──────────────────────────────────────────────────────────────
@router.post("/invites", status_code=201)
def create_invite(
    body: InviteCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()

    invite = InviteToken(
        created_by=user.id,
        email=body.email,
        token=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return ok(InviteOut(
        token=str(invite.token),
        email=invite.email,
        expires_at=invite.expires_at,
    ))


# ── POST /invites/accept ───────────────────────────────────────────────────────
@router.post("/invites/accept")
def accept_invite(
    body: InviteAccept,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    try:
        token_uuid = uuid.UUID(body.token)
    except ValueError:
        raise NotFound("Invite token")

    invite = db.query(InviteToken).filter(InviteToken.token == token_uuid).first()
    if not invite:
        raise NotFound("Invite token")
    if invite.accepted_at is not None:
        raise Conflict("Invite already accepted")
    if invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise AppException(410, "INVITE_EXPIRED", "Invite token has expired")

    invite.accepted_at = datetime.now(timezone.utc)
    invite.accepted_by = user.id
    user.role = "employee"
    db.commit()

    return ok({"role": "employee"})
