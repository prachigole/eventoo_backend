import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import Conflict, NotFound
from ..models.candidate import Candidate
from ..models.event import Event
from ..models.vendor import Vendor
from ..schemas.candidate import CandidateCreate, CandidateUpdate, CandidateWithVendor
from ..schemas.common import ok

router = APIRouter(prefix="/events/{event_id}/candidates", tags=["Candidates"])


def _get_owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
    if not event:
        raise NotFound("Event")
    return event


def _get_candidate(db: Session, event_id: uuid.UUID, vendor_id: uuid.UUID) -> Candidate:
    c = (
        db.query(Candidate)
        .options(selectinload(Candidate.vendor))
        .filter(Candidate.event_id == event_id, Candidate.vendor_id == vendor_id)
        .first()
    )
    if not c:
        raise NotFound("Candidate")
    return c


# ── GET /events/{event_id}/candidates ─────────────────────────────────────────
@router.get("")
def list_candidates(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _get_owned_event(db, event_id, user.id)

    candidates = (
        db.query(Candidate)
        .options(selectinload(Candidate.vendor))
        .filter(Candidate.event_id == event_id)
        .order_by(Candidate.created_at)
        .all()
    )

    return ok([CandidateWithVendor.model_validate(c).model_dump(by_alias=True) for c in candidates])


# ── POST /events/{event_id}/candidates ────────────────────────────────────────
@router.post("", status_code=201)
def add_candidate(
    event_id: uuid.UUID,
    body: CandidateCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _get_owned_event(db, event_id, user.id)

    # Vendor must belong to the same user
    vendor = db.query(Vendor).filter(Vendor.id == body.vendor_id, Vendor.user_id == user.id).first()
    if not vendor:
        raise NotFound("Vendor")

    # Prevent duplicate shortlisting
    exists = db.query(Candidate).filter(
        Candidate.event_id == event_id, Candidate.vendor_id == body.vendor_id
    ).first()
    if exists:
        raise Conflict("Vendor is already shortlisted for this event")

    candidate = Candidate(
        event_id=event_id,
        vendor_id=body.vendor_id,
        quoted_cost=body.quoted_cost,
        notes=body.notes,
    )
    db.add(candidate)
    db.commit()

    # Reload with vendor relation for response
    candidate = _get_candidate(db, event_id, body.vendor_id)

    return ok(CandidateWithVendor.model_validate(candidate).model_dump(by_alias=True), "Vendor shortlisted")


# ── PATCH /events/{event_id}/candidates/{vendor_id} ───────────────────────────
@router.patch("/{vendor_id}")
def update_candidate(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    body: CandidateUpdate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _get_owned_event(db, event_id, user.id)

    candidate = _get_candidate(db, event_id, vendor_id)

    for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)

    # Reload vendor relation after refresh
    candidate = _get_candidate(db, event_id, vendor_id)

    return ok(CandidateWithVendor.model_validate(candidate).model_dump(by_alias=True), "Candidate updated")


# ── DELETE /events/{event_id}/candidates/{vendor_id} ──────────────────────────
@router.delete("/{vendor_id}", status_code=200)
def remove_candidate(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _get_owned_event(db, event_id, user.id)

    candidate = (
        db.query(Candidate)
        .filter(Candidate.event_id == event_id, Candidate.vendor_id == vendor_id)
        .first()
    )
    if not candidate:
        raise NotFound("Candidate")

    db.delete(candidate)
    db.commit()

    return ok(None, "Vendor removed from shortlist")
