"""Initial migration - baseline

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-10

This is an empty migration to establish the baseline.
Since your database already has tables, we start with an empty migration
so that Alembic can track future changes.

Run `alembic stamp head` to mark this as applied without running it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Initial migration - baseline.
    
    Since the database already exists with tables, this migration is empty.
    It serves as a starting point for Alembic to track future schema changes.
    
    If you're setting up a new database from scratch, you can add the 
    table creation statements here.
    """
    pass


def downgrade() -> None:
    """
    Downgrade - nothing to do for baseline migration.
    """
    pass
