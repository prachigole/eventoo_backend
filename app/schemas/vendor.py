import uuid
from datetime import datetime

from pydantic import Field

from ..models.vendor import VendorCategory
from .common import CamelSchema


# ── Write schemas ──────────────────────────────────────────────────────────────
class VendorCreate(CamelSchema):
    name: str = Field(..., min_length=1, max_length=255)
    category: VendorCategory
    phone: str = Field(..., min_length=1, max_length=50)
    email: str | None = None
    location: str | None = None
    price_range: str | None = None
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    events_worked: int = Field(default=0, ge=0)
    notes: str | None = None


class VendorUpdate(CamelSchema):
    """All fields optional — PATCH semantics."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: VendorCategory | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = None
    location: str | None = None
    price_range: str | None = None
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    events_worked: int | None = Field(default=None, ge=0)
    notes: str | None = None


# ── Read schemas ───────────────────────────────────────────────────────────────
class VendorSummary(CamelSchema):
    """Used in list responses and nested inside CandidateWithVendor."""
    id: uuid.UUID
    name: str
    category: VendorCategory
    phone: str
    email: str | None
    location: str | None
    price_range: str | None
    rating: float
    events_worked: int


class VendorDetail(CamelSchema):
    """Full vendor — single-vendor GET."""
    id: uuid.UUID
    name: str
    category: VendorCategory
    phone: str
    email: str | None
    location: str | None
    price_range: str | None
    rating: float
    events_worked: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
