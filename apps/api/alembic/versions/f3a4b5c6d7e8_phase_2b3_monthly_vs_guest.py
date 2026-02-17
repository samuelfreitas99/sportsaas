"""Phase 2B.3 monthly vs guest

Revision ID: f3a4b5c6d7e8
Revises: e1f2a3b4c5d6
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("org_members"):
        return

    member_type_create = postgresql.ENUM("MONTHLY", "GUEST", name="member_type")
    member_type_create.create(bind, checkfirst=True)
    member_type = postgresql.ENUM("MONTHLY", "GUEST", name="member_type", create_type=False)

    cols = {c["name"] for c in insp.get_columns("org_members")}

    if "nickname" not in cols:
        op.add_column("org_members", sa.Column("nickname", sa.String(length=255), nullable=True))

    if "member_type" not in cols:
        op.add_column(
            "org_members",
            sa.Column("member_type", member_type, nullable=True, server_default="GUEST"),
        )
    else:
        op.alter_column(
            "org_members",
            "member_type",
            server_default="GUEST",
            existing_type=member_type,
        )

    op.execute("UPDATE org_members SET member_type = 'GUEST' WHERE member_type IS NULL")
    op.alter_column(
        "org_members",
        "member_type",
        nullable=False,
        existing_type=member_type,
        server_default="GUEST",
    )

    if "is_active" not in cols:
        op.add_column(
            "org_members",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    else:
        op.alter_column(
            "org_members",
            "is_active",
            nullable=False,
            existing_type=sa.Boolean(),
            server_default=sa.true(),
        )

    existing_indexes = {ix["name"] for ix in insp.get_indexes("org_members")}
    if "ix_org_members_org_member_type" not in existing_indexes:
        op.create_index("ix_org_members_org_member_type", "org_members", ["org_id", "member_type"])
    if "ix_org_members_org_is_active" not in existing_indexes:
        op.create_index("ix_org_members_org_is_active", "org_members", ["org_id", "is_active"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("org_members"):
        return

    existing_indexes = {ix["name"] for ix in insp.get_indexes("org_members")}
    if "ix_org_members_org_is_active" in existing_indexes:
        op.drop_index("ix_org_members_org_is_active", table_name="org_members")
    if "ix_org_members_org_member_type" in existing_indexes:
        op.drop_index("ix_org_members_org_member_type", table_name="org_members")

    cols = {c["name"] for c in insp.get_columns("org_members")}
    if "nickname" in cols:
        op.drop_column("org_members", "nickname")

    if "is_active" in cols:
        op.drop_column("org_members", "is_active")

    if "member_type" in cols:
        op.drop_column("org_members", "member_type")
