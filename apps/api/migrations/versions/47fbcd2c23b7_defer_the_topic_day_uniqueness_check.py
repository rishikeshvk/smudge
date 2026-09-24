"""defer the topic day uniqueness check

Revision ID: 47fbcd2c23b7
Revises: ede27df4c6a8
Create Date: 2026-09-24 19:07:28.374478

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "47fbcd2c23b7"
down_revision: str | Sequence[str] | None = "ede27df4c6a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Postgres can't make an existing unique constraint deferrable, so recreate it.
    op.drop_constraint("uq_topic_nodes_plan_id_day", "topic_nodes", type_="unique")
    op.create_unique_constraint(
        "uq_topic_nodes_plan_id_day",
        "topic_nodes",
        ["plan_id", "day"],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_topic_nodes_plan_id_day", "topic_nodes", type_="unique")
    op.create_unique_constraint(
        "uq_topic_nodes_plan_id_day", "topic_nodes", ["plan_id", "day"]
    )
