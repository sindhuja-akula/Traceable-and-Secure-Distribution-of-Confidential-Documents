"""tracking_routes.py - Secure viewer access and activity tracking."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from backend.database import get_db
from backend.schemas.email_schema import AccessRequest
from backend.services.tracking_service import validate_and_open, log_activity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/view-api", tags=["Tracking"])


class ActionLog(BaseModel):
    token: str
    action: str
    session_duration: Optional[float] = None


@router.post("/access")
async def access_document(
    data: AccessRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate token + password and return document content if allowed."""
    try:
        return await validate_and_open(db, data.token, data.password)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Access endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Access validation failed") from exc


@router.post("/track")
async def track_action(
    data: ActionLog,
    db: AsyncSession = Depends(get_db),
):
    """Log a user action event (copy_attempt, download_attempt, close)."""
    try:
        await log_activity(db, data.token, data.action, data.session_duration)
        return {"status": "logged"}
    except Exception as exc:
        # Non-fatal
        logger.warning("Track action error (non-fatal): %s", exc)
        return {"status": "error", "detail": str(exc)}
