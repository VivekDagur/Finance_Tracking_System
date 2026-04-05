import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

# Generate a secure random key if not provided in production
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
# In production, always set SECRET_KEY environment variable
if os.getenv("SECRET_KEY") is None:
    import warnings
    warnings.warn("SECRET_KEY not set in environment variables. Using auto-generated key. Set SECRET_KEY for production.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

