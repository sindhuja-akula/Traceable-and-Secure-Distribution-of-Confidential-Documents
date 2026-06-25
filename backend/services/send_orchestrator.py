"""
send_orchestrator.py - Orchestrates fingerprinting + email sending for all recipients.
Creates EmailLog records, generates PDFs, sends emails, updates statuses.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import AsyncSessionLocal
from sqlalchemy import select

from backend.models.email_model import EmailLog, EmailStatus
from backend.models.document_model import Document
from backend.services.ai_paraphrase_service import paraphrase_text_async
from backend.services.fingerprint_service import fingerprint_content, build_watermark_text
from backend.services.email_service import send_document_email
from backend.utils.token_utils import generate_token, generate_trace_id, generate_doc_password
from backend.utils.pdf_generator import generate_pdf
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_email_logs(
    db: AsyncSession,
    document: Document,
    recipients: List[Dict[str, str]],
    duration_hrs: int = 24,
    duration_mins: int = 0,
    duration_secs: int = 0,
) -> List[EmailLog]:
    """Pre-create EmailLog records for all recipients (PENDING state)."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=duration_hrs, minutes=duration_mins, seconds=duration_secs)
    
    logs = []
    for recipient in recipients:
        token = generate_token()
        trace_id = generate_trace_id()
        password = generate_doc_password()
        unique_url = f"{settings.FRONTEND_ORIGIN}/view/{token}"

        log = EmailLog(
            document_id=document.id,
            receiver_email=recipient["email"],
            unique_url=unique_url,
            token=token,
            password=password,
            trace_id=trace_id,
            status=EmailStatus.PENDING,
            expires_at=expires_at,
        )
        db.add(log)
        logs.append((log, recipient))

    await db.flush()
    logger.info("Created %d email log records for document %s", len(logs), document.id)
    return logs


def _calculate_duration_text(expires_at: datetime, created_at: datetime) -> str:
    """Helper to format duration into human readable text."""
    diff = expires_at - created_at
    total_seconds = int(diff.total_seconds())
    if total_seconds <= 0:
        return "immediately"
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and hours == 0: # Only show seconds if less than an hour
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
    if not parts:
        return "24 hours" # Fallback
    
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


async def _process_single_recipient(
    db: AsyncSession,
    log: EmailLog,
    recipient: Dict[str, str],
    document: Document,
    recipient_index: int,
    sender_email: str = None,
) -> None:
    """Fingerprint, generate PDF, send email for one recipient."""
    try:
        log.status = EmailStatus.IN_PROGRESS
        await db.commit() # Commit status immediately so SSE can pick it up
        await db.refresh(log)

        # First dynamically paraphrase the text using Gemini API
        log.processing_step = f"Paraphrasing document for {log.receiver_email}..."
        await db.commit()
        await db.refresh(log)

        unique_content = await paraphrase_text_async(
            content=document.content or "", 
            recipient_index=recipient_index, 
            receiver_email=log.receiver_email
        )

        # Store the exact generated phrases into the DB for future semantic leak detection
        log.paraphrased_content = unique_content

        # Fingerprint the uniquely generated text with zero-width invisible trace
        log.processing_step = "Applying unique fingerprint..."
        await db.commit()
        await db.refresh(log)

        fp_content = fingerprint_content(
            content=unique_content,
            trace_id=log.trace_id,
            receiver_email=log.receiver_email,
            recipient_index=recipient_index,
        )
        watermark = build_watermark_text(log.receiver_email, log.trace_id)

        # Generate a PDF (not required to send but available for future attachment)
        # pdf_bytes = generate_pdf(fp_content, document.font_size, document.font_style,
        #                          document.header, document.footer, watermark)

        # Calculate human-friendly duration text
        expiry_text = _calculate_duration_text(log.expires_at, log.created_at)

        # Send email
        log.processing_step = f"Sending secure email to {log.receiver_email}..."
        await db.commit()
        await db.refresh(log)

        success = await send_document_email(
            to_email=log.receiver_email,
            recipient_name=recipient.get("name", log.receiver_email),
            unique_url=log.unique_url,
            password=log.password,
            document_name=document.name,
            sender_email=sender_email,
            expiry_text=expiry_text,
        )

        if success:
            log.status = EmailStatus.SENT
            log.processing_step = "Completed."
        else:
            log.status = EmailStatus.FAILED
            log.processing_step = "Final send attempt failed."
            log.retry_count = 3  # max retries exhausted

        await db.commit()

    except Exception as exc:
        logger.error("Failed processing recipient %s: %s", log.receiver_email, exc)
        log.status = EmailStatus.FAILED
        try:
            await db.flush()
        except Exception:
            pass


async def send_to_all_recipients(
    document_id: int,
    email_log_ids: List[int],
    recipients: List[Dict[str, str]],
    sender_email: str = None,
) -> None:
    """
    Background task: processes existing EmailLog records.
    recipients list is passed separately for name/email convenience.
    """
    logger.info("Background sender started for Doc %s with %d log IDs", document_id, len(email_log_ids))
    try:
        # 1. Process each recipient by ID
        # We pair them by index assuming order is preserved during log creation
        for idx, (log_id, recipient_data) in enumerate(zip(email_log_ids, recipients)):
            logger.debug("Processing recipient %d/%d (LogID: %s)", idx + 1, len(email_log_ids), log_id)
            async with AsyncSessionLocal() as session:
                try:
                    # Fetch log and doc again to avoid detached object errors
                    log_res = await session.execute(select(EmailLog).where(EmailLog.id == log_id))
                    log = log_res.scalar_one_or_none()
                    doc_res = await session.execute(select(Document).where(Document.id == document_id))
                    doc = doc_res.scalar_one_or_none()
                    
                    if log and doc:
                        await _process_single_recipient(session, log, recipient_data, doc, idx, sender_email)
                        await session.commit()
                        logger.info("Successfully processed recipient %s (LogID: %s)", recipient_data['email'], log_id)
                    else:
                        logger.error("Missing log %s or doc %s during processing", log_id, document_id)
                except Exception as exc:
                    await session.rollback()
                    logger.error("Error processing log %s: %s", log_id, exc)
                finally:
                    await session.close()

        logger.info("Completed background sending for document %s", document_id)
    except Exception as exc:
        logger.error("Orchestration top-level error for document %s: %s", document_id, exc)
