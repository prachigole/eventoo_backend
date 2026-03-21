"""add task_photos table

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-21
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_photos (
            id            UUID        NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id       UUID        NOT NULL REFERENCES tasks(id)  ON DELETE CASCADE,
            event_id      UUID        NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            uploaded_by   UUID        NOT NULL REFERENCES users(id),
            file_path     TEXT        NOT NULL,
            original_name TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS ix_task_photos_task_id  ON task_photos (task_id);
        CREATE INDEX IF NOT EXISTS ix_task_photos_event_id ON task_photos (event_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS task_photos CASCADE;")
