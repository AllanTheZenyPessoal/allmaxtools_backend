from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from datetime import timedelta, datetime
from jose import JWTError, jwt 
from fastapi.security import OAuth2PasswordBearer 

 
SECRET_KEY="mysecretkey"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=120
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(
    email: str,
    username: str,
    id_user: int,
    role: str = "user",
    company_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None
):
    to_encode = {
        "sub": email,
        "username": username,
        "id_user": id_user,
        "role": role,
        "company_id": company_id
    }
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        username = payload.get("username")
        id_user = payload.get("id_user")
        role = payload.get("role", "user")
        company_id = payload.get("company_id")
        if email is None or username is None or id_user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "email": email,
            "username": username,
            "id_user": id_user,
            "role": role,
            "company_id": company_id
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = payload.get("sub")
        if token_data is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {
        "email": payload.get("sub"),
        "username": payload.get("username"),
        "id_user": payload.get("id_user"),
        "role": payload.get("role", "user"),
        "company_id": payload.get("company_id")
    }

