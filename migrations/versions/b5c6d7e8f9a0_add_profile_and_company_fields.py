"""add_profile_and_company_fields

Revision ID: b5c6d7e8f9a0
Revises: c7e4a19b82d3
Create Date: 2026-09-22 21:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'c7e4a19b82d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users new fields
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('job_title', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('document', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('zip_code', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('street', sa.String(length=150), nullable=True))
    op.add_column('users', sa.Column('number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('complement', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('neighborhood', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('state', sa.String(length=2), nullable=True))

    # companies new fields
    op.add_column('companies', sa.Column('logo_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('document', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('email', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('website', sa.String(length=150), nullable=True))
    op.add_column('companies', sa.Column('zip_code', sa.String(length=10), nullable=True))
    op.add_column('companies', sa.Column('street', sa.String(length=150), nullable=True))
    op.add_column('companies', sa.Column('number', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('complement', sa.String(length=50), nullable=True))
    op.add_column('companies', sa.Column('neighborhood', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('state', sa.String(length=2), nullable=True))


def downgrade() -> None:
    # companies new fields
    op.drop_column('companies', 'state')
    op.drop_column('companies', 'city')
    op.drop_column('companies', 'neighborhood')
    op.drop_column('companies', 'complement')
    op.drop_column('companies', 'number')
    op.drop_column('companies', 'street')
    op.drop_column('companies', 'zip_code')
    op.drop_column('companies', 'website')
    op.drop_column('companies', 'phone')
    op.drop_column('companies', 'email')
    op.drop_column('companies', 'document')
    op.drop_column('companies', 'logo_url')

    # users new fields
    op.drop_column('users', 'state')
    op.drop_column('users', 'city')
    op.drop_column('users', 'neighborhood')
    op.drop_column('users', 'complement')
    op.drop_column('users', 'number')
    op.drop_column('users', 'street')
    op.drop_column('users', 'zip_code')
    op.drop_column('users', 'document')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'avatar_url')
