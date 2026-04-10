from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

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
    btc: Optional[CryptoTickerResponse] = None
    eth: Optional[CryptoTickerResponse] = None

class CryptoHistoryResponse(BaseModel):
    symbol: str
    items: List[CryptoTickerResponse]