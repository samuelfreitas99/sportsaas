"""rename created_by to created_by_id on ledger_entries

Revision ID: f29810277dfd
Revises: 
Create Date: 2026-02-17 02:22:52.694104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f29810277dfd"
down_revision: Union[str, None] = "c9cbabbccc08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE ledger_entries RENAME COLUMN created_by TO created_by_id')


def downgrade() -> None:
    op.execute('ALTER TABLE ledger_entries RENAME COLUMN created_by_id TO created_by')

