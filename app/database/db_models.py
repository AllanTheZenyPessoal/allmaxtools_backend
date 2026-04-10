from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
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
