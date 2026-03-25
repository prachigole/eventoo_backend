"""add invite_tokens table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-20
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS invite_tokens (
            id           UUID         NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
            created_by   UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email        VARCHAR(255) NOT NULL,
            token        UUID         NOT NULL UNIQUE DEFAULT gen_random_uuid(),
            expires_at   TIMESTAMPTZ  NOT NULL,
            accepted_at  TIMESTAMPTZ,
            accepted_by  UUID         REFERENCES users(id) ON DELETE SET NULL,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_invite_tokens_token ON invite_tokens (token);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invite_tokens CASCADE;")
