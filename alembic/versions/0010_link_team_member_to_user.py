"""add linked_user_id to team_members

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-25
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE team_members
          ADD COLUMN linked_user_id UUID REFERENCES users(id) ON DELETE SET NULL
    """)
    op.execute(
        "CREATE INDEX ix_team_members_linked_user_id ON team_members (linked_user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_team_members_linked_user_id")
    op.execute("ALTER TABLE team_members DROP COLUMN IF EXISTS linked_user_id")
