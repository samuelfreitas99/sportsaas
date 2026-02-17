"""Phase 2B.2 guests

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("org_guests"):
        op.create_table(
            "org_guests",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        )
        op.create_index("ix_org_guests_org_id", "org_guests", ["org_id"])
        op.create_index(
            "uq_org_guests_org_phone_not_null",
            "org_guests",
            ["org_id", "phone"],
            unique=True,
            postgresql_where=sa.text("phone IS NOT NULL"),
        )

    if not insp.has_table("game_guests"):
        op.create_table(
            "game_guests",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_guest_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("created_by_member_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["org_guest_id"], ["org_guests.id"]),
            sa.ForeignKeyConstraint(["created_by_member_id"], ["org_members.id"]),
        )
        op.create_index("ix_game_guests_org_id", "game_guests", ["org_id"])
        op.create_index("ix_game_guests_game_id", "game_guests", ["game_id"])
        op.create_index("ix_game_guests_org_game", "game_guests", ["org_id", "game_id"])

        op.execute(
            """
            CREATE UNIQUE INDEX uq_game_guests_game_person
            ON game_guests (game_id, lower(btrim(name)), coalesce(btrim(phone), ''))
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("game_guests"):
        op.execute("DROP INDEX IF EXISTS uq_game_guests_game_person")
        op.drop_index("ix_game_guests_org_game", table_name="game_guests")
        op.drop_index("ix_game_guests_game_id", table_name="game_guests")
        op.drop_index("ix_game_guests_org_id", table_name="game_guests")
        op.drop_table("game_guests")

    if insp.has_table("org_guests"):
        op.drop_index("uq_org_guests_org_phone_not_null", table_name="org_guests")
        op.drop_index("ix_org_guests_org_id", table_name="org_guests")
        op.drop_table("org_guests")
