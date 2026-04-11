"""
security.py - JWT creation/verification and bcrypt password utilities.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

import bcrypt

def hash_password(plain: str) -> str:
    try:
        # bcrypt.hashpw expects bytes for both password and salt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    except Exception as exc:
        logger.error("Password hashing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Password processing error") from exc


def verify_password(plain: str, hashed: str) -> bool:
    try:
        # bcrypt.checkpw expects bytes for both the plain and the hashed password
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode["exp"] = expire
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except Exception as exc:
        logger.error("Token creation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Token generation error") from exc


def decode_access_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning("JWT decode error: %s", exc)
        raise credentials_exception from exc
