import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EventCategory(str, enum.Enum):
    music = "music"
    corporate = "corporate"
    wedding = "wedding"
    sports = "sports"
    art = "art"
    food = "food"


class EventStatus(str, enum.Enum):
    upcoming = "upcoming"
    ongoing = "ongoing"
    past = "past"
    cancelled = "cancelled"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Core fields — mirror the Flutter EventModel exactly
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[str | None] = mapped_column(String(50))
    venue: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[EventCategory] = mapped_column(
        SQLEnum(EventCategory, name="eventcategory"), nullable=False
    )
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus, name="eventstatus"),
        nullable=False,
        default=EventStatus.upcoming,
    )
    attendee_count: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    description: Mapped[str | None] = mapped_column(Text)

    # Stored as [int, int, ...] — each int is an ARGB colour value
    cover_gradient: Mapped[list | None] = mapped_column(JSONB)

    # Client & commercial info
    client_name: Mapped[str | None] = mapped_column(String(255))
    client_phone: Mapped[str | None] = mapped_column(String(50))
    client_email: Mapped[str | None] = mapped_column(String(255))
    budget: Mapped[int | None] = mapped_column(Integer)  # ₹ thousands
    notes: Mapped[str | None] = mapped_column(Text)
    vendor_ids: Mapped[list | None] = mapped_column(JSONB, default=list)  # list of vendor ID strings

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="events", foreign_keys="[Event.user_id]"
    )
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        "Candidate", back_populates="event", cascade="all, delete-orphan"
    )
    todos: Mapped[list["Todo"]] = relationship(  # noqa: F821
        "Todo", back_populates="event", cascade="all, delete-orphan"
    )
    team_members: Mapped[list["TeamMember"]] = relationship(  # noqa: F821
        "TeamMember", back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_events_user_id", "user_id"),
        Index("ix_events_status", "status"),
        Index("ix_events_date", "date"),
    )
