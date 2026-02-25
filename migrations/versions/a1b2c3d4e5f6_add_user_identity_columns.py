"""add_user_identity_columns

Revision ID: a1b2c3d4e5f6
Revises: e7c83ff27d50
Create Date: 2026-02-21 00:00:00.000000

Adds the following columns to the `users` table for Phase 5 identity upgrades:
  - role           : UserRole enum (user | admin), NOT NULL, default 'user'
  - refresh_token_hash         : TEXT, nullable  (bcrypt hash of latest refresh token)
  - refresh_token_expires_at   : TIMESTAMPTZ, nullable
  - token_version  : INTEGER, NOT NULL, default 0  (incremented on logout/revocation)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "e7c83ff27d50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the UserRole postgres enum type
    userrole = sa.Enum("user", "admin", name="userrole")
    userrole.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="userrole"),
            nullable=False,
            server_default="user",
        ),
    )
    op.add_column(
        "users",
        sa.Column("refresh_token_hash", sa.String(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "refresh_token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
    op.drop_column("users", "refresh_token_expires_at")
    op.drop_column("users", "refresh_token_hash")
    op.drop_column("users", "role")

    # Drop the enum type only after the column that uses it is gone
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
