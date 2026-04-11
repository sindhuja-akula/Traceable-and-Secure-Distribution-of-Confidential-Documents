"""user_model.py - SQLAlchemy User table."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login    = Column(DateTime(timezone=True), nullable=True)
    last_logout   = Column(DateTime(timezone=True), nullable=True)
