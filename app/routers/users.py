from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..schemas.common import ok
from ..schemas.user import PatchMeBody, UserOut

router = APIRouter(tags=["Users"])


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    return ok(UserOut.model_validate(user))


@router.patch("/me")
def patch_me(
    body: PatchMeBody,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Update fcm_token (device push token). Role and company are set via /companies/join-or-create."""
    user = get_or_create_user(db, token.uid, token.phone)
    if body.fcm_token is not None:
        user.fcm_token = body.fcm_token
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user))
