"""auth_routes.py - Authentication endpoints including password reset."""
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel, EmailStr

from backend.database import get_db
from backend.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.models.user_model import User
from backend.models.auth_model import OTPVerification
from backend.services.auth_service import register_user, login_user, logout_user
from backend.services.email_service import send_otp_email
from backend.core.security import decode_access_token, hash_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# --- Schemas for Password Reset ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp_code: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

# --- Dependency ---
def _get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
) -> int:
    try:
        final_token = credentials.credentials if credentials else token
        if not final_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        payload = decode_access_token(final_token)
        return int(payload.get("sub"))
    except Exception as exc:
        logger.error("Authentication failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc

# --- Auth Routes ---

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await register_user(db, data)
    except HTTPException: raise
    except Exception as exc:
        logger.error("Register error: %s", exc)
        raise HTTPException(status_code=500, detail="Registration failed") from exc

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        return await login_user(db, data)
    except HTTPException: raise
    except Exception as exc:
        logger.error("Login error: %s", exc)
        raise HTTPException(status_code=500, detail="Login failed") from exc

@router.post("/logout")
async def logout(user_id: int = Depends(_get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        await logout_user(db, user_id)
        return {"message": "Logged out successfully"}
    except Exception as exc:
        logger.error("Logout error: %s", exc)
        raise HTTPException(status_code=500, detail="Logout failed") from exc

@router.get("/me", response_model=UserResponse)
async def get_me(user_id: int = Depends(_get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException: raise
    except Exception as exc:
        logger.error("Get-me error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not fetch user") from exc

# --- Password Reset Flow ---

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Generate and send a 6-digit OTP to the user's email."""
    try:
        user_email = data.email.lower().strip()
        # 1. Verify user exists
        result = await db.execute(select(User).where(func.lower(User.email) == user_email))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Email not found")

        # 2. Cleanup old OTPs for this email
        await db.execute(delete(OTPVerification).where(func.lower(OTPVerification.email) == user_email))

        # 3. Generate 6-digit OTP
        otp = "".join(random.choices(string.digits, k=6))
        expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

        # 4. Save to DB
        new_otp = OTPVerification(email=user_email, otp_code=otp, expires_at=expiry)
        db.add(new_otp)
        await db.commit()

        # 5. Send via Email
        await send_otp_email(user_email, otp)
        logger.info("OTP sent to %s", data.email)
        
        return {"message": "OTP sent to your email"}
    except HTTPException: raise
    except Exception as exc:
        logger.error("Forgot password error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not process forgot password request")

@router.post("/verify-otp")
async def verify_otp(data: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    """Check if the provided OTP is valid and not expired."""
    try:
        user_email = data.email.lower().strip()
        result = await db.execute(
            select(OTPVerification).where(
                func.lower(OTPVerification.email) == user_email, 
                OTPVerification.otp_code == data.otp_code
            )
        )
        record = result.scalar_one_or_none()
        
        if not record or record.is_expired:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        record.is_verified = True
        await db.commit()
        return {"message": "OTP verified successfully"}
    except HTTPException: raise
    except Exception as exc:
        logger.error("OTP verification error: %s", exc)
        raise HTTPException(status_code=500, detail="OTP verification failed")

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset the user's password if the OTP has been verified."""
    try:
        user_email = data.email.lower().strip()
        # 1. Check if OTP was verified
        result = await db.execute(
            select(OTPVerification).where(
                func.lower(OTPVerification.email) == user_email,
                OTPVerification.otp_code == data.otp_code,
                OTPVerification.is_verified == True
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=400, detail="OTP not verified or invalid")

        # 2. Update user password
        hashed = hash_password(data.new_password)
        await db.execute(
            update(User).where(func.lower(User.email) == user_email).values(hashed_password=hashed)
        )
        
        # 3. Cleanup: Delete the used OTP
        await db.execute(delete(OTPVerification).where(func.lower(OTPVerification.email) == user_email))
        
        await db.commit()
        logger.info("Password reset successfully for %s", user_email)
        return {"message": "Password reset successfully"}
    except HTTPException: raise
    except Exception as exc:
        logger.error("Reset password error: %s", exc)
        raise HTTPException(status_code=500, detail="Password reset failed")
