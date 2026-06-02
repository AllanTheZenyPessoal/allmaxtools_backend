"""Add trade_mode to trade/transaction tables and create paper_balance/paper_holdings

Revision ID: 006_add_trade_mode_and_paper_tables
Revises: 005_add_user_account_balance
Create Date: 2026-05-08

Strategy
--------
All changes are additive / backward-compatible:
- New columns are NULLABLE with server_default 'live', so existing rows remain valid.
- New tables are independent; no existing constraints are dropped or renamed.
- Indexes improve query performance when filtering by user + mode.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_add_trade_mode_and_paper_tables"
down_revision: Union[str, None] = "005_add_user_account_balance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Add TradeMode to crypto_trade_history
    # ------------------------------------------------------------------
    op.add_column(
        "crypto_trade_history",
        sa.Column("TradeMode", sa.String(10), nullable=True, server_default="live"),
    )
    op.create_index(
        "idx_trade_history_user_mode",
        "crypto_trade_history",
        ["IdUser", "TradeMode"],
    )

    # ------------------------------------------------------------------
    # 2. Add TradeMode to account_transactions
    # ------------------------------------------------------------------
    op.add_column(
        "account_transactions",
        sa.Column("TradeMode", sa.String(10), nullable=True, server_default="live"),
    )
    op.create_index(
        "idx_account_transactions_user_mode",
        "account_transactions",
        ["IdUser", "TradeMode"],
    )

    # ------------------------------------------------------------------
    # 3. Create paper_balance table (mirrors user_account, paper-only)
    # ------------------------------------------------------------------
    op.create_table(
        "paper_balance",
        sa.Column("IdPaperBalance", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False, unique=True),
        sa.Column("BalanceUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("TotalDepositedUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("TotalWithdrawnUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("UpdatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # 4. Create paper_holdings table (mirrors user_holdings, paper-only)
    # ------------------------------------------------------------------
    op.create_table(
        "paper_holdings",
        sa.Column("IdPaperHolding", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False),
        sa.Column("Symbol", sa.String(10), nullable=False),
        sa.Column("Quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("AvgCostUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CurrentValueUSDT", sa.Float(), nullable=False, server_default="0"),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("UpdatedAt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("IdUser", "Symbol", name="uq_paper_holdings_user_symbol"),
    )
    op.create_index(
        "idx_paper_holdings_user_symbol",
        "paper_holdings",
        ["IdUser", "Symbol"],
    )


def downgrade() -> None:
    op.drop_index("idx_paper_holdings_user_symbol", table_name="paper_holdings")
    op.drop_table("paper_holdings")
    op.drop_table("paper_balance")

    op.drop_index("idx_account_transactions_user_mode", table_name="account_transactions")
    op.drop_column("account_transactions", "TradeMode")

    op.drop_index("idx_trade_history_user_mode", table_name="crypto_trade_history")
    op.drop_column("crypto_trade_history", "TradeMode")
