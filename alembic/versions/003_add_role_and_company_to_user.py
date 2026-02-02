"""Add role and company_id columns to User table

Revision ID: 003
Revises: 002
Create Date: 2026-01-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_role_and_company_to_user'
down_revision: Union[str, None] = '002_fix_salesorder'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to User table
    op.add_column('User', sa.Column('role', sa.String(50), nullable=False, server_default='user'))
    
    # Add company_id column to User table
    op.add_column('User', sa.Column('company_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('User', 'role')
    op.drop_column('User', 'company_id')
