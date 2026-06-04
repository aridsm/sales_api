"""add_user_id_to_sale_products

Revision ID: b4e7c2d19a3f
Revises: ac1f0b12990f
Create Date: 2026-05-28 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b4e7c2d19a3f'
down_revision: Union[str, Sequence[str], None] = 'ac1f0b12990f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sale_products', sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.create_foreign_key('fk_sale_products_user_id', 'sale_products', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_sale_products_user_id', 'sale_products', type_='foreignkey')
    op.drop_column('sale_products', 'user_id')
