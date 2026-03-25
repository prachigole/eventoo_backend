"""add vendor_ids to events, create todos and team_members tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-19
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        -- ── Add vendor_ids to events ───────────────────────────────────────────
        ALTER TABLE events
            ADD COLUMN IF NOT EXISTS vendor_ids JSONB DEFAULT '[]'::jsonb;

        -- ── todopriority enum ──────────────────────────────────────────────────
        DO $$ BEGIN
            CREATE TYPE todopriority AS ENUM ('low', 'medium', 'high');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        -- ── todos ──────────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS todos (
            id            VARCHAR(255) NOT NULL PRIMARY KEY,
            user_id       UUID         NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            event_id      UUID         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            title         TEXT         NOT NULL,
            completed     BOOLEAN      NOT NULL DEFAULT false,
            assignee_id   VARCHAR(255),
            assignee_name VARCHAR(255),
            priority      todopriority NOT NULL DEFAULT 'medium',
            notes         TEXT,
            sort_order    INTEGER      NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ  NOT NULL,
            updated_at    TIMESTAMPTZ  NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_todos_event_id ON todos (event_id);
        CREATE INDEX IF NOT EXISTS ix_todos_user_id  ON todos (user_id);

        -- ── team_members ───────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS team_members (
            id         VARCHAR(255) NOT NULL PRIMARY KEY,
            user_id    UUID         NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
            event_id   UUID         NOT NULL REFERENCES events(id)  ON DELETE CASCADE,
            name       VARCHAR(255) NOT NULL,
            role       VARCHAR(255),
            phone      VARCHAR(50),
            email      VARCHAR(255),
            created_at TIMESTAMPTZ  NOT NULL,
            updated_at TIMESTAMPTZ  NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_team_members_event_id ON team_members (event_id);
        CREATE INDEX IF NOT EXISTS ix_team_members_user_id  ON team_members (user_id);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS team_members CASCADE;
        DROP TABLE IF EXISTS todos        CASCADE;
        DROP TYPE IF EXISTS todopriority;
        ALTER TABLE events DROP COLUMN IF EXISTS vendor_ids;
    """)
