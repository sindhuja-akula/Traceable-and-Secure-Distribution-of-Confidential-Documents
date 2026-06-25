"""progress_service.py - Aggregate email sending progress stats."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from backend.models.email_model import EmailLog, EmailStatus
from backend.schemas.email_schema import ProgressStats

logger = logging.getLogger(__name__)


async def get_progress(db: AsyncSession, document_id: int) -> ProgressStats:
    try:
        result = await db.execute(
            select(
                EmailLog.status,
                func.count(EmailLog.id).label("count")
            )
            .where(EmailLog.document_id == document_id)
            .group_by(EmailLog.status)
        )
        rows = result.all()
        counts = {row.status: row.count for row in rows}
        total = sum(counts.values())
        
        # Identify current recipient and action
        current_recipient = None
        current_action = None
        
        if counts.get(EmailStatus.IN_PROGRESS, 0) > 0:
            ip_res = await db.execute(
                select(EmailLog)
                .where(EmailLog.document_id == document_id, EmailLog.status == EmailStatus.IN_PROGRESS)
                .limit(1)
            )
            ip_log = ip_res.scalar_one_or_none()
            if ip_log:
                current_recipient = ip_log.receiver_email
                current_action = ip_log.processing_step

        return ProgressStats(
            total=total,
            sent=counts.get(EmailStatus.SENT, 0),
            failed=counts.get(EmailStatus.FAILED, 0),
            in_progress=counts.get(EmailStatus.IN_PROGRESS, 0),
            pending=counts.get(EmailStatus.PENDING, 0),
            current_recipient=current_recipient,
            current_action=current_action,
        )
    except Exception as exc:
        logger.error("Progress fetch error for doc %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve progress stats") from exc


async def get_email_logs(db: AsyncSession, document_id: int):
    try:
        result = await db.execute(
            select(EmailLog)
            .where(EmailLog.document_id == document_id)
            .order_by(EmailLog.created_at.desc())
        )
        return result.scalars().all()
    except Exception as exc:
        logger.error("Email log fetch error for doc %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve email logs") from exc
