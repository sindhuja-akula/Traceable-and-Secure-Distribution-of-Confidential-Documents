"""activity_routes.py - Activity logs for dashboard."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from backend.database import get_db
from backend.routes.auth_routes import _get_current_user_id
from backend.models.activity_model import ActivityLog
from backend.models.email_model import EmailLog
from backend.models.document_model import Document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/activity", tags=["Activity"])


class ActivityLogResponse(BaseModel):
    id: int
    receiver_email: str
    action: str
    timestamp: datetime
    session_duration: Optional[float] = None
    model_config = {"from_attributes": True}


@router.get("/{doc_id}", response_model=List[ActivityLogResponse])
async def get_activity_logs(
    doc_id: int,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all activity logs for a document (owned by caller)."""
    try:
        # Verify ownership
        doc_result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        )
        if not doc_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Document not found")

        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.document_id == doc_id)
            .order_by(ActivityLog.timestamp.desc())
        )
        return result.scalars().all()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Activity logs error for doc %s: %s", doc_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve activity logs") from exc
