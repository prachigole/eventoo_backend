import uuid
from datetime import datetime

from pydantic import Field

from ..models.todo import TodoPriority
from .common import CamelSchema


# ── Todos ──────────────────────────────────────────────────────────────────────
class TodoCreate(CamelSchema):
    id: str = Field(..., min_length=1, max_length=255)  # client-generated ID
    title: str = Field(..., min_length=1)
    completed: bool = False
    assignee_id: str | None = None
    assignee_name: str | None = None
    priority: TodoPriority = TodoPriority.medium
    notes: str | None = None
    sort_order: int = 0


class TodoUpdate(CamelSchema):
    """All fields optional — PATCH semantics."""
    title: str | None = Field(default=None, min_length=1)
    completed: bool | None = None
    assignee_id: str | None = None
    assignee_name: str | None = None
    priority: TodoPriority | None = None
    notes: str | None = None
    sort_order: int | None = None


class TodoOut(CamelSchema):
    id: str
    event_id: uuid.UUID
    title: str
    completed: bool
    assignee_id: str | None
    assignee_name: str | None
    priority: TodoPriority
    notes: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


# ── Team members ───────────────────────────────────────────────────────────────
class TeamMemberCreate(CamelSchema):
    id: str = Field(..., min_length=1, max_length=255)  # client-generated ID
    name: str = Field(..., min_length=1)
    role: str | None = None
    phone: str | None = None
    email: str | None = None


class TeamMemberOut(CamelSchema):
    id: str
    event_id: uuid.UUID
    name: str
    role: str | None
    phone: str | None
    email: str | None
    linked_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
