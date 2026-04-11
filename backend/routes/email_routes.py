"""email_routes.py - Email sending and recipient upload endpoints."""
import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.routes.auth_routes import _get_current_user_id
from backend.schemas.document_schema import RecipientEntry
from backend.schemas.email_schema import EmailLogResponse, SendEmailRequest
from backend.models.document_model import Document
from backend.services.send_orchestrator import send_to_all_recipients, create_email_logs
from backend.services.progress_service import get_email_logs
from backend.utils.email_parser import parse_recipients
from backend.models.user_model import User
from backend.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emails", tags=["Emails"])


@router.post("/send/{doc_id}", status_code=202)
async def send_emails(
    doc_id: int,
    request_data: SendEmailRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger fingerprinting + email sending to all recipients in background."""
    try:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if not doc.content:
            raise HTTPException(status_code=422, detail="Document has no content to send")
        
        recipients = request_data.recipients
        if not recipients:
            raise HTTPException(status_code=422, detail="No recipients provided")

        recipient_dicts = [{"name": r.name, "email": r.email} for r in recipients]
        logger.info("Starting email send for Doc %s by User %s (%d recipients, expiry: %dh:%dm:%ds)", 
                    doc_id, user_id, len(recipients), 
                    request_data.duration_hrs, request_data.duration_mins, request_data.duration_secs)
        
        # Fetch current user email for the 'From' header
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        sender_email = user.email if user else settings.SMTP_FROM
        
        # Create records synchronously
        logs = await create_email_logs(
            db, 
            doc, 
            recipient_dicts, 
            request_data.duration_hrs, 
            request_data.duration_mins, 
            request_data.duration_secs
        )
        await db.commit()
        
        log_ids = [log[0].id for log in logs]
        logger.info("Created %d log records. Triggering background task...", len(log_ids))
        
        background_tasks.add_task(send_to_all_recipients, doc_id, log_ids, recipient_dicts, sender_email)
        return {"message": f"Sending started for {len(recipients)} recipients", "document_id": doc_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Send emails endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to start email sending") from exc


@router.post("/upload-recipients", response_model=List[RecipientEntry])
async def upload_recipients(
    file: UploadFile = File(...),
    user_id: int = Depends(_get_current_user_id),
):
    """Parse a CSV/Excel file and return extracted recipient list."""
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        recipients = parse_recipients(file_bytes, file.filename)
        return recipients
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload recipients error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to parse recipients file") from exc


@router.get("/logs/{doc_id}", response_model=List[EmailLogResponse])
async def email_logs(
    doc_id: int,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all email logs for a document."""
    try:
        # Verify ownership
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Document not found")
        return await get_email_logs(db, doc_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Email logs endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not retrieve logs") from exc
