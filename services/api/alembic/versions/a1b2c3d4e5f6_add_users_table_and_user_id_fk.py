"""Add users table and user_id FK to exercises

Revision ID: a1b2c3d4e5f6
Revises: 2cf86d906028
Create Date: 2026-02-12 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "2cf86d906028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table, insert system user, add user_id FK to exercises."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create users table (skip if init_db already created it)
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("google_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
            sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
            sa.Column("picture_url", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True),
            sa.Column("role", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default="user"),
            sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("google_id"),
        )
        op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)

    # Insert system user (id=1) if not already present
    result = bind.execute(sa.text("SELECT id FROM users WHERE id = 1"))
    if result.fetchone() is None:
        op.execute(
            "INSERT INTO users (id, google_id, email, name, role) "
            "VALUES (1, 'system', 'system@workout.local', 'System User', 'admin')"
        )

    # Add user_id column to exercises (skip if init_db already added it)
    existing_columns = [c["name"] for c in inspector.get_columns("exercises")]
    if "user_id" not in existing_columns:
        op.add_column(
            "exercises",
            sa.Column("user_id", sa.Integer(), nullable=False, server_default="1"),
        )

        # Create FK constraint and index
        op.create_foreign_key("fk_exercises_user_id", "exercises", "users", ["user_id"], ["id"])
        op.create_index(op.f("ix_exercises_user_id"), "exercises", ["user_id"])

        # Remove the server default (it was only needed for backfilling existing rows)
        op.alter_column("exercises", "user_id", server_default=None)


def downgrade() -> None:
    """Drop user_id from exercises and drop users table."""
    op.drop_index(op.f("ix_exercises_user_id"), table_name="exercises")
    op.drop_constraint("fk_exercises_user_id", "exercises", type_="foreignkey")
    op.drop_column("exercises", "user_id")
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_table("users")
