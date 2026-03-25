import uuid
from datetime import date as Date, datetime

from .common import CamelSchema
from ..models.event import EventCategory, EventStatus


class ClientInviteOut(CamelSchema):
    token: str
    event_id: uuid.UUID


class ClientEventInfo(CamelSchema):
    """Public event fields shown to a client."""
    id: uuid.UUID
    title: str
    date: Date
    time: str | None
    venue: str
    city: str | None
    category: EventCategory
    status: EventStatus
    description: str | None
    attendee_count: int
    capacity: int


class TaskSummary(CamelSchema):
    total: int
    approved: int
    submitted: int
    in_progress: int


class ApprovedTask(CamelSchema):
    id: uuid.UUID
    title: str
    description: str | None


class ClientPortalData(CamelSchema):
    event: ClientEventInfo
    task_summary: TaskSummary
    approved_tasks: list[ApprovedTask]
