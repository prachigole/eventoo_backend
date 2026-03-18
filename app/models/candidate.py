import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CandidateStatus(str, enum.Enum):
    # Values match the Flutter CandidateStatus enum names exactly
    shortlisted = "shortlisted"
    awaiting_confirmation = "awaitingConfirmation"
    finalised = "finalised"
    rejected = "rejected"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CandidateStatus] = mapped_column(
        # values_callable ensures SQLAlchemy stores the .value ("awaitingConfirmation")
        # rather than the .name ("awaiting_confirmation") in the DB.
        SQLEnum(CandidateStatus, name="candidatestatus",
                values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CandidateStatus.shortlisted,
    )
    quoted_cost: Mapped[int | None] = mapped_column(Integer)  # ₹ thousands
    notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    event: Mapped["Event"] = relationship("Event", back_populates="candidates")  # noqa: F821
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="candidacies")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("event_id", "vendor_id", name="uq_candidate_event_vendor"),
        Index("ix_candidates_event_id", "event_id"),
        Index("ix_candidates_vendor_id", "vendor_id"),
        Index("ix_candidates_status", "status"),
    )
