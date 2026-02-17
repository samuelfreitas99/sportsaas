"""baseline

Revision ID: c9cbabbccc08
Revises:
Create Date: 2026-02-17 02:26:42.202813
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c9cbabbccc08"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
