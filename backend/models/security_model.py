"""security_model.py - SQLAlchemy SecurityLog table."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from backend.database import Base

class SecurityLog(Base):
    __tablename__ = "security_logs"
    id             = Column(Integer, primary_key=True, index=True)
    email_log_id   = Column(Integer, ForeignKey("email_logs.id", ondelete="CASCADE"), nullable=False)
    receiver_email = Column(String, nullable=False)
    warning_count  = Column(Integer, default=0)
    blocked_status = Column(Boolean, default=False)
    blocked_at     = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
