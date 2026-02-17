"""Phase 2B.10 draft v1

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    team_side_create = postgresql.ENUM("A", "B", name="team_side")
    team_side_create.create(bind, checkfirst=True)

    draft_status_create = postgresql.ENUM("NOT_STARTED", "IN_PROGRESS", "FINISHED", name="draft_status")
    draft_status_create.create(bind, checkfirst=True)
    draft_status = postgresql.ENUM("NOT_STARTED", "IN_PROGRESS", "FINISHED", name="draft_status", create_type=False)
    team_side = postgresql.ENUM("A", "B", name="team_side", create_type=False)

    if not insp.has_table("game_drafts"):
        op.create_table(
            "game_drafts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", draft_status, nullable=False, server_default="NOT_STARTED"),
            sa.Column("order_mode", sa.String(length=32), nullable=False, server_default="ABBA"),
            sa.Column("current_pick_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.UniqueConstraint("game_id", name="uq_game_drafts_game_id"),
        )
        op.create_index("ix_game_drafts_org_id", "game_drafts", ["org_id"])
        op.create_index("ix_game_drafts_game_id", "game_drafts", ["game_id"])

    if not insp.has_table("game_draft_picks"):
        op.create_table(
            "game_draft_picks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("draft_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("round_number", sa.Integer(), nullable=False),
            sa.Column("pick_number", sa.Integer(), nullable=False),
            sa.Column("team_side", team_side, nullable=False),
            sa.Column("org_member_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("game_guest_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["draft_id"], ["game_drafts.id"]),
            sa.ForeignKeyConstraint(["org_member_id"], ["org_members.id"]),
            sa.ForeignKeyConstraint(["game_guest_id"], ["game_guests.id"]),
            sa.UniqueConstraint("draft_id", "pick_number", name="uq_game_draft_picks_draft_pick_number"),
            sa.CheckConstraint(
                "(org_member_id IS NOT NULL AND game_guest_id IS NULL) OR (org_member_id IS NULL AND game_guest_id IS NOT NULL)",
                name="ck_game_draft_picks_exactly_one_target",
            ),
        )
        op.create_index("ix_game_draft_picks_org_id", "game_draft_picks", ["org_id"])
        op.create_index("ix_game_draft_picks_game_id", "game_draft_picks", ["game_id"])
        op.create_index("ix_game_draft_picks_draft_id", "game_draft_picks", ["draft_id"])

        op.create_index(
            "uq_game_draft_picks_game_org_member",
            "game_draft_picks",
            ["game_id", "org_member_id"],
            unique=True,
            postgresql_where=sa.text("org_member_id IS NOT NULL"),
        )
        op.create_index(
            "uq_game_draft_picks_game_guest",
            "game_draft_picks",
            ["game_id", "game_guest_id"],
            unique=True,
            postgresql_where=sa.text("game_guest_id IS NOT NULL"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("game_draft_picks"):
        existing_indexes = {ix["name"] for ix in insp.get_indexes("game_draft_picks")}
        if "uq_game_draft_picks_game_guest" in existing_indexes:
            op.drop_index("uq_game_draft_picks_game_guest", table_name="game_draft_picks")
        if "uq_game_draft_picks_game_org_member" in existing_indexes:
            op.drop_index("uq_game_draft_picks_game_org_member", table_name="game_draft_picks")
        op.drop_index("ix_game_draft_picks_draft_id", table_name="game_draft_picks")
        op.drop_index("ix_game_draft_picks_game_id", table_name="game_draft_picks")
        op.drop_index("ix_game_draft_picks_org_id", table_name="game_draft_picks")
        op.drop_table("game_draft_picks")

    if insp.has_table("game_drafts"):
        op.drop_index("ix_game_drafts_game_id", table_name="game_drafts")
        op.drop_index("ix_game_drafts_org_id", table_name="game_drafts")
        op.drop_table("game_drafts")
