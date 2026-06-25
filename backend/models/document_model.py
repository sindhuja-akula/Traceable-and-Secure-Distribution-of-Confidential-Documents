"""document_model.py - SQLAlchemy Document table."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base

class Document(Base):
    __tablename__ = "documents"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(255), nullable=False)
    content    = Column(Text, nullable=True)
    font_size  = Column(Integer, default=12)
    font_style = Column(String(50), default="Helvetica")
    header     = Column(String(500), nullable=True)
    footer     = Column(String(500), nullable=True)
    file_path  = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
