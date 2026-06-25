"""security_service.py - Warning counter, auto-block at 5 violations, owner notification."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from backend.models.security_model import SecurityLog
from backend.models.email_model import EmailLog
from backend.models.document_model import Document
from backend.models.user_model import User
from backend.models.activity_model import ActivityLog, ActivityAction
from backend.services.email_service import send_block_notification, send_copy_attempt_notification

logger = logging.getLogger(__name__)
WARNING_LIMIT = 5


async def record_warning(db: AsyncSession, token: str) -> dict:
    """Increment warning count for a token. Auto-block at WARNING_LIMIT."""
    try:
        result = await db.execute(select(EmailLog).where(EmailLog.token == token))
        log: EmailLog | None = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="Token not found")

        sec_result = await db.execute(
            select(SecurityLog).where(SecurityLog.email_log_id == log.id)
        )
        sec: SecurityLog | None = sec_result.scalar_one_or_none()

        if not sec:
            sec = SecurityLog(email_log_id=log.id, receiver_email=log.receiver_email)
            db.add(sec)
            await db.flush()

        sec.warning_count += 1
        blocked = False
        
        # 1. Log the copy attempt in ActivityLog
        activity = ActivityLog(
            email_log_id=log.id,
            document_id=log.document_id,
            receiver_email=log.receiver_email,
            action=ActivityAction.COPY_ATTEMPT,
        )
        db.add(activity)

        # 2. Fetch document and owner for notifications
        doc_result = await db.execute(select(Document).where(Document.id == log.document_id))
        doc = doc_result.scalar_one_or_none()
        owner = None
        if doc:
            user_result = await db.execute(select(User).where(User.id == doc.user_id))
            owner = user_result.scalar_one_or_none()

        # 3. Handle Auto-Block
        if sec.warning_count >= WARNING_LIMIT and not sec.blocked_status:
            sec.blocked_status = True
            sec.blocked_at = datetime.now(timezone.utc)
            log.is_blocked = True
            blocked = True
            await db.flush()

            if owner:
                import asyncio
                asyncio.create_task(
                    send_block_notification(owner.email, log.receiver_email, doc.name)
                )
            logger.warning("URL BLOCKED for %s (token %s)", log.receiver_email, token)
        
        # 4. Send "Copy Attempt" notification to owner (regardless of block status)
        if owner:
            import asyncio
            asyncio.create_task(
                send_copy_attempt_notification(owner.email, log.receiver_email, doc.name if doc else "Unknown")
            )

        await db.flush()
        return {"warning_count": sec.warning_count, "blocked": blocked}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Warning record error for token %s: %s", token, exc)
        raise HTTPException(status_code=500, detail="Could not record warning") from exc


async def get_security_status(db: AsyncSession, token: str) -> dict:
    try:
        result = await db.execute(select(EmailLog).where(EmailLog.token == token))
        log: EmailLog | None = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="Token not found")

        sec_result = await db.execute(
            select(SecurityLog).where(SecurityLog.email_log_id == log.id)
        )
        sec = sec_result.scalar_one_or_none()
        return {
            "blocked": log.is_blocked,
            "warning_count": sec.warning_count if sec else 0,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Security status error for token %s: %s", token, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve security status") from exc
