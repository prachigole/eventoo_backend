import enum
import uuid
from datetime import date as Date, datetime, timezone

from sqlalchemy import Date as SADate, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TaskStatus(str, enum.Enum):
    draft = "draft"
    assigned = "assigned"
    accepted = "accepted"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_required = "revision_required"
    approved = "approved"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="taskpriority"),
        nullable=False,
        default=TaskPriority.medium,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="taskstatus"),
        nullable=False,
        default=TaskStatus.draft,
    )
    due_date: Mapped[Date | None] = mapped_column(SADate)
    due_time: Mapped[str | None] = mapped_column(String(8))
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submission_note: Mapped[str | None] = mapped_column(Text)
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
