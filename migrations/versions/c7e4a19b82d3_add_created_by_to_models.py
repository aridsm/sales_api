"""add_created_by_to_models

Revision ID: c7e4a19b82d3
Revises: eccad1be1534
Create Date: 2026-09-05 12:31:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7e4a19b82d3'
down_revision: Union[str, Sequence[str], None] = 'eccad1be1534'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tables = [
    'categories',
    'products',
    'sales',
    'stock_entries',
    'history',
    'other_expenses',
]


def upgrade() -> None:
    for table in tables:
        op.add_column(table, sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index(op.f(f'ix_{table}_created_by'), table, ['created_by'], unique=False)
        op.create_foreign_key(
            f'fk_{table}_created_by_users',
            table,
            'users',
            ['created_by'],
            ['id'],
            ondelete='SET NULL',
        )
        # Backfill existing records with user_id
        op.execute(f"UPDATE {table} SET created_by = user_id WHERE created_by IS NULL")


def downgrade() -> None:
    for table in tables:
        op.drop_constraint(f'fk_{table}_created_by_users', table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_created_by'), table_name=table)
        op.drop_column(table, 'created_by')
