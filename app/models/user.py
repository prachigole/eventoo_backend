import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="manager")
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL", use_alter=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="user", cascade="all, delete-orphan",
        foreign_keys="[Event.user_id]"
    )
    vendors: Mapped[list["Vendor"]] = relationship(  # noqa: F821
        "Vendor", back_populates="user", cascade="all, delete-orphan"
    )
    company: Mapped["Company | None"] = relationship(  # noqa: F821
        "Company", back_populates="users", foreign_keys="[User.company_id]"
    )

    __table_args__ = (Index("ix_users_firebase_uid", "firebase_uid"),)
