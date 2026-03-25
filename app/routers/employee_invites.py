import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest, Forbidden, NotFound
from ..models.employee_invite import EmployeeInviteToken
from ..models.event import Event
from ..models.todo import TeamMember
from ..schemas.common import ok
from ..schemas.employee_invite import EmployeeInviteAcceptBody, EmployeeInviteOut

router = APIRouter(tags=["Employee Invites"])


class _CreateInviteBody(BaseModel):
    team_member_id: str


# ── POST /events/{event_id}/employee-invite ───────────────────────────────────
@router.post("/events/{event_id}/employee-invite", status_code=201)
def create_employee_invite(
    event_id: uuid.UUID,
    body: _CreateInviteBody,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()

    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user.id).first()
    if not event:
        raise NotFound("Event")

    member = db.query(TeamMember).filter(
        TeamMember.id == body.team_member_id,
        TeamMember.event_id == event_id,
        TeamMember.user_id == user.id,
    ).first()
    if not member:
        raise NotFound("Team member")

    raw_token = secrets.token_urlsafe(32)
    invite = EmployeeInviteToken(
        token=raw_token,
        event_id=event_id,
        team_member_id=body.team_member_id,
        created_by=user.id,
    )
    db.add(invite)
    db.commit()

    return ok(
        EmployeeInviteOut(
            token=raw_token,
            event_id=event_id,
            team_member_id=body.team_member_id,
            team_member_name=member.name,
        ).model_dump(by_alias=True),
        "Employee invite created",
    )


# ── POST /employee-invites/accept ─────────────────────────────────────────────
@router.post("/employee-invites/accept")
def accept_employee_invite(
    body: EmployeeInviteAcceptBody,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    invite = db.query(EmployeeInviteToken).filter(
        EmployeeInviteToken.token == body.token
    ).first()

    if not invite:
        raise NotFound("Invite token")
    if invite.redeemed_by is not None:
        raise BadRequest("This invite has already been used")

    member = db.query(TeamMember).filter(TeamMember.id == invite.team_member_id).first()
    if member and member.linked_user_id is not None:
        raise BadRequest("This team member is already linked to an account")

    invite.redeemed_by = user.id
    invite.redeemed_at = datetime.now(timezone.utc)
    user.role = "employee"
    if member:
        member.linked_user_id = user.id
    db.commit()

    return ok(
        {"eventId": str(invite.event_id), "teamMemberId": invite.team_member_id},
        "Invite accepted",
    )
