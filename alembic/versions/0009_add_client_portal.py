"""add client_event_id to users and client_invite_tokens table

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-24
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN client_event_id UUID REFERENCES events(id) ON DELETE SET NULL"
    )
    op.execute(
        """
        CREATE TABLE client_invite_tokens (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            token       TEXT        NOT NULL UNIQUE,
            event_id    UUID        NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            created_by  UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            redeemed_by UUID        REFERENCES users(id) ON DELETE SET NULL,
            redeemed_at TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_client_invites_event_id   ON client_invite_tokens (event_id)")
    op.execute("CREATE INDEX ix_client_invites_created_by ON client_invite_tokens (created_by)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_client_invites_created_by")
    op.execute("DROP INDEX IF EXISTS ix_client_invites_event_id")
    op.execute("DROP TABLE IF EXISTS client_invite_tokens")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS client_event_id")
