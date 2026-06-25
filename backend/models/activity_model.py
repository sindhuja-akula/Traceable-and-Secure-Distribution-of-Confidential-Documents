"""activity_model.py - SQLAlchemy ActivityLog table."""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from backend.database import Base

class ActivityAction(str, enum.Enum):
    OPEN             = "OPEN"
    CLOSE            = "CLOSE"
    COPY_ATTEMPT     = "COPY_ATTEMPT"
    DOWNLOAD_ATTEMPT = "DOWNLOAD_ATTEMPT"

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id               = Column(Integer, primary_key=True, index=True)
    email_log_id     = Column(Integer, ForeignKey("email_logs.id", ondelete="CASCADE"), nullable=False)
    document_id      = Column(Integer, nullable=False)
    receiver_email   = Column(String, nullable=False)
    action           = Column(Enum(ActivityAction), nullable=False)
    timestamp        = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    session_duration = Column(Float, nullable=True)
