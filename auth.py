from datetime import datetime, timedelta, timezone
import os
from typing import Optional
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRY = 30
REFRESH_TOKEN_EXPIRY = 7

assert JWT_SECRET_KEY is not None
assert JWT_ALGORITHM is not None

ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return ctx.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return ctx.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRY
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


# Function to create refresh token
def create_refresh_token(data: dict) -> str:
    encoded_jwt = create_access_token(
        data, timedelta(days=REFRESH_TOKEN_EXPIRY)
    )
    return encoded_jwt


# Function to decode token
def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
