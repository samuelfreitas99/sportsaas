"""phase_2c1 charges add game_id

Revision ID: 865ed759440a
Revises: c3d4e5f6a7b8
Create Date: 2026-02-18 00:16:43.582424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '865ed759440a'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("org_charges", sa.Column("game_id", sa.UUID(), nullable=True))

    # indexes para relatórios/lookup
    op.create_index("ix_org_charges_game_id", "org_charges", ["game_id"])
    op.create_index("ix_org_charges_org_game", "org_charges", ["org_id", "game_id"])

    # FK opcional (SET NULL evita travar deletes de games no futuro)
    op.create_foreign_key(
        "org_charges_game_id_fkey",
        "org_charges",
        "games",
        ["game_id"],
        ["id"],
        ondelete="SET NULL",
    )

def downgrade():
    op.drop_constraint("org_charges_game_id_fkey", "org_charges", type_="foreignkey")
    op.drop_index("ix_org_charges_org_game", table_name="org_charges")
    op.drop_index("ix_org_charges_game_id", table_name="org_charges")
    op.drop_column("org_charges", "game_id")
