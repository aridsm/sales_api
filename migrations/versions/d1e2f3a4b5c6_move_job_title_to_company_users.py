"""move_job_title_to_company_users

Revision ID: d1e2f3a4b5c6
Revises: b5c6d7e8f9a0
Create Date: 2026-09-25 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'b5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('company_users', sa.Column('job_title', sa.String(length=100), nullable=True))
    op.drop_column('users', 'job_title')


def downgrade() -> None:
    op.add_column('users', sa.Column('job_title', sa.String(length=100), nullable=True))
    op.drop_column('company_users', 'job_title')
