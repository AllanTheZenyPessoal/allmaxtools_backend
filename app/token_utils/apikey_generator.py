from typing import Optional
from fastapi import HTTPException, Depends, status
from datetime import timedelta, datetime, timezone
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer


SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(
    email: str,
    username: str,
    id_user: int,
    role: str = "user",
    company_id: Optional[int] = None,
    trade_mode: str = "live",
    expires_delta: Optional[timedelta] = None,
    permanent: bool = False,
):
    now = datetime.utcnow()
    to_encode = {
        "sub": email,
        "username": username,
        "id_user": id_user,
        "role": role,
        "company_id": company_id,
        "trade_mode": trade_mode,
        "permanent": permanent,
    }
    if permanent:
        expires_at = None
    else:
        expires_at = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode["exp"] = expires_at

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM), expires_at


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        email = payload.get("sub")
        username = payload.get("username")
        id_user = payload.get("id_user")
        role = payload.get("role", "user")
        company_id = payload.get("company_id")
        trade_mode = payload.get("trade_mode", "live")
        permanent = payload.get("permanent", False)
        if email is None or username is None or id_user is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        exp = payload.get("exp")
        expired = False
        expires_at = None
        if not permanent and exp is not None:
            expires_at = datetime.utcfromtimestamp(exp)
            expired = datetime.utcnow() > expires_at

        return {
            "email": email,
            "username": username,
            "id_user": id_user,
            "role": role,
            "company_id": company_id,
            "trade_mode": trade_mode,
            "permanent": permanent,
            "expired": expired,
            "expires_at": expires_at,
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode without verifying exp — we do manual check below
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        if payload.get("sub") is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    permanent = payload.get("permanent", False)
    exp = payload.get("exp")

    if not permanent:
        if exp is None:
            raise credentials_exception
        if datetime.utcnow() > datetime.utcfromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return {
        "email": payload.get("sub"),
        "username": payload.get("username"),
        "id_user": payload.get("id_user"),
        "role": payload.get("role", "user"),
        "company_id": payload.get("company_id"),
        "trade_mode": payload.get("trade_mode", "live"),
        "permanent": permanent,
    }

