"""add company multi tenant system

Revision ID: 62b93feecf28
Revises: 0a46e29fe505
Create Date: 2026-08-24 01:38:48.973605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import uuid


# revision identifiers, used by Alembic.
revision: str = '62b93feecf28'
down_revision: Union[str, Sequence[str], None] = '0a46e29fe505'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create new tables
    op.create_table('companies',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('company_invitations',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('company_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('invited_by', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('permission', sa.Enum('VIEW', 'VIEW_EDIT', 'ADMIN', name='companypermission'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='invitationstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_invitations_company_id'), 'company_invitations', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_invitations_status'), 'company_invitations', ['status'], unique=False)
    op.create_index(op.f('ix_company_invitations_user_id'), 'company_invitations', ['user_id'], unique=False)
    op.create_table('company_users',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('company_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('permission', sa.Enum('VIEW', 'VIEW_EDIT', 'ADMIN', name='companypermission', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'user_id', name='uq_company_user')
    )
    op.create_index(op.f('ix_company_users_company_id'), 'company_users', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_users_user_id'), 'company_users', ['user_id'], unique=False)

    # 2. Add company_id as NULLABLE first to users
    op.add_column('users', sa.Column('company_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_index(op.f('ix_users_company_id'), 'users', ['company_id'], unique=False)
    op.create_foreign_key('fk_users_company_id', 'users', 'companies', ['company_id'], ['id'])

    # 3. Add company_id as NULLABLE to all data tables
    data_tables = [
        'categories', 'history', 'other_expenses', 'products',
        'sale_products', 'sales', 'stock_entries', 'stock_entry_products'
    ]
    for table in data_tables:
        op.add_column(table, sa.Column('company_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
        op.create_index(op.f(f'ix_{table}_company_id'), table, ['company_id'], unique=False)

    # 4. Data migration: Create a company for each existing user and migrate data
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id, name FROM users")).fetchall()

    for user_row in users:
        user_id = user_row[0]
        user_name = user_row[1]
        company_id = str(uuid.uuid4())

        # Create company
        conn.execute(sa.text(
            "INSERT INTO companies (id, name, created_at, updated_at) VALUES (:id, :name, now(), now())"
        ), {"id": company_id, "name": user_name})

        # Create company_user with ADMIN permission
        conn.execute(sa.text(
            "INSERT INTO company_users (id, company_id, user_id, permission, created_at) VALUES (:id, :company_id, :user_id, 'ADMIN', now())"
        ), {"id": str(uuid.uuid4()), "company_id": company_id, "user_id": str(user_id)})

        # Set active company on user
        conn.execute(sa.text(
            "UPDATE users SET company_id = :company_id WHERE id = :user_id"
        ), {"company_id": company_id, "user_id": str(user_id)})

        # Migrate all data tables for this user
        for table in data_tables:
            conn.execute(sa.text(
                f"UPDATE {table} SET company_id = :company_id WHERE user_id = :user_id"
            ), {"company_id": company_id, "user_id": str(user_id)})

    # 5. Now set company_id to NOT NULL on data tables and add foreign keys
    for table in data_tables:
        op.alter_column(table, 'company_id', nullable=False)
        op.create_foreign_key(f'fk_{table}_company_id', table, 'companies', ['company_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    data_tables = [
        'categories', 'history', 'other_expenses', 'products',
        'sale_products', 'sales', 'stock_entries', 'stock_entry_products'
    ]
    for table in data_tables:
        op.drop_constraint(f'fk_{table}_company_id', table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_company_id'), table_name=table)
        op.drop_column(table, 'company_id')

    op.drop_constraint('fk_users_company_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_column('users', 'company_id')

    op.drop_index(op.f('ix_company_users_user_id'), table_name='company_users')
    op.drop_index(op.f('ix_company_users_company_id'), table_name='company_users')
    op.drop_table('company_users')
    op.drop_index(op.f('ix_company_invitations_user_id'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_status'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_company_id'), table_name='company_invitations')
    op.drop_table('company_invitations')
    op.drop_table('companies')
