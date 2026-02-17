"""add unique constraint on org_members (user_id, org_id)

Revision ID: a7b1c2d3e4f5
Revises: f29810277dfd
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a7b1c2d3e4f5"
down_revision: Union[str, None] = "f29810277dfd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_org_members_user_org",
        "org_members",
        ["user_id", "org_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_org_members_user_org", "org_members", type_="unique")
