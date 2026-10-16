"""add_discount_to_sales_and_stock_entries

Revision ID: f1a2b3c4d5e6
Revises: e2f3a4b5c6d7
Create Date: 2026-10-13 19:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sales', sa.Column('discount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('stock_entries', sa.Column('discount', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('stock_entries', 'discount')
    op.drop_column('sales', 'discount')
