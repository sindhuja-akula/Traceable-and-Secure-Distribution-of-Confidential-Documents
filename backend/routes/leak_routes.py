"""leak_routes.py - Leak detection endpoint."""
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.routes.auth_routes import _get_current_user_id
from backend.services.leak_detection_service import identify_leaker, identify_leaker_by_text, analyze_leaked_document_comprehensive, identify_leaker_by_token
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leak", tags=["Leak Detection"])

class UrlLeakRequest(BaseModel):
    url: str

@router.post("/analyze-url")
async def analyze_url_leak(
    request: UrlLeakRequest,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Identify a leaker by pasting their unique viewing URL."""
    try:
        # Extract token from URL (e.g. .../view/abc123token)
        url = request.url.strip().rstrip('/')
        token = url.split('/')[-1]
        
        if not token:
            raise HTTPException(status_code=400, detail="Invalid URL format. Could not find token.")
            
        return await identify_leaker_by_token(db, token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Analyze URL endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="URL analysis failed") from exc


@router.post("/detect")
async def detect_leak(
    file: UploadFile = File(...),
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a suspected leaked PDF and identify the leaker."""
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for leak detection")
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        return await identify_leaker(db, file_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Leak detect endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Leak detection failed") from exc

class TextLeakRequest(BaseModel):
    leaked_text: str

@router.post("/text-scan")
async def detect_leak_text(
    request: TextLeakRequest,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Scan leaked plain-text against the database to identify the leaker semantically."""
    try:
        if not request.leaked_text or len(request.leaked_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Provided text is empty")
        return await identify_leaker_by_text(db, request.leaked_text)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Text leak detect endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Text leak detection failed") from exc

@router.post("/analyze")
async def analyze_document_comprehensive(
    file: UploadFile = File(...),
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a leaked document/screenshot and perform a comprehensive scan on all bases."""
    try:
        # Just check it's a file
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        return await analyze_leaked_document_comprehensive(db, file_bytes, filename=file.filename)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Analyze document endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Document analysis failed") from exc

