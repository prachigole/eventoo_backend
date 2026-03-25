import uuid

from .common import CamelSchema


class CompanyOut(CamelSchema):
    id: uuid.UUID
    name: str


class CompanyEmployeeOut(CamelSchema):
    id: uuid.UUID       # users.id — used as tasks.assigned_to
    name: str
    phone: str | None = None
