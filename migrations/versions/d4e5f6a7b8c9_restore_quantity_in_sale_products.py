"""restore_quantity_in_sale_products

Revision ID: d4e5f6a7b8c9
Revises: c7e4a19b82d3
Create Date: 2026-09-05 14:04:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c7e4a19b82d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sale_products', sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'))
    op.alter_column('sale_products', 'quantity', server_default=None)


def downgrade() -> None:
    op.drop_column('sale_products', 'quantity')
