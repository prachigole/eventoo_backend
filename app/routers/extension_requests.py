import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest, Forbidden, NotFound
from ..models.event import Event
from ..models.extension_request import ExtReqStatus, ExtensionRequest
from ..models.task import Task
from ..schemas.common import ok
from ..schemas.extension_request import ExtReqCreate, ExtReqOut, ExtReqReview

router = APIRouter(tags=["ExtensionRequests"])


def _owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
    if not event:
        raise NotFound("Event")
    return event


# ── POST /events/{event_id}/tasks/{task_id}/extension-requests ────────────────
@router.post("/events/{event_id}/tasks/{task_id}/extension-requests", status_code=201)
def create_extension_request(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    body: ExtReqCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "employee":
        raise Forbidden()

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.event_id == event_id, Task.assigned_to == user.id)
        .first()
    )
    if not task:
        raise NotFound("Task")

    req = ExtensionRequest(
        task_id=task_id,
        event_id=event_id,
        requested_by=user.id,
        new_due_date=body.new_due_date,
        reason=body.reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return ok(ExtReqOut.model_validate(req).model_dump(by_alias=True), "Extension request submitted")


# ── GET /events/{event_id}/extension-requests ────────────────────────────────
@router.get("/events/{event_id}/extension-requests")
def list_extension_requests(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()
    _owned_event(db, event_id, user.id)

    reqs = (
        db.query(ExtensionRequest)
        .filter(ExtensionRequest.event_id == event_id)
        .order_by(ExtensionRequest.created_at.desc())
        .all()
    )
    return ok([ExtReqOut.model_validate(r).model_dump(by_alias=True) for r in reqs])


# ── PATCH /events/{event_id}/extension-requests/{req_id} ─────────────────────
@router.patch("/events/{event_id}/extension-requests/{req_id}")
def review_extension_request(
    event_id: uuid.UUID,
    req_id: uuid.UUID,
    body: ExtReqReview,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()
    _owned_event(db, event_id, user.id)

    req = (
        db.query(ExtensionRequest)
        .filter(ExtensionRequest.id == req_id, ExtensionRequest.event_id == event_id)
        .first()
    )
    if not req:
        raise NotFound("Extension request")
    if req.status != ExtReqStatus.pending:
        raise BadRequest("Request already reviewed")
    if body.status not in (ExtReqStatus.approved, ExtReqStatus.rejected):
        raise BadRequest("Status must be 'approved' or 'rejected'")

    req.status = body.status
    req.reviewed_by = user.id
    req.reviewed_at = datetime.now(timezone.utc)

    if body.status == ExtReqStatus.approved:
        task = db.query(Task).filter(Task.id == req.task_id).first()
        if task:
            task.due_date = req.new_due_date

    db.commit()
    db.refresh(req)
    return ok(ExtReqOut.model_validate(req).model_dump(by_alias=True), "Request reviewed")
