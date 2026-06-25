"""security_routes.py - Warning and block management endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.services.security_service import record_warning, get_security_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["Security"])


class WarnRequest(BaseModel):
    token: str


@router.post("/warn")
async def warn(data: WarnRequest, db: AsyncSession = Depends(get_db)):
    """Record a security violation warning for a token."""
    try:
        return await record_warning(db, data.token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Warn endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not record warning") from exc


@router.get("/status/{token}")
async def security_status(token: str, db: AsyncSession = Depends(get_db)):
    """Check if a token is blocked and its warning count."""
    try:
        return await get_security_status(db, token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Security status error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not retrieve security status") from exc
