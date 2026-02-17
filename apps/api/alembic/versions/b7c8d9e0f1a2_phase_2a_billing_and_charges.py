"""Phase 2A billing and charges

Revision ID: b7c8d9e0f1a2
Revises: a7b1c2d3e4f5
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a7b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    billing_mode_create = postgresql.ENUM(
        "MEMBERSHIP", "PER_SESSION", "HYBRID", name="billing_mode"
    )
    billing_cycle_create = postgresql.ENUM(
        "MONTHLY", "WEEKLY", "CUSTOM_WEEKS", name="billing_cycle"
    )
    charge_type_create = postgresql.ENUM("MEMBERSHIP", "PER_SESSION", name="charge_type")
    charge_status_create = postgresql.ENUM("PENDING", "PAID", "VOID", name="charge_status")

    billing_mode_create.create(op.get_bind(), checkfirst=True)
    billing_cycle_create.create(op.get_bind(), checkfirst=True)
    charge_type_create.create(op.get_bind(), checkfirst=True)
    charge_status_create.create(op.get_bind(), checkfirst=True)

    billing_mode = postgresql.ENUM(
        "MEMBERSHIP", "PER_SESSION", "HYBRID", name="billing_mode", create_type=False
    )
    billing_cycle = postgresql.ENUM(
        "MONTHLY", "WEEKLY", "CUSTOM_WEEKS", name="billing_cycle", create_type=False
    )
    charge_type = postgresql.ENUM(
        "MEMBERSHIP", "PER_SESSION", name="charge_type", create_type=False
    )
    charge_status = postgresql.ENUM(
        "PENDING", "PAID", "VOID", name="charge_status", create_type=False
    )

    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("org_billing_settings"):
        op.create_table(
            "org_billing_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("billing_mode", billing_mode, nullable=False, server_default="HYBRID"),
            sa.Column("cycle", billing_cycle, nullable=False, server_default="MONTHLY"),
            sa.Column("cycle_weeks", sa.Integer(), nullable=True),
            sa.Column("anchor_date", sa.Date(), nullable=False),
            sa.Column("due_day", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("membership_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("session_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.UniqueConstraint("org_id", name="uq_org_billing_settings_org_id"),
        )
        op.create_index("ix_org_billing_settings_org_id", "org_billing_settings", ["org_id"])

    if not insp.has_table("org_charges"):
        op.create_table(
            "org_charges",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_member_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("cycle_key", sa.String(length=64), nullable=False),
            sa.Column("type", charge_type, nullable=False),
            sa.Column("status", charge_status, nullable=False, server_default="PENDING"),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("ledger_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["org_member_id"], ["org_members.id"]),
            sa.ForeignKeyConstraint(["ledger_entry_id"], ["ledger_entries.id"]),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
            sa.UniqueConstraint(
                "org_id",
                "org_member_id",
                "cycle_key",
                "type",
                name="uq_org_charges_org_member_cycle_type",
            ),
        )
        op.create_index("ix_org_charges_org_id", "org_charges", ["org_id"])
        op.create_index("ix_org_charges_org_member_id", "org_charges", ["org_member_id"])
        op.create_index("ix_org_charges_cycle_key", "org_charges", ["cycle_key"])
        op.create_index("ix_org_charges_org_cycle", "org_charges", ["org_id", "cycle_key"])
        op.create_index("ix_org_charges_org_status", "org_charges", ["org_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_org_charges_org_status", table_name="org_charges")
    op.drop_index("ix_org_charges_org_cycle", table_name="org_charges")
    op.drop_index("ix_org_charges_cycle_key", table_name="org_charges")
    op.drop_index("ix_org_charges_org_member_id", table_name="org_charges")
    op.drop_index("ix_org_charges_org_id", table_name="org_charges")
    op.drop_table("org_charges")

    op.drop_index("ix_org_billing_settings_org_id", table_name="org_billing_settings")
    op.drop_table("org_billing_settings")

    op.execute("DROP TYPE IF EXISTS charge_status")
    op.execute("DROP TYPE IF EXISTS charge_type")
    op.execute("DROP TYPE IF EXISTS billing_cycle")
    op.execute("DROP TYPE IF EXISTS billing_mode")
