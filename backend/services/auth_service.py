"""auth_service.py - Registration, login, logout logic."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from backend.models.user_model import User
from backend.core.security import hash_password, verify_password, create_access_token
from backend.schemas.user_schema import UserCreate, UserLogin

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    try:
        # 1. Check password length for bcrypt (max 72 chars)
        if len(data.password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=400,
                detail="Password too long (max 72 characters)"
            )

        # 2. Check for existing user
        email_lower = data.email.lower().strip()
        existing = await db.execute(select(User).where(func.lower(User.email) == email_lower))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # 3. Hash and create
        hashed = hash_password(data.password)
        user = User(email=email_lower, hashed_password=hashed)
        db.add(user)
        
        # 4. Save and Commit
        await db.flush()
        await db.commit()
        logger.info("User registered: %s", data.email)
        
        return user
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Registration error for %s: %s", data.email, exc, exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Registration failed: {type(exc).__name__} - {str(exc)}"
        ) from exc


async def login_user(db: AsyncSession, data: UserLogin) -> dict:
    try:
        email_lower = data.email.lower().strip()
        result = await db.execute(select(User).where(func.lower(User.email) == email_lower))
        user: User | None = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        user.last_login = datetime.now(timezone.utc)
        await db.flush()
        token = create_access_token({"sub": str(user.id), "email": user.email})
        logger.info("User logged in: %s", data.email)
        return {"access_token": token, "token_type": "bearer", "user": user}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Login error for %s: %s", data.email, exc)
        raise HTTPException(status_code=500, detail="Login failed") from exc


async def logout_user(db: AsyncSession, user_id: int) -> None:
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if user:
            user.last_logout = datetime.now(timezone.utc)
            await db.flush()
            logger.info("User %s logged out", user_id)
    except Exception as exc:
        logger.error("Logout error for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Logout failed") from exc
