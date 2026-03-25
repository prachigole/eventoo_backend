import uuid
from datetime import date as Date, datetime

from pydantic import Field

from ..models.task import TaskPriority, TaskStatus
from .common import CamelSchema


class TaskCreate(CamelSchema):
    title: str = Field(..., min_length=1)
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium
    due_date: Date | None = None
    due_time: str | None = None
    assigned_to: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    sort_order: int = 0


class TaskUpdate(CamelSchema):
    """All fields optional — PATCH semantics."""
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: Date | None = None
    due_time: str | None = None
    assigned_to: uuid.UUID | None = None
    sort_order: int | None = None
    submission_note: str | None = None
    review_note: str | None = None


class TaskOut(CamelSchema):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    assigned_to: uuid.UUID | None
    assigned_to_name: str | None = None   # injected by router; not a DB column
    event_title: str | None = None        # injected by router for /my-tasks; not a DB column
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: Date | None
    due_time: str | None
    parent_task_id: uuid.UUID | None
    sort_order: int
    submission_note: str | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime
