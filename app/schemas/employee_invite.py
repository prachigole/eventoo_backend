import uuid

from pydantic import BaseModel

from .common import CamelSchema


class EmployeeInviteOut(CamelSchema):
    token: str
    event_id: uuid.UUID
    team_member_id: str
    team_member_name: str   # denormalised so Flutter can display it in the share sheet


class EmployeeInviteAcceptBody(BaseModel):
    token: str
