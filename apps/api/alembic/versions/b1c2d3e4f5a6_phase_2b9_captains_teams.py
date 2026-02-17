"""Phase 2B.9 captains and teams

Revision ID: b1c2d3e4f5a6
Revises: a8b9c0d1e2f3
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("games"):
        cols = {c["name"] for c in insp.get_columns("games")}

        if "captain_a_member_id" not in cols:
            op.add_column("games", sa.Column("captain_a_member_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_games_captain_a_member_id",
                "games",
                "org_members",
                ["captain_a_member_id"],
                ["id"],
            )
            op.create_index("ix_games_captain_a_member_id", "games", ["captain_a_member_id"])

        if "captain_b_member_id" not in cols:
            op.add_column("games", sa.Column("captain_b_member_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_games_captain_b_member_id",
                "games",
                "org_members",
                ["captain_b_member_id"],
                ["id"],
            )
            op.create_index("ix_games_captain_b_member_id", "games", ["captain_b_member_id"])

        if "captain_a_guest_id" not in cols:
            op.add_column("games", sa.Column("captain_a_guest_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_games_captain_a_guest_id",
                "games",
                "game_guests",
                ["captain_a_guest_id"],
                ["id"],
            )
            op.create_index("ix_games_captain_a_guest_id", "games", ["captain_a_guest_id"])

        if "captain_b_guest_id" not in cols:
            op.add_column("games", sa.Column("captain_b_guest_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_games_captain_b_guest_id",
                "games",
                "game_guests",
                ["captain_b_guest_id"],
                ["id"],
            )
            op.create_index("ix_games_captain_b_guest_id", "games", ["captain_b_guest_id"])

    team_side_create = postgresql.ENUM("A", "B", name="team_side")
    team_side_create.create(bind, checkfirst=True)
    team_side = postgresql.ENUM("A", "B", name="team_side", create_type=False)

    if not insp.has_table("game_team_members"):
        op.create_table(
            "game_team_members",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_member_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("team", team_side, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["org_member_id"], ["org_members.id"]),
            sa.UniqueConstraint("game_id", "org_member_id", name="uq_game_team_members_game_member"),
        )
        op.create_index("ix_game_team_members_org_id", "game_team_members", ["org_id"])
        op.create_index("ix_game_team_members_game_id", "game_team_members", ["game_id"])

    if not insp.has_table("game_team_guests"):
        op.create_table(
            "game_team_guests",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("game_guest_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("team", team_side, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["game_guest_id"], ["game_guests.id"]),
            sa.UniqueConstraint("game_id", "game_guest_id", name="uq_game_team_guests_game_guest"),
        )
        op.create_index("ix_game_team_guests_org_id", "game_team_guests", ["org_id"])
        op.create_index("ix_game_team_guests_game_id", "game_team_guests", ["game_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("game_team_guests"):
        op.drop_index("ix_game_team_guests_game_id", table_name="game_team_guests")
        op.drop_index("ix_game_team_guests_org_id", table_name="game_team_guests")
        op.drop_table("game_team_guests")

    if insp.has_table("game_team_members"):
        op.drop_index("ix_game_team_members_game_id", table_name="game_team_members")
        op.drop_index("ix_game_team_members_org_id", table_name="game_team_members")
        op.drop_table("game_team_members")

    if insp.has_table("games"):
        cols = {c["name"] for c in insp.get_columns("games")}
        existing_indexes = {ix["name"] for ix in insp.get_indexes("games")}

        if "captain_b_guest_id" in cols:
            if "ix_games_captain_b_guest_id" in existing_indexes:
                op.drop_index("ix_games_captain_b_guest_id", table_name="games")
            op.drop_constraint("fk_games_captain_b_guest_id", "games", type_="foreignkey")
            op.drop_column("games", "captain_b_guest_id")

        if "captain_a_guest_id" in cols:
            if "ix_games_captain_a_guest_id" in existing_indexes:
                op.drop_index("ix_games_captain_a_guest_id", table_name="games")
            op.drop_constraint("fk_games_captain_a_guest_id", "games", type_="foreignkey")
            op.drop_column("games", "captain_a_guest_id")

        if "captain_b_member_id" in cols:
            if "ix_games_captain_b_member_id" in existing_indexes:
                op.drop_index("ix_games_captain_b_member_id", table_name="games")
            op.drop_constraint("fk_games_captain_b_member_id", "games", type_="foreignkey")
            op.drop_column("games", "captain_b_member_id")

        if "captain_a_member_id" in cols:
            if "ix_games_captain_a_member_id" in existing_indexes:
                op.drop_index("ix_games_captain_a_member_id", table_name="games")
            op.drop_constraint("fk_games_captain_a_member_id", "games", type_="foreignkey")
            op.drop_column("games", "captain_a_member_id")
