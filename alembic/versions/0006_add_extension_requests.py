"""add extension_requests table

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-21
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE extreqstatus AS ENUM ('pending', 'approved', 'rejected');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE IF NOT EXISTS extension_requests (
            id            UUID         NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id       UUID         NOT NULL REFERENCES tasks(id)  ON DELETE CASCADE,
            event_id      UUID         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            requested_by  UUID         NOT NULL REFERENCES users(id),
            new_due_date  DATE         NOT NULL,
            reason        TEXT,
            status        extreqstatus NOT NULL DEFAULT 'pending',
            reviewed_by   UUID                  REFERENCES users(id),
            reviewed_at   TIMESTAMPTZ,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS ix_ext_req_event_id ON extension_requests (event_id);
        CREATE INDEX IF NOT EXISTS ix_ext_req_task_id  ON extension_requests (task_id);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS extension_requests CASCADE;
        DROP TYPE IF EXISTS extreqstatus;
    """)
