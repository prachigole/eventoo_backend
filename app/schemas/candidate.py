import uuid
from datetime import datetime

from pydantic import Field

from ..models.candidate import CandidateStatus
from .common import CamelSchema
from .vendor import VendorSummary


# ── Write schemas ──────────────────────────────────────────────────────────────
class CandidateCreate(CamelSchema):
    vendor_id: uuid.UUID
    quoted_cost: int | None = Field(default=None, ge=0)  # ₹ thousands
    notes: str | None = None


class CandidateUpdate(CamelSchema):
    """PATCH — update status, quoted cost, notes, or rejection reason."""
    status: CandidateStatus | None = None
    quoted_cost: int | None = Field(default=None, ge=0)
    notes: str | None = None
    rejection_reason: str | None = None


# ── Read schemas ───────────────────────────────────────────────────────────────
class CandidateWithVendor(CamelSchema):
    """Used inside EventDetail and standalone candidate list."""
    id: uuid.UUID
    event_id: uuid.UUID
    vendor_id: uuid.UUID
    status: CandidateStatus
    quoted_cost: int | None
    notes: str | None
    rejection_reason: str | None
    vendor: VendorSummary
    created_at: datetime
    updated_at: datetime
