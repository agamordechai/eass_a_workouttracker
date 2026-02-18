"""Add email/password authentication support

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make google_id nullable, add password_hash column, add unique index on email."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = [c["name"] for c in inspector.get_columns("users")]

    # Add password_hash column if not present
    if "password_hash" not in existing_columns:
        op.add_column(
            "users",
            sa.Column(
                "password_hash",
                sqlmodel.sql.sqltypes.AutoString(length=255),
                nullable=True,
            ),
        )

    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("users") as batch_op:
        # Make google_id nullable
        batch_op.alter_column(
            "google_id",
            existing_type=sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        )

    # Add unique index on email (skip if already exists)
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_email" not in existing_indexes:
        op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    """Revert: drop password_hash, make google_id non-nullable, drop email index."""
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "password_hash")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "google_id",
            existing_type=sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        )
