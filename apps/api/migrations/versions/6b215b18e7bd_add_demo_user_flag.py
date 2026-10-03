"""add demo user flag

Revision ID: 6b215b18e7bd
Revises: d57cc0f9961c
Create Date: 2026-10-03 22:53:20.735236

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b215b18e7bd"
down_revision: str | Sequence[str] | None = "d57cc0f9961c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(
        "uq_users_one_demo",
        "users",
        ["is_demo"],
        unique=True,
        postgresql_where="is_demo",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_users_one_demo", table_name="users", postgresql_where="is_demo")
    op.drop_column("users", "is_demo")
