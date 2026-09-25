"""add invites and auth tokens

Revision ID: d57cc0f9961c
Revises: ccb22226e028
Create Date: 2026-09-25 12:01:26.198530

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d57cc0f9961c"
down_revision: str | Sequence[str] | None = "ccb22226e028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_auth_tokens_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_tokens_token_hash")),
    )
    op.create_index(
        op.f("ix_auth_tokens_user_id"), "auth_tokens", ["user_id"], unique=False
    )
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_invites_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invites")),
        sa.UniqueConstraint("code_hash", name=op.f("uq_invites_code_hash")),
    )
    op.create_index(op.f("ix_invites_user_id"), "invites", ["user_id"], unique=False)

    op.add_column(
        "users",
        sa.Column("is_owner", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(
        "uq_users_one_owner",
        "users",
        ["is_owner"],
        unique=True,
        postgresql_where="is_owner",
    )
    # Until now there was one user, and they run the server.
    op.execute(
        "UPDATE users SET is_owner = true WHERE id = (SELECT min(id) FROM users)"
    )

    # Registered phones were that user's; with no user there is nobody to push to.
    op.add_column("push_tokens", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute("UPDATE push_tokens SET user_id = (SELECT min(id) FROM users)")
    op.execute("DELETE FROM push_tokens WHERE user_id IS NULL")
    op.alter_column("push_tokens", "user_id", nullable=False)
    op.create_index(
        op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_push_tokens_user_id_users"),
        "push_tokens",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_push_tokens_user_id_users"), "push_tokens", type_="foreignkey"
    )
    op.drop_index(op.f("ix_push_tokens_user_id"), table_name="push_tokens")
    op.drop_column("push_tokens", "user_id")
    op.drop_index("uq_users_one_owner", table_name="users")
    op.drop_column("users", "is_owner")
    op.drop_index(op.f("ix_invites_user_id"), table_name="invites")
    op.drop_table("invites")
    op.drop_index(op.f("ix_auth_tokens_user_id"), table_name="auth_tokens")
    op.drop_table("auth_tokens")
