# Import all models here so Alembic autogenerate can discover them
from .base import Base
from .user import User
from .event import Event, EventCategory, EventStatus
from .vendor import Vendor, VendorCategory
from .candidate import Candidate, CandidateStatus

__all__ = [
    "Base",
    "User",
    "Event",
    "EventCategory",
    "EventStatus",
    "Vendor",
    "VendorCategory",
    "Candidate",
    "CandidateStatus",
]
