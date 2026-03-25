import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest, Forbidden, NotFound
from ..models.client_invite import ClientInviteToken
from ..models.event import Event
from ..models.task import Task, TaskStatus
from ..schemas.client_invite import (
    ApprovedTask,
    ClientEventInfo,
    ClientInviteOut,
    ClientPortalData,
    TaskSummary,
)
from ..schemas.common import ok

router = APIRouter(tags=["Client Portal"])


class _AcceptBody(BaseModel):
    token: str


# ── POST /events/{event_id}/client-invite ─────────────────────────────────────
@router.post("/events/{event_id}/client-invite", status_code=201)
def create_client_invite(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()

    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user.id).first()
    if not event:
        raise NotFound("Event")

    raw_token = secrets.token_urlsafe(32)
    invite = ClientInviteToken(
        token=raw_token,
        event_id=event_id,
        created_by=user.id,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return ok(
        ClientInviteOut(token=raw_token, event_id=event_id).model_dump(by_alias=True),
        "Client invite created",
    )


# ── POST /client-invites/accept ───────────────────────────────────────────────
@router.post("/client-invites/accept")
def accept_client_invite(
    body: _AcceptBody,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    invite = db.query(ClientInviteToken).filter(
        ClientInviteToken.token == body.token
    ).first()

    if not invite:
        raise NotFound("Invite token")
    if invite.redeemed_by is not None:
        raise BadRequest("This invite has already been used")

    invite.redeemed_by = user.id
    invite.redeemed_at = datetime.now(timezone.utc)
    user.role = "client"
    user.client_event_id = invite.event_id
    db.commit()

    return ok({"eventId": str(invite.event_id)}, "Invite accepted")


# ── GET /my-client-event ──────────────────────────────────────────────────────
@router.get("/my-client-event")
def my_client_event(
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "client":
        raise Forbidden()
    if not user.client_event_id:
        raise NotFound("Client event")

    event = db.query(Event).filter(Event.id == user.client_event_id).first()
    if not event:
        raise NotFound("Event")

    tasks = db.query(Task).filter(Task.event_id == event.id).all()
    approved = [t for t in tasks if t.status == TaskStatus.approved]
    submitted = [t for t in tasks if t.status == TaskStatus.submitted]
    in_progress = [t for t in tasks if t.status == TaskStatus.in_progress]

    data = ClientPortalData(
        event=ClientEventInfo.model_validate(event),
        task_summary=TaskSummary(
            total=len(tasks),
            approved=len(approved),
            submitted=len(submitted),
            in_progress=len(in_progress),
        ),
        approved_tasks=[
            ApprovedTask(id=t.id, title=t.title, description=t.description)
            for t in approved
        ],
    )
    return ok(data.model_dump(by_alias=True))
