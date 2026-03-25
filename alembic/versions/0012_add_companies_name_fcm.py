"""add companies table, users.name, users.company_id, users.fcm_token

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-25
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Companies table
    op.execute("""
        CREATE TABLE companies (
            id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            name       TEXT        NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE UNIQUE INDEX ix_companies_name_lower ON companies (lower(name))")

    # 2. Add columns to users
    op.execute("ALTER TABLE users ADD COLUMN name       TEXT")
    op.execute("ALTER TABLE users ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE users ADD COLUMN fcm_token  TEXT")
    op.execute("CREATE INDEX ix_users_company_id ON users (company_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_company_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS fcm_token")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS company_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS name")
    op.execute("DROP INDEX IF EXISTS ix_companies_name_lower")
    op.execute("DROP TABLE IF EXISTS companies")
