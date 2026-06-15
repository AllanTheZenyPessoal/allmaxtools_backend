"""
Symmetric encryption helpers for sensitive credentials (Binance API keys).

Requires the BINANCE_ENCRYPTION_KEY environment variable to be set to a
valid Fernet key (32 url-safe base64 bytes).

Generate a key once and store it permanently:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException


def _get_fernet() -> Fernet:
    key = os.environ.get("BINANCE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="BINANCE_ENCRYPTION_KEY not configured on the server.",
        )
    try:
        return Fernet(key.encode())
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Invalid BINANCE_ENCRYPTION_KEY format. Generate one with: "
                   "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
        )


def encrypt(text: str) -> str:
    return _get_fernet().encrypt(text.encode()).decode()


def decrypt(text: str) -> str:
    try:
        return _get_fernet().decrypt(text.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Failed to decrypt stored credentials.")
