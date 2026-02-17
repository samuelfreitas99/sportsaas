"""Phase 2B.8 game details

Revision ID: a8b9c0d1e2f3
Revises: f3a4b5c6d7e8
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("games"):
        return

    cols = {c["name"] for c in insp.get_columns("games")}
    if "created_by_member_id" not in cols:
        op.add_column(
            "games",
            sa.Column("created_by_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_games_created_by_member_id",
            "games",
            "org_members",
            ["created_by_member_id"],
            ["id"],
        )
        op.create_index("ix_games_created_by_member_id", "games", ["created_by_member_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("games"):
        return

    cols = {c["name"] for c in insp.get_columns("games")}
    if "created_by_member_id" in cols:
        existing_indexes = {ix["name"] for ix in insp.get_indexes("games")}
        if "ix_games_created_by_member_id" in existing_indexes:
            op.drop_index("ix_games_created_by_member_id", table_name="games")
        op.drop_constraint("fk_games_created_by_member_id", "games", type_="foreignkey")
        op.drop_column("games", "created_by_member_id")
