import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import Forbidden, NotFound
from ..models.candidate import Candidate
from ..models.event import Event, EventCategory, EventStatus
from ..schemas.common import ok, paginated
from ..schemas.event import EventCreate, EventDetail, EventSummary, EventUpdate

router = APIRouter(prefix="/events", tags=["Events"])

# ── Dependency: resolve current user row ──────────────────────────────────────
def current_user(
    token: Annotated[TokenData, Depends(verify_token)],
    db: Annotated[Session, Depends(get_db)],
):
    return get_or_create_user(db, token.uid, token.phone)


# ── Helper: fetch event that belongs to the authenticated user ─────────────────
def _get_owned(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == user_id)
        .first()
    )
    if not event:
        raise NotFound("Event")
    return event


# ── GET /events ───────────────────────────────────────────────────────────────
@router.get("")
def list_events(
    status: EventStatus | None = None,
    category: EventCategory | None = None,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    q = db.query(Event).filter(Event.user_id == user.id)

    if status:
        q = q.filter(Event.status == status)
    if category:
        q = q.filter(Event.category == category)
    if search:
        q = q.filter(Event.title.ilike(f"%{search}%"))

    events = q.order_by(Event.date).offset((page - 1) * per_page).limit(per_page).all()

    return paginated(
        items=[EventSummary.model_validate(e).model_dump(by_alias=True) for e in events],
        total=len(events),
        page=page,
        per_page=per_page,
    )


# ── POST /events ──────────────────────────────────────────────────────────────
@router.post("", status_code=201)
def create_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    event = Event(**body.model_dump(by_alias=False), user_id=user.id)
    db.add(event)
    db.commit()
    db.refresh(event)

    return ok(EventSummary.model_validate(event).model_dump(by_alias=True), "Event created")


# ── GET /events/{id} ──────────────────────────────────────────────────────────
@router.get("/{event_id}")
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    # Eagerly load candidates → vendor in two efficient round-trip queries
    event = (
        db.query(Event)
        .options(selectinload(Event.candidates).selectinload(Candidate.vendor))
        .filter(Event.id == event_id, Event.user_id == user.id)
        .first()
    )
    if not event:
        raise NotFound("Event")

    return ok(EventDetail.model_validate(event).model_dump(by_alias=True))


# ── PATCH /events/{id} ───────────────────────────────────────────────────────
@router.patch("/{event_id}")
def update_event(
    event_id: uuid.UUID,
    body: EventUpdate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    event = _get_owned(db, event_id, user.id)

    # Only update fields that were explicitly provided in the request
    for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return ok(EventSummary.model_validate(event).model_dump(by_alias=True), "Event updated")


# ── DELETE /events/{id} ───────────────────────────────────────────────────────
@router.delete("/{event_id}", status_code=200)
def delete_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    event = _get_owned(db, event_id, user.id)

    db.delete(event)
    db.commit()

    return ok(None, "Event deleted")
