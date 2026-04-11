"""document_schema.py - Pydantic schemas for Document endpoints."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class RecipientEntry(BaseModel):
    name: str
    email: EmailStr

class DocumentCreate(BaseModel):
    name: str
    content: Optional[str] = None
    font_size: int = 12
    font_style: str = "Helvetica"
    header: Optional[str] = None
    footer: Optional[str] = None
    recipients: List[RecipientEntry]

class DocumentResponse(BaseModel):
    id: int
    name: str
    content: Optional[str] = None
    font_size: int
    font_style: str
    header: Optional[str] = None
    footer: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
