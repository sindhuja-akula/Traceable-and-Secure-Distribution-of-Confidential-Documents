"""email_service.py - Async SMTP email sender with retry logic."""
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from fastapi import HTTPException

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubled each retry


async def _send_single_email(to_email: str, subject: str, html_body: str, sender_email: str = None) -> None:
    """Low-level single SMTP send attempt."""
    # Brevo requires the 'From' address to be a verified sender.
    # We MUST use settings.SMTP_FROM as the From header to avoid DMARC/SPF drops by Brevo.
    # The actual user's email can be used as the Reply-To so that replies go to them.
    from_header = settings.SMTP_FROM.strip()
    reply_to = (sender_email or settings.SMTP_FROM).strip()
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_header
    msg["To"]      = to_email
    msg["Reply-To"] = reply_to
    msg["Sender"]   = settings.SMTP_USER
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.debug("Successfully executed aiosmtplib.send to %s", to_email)
    except Exception as exc:
        logger.error("aiosmtplib.send high-level error for %s: %s", to_email, exc)
        raise


async def send_document_email(
    to_email: str,
    recipient_name: str,
    unique_url: str,
    password: str,
    document_name: str,
    sender_email: str = None,
    expiry_text: str = "24 hours",
) -> bool:
    """
    Send a secure document access email with retry logic.
    Returns True on success, False after exhausting retries.
    """
    subject = f"Secure Document: {document_name}"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Inter,Helvetica,sans-serif;background:#0f1117;color:#e2e8f0;padding:40px;">
      <div style="max-width:560px;margin:0 auto;background:#1a1d2e;border-radius:12px;padding:36px;border:1px solid #2d3748;">
        <h2 style="color:#6366f1;margin-bottom:8px;">Confidential Document</h2>
        <p style="color:#94a3b8;margin-bottom:24px;">You have received a secure document.</p>
        <p>Hello <strong style="color:#f8fafc;">{recipient_name}</strong>,</p>
        <p>You have been granted access to the confidential document: <strong style="color:#f8fafc;">{document_name}</strong>.</p>
        <div style="background:#0f1117;border-radius:8px;padding:20px;margin:24px 0;border:1px solid #374151;">
          <p style="margin:0 0 12px 0;font-size:13px;color:#9ca3af;">ACCESS DETAILS</p>
          <p style="margin:0 0 8px 0;"><span style="color:#9ca3af;">Password:</span> <strong style="color:#6366f1;font-size:18px;letter-spacing:2px;">{password}</strong></p>
        </div>
        <a href="{unique_url}" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px;">Open Secure Document</a>
        <p style="margin-top:24px;font-size:12px;color:#6b7280;">This link will expire {expiry_text} after your first access. Do not share this email.</p>
      </div>
    </body>
    </html>
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await _send_single_email(to_email, subject, html_body, sender_email)
            logger.info("Email sent to %s on attempt %d", to_email, attempt)
            return True
        except aiosmtplib.SMTPException as exc:
            logger.warning("SMTP error sending to %s (attempt %d/%d): %s", to_email, attempt, MAX_RETRIES, exc)
        except Exception as exc:
            logger.warning("Email send error to %s (attempt %d/%d): %s", to_email, attempt, MAX_RETRIES, exc)

        if attempt < MAX_RETRIES:
            backoff = RETRY_BACKOFF ** attempt
            logger.info("Retrying email to %s in %ds...", to_email, backoff)
            await asyncio.sleep(backoff)

    logger.error("Failed to send email to %s after %d attempts", to_email, MAX_RETRIES)
    return False

async def send_otp_email(to_email: str, otp_code: str) -> None:
    """Send a 6-digit OTP for password reset with clean branding."""
    subject = "Password Reset - Security Code"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Inter,Helvetica,sans-serif;background:#0f1117;color:#e2e8f0;padding:40px;">
      <div style="max-width:480px;margin:0 auto;background:#1a1d2e;border-radius:12px;padding:36px;border:1px solid #2d3748;text-align:center;">
        <h2 style="color:#6366f1;margin-bottom:8px;">Security Verification</h2>
        <p style="color:#94a3b8;margin-bottom:24px;">Use the code below to reset your password.</p>
        <div style="background:#0f1117;border-radius:8px;padding:24px;margin:24px 0;border:1px solid #374151;">
          <span style="color:#6366f1;font-size:32px;font-weight:700;letter-spacing:8px;">{otp_code}</span>
        </div>
        <p style="font-size:13px;color:#6b7280;margin-top:24px;">This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
      </div>
    </body>
    </html>
    """
    await _send_single_email(to_email, subject, html_body)


async def send_block_notification(owner_email: str, receiver_email: str, document_name: str) -> None:
    """Notify document owner that a recipient has been blocked."""
    try:
        subject = f"[Security Alert] URL Blocked - {document_name}"
        html_body = f"""
        <html><body style="font-family:Inter,sans-serif;padding:30px;">
          <h3 style="color:#ef4444;">Security Alert: URL Blocked</h3>
          <p>The secure document URL for <strong>{receiver_email}</strong> accessing
          <strong>{document_name}</strong> has been automatically blocked after 5 security violations.</p>
          <p>Please review the activity logs in your dashboard.</p>
        </body></html>
        """
        await _send_single_email(owner_email, subject, html_body)
        logger.info("Block notification sent to %s", owner_email)
    except Exception as exc:
        logger.error("Could not send block notification to %s: %s", owner_email, exc)
        # Non-fatal: we do not re-raise


async def send_copy_attempt_notification(owner_email: str, receiver_email: str, document_name: str) -> None:
    """Notify document owner that a recipient tried to copy content."""
    try:
        subject = f"[Security Notice] Copy Attempt - {document_name}"
        html_body = f"""
        <html><body style="font-family:Inter,sans-serif;padding:30px;">
          <h3 style="color:#f59e0b;">Security Notice: Copy Attempted</h3>
          <p>Recipient <strong>{receiver_email}</strong> tried to copy/cut text from the secure document: 
          <strong>{document_name}</strong>.</p>
          <p>Access was prevented, and the violation has been logged in your dashboard.</p>
        </body></html>
        """
        await _send_single_email(owner_email, subject, html_body)
        logger.info("Copy attempt notification sent to %s", owner_email)
    except Exception as exc:
        logger.error("Could not send copy attempt notification to %s: %s", owner_email, exc)
