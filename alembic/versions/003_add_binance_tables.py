"""Add binance_credentials table and binance_order_id to crypto_trade_history

Revision ID: 003_binance
Revises: 002_fix_salesorder_column_names
Create Date: 2026-06-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_binance"
down_revision: Union[str, None] = "006_add_trade_mode_and_paper_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "binance_credentials",
        sa.Column("IdCredential", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("IdUser", sa.Integer(), sa.ForeignKey("User.IdUser"), nullable=False),
        sa.Column("ApiKeyEncrypted", sa.String(512), nullable=False),
        sa.Column("ApiSecretEncrypted", sa.String(512), nullable=False),
        sa.Column("ApiKeyHint", sa.String(10), nullable=False),
        sa.Column("Testnet", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("CreatedAt", sa.DateTime(), nullable=False),
        sa.Column("UpdatedAt", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("IdCredential"),
        sa.UniqueConstraint("IdUser", name="uq_binance_credentials_user"),
    )

    op.add_column(
        "crypto_trade_history",
        sa.Column("BinanceOrderId", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crypto_trade_history", "BinanceOrderId")
    op.drop_table("binance_credentials")
