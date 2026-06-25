"""tracking_service.py - URL access validation, open tracking, session logging."""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from backend.models.email_model import EmailLog, EmailStatus
from backend.models.activity_model import ActivityLog, ActivityAction
from backend.models.document_model import Document

logger = logging.getLogger(__name__)
URL_EXPIRY_HOURS = 24


async def validate_and_open(db: AsyncSession, token: str, password: str) -> dict:
    """Validate token + password, check expiry, record OPEN event."""
    try:
        result = await db.execute(select(EmailLog).where(EmailLog.token == token))
        log: EmailLog | None = result.scalar_one_or_none()

        if not log:
            raise HTTPException(status_code=404, detail="Access link not found")
        if log.is_blocked:
            raise HTTPException(status_code=403, detail="This access link has been blocked")
        if log.password != password:
            raise HTTPException(status_code=401, detail="Incorrect password")

        now = datetime.now(timezone.utc)

        # Set first_opened_at and default expiry if not already set
        if not log.first_opened_at:
            log.first_opened_at = now
            if not log.expires_at:
                log.expires_at = now + timedelta(hours=URL_EXPIRY_HOURS)
        elif log.expires_at and now > log.expires_at:
            raise HTTPException(status_code=410, detail="This access link has expired")

        log.opened_at = now
        if log.status != EmailStatus.SENT:
            log.status = EmailStatus.SENT

        # Fetch document content
        doc_result = await db.execute(select(Document).where(Document.id == log.document_id))
        doc: Document | None = doc_result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Log OPEN activity
        activity = ActivityLog(
            email_log_id=log.id,
            document_id=log.document_id,
            receiver_email=log.receiver_email,
            action=ActivityAction.OPEN,
        )
        db.add(activity)
        await db.flush()

        from backend.services.fingerprint_service import fingerprint_content
        
        # We must serve the uniquely paraphrased content (or fallback to doc.content)
        base_content = log.paraphrased_content or doc.content or ""
        
        # Inject the invisible zero-width tracing identifiers before sending to frontend
        delivered_content = fingerprint_content(
            content=base_content,
            trace_id=log.trace_id,
            receiver_email=log.receiver_email,
        )

        logger.info("Document %s opened by %s", doc.id, log.receiver_email)
        return {
            "document_name": doc.name,
            "content": delivered_content,
            "font_size": doc.font_size,
            "font_style": doc.font_style,
            "header": doc.header,
            "footer": doc.footer,
            "receiver_email": log.receiver_email,
            "expires_at": log.expires_at.isoformat() if log.expires_at else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Access validation error for token %s: %s", token, exc)
        raise HTTPException(status_code=500, detail="Access validation failed") from exc


async def log_activity(
    db: AsyncSession,
    token: str,
    action: str,
    session_duration: float | None = None,
) -> None:
    """Log a tracking action (copy/download/close)."""
    try:
        result = await db.execute(select(EmailLog).where(EmailLog.token == token))
        log: EmailLog | None = result.scalar_one_or_none()
        if not log:
            return  # ignore unknown tokens gracefully

        try:
            act = ActivityAction(action.upper())
        except ValueError:
            logger.warning("Unknown activity action: %s", action)
            return

        activity = ActivityLog(
            email_log_id=log.id,
            document_id=log.document_id,
            receiver_email=log.receiver_email,
            action=act,
            session_duration=session_duration,
        )
        db.add(activity)
        await db.flush()
        logger.info("Activity %s logged for %s", action, log.receiver_email)
    except Exception as exc:
        logger.error("Activity log error (non-fatal): %s", exc)
        # Non-fatal, do not raise
