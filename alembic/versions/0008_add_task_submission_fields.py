"""add submission_note and review_note to tasks

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-21
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tasks ADD COLUMN submission_note TEXT")
    op.execute("ALTER TABLE tasks ADD COLUMN review_note TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN submission_note")
    op.execute("ALTER TABLE tasks DROP COLUMN review_note")
