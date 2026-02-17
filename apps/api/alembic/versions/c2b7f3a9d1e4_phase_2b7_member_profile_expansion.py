"""Phase 2B.7 member profile expansion

Revision ID: c2b7f3a9d1e4
Revises: b7c8d9e0f1a2
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c2b7f3a9d1e4"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    user_cols = {c["name"] for c in insp.get_columns("users")} if insp.has_table("users") else set()
    if "avatar_url" not in user_cols:
        op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))
    if "phone" not in user_cols:
        op.add_column("users", sa.Column("phone", sa.String(length=64), nullable=True))

    if insp.has_table("org_members"):
        member_cols = {c["name"] for c in insp.get_columns("org_members")}

        member_type_create = postgresql.ENUM("MONTHLY", "GUEST", name="member_type")
        member_type_create.create(bind, checkfirst=True)
        member_type = postgresql.ENUM("MONTHLY", "GUEST", name="member_type", create_type=False)

        if "nickname" not in member_cols:
            op.add_column("org_members", sa.Column("nickname", sa.String(length=255), nullable=True))

        if "member_type" not in member_cols:
            op.add_column(
                "org_members",
                sa.Column("member_type", member_type, nullable=False, server_default="MONTHLY"),
            )
        else:
            op.alter_column(
                "org_members",
                "member_type",
                server_default="MONTHLY",
                existing_type=member_type,
            )

        if "is_active" not in member_cols:
            op.add_column(
                "org_members",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            )
        else:
            op.alter_column(
                "org_members",
                "is_active",
                nullable=False,
                server_default=sa.true(),
                existing_type=sa.Boolean(),
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("org_members"):
        member_cols = {c["name"] for c in insp.get_columns("org_members")}
        if "is_active" in member_cols:
            op.drop_column("org_members", "is_active")
        if "nickname" in member_cols:
            op.drop_column("org_members", "nickname")

    if insp.has_table("users"):
        user_cols = {c["name"] for c in insp.get_columns("users")}
        if "phone" in user_cols:
            op.drop_column("users", "phone")
        if "avatar_url" in user_cols:
            op.drop_column("users", "avatar_url")
