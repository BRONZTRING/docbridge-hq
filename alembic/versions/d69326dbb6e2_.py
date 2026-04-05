"""empty message

Revision ID: d69326dbb6e2
Revises: e12bd31aab2b
Create Date: 2026-04-05 23:37:32.480459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd69326dbb6e2'
down_revision: Union[str, Sequence[str], None] = 'e12bd31aab2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
