"""add employee_invite_tokens table

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-25
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE employee_invite_tokens (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            token           TEXT        NOT NULL UNIQUE,
            event_id        UUID        NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            team_member_id  TEXT        NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,
            created_by      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            redeemed_by     UUID        REFERENCES users(id) ON DELETE SET NULL,
            redeemed_at     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX ix_emp_invites_event_id       ON employee_invite_tokens (event_id)"
    )
    op.execute(
        "CREATE INDEX ix_emp_invites_team_member_id ON employee_invite_tokens (team_member_id)"
    )
    op.execute(
        "CREATE INDEX ix_emp_invites_created_by     ON employee_invite_tokens (created_by)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_emp_invites_created_by")
    op.execute("DROP INDEX IF EXISTS ix_emp_invites_team_member_id")
    op.execute("DROP INDEX IF EXISTS ix_emp_invites_event_id")
    op.execute("DROP TABLE IF EXISTS employee_invite_tokens")
