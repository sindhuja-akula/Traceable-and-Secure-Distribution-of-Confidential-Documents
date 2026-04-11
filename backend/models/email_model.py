"""email_model.py - SQLAlchemy EmailLog table."""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from backend.database import Base

class EmailStatus(str, enum.Enum):
    PENDING    = "PENDING"
    SENT       = "SENT"
    FAILED     = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"

class EmailLog(Base):
    __tablename__ = "email_logs"
    id             = Column(Integer, primary_key=True, index=True)
    document_id    = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    receiver_email = Column(String, nullable=False)
    unique_url     = Column(String, unique=True, nullable=False)
    token          = Column(String, unique=True, nullable=False)
    password       = Column(String, nullable=False)
    trace_id       = Column(String, nullable=False)
    status         = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    retry_count    = Column(Integer, default=0)
    paraphrased_content = Column(String, nullable=True)
    processing_step     = Column(String, nullable=True)
    opened_at      = Column(DateTime(timezone=True), nullable=True)
    first_opened_at = Column(DateTime(timezone=True), nullable=True)
    expires_at     = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_blocked     = Column(Boolean, default=False)
