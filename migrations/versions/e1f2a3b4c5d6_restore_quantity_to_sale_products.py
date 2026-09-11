"""restore_quantity_to_sale_products

Revision ID: e1f2a3b4c5d6
Revises: eccad1be1534
Create Date: 2026-09-01 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'eccad1be1534'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sale_products', sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'))
    op.alter_column('sale_products', 'quantity', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sale_products', 'quantity')
