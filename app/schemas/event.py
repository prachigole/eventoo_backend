import uuid
from datetime import date as Date, datetime

from pydantic import Field

from ..models.event import EventCategory, EventStatus
from .common import CamelSchema


# ── Write schemas (request bodies) ────────────────────────────────────────────
class EventCreate(CamelSchema):
    title: str = Field(..., min_length=1, max_length=255)
    date: Date
    time: str | None = None
    venue: str = Field(default="", max_length=255)
    city: str | None = None
    category: EventCategory
    status: EventStatus = EventStatus.upcoming
    attendee_count: int = Field(default=0, ge=0)
    capacity: int = Field(default=100, ge=1)
    description: str | None = None
    cover_gradient: list[int] | None = None
    client_name: str | None = None
    client_phone: str | None = None
    client_email: str | None = None
    budget: int | None = Field(default=None, ge=0)  # ₹ thousands
    notes: str | None = None


class EventUpdate(CamelSchema):
    """All fields optional — PATCH semantics."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    date: Date | None = None
    time: str | None = None
    venue: str | None = None
    city: str | None = None
    category: EventCategory | None = None
    status: EventStatus | None = None
    attendee_count: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, ge=1)
    description: str | None = None
    cover_gradient: list[int] | None = None
    client_name: str | None = None
    client_phone: str | None = None
    client_email: str | None = None
    budget: int | None = Field(default=None, ge=0)
    notes: str | None = None
    vendor_ids: list[str] | None = None


# ── Read schemas (response bodies) ────────────────────────────────────────────
class EventSummary(CamelSchema):
    """Lightweight — used in list responses.  No candidates, no client detail."""
    id: uuid.UUID
    title: str
    date: Date
    time: str | None
    venue: str
    city: str | None
    category: EventCategory
    status: EventStatus
    attendee_count: int
    capacity: int
    cover_gradient: list[int] | None
    vendor_ids: list[str] | None
    created_at: datetime
    updated_at: datetime


class EventDetail(CamelSchema):
    """Full event — used in single-event GET.  Includes candidates via nested schema."""
    id: uuid.UUID
    title: str
    date: Date
    time: str | None
    venue: str
    city: str | None
    category: EventCategory
    status: EventStatus
    attendee_count: int
    capacity: int
    description: str | None
    cover_gradient: list[int] | None
    client_name: str | None
    client_phone: str | None
    client_email: str | None
    budget: int | None
    notes: str | None
    vendor_ids: list[str] | None
    candidates: list["CandidateWithVendor"] = []  # populated via selectinload
    created_at: datetime
    updated_at: datetime


# Resolved after CandidateWithVendor is defined in candidate.py
from .candidate import CandidateWithVendor  # noqa: E402

EventDetail.model_rebuild()
