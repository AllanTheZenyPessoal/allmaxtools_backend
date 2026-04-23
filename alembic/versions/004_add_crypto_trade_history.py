"""Add crypto trade history table

Revision ID: 004_add_crypto_trade_history
Revises: 003_add_role_and_company_to_user
Create Date: 2026-04-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004_add_crypto_trade_history"
down_revision: Union[str, None] = "003_add_role_and_company_to_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crypto_trade_history",
        sa.Column("IdTrade", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("TradeType", sa.String(length=10), nullable=False),
        sa.Column("Symbol", sa.String(length=10), nullable=False),
        sa.Column("Quantity", sa.Float(), nullable=False),
        sa.Column("UnitPriceUSDT", sa.Float(), nullable=False),
        sa.Column("TotalUSDT", sa.Float(), nullable=False),
        sa.Column("ExecutedAt", sa.DateTime(), nullable=False),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("crypto_trade_history")
