import uuid
from datetime import date as Date, datetime

from pydantic import Field

from ..models.extension_request import ExtReqStatus
from .common import CamelSchema


class ExtReqCreate(CamelSchema):
    new_due_date: Date = Field(...)
    reason: str | None = None


class ExtReqReview(CamelSchema):
    """Manager approves or rejects a pending request."""
    status: ExtReqStatus  # must be 'approved' or 'rejected'


class ExtReqOut(CamelSchema):
    id: uuid.UUID
    task_id: uuid.UUID
    event_id: uuid.UUID
    requested_by: uuid.UUID
    new_due_date: Date
    reason: str | None
    status: ExtReqStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
