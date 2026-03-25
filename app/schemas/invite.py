from datetime import datetime

from .common import CamelSchema


class InviteCreate(CamelSchema):
    email: str


class InviteOut(CamelSchema):
    token: str
    email: str
    expires_at: datetime


class InviteAccept(CamelSchema):
    token: str
