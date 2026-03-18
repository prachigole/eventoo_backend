"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-17
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        -- ── Enum types ────────────────────────────────────────────────────────
        CREATE TYPE eventcategory   AS ENUM ('music','corporate','wedding','sports','art','food');
        CREATE TYPE eventstatus     AS ENUM ('upcoming','ongoing','past','cancelled');
        CREATE TYPE vendorcategory  AS ENUM ('catering','photography','music','decoration','venue','lighting','av','security','transport','other');
        CREATE TYPE candidatestatus AS ENUM ('shortlisted','awaitingConfirmation','finalised','rejected');

        -- ── users ──────────────────────────────────────────────────────────────
        CREATE TABLE users (
            id           UUID        PRIMARY KEY,
            firebase_uid VARCHAR(128) NOT NULL UNIQUE,
            phone        VARCHAR(32),
            created_at   TIMESTAMPTZ NOT NULL,
            updated_at   TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX ix_users_firebase_uid ON users (firebase_uid);

        -- ── events ─────────────────────────────────────────────────────────────
        CREATE TABLE events (
            id             UUID         PRIMARY KEY,
            user_id        UUID         NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            title          VARCHAR(255) NOT NULL,
            date           DATE         NOT NULL,
            time           VARCHAR(50),
            venue          VARCHAR(255) NOT NULL DEFAULT '',
            city           VARCHAR(100),
            category       eventcategory NOT NULL,
            status         eventstatus   NOT NULL DEFAULT 'upcoming',
            attendee_count INTEGER      NOT NULL DEFAULT 0,
            capacity       INTEGER      NOT NULL DEFAULT 100,
            description    TEXT,
            cover_gradient JSONB,
            client_name    VARCHAR(255),
            client_phone   VARCHAR(50),
            client_email   VARCHAR(255),
            budget         INTEGER,
            notes          TEXT,
            created_at     TIMESTAMPTZ NOT NULL,
            updated_at     TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX ix_events_user_id ON events (user_id);
        CREATE INDEX ix_events_status  ON events (status);
        CREATE INDEX ix_events_date    ON events (date);

        -- ── vendors ────────────────────────────────────────────────────────────
        CREATE TABLE vendors (
            id            UUID          PRIMARY KEY,
            user_id       UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name          VARCHAR(255)  NOT NULL,
            category      vendorcategory NOT NULL,
            phone         VARCHAR(50)   NOT NULL,
            email         VARCHAR(255),
            location      VARCHAR(255),
            price_range   VARCHAR(100),
            rating        FLOAT         NOT NULL DEFAULT 0.0,
            events_worked INTEGER       NOT NULL DEFAULT 0,
            notes         TEXT,
            created_at    TIMESTAMPTZ   NOT NULL,
            updated_at    TIMESTAMPTZ   NOT NULL
        );
        CREATE INDEX ix_vendors_user_id  ON vendors (user_id);
        CREATE INDEX ix_vendors_category ON vendors (category);
        CREATE INDEX ix_vendors_rating   ON vendors (rating);

        -- ── candidates (shortlist + hire tracking) ─────────────────────────────
        CREATE TABLE candidates (
            id               UUID             PRIMARY KEY,
            event_id         UUID             NOT NULL REFERENCES events(id)  ON DELETE CASCADE,
            vendor_id        UUID             NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
            status           candidatestatus  NOT NULL DEFAULT 'shortlisted',
            quoted_cost      INTEGER,
            notes            TEXT,
            rejection_reason TEXT,
            created_at       TIMESTAMPTZ      NOT NULL,
            updated_at       TIMESTAMPTZ      NOT NULL,
            CONSTRAINT uq_candidate_event_vendor UNIQUE (event_id, vendor_id)
        );
        CREATE INDEX ix_candidates_event_id  ON candidates (event_id);
        CREATE INDEX ix_candidates_vendor_id ON candidates (vendor_id);
        CREATE INDEX ix_candidates_status    ON candidates (status);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS candidates CASCADE;
        DROP TABLE IF EXISTS vendors    CASCADE;
        DROP TABLE IF EXISTS events     CASCADE;
        DROP TABLE IF EXISTS users      CASCADE;
        DROP TYPE IF EXISTS candidatestatus;
        DROP TYPE IF EXISTS vendorcategory;
        DROP TYPE IF EXISTS eventstatus;
        DROP TYPE IF EXISTS eventcategory;
    """)
