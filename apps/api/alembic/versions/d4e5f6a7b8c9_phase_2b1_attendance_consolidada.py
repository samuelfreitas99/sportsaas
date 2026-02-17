"""Phase 2B.1 attendance consolidada

Revision ID: d4e5f6a7b8c9
Revises: c2b7f3a9d1e4
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c2b7f3a9d1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    attendance_status_create = postgresql.ENUM(
        "GOING", "MAYBE", "NOT_GOING", name="attendance_status"
    )
    attendance_status_create.create(bind, checkfirst=True)

    if not insp.has_table("game_attendance"):
        attendance_status = postgresql.ENUM(
            "GOING", "MAYBE", "NOT_GOING", name="attendance_status", create_type=False
        )
        op.create_table(
            "game_attendance",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_member_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", attendance_status, nullable=False, server_default="MAYBE"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["org_member_id"], ["org_members.id"]),
            sa.UniqueConstraint("org_member_id", "game_id", name="uq_game_attendance_org_member_game"),
        )
        op.create_index("ix_game_attendance_game_id", "game_attendance", ["game_id"])
        op.create_index("ix_game_attendance_user_id", "game_attendance", ["user_id"])
        op.create_index("ix_game_attendance_org_id", "game_attendance", ["org_id"])
        op.create_index("ix_game_attendance_org_member_id", "game_attendance", ["org_member_id"])
        op.create_index("ix_game_attendance_org_game", "game_attendance", ["org_id", "game_id"])
        op.create_index(
            "ix_game_attendance_org_member_game", "game_attendance", ["org_member_id", "game_id"]
        )
        return

    cols = {c["name"] for c in insp.get_columns("game_attendance")}

    if "org_id" not in cols:
        op.add_column(
            "game_attendance",
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_game_attendance_org_id",
            "game_attendance",
            "organizations",
            ["org_id"],
            ["id"],
        )
        op.create_index("ix_game_attendance_org_id", "game_attendance", ["org_id"])

    if "org_member_id" not in cols:
        op.add_column(
            "game_attendance",
            sa.Column("org_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_game_attendance_org_member_id",
            "game_attendance",
            "org_members",
            ["org_member_id"],
            ["id"],
        )
        op.create_index("ix_game_attendance_org_member_id", "game_attendance", ["org_member_id"])

    if "org_id" in cols or "org_member_id" in cols:
        op.execute(
            """
            UPDATE game_attendance ga
            SET org_id = g.org_id
            FROM games g
            WHERE ga.game_id = g.id
              AND ga.org_id IS NULL
            """
        )
        op.execute(
            """
            UPDATE game_attendance ga
            SET org_member_id = om.id
            FROM games g
            JOIN org_members om
              ON om.org_id = g.org_id AND om.user_id = ga.user_id
            WHERE ga.game_id = g.id
              AND ga.org_member_id IS NULL
            """
        )

    if "org_id" in cols:
        op.execute("UPDATE game_attendance SET org_id = org_id WHERE org_id IS NOT NULL")
    if "org_member_id" in cols:
        op.execute("UPDATE game_attendance SET org_member_id = org_member_id WHERE org_member_id IS NOT NULL")

    if "org_id" in {c["name"] for c in insp.get_columns("game_attendance")}:
        op.alter_column("game_attendance", "org_id", nullable=False, existing_type=postgresql.UUID(as_uuid=True))
    if "org_member_id" in {c["name"] for c in insp.get_columns("game_attendance")}:
        op.alter_column(
            "game_attendance",
            "org_member_id",
            nullable=False,
            existing_type=postgresql.UUID(as_uuid=True),
        )

    existing_indexes = {ix["name"] for ix in insp.get_indexes("game_attendance")}
    if "ix_game_attendance_org_game" not in existing_indexes:
        op.create_index("ix_game_attendance_org_game", "game_attendance", ["org_id", "game_id"])
    if "ix_game_attendance_org_member_game" not in existing_indexes:
        op.create_index("ix_game_attendance_org_member_game", "game_attendance", ["org_member_id", "game_id"])

    existing_uq = {uc["name"] for uc in insp.get_unique_constraints("game_attendance")}
    if "uq_game_attendance_org_member_game" not in existing_uq:
        op.create_unique_constraint(
            "uq_game_attendance_org_member_game", "game_attendance", ["org_member_id", "game_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("game_attendance"):
        return

    cols = {c["name"] for c in insp.get_columns("game_attendance")}

    existing_indexes = {ix["name"] for ix in insp.get_indexes("game_attendance")}
    if "ix_game_attendance_org_member_game" in existing_indexes:
        op.drop_index("ix_game_attendance_org_member_game", table_name="game_attendance")
    if "ix_game_attendance_org_game" in existing_indexes:
        op.drop_index("ix_game_attendance_org_game", table_name="game_attendance")

    existing_uq = {uc["name"] for uc in insp.get_unique_constraints("game_attendance")}
    if "uq_game_attendance_org_member_game" in existing_uq:
        op.drop_constraint("uq_game_attendance_org_member_game", "game_attendance", type_="unique")

    if "org_member_id" in cols:
        op.drop_index("ix_game_attendance_org_member_id", table_name="game_attendance")
        op.drop_constraint("fk_game_attendance_org_member_id", "game_attendance", type_="foreignkey")
        op.drop_column("game_attendance", "org_member_id")

    if "org_id" in cols:
        op.drop_index("ix_game_attendance_org_id", table_name="game_attendance")
        op.drop_constraint("fk_game_attendance_org_id", "game_attendance", type_="foreignkey")
        op.drop_column("game_attendance", "org_id")
