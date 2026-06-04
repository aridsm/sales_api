"""add_sale_products_table_and_sale_total

Revision ID: ac1f0b12990f
Revises: ece4f402b06c
Create Date: 2026-05-27 19:31:11.016808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ac1f0b12990f'
down_revision: Union[str, Sequence[str], None] = 'ece4f402b06c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sale_products',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('sale_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('product_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('sales', sa.Column('total', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sales', 'total')
    op.drop_table('sale_products')
