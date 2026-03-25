import uuid

from .common import CamelSchema


class UserOut(CamelSchema):
    id: uuid.UUID
    role: str
    phone: str | None = None
    name: str | None = None
    company_id: uuid.UUID | None = None   # null → Flutter shows OnboardingScreen


class PatchMeBody(CamelSchema):
    fcm_token: str | None = None          # only field the client may self-patch
