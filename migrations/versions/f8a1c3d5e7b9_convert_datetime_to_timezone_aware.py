"""Convert datetime columns to timezone-aware

Revision ID: f8a1c3d5e7b9
Revises: 33cef838c210
Create Date: 2026-06-21 13:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a1c3d5e7b9'
down_revision: Union[str, Sequence[str], None] = '33cef838c210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert all datetime columns from TIMESTAMP to TIMESTAMP WITH TIME ZONE."""
    # users
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('users', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'")

    # categories
    op.alter_column('categories', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")

    # products
    op.alter_column('products', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")

    # sales
    op.alter_column('sales', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('sales', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'")

    # sale_products
    op.alter_column('sale_products', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")

    # other_expenses
    op.alter_column('other_expenses', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('other_expenses', 'date',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="date AT TIME ZONE 'UTC'")

    # history
    op.alter_column('history', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Revert all datetime columns back to TIMESTAMP WITHOUT TIME ZONE."""
    op.alter_column('users', 'created_at', type_=sa.DateTime())
    op.alter_column('users', 'updated_at', type_=sa.DateTime())
    op.alter_column('categories', 'created_at', type_=sa.DateTime())
    op.alter_column('products', 'created_at', type_=sa.DateTime())
    op.alter_column('sales', 'created_at', type_=sa.DateTime())
    op.alter_column('sales', 'updated_at', type_=sa.DateTime())
    op.alter_column('sale_products', 'created_at', type_=sa.DateTime())
    op.alter_column('other_expenses', 'created_at', type_=sa.DateTime())
    op.alter_column('other_expenses', 'date', type_=sa.DateTime())
    op.alter_column('history', 'created_at', type_=sa.DateTime())
