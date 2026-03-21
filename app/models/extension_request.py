import enum
import uuid
from datetime import date, datetime

from sqlalchemy import TIMESTAMP, Date, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ExtReqStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"


class ExtensionRequest(Base):
    __tablename__ = "extension_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    new_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExtReqStatus] = mapped_column(
        SAEnum(ExtReqStatus), nullable=False, default=ExtReqStatus.pending
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
