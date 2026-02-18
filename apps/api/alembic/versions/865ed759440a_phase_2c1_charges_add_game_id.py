from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "865ed759440a"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) coluna game_id
    cols = {c["name"] for c in insp.get_columns("org_charges")}
    if "game_id" not in cols:
        op.add_column("org_charges", sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 2) índice(s) / FK(s) (se a migration cria)
    existing_indexes = {ix["name"] for ix in insp.get_indexes("org_charges")}
    if "ix_org_charges_game_id" not in existing_indexes:
        op.create_index("ix_org_charges_game_id", "org_charges", ["game_id"])

    # se tiver FK, cheque também
    existing_fks = {fk["name"] for fk in insp.get_foreign_keys("org_charges")}
    if "fk_org_charges_game_id" not in existing_fks:
        op.create_foreign_key(
            "fk_org_charges_game_id",
            "org_charges",
            "games",
            ["game_id"],
            ["id"],
        )

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    cols = {c["name"] for c in insp.get_columns("org_charges")}
    if "game_id" not in cols:
        return

    existing_fks = {fk["name"] for fk in insp.get_foreign_keys("org_charges")}
    if "fk_org_charges_game_id" in existing_fks:
        op.drop_constraint("fk_org_charges_game_id", "org_charges", type_="foreignkey")

    existing_indexes = {ix["name"] for ix in insp.get_indexes("org_charges")}
    if "ix_org_charges_game_id" in existing_indexes:
        op.drop_index("ix_org_charges_game_id", table_name="org_charges")

    op.drop_column("org_charges", "game_id")
