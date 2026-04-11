"""email_schema.py - Pydantic schemas for Email/Progress/Access endpoints."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from backend.models.email_model import EmailStatus
from backend.schemas.document_schema import RecipientEntry

class SendEmailRequest(BaseModel):
    recipients: List[RecipientEntry]
    duration_hrs: int = 24
    duration_mins: int = 0
    duration_secs: int = 0

class EmailLogResponse(BaseModel):
    id: int
    document_id: int
    receiver_email: str
    unique_url: str
    token: str
    status: EmailStatus
    retry_count: int
    opened_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_blocked: bool
    model_config = {"from_attributes": True}

class ProgressStats(BaseModel):
    total: int
    sent: int
    failed: int
    in_progress: int
    pending: int
    current_recipient: Optional[str] = None
    current_action: Optional[str] = None

class AccessRequest(BaseModel):
    token: str
    password: str
