from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    token: Optional[str] = None 
    role: Optional[str] = None  # 'superadmin', 'admin', 'user'
    company_id: Optional[int] = None
    id_address: Optional[int] = None
    active: Optional[bool] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    trade_mode: str = "live"  # bound mode for the issued token

class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: str = "user"
    company_id: Optional[int] = None

class CryptoCollectorPlayRequest(BaseModel):
    interval_seconds: int = 2

class CryptoCollectorStatusResponse(BaseModel):
    is_running: bool
    interval_seconds: int
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

class CryptoPriceItem(BaseModel):
    price_usdt: float = Field(..., example=105000.0)
    created_at: datetime = Field(..., example="2026-06-09T12:00:00")

class CryptoTickerResponse(BaseModel):
    symbol: str
    pair: str
    price_usdt: float
    price_change_percent_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_quote_24h: Optional[float] = None
    created_at: datetime

class CryptoLatestResponse(BaseModel):
    btc: Optional[CryptoPriceItem] = None
    eth: Optional[CryptoPriceItem] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "btc": {"price_usdt": 105000.0, "created_at": "2026-06-09T12:00:00"},
                "eth": {"price_usdt": 2800.0,   "created_at": "2026-06-09T12:00:00"},
            }
        }
    }

class CryptoHistoryResponse(BaseModel):
    symbol: str
    items: List[CryptoTickerResponse]


class CryptoPriceHistoryRangeRequest(BaseModel):
    symbol: str = Field(..., example="BTC")
    start_date: datetime = Field(..., example="2026-06-02T12:00:00")
    end_date: datetime = Field(..., example="2026-06-09T12:00:00")


class CryptoHistoryByDateResponse(BaseModel):
    items: List[CryptoPriceItem]

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {"price_usdt": 104500.0, "created_at": "2026-06-02T12:00:00"}
                ]
            }
        }
    }


class CryptoTradeCreateRequest(BaseModel):
    symbol: str = Field(..., example="BTC")
    unit_price_usdt: float = Field(..., example=104500.0)
    quantity: Optional[float] = Field(None, example=0.000957)
    executed_at: Optional[datetime] = Field(None, example="2026-06-09T12:00:00.000Z")


class CryptoTradeResponse(BaseModel):
    id_trade: int
    user_id: int
    trade_type: str
    symbol: str
    trade_mode: str
    quantity: float
    unit_price_usdt: float
    total_usdt: float
    executed_at: datetime
    created_at: datetime
    balance_usdt: Optional[float] = None
    holding_quantity: Optional[float] = None
    holding_value_usdt: Optional[float] = None
    avg_cost_usdt: Optional[float] = None


class CryptoTradeHistoryRequest(BaseModel):
    start_date: datetime = Field(..., example="2026-05-10T00:00:00.000Z")
    end_date: datetime = Field(..., example="2026-06-09T00:00:00.000Z")
    symbol: Optional[str] = Field(None, example="BTC", description="Opcional. BTC ou ETH.")
    trade_type: Optional[str] = Field(None, example="buy", description="Opcional. 'buy' ou 'sell'.")


class CryptoTradeHistoryItem(BaseModel):
    symbol: str = Field(..., example="BTC")
    trade_type: str = Field(..., example="buy")
    unit_price_usdt: float = Field(..., example=104500.0)
    quantity: float = Field(..., example=0.000957)
    executed_at: datetime = Field(..., example="2026-06-09T12:00:00")


class CryptoTradeHistoryResponse(BaseModel):
    items: List[CryptoTradeHistoryItem]

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "symbol": "BTC",
                        "trade_type": "buy",
                        "unit_price_usdt": 104500.0,
                        "quantity": 0.000957,
                        "executed_at": "2026-06-09T12:00:00",
                    }
                ]
            }
        }
    }


class AccountMutationRequest(BaseModel):
    amount_usdt: float = Field(..., example=100.0)
    description: Optional[str] = Field(None, example="Depósito inicial")
    user_id: Optional[int] = Field(None, example=1, description="Opcional. Apenas admins podem informar outro user_id.")


class UserAccountResponse(BaseModel):
    balance_usdt: float = Field(..., example=500.0)

    model_config = {
        "json_schema_extra": {"example": {"balance_usdt": 500.0}}
    }


class UserHoldingResponse(BaseModel):
    symbol: str
    trade_mode: str
    quantity: float
    avg_cost_usdt: float
    current_price_usdt: float
    current_value_usdt: float
    updated_at: datetime


class UserHoldingsResponse(BaseModel):
    user_id: int
    holdings: List[UserHoldingResponse]

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "holdings": [
                    {
                        "symbol": "BTC",
                        "trade_mode": "live",
                        "quantity": 0.000957,
                        "avg_cost_usdt": 104500.0,
                        "current_price_usdt": 105000.0,
                        "current_value_usdt": 100.49,
                        "updated_at": "2026-06-09T12:00:00",
                    }
                ],
            }
        }
    }


class PortfolioResponse(BaseModel):
    user_id: int
    trade_mode: str = "live"
    balance_usdt: float
    total_holdings_value_usdt: float
    total_portfolio_value_usdt: float
    holdings: List[UserHoldingResponse] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "trade_mode": "live",
                "balance_usdt": 500.0,
                "total_holdings_value_usdt": 100.49,
                "total_portfolio_value_usdt": 600.49,
                "holdings": [
                    {
                        "symbol": "BTC",
                        "trade_mode": "live",
                        "quantity": 0.000957,
                        "avg_cost_usdt": 104500.0,
                        "current_price_usdt": 105000.0,
                        "current_value_usdt": 100.49,
                        "updated_at": "2026-06-09T12:00:00",
                    }
                ],
            }
        }
    }