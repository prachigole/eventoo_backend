import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # drop stale connections before use
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── User upsert with in-process cache ──────────────────────────────────────────
# firebase_uid → internal user UUID. Avoids a DB round-trip on every request
# after the first time a user is seen. Safe to keep in-process memory because
# the mapping never changes once created.
_uid_to_user_id: dict[str, uuid.UUID] = {}


def get_or_create_user(db: Session, firebase_uid: str, phone: str | None = None):
    from .models.user import User  # local import avoids circular dependency

    if firebase_uid in _uid_to_user_id:
        user_id = _uid_to_user_id[firebase_uid]
        user = db.get(User, user_id)
        if user is not None:
            return user
        # Cache is stale (e.g. row was deleted) — fall through to re-create
        del _uid_to_user_id[firebase_uid]

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        user = User(firebase_uid=firebase_uid, phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    _uid_to_user_id[firebase_uid] = user.id
    return user
