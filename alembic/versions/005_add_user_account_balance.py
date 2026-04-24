"""Add user account balance and holdings tables

Revision ID: 005_add_user_account_balance
Revises: 004_add_crypto_trade_history
Create Date: 2026-04-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_add_user_account_balance"
down_revision: Union[str, None] = "004_add_crypto_trade_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("IdAccount", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False, unique=True),
        sa.Column("BalanceUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("TotalDepositedUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("TotalWithdrawnUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("UpdatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_holdings",
        sa.Column("IdHolding", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False),
        sa.Column("Symbol", sa.String(length=10), nullable=False),
        sa.Column("Quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("AvgCostUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CurrentValueUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("UpdatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("IdUser", "Symbol", name="uq_user_holdings_user_symbol"),
    )

    op.add_column("crypto_trade_history", sa.Column("IdUser", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_crypto_trade_history_user",
        "crypto_trade_history",
        "User",
        ["IdUser"],
        ["IdUser"],
    )

    op.create_table(
        "account_transactions",
        sa.Column("IdTransaction", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False),
        sa.Column("TransactionType", sa.String(length=20), nullable=False),
        sa.Column("Symbol", sa.String(length=10), nullable=True),
        sa.Column("AmountUSDT", sa.Float(), nullable=False),
        sa.Column("Quantity", sa.Float(), nullable=True),
        sa.Column("Description", sa.String(length=255), nullable=True),
        sa.Column("ReferenceTradeId", sa.Integer(), sa.ForeignKey("crypto_trade_history.IdTrade"), nullable=True),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("account_transactions")
    op.drop_constraint("fk_crypto_trade_history_user", "crypto_trade_history", type_="foreignkey")
    op.drop_column("crypto_trade_history", "IdUser")
    op.drop_table("user_holdings")
    op.drop_table("user_account")