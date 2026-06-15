from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'

    id_user = Column("IdUser", Integer, primary_key=True, autoincrement=True)
    username = Column("UserName", String(250), unique=True, nullable=True)
    password = Column("Password", String(250))
    email = Column("Email", String(250), unique=True)
    phone = Column("Phone", String(45), nullable=True)
    token = Column("Token", String(500), unique=True, nullable=True)
    role = Column("role", String(50), nullable=False, default='user')  # 'superadmin', 'admin', 'user'
    company_id = Column("company_id", Integer, nullable=True)  # Removendo ForeignKey temporariamente
    created_at = Column("CreatedAt", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("UpdatedAt", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)
    active = Column("Active", Boolean, nullable=True, default=True)

class CryptoPriceSnapshot(Base):
    __tablename__ = "crypto_price_snapshot"

    id_snapshot = Column("IdSnapshot", Integer, primary_key=True, autoincrement=True)
    symbol = Column("Symbol", String(10), nullable=False)  # BTC or ETH
    pair = Column("Pair", String(20), nullable=False)  # BTCUSDT or ETHUSDT
    price_usdt = Column("PriceUSDT", Float, nullable=False)
    price_change_percent_24h = Column("PriceChangePercent24h", Float, nullable=True)
    high_24h = Column("High24h", Float, nullable=True)
    low_24h = Column("Low24h", Float, nullable=True)
    volume_quote_24h = Column("VolumeQuote24h", Float, nullable=True)
    source = Column("Source", String(50), nullable=False, default="binance")
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)

class CryptoCollectorState(Base):
    __tablename__ = "crypto_collector_state"

    id_state = Column("IdState", Integer, primary_key=True, autoincrement=True)
    is_running = Column("IsRunning", Boolean, nullable=False, default=False)
    interval_seconds = Column("IntervalSeconds", Integer, nullable=False, default=5)
    started_at = Column("StartedAt", DateTime, nullable=True)
    stopped_at = Column("StoppedAt", DateTime, nullable=True)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CryptoTradeHistory(Base):
    __tablename__ = "crypto_trade_history"

    id_trade = Column("IdTrade", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False)
    trade_type = Column("TradeType", String(10), nullable=False)  # buy or sell
    symbol = Column("Symbol", String(10), nullable=False)  # BTC or ETH
    trade_mode = Column("TradeMode", String(10), nullable=False, default="live")  # live or paper
    quantity = Column("Quantity", Float, nullable=False)
    unit_price_usdt = Column("UnitPriceUSDT", Float, nullable=False)
    total_usdt = Column("TotalUSDT", Float, nullable=False)
    executed_at = Column("ExecutedAt", DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    binance_order_id = Column("BinanceOrderId", String(50), nullable=True)


class UserAccount(Base):
    __tablename__ = "user_account"

    id_account = Column("IdAccount", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False, unique=True)
    balance_usdt = Column("BalanceUSDT", Float, nullable=False, default=0)
    total_deposited_usdt = Column("TotalDepositedUSDT", Float, nullable=False, default=0)
    total_withdrawn_usdt = Column("TotalWithdrawnUSDT", Float, nullable=False, default=0)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserHolding(Base):
    __tablename__ = "user_holdings"
    __table_args__ = (UniqueConstraint("IdUser", "Symbol", name="uq_user_holdings_user_symbol"),)

    id_holding = Column("IdHolding", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False)
    symbol = Column("Symbol", String(10), nullable=False)
    quantity = Column("Quantity", Float, nullable=False, default=0)
    avg_cost_usdt = Column("AvgCostUSDT", Float, nullable=False, default=0)
    current_value_usdt = Column("CurrentValueUSDT", Float, nullable=False, default=0)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccountTransaction(Base):
    __tablename__ = "account_transactions"

    id_transaction = Column("IdTransaction", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False)
    transaction_type = Column("TransactionType", String(20), nullable=False)
    trade_mode = Column("TradeMode", String(10), nullable=False, default="live")  # live or paper
    symbol = Column("Symbol", String(10), nullable=True)
    amount_usdt = Column("AmountUSDT", Float, nullable=False)
    quantity = Column("Quantity", Float, nullable=True)
    description = Column("Description", String(255), nullable=True)
    reference_trade_id = Column("ReferenceTradeId", Integer, ForeignKey("crypto_trade_history.IdTrade"), nullable=True)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)


class PaperBalance(Base):
    """Virtual account balance used exclusively for paper trading."""
    __tablename__ = "paper_balance"

    id_paper_balance = Column("IdPaperBalance", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False, unique=True)
    balance_usdt = Column("BalanceUSDT", Float, nullable=False, default=0)
    total_deposited_usdt = Column("TotalDepositedUSDT", Float, nullable=False, default=0)
    total_withdrawn_usdt = Column("TotalWithdrawnUSDT", Float, nullable=False, default=0)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BinanceCredentials(Base):
    """Encrypted Binance API credentials stored per user."""
    __tablename__ = "binance_credentials"

    id_credential = Column("IdCredential", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False, unique=True)
    api_key_encrypted = Column("ApiKeyEncrypted", String(512), nullable=False)
    api_secret_encrypted = Column("ApiSecretEncrypted", String(512), nullable=False)
    api_key_hint = Column("ApiKeyHint", String(10), nullable=False)
    testnet = Column("Testnet", Boolean, nullable=False, default=False)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaperHolding(Base):
    """Simulated crypto positions used exclusively for paper trading."""
    __tablename__ = "paper_holdings"
    __table_args__ = (UniqueConstraint("IdUser", "Symbol", name="uq_paper_holdings_user_symbol"),)

    id_paper_holding = Column("IdPaperHolding", Integer, primary_key=True, autoincrement=True)
    user_id = Column("IdUser", Integer, ForeignKey("User.IdUser"), nullable=False)
    symbol = Column("Symbol", String(10), nullable=False)
    quantity = Column("Quantity", Float, nullable=False, default=0)
    avg_cost_usdt = Column("AvgCostUSDT", Float, nullable=False, default=0)
    current_value_usdt = Column("CurrentValueUSDT", Float, nullable=False, default=0)
    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column("UpdatedAt", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
