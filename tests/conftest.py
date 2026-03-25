"""
Shared fixtures for the Eventoo test suite.
Uses a SQLite file database so tests are isolated and fast.
DEV_SKIP_AUTH=true is enabled so any Bearer token is accepted.

SQLite compatibility notes:
  - PostgreSQL UUID columns are replaced with Text for SQLite
  - PostgreSQL JSONB columns are replaced with Text for SQLite
  - PostgreSQL Enum types use native Python enums (no CREATE TYPE needed)
"""
import os
import shutil
import uuid as _uuid_module
import sqlite3
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, TypeDecorator, create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

# Set env vars before importing the app so settings picks them up
os.environ["DEV_SKIP_AUTH"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["FIREBASE_CREDENTIALS_PATH"] = ""
os.environ["SKIP_MDNS"] = "true"  # tests restart the app many times; avoid Zeroconf re-registration errors

# ── Monkey-patch postgresql.UUID before app imports it ────────────────────────
# We replace the PostgreSQL UUID dialect type with a TypeDecorator that stores
# UUIDs as strings in SQLite. This is done BEFORE the models import it.
import sqlalchemy.dialects.postgresql as _pg_dialect


class _SQLiteUUID(TypeDecorator):
    """Stores UUID as a 36-char string in SQLite; no-op in PostgreSQL."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, _uuid_module.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        return value  # keep as string; callers accept str UUIDs in tests


# Patch the UUID class in the postgresql dialect module
_pg_dialect.UUID = _SQLiteUUID

# Also patch the direct import path used in models
import sqlalchemy.dialects.postgresql.types as _pg_types
_pg_types.UUID = _SQLiteUUID

# And the JSONB type → JSON fallback
from sqlalchemy import JSON as _SA_JSON


class _SQLiteJSONB(TypeDecorator):
    """Stores JSONB as plain JSON text in SQLite."""
    impl = _SA_JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


_pg_dialect.JSONB = _SQLiteJSONB
_pg_types.JSONB = _SQLiteJSONB

# ─────────────────────────────────────────────────────────────────────────────

from app.main import app as fastapi_app  # noqa: E402
from app.database import get_db  # noqa: E402
from app.models.base import Base  # noqa: E402
# Import all models so SQLAlchemy registers them with Base.metadata
import app.models.user  # noqa: F401, E402
import app.models.event  # noqa: F401, E402
import app.models.vendor  # noqa: F401, E402
import app.models.candidate  # noqa: F401, E402
import app.models.todo       # noqa: F401, E402
import app.models.invite     # noqa: F401, E402
import app.models.task               # noqa: F401, E402
import app.models.extension_request  # noqa: F401, E402
import app.models.task_photo          # noqa: F401, E402
import app.models.client_invite       # noqa: F401, E402
import app.models.company             # noqa: F401, E402

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    # Clear the in-process user cache between tests
    from app.database import _uid_to_user_id
    _uid_to_user_id.clear()
    yield
    Base.metadata.drop_all(bind=engine)
    shutil.rmtree("uploads", ignore_errors=True)


@pytest.fixture()
def db_session():
    """Direct DB session for test setup (inserting seed data)."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """TestClient with DB override and DEV_SKIP_AUTH enabled."""
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers():
    """Fake auth headers — accepted by DEV_SKIP_AUTH mode.
    The raw token string becomes the uid since the payload cannot be decoded."""
    return {"Authorization": "Bearer test-user-uid-abc123"}


@pytest.fixture()
def auth_headers_b():
    """A second user — different uid, used for IDOR tests."""
    return {"Authorization": "Bearer test-user-uid-xyz789"}


@pytest.fixture()
def sample_event():
    return {
        "title": "Test Concert",
        "date": "2026-06-15",
        "venue": "Test Venue",
        "city": "Mumbai",
        "category": "music",
        "status": "upcoming",
        "attendeeCount": 0,
        "capacity": 200,
    }


@pytest.fixture()
def sample_vendor():
    return {
        "name": "Test Caterer",
        "category": "catering",
        "phone": "+919876543210",
        "email": "test@caterer.com",
        "rating": 4.5,
        "eventsWorked": 10,
        "location": "Mumbai",
        "priceRange": "₹50k-₹1L",
    }
