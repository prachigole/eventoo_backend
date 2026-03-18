import base64
import json

from fastapi import Header
from firebase_admin import auth, credentials
import firebase_admin
from pydantic import BaseModel

from .config import settings
from .exceptions import AppException

_firebase_app: firebase_admin.App | None = None


def _get_app() -> firebase_admin.App:
    global _firebase_app
    if _firebase_app is None:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verifying the signature (dev only)."""
    try:
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}


class TokenData(BaseModel):
    uid: str
    phone: str | None = None


async def verify_token(authorization: str | None = Header(default=None)) -> TokenData:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(401, "UNAUTHORIZED", "Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")

    # ── Dev mode: skip Firebase signature verification ─────────────────────────
    if settings.dev_skip_auth:
        payload = _decode_jwt_payload(token)
        uid = payload.get("user_id") or payload.get("sub") or payload.get("uid") or token
        return TokenData(uid=uid, phone=payload.get("phone_number"))

    # ── Production: full Firebase Admin SDK verification ──────────────────────
    try:
        decoded = auth.verify_id_token(token, app=_get_app())
        return TokenData(uid=decoded["uid"], phone=decoded.get("phone_number"))
    except Exception:
        raise AppException(401, "UNAUTHORIZED", "Invalid or expired token")
