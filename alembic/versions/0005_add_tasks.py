"""add tasks table

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-20
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        -- ── Enums ──────────────────────────────────────────────────────────────
        DO $$ BEGIN
            CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM (
                'draft', 'assigned', 'accepted', 'in_progress',
                'submitted', 'revision_required', 'approved'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        -- ── tasks ───────────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS tasks (
            id             UUID         NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id       UUID         NOT NULL REFERENCES events(id)  ON DELETE CASCADE,
            user_id        UUID         NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
            assigned_to    UUID                  REFERENCES users(id)   ON DELETE SET NULL,
            title          TEXT         NOT NULL,
            description    TEXT,
            priority       taskpriority NOT NULL DEFAULT 'medium',
            status         taskstatus   NOT NULL DEFAULT 'draft',
            due_date       DATE,
            due_time       VARCHAR(8),
            parent_task_id UUID                  REFERENCES tasks(id)   ON DELETE CASCADE,
            sort_order     INTEGER      NOT NULL DEFAULT 0,
            created_at     TIMESTAMPTZ  NOT NULL,
            updated_at     TIMESTAMPTZ  NOT NULL
        );

        CREATE INDEX IF NOT EXISTS ix_tasks_event_id    ON tasks (event_id);
        CREATE INDEX IF NOT EXISTS ix_tasks_assigned_to ON tasks (assigned_to);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS tasks CASCADE;
        DROP TYPE IF EXISTS taskstatus;
        DROP TYPE IF EXISTS taskpriority;
    """)
