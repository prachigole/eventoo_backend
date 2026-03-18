import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VendorCategory(str, enum.Enum):
    catering = "catering"
    photography = "photography"
    music = "music"
    decoration = "decoration"
    venue = "venue"
    lighting = "lighting"
    av = "av"
    security = "security"
    transport = "transport"
    other = "other"


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[VendorCategory] = mapped_column(
        SQLEnum(VendorCategory, name="vendorcategory"), nullable=False
    )
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    price_range: Mapped[str | None] = mapped_column(String(100))
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    events_worked: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship("User", back_populates="vendors")  # noqa: F821
    candidacies: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        "Candidate", back_populates="vendor"
    )

    __table_args__ = (
        Index("ix_vendors_user_id", "user_id"),
        Index("ix_vendors_category", "category"),
        Index("ix_vendors_rating", "rating"),
    )
