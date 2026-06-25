"""document_routes.py - Document CRUD and file upload endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.routes.auth_routes import _get_current_user_id
from backend.schemas.document_schema import DocumentCreate, DocumentResponse
from backend.services.document_service import (
    create_document, create_document_from_file,
    get_user_documents, get_document, delete_document, bulk_delete_documents
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

class BulkDeleteRequest(BaseModel):
    doc_ids: List[int]

@router.post("/bulk-delete", status_code=204)
async def bulk_delete_docs(
    request: BulkDeleteRequest,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Efficiently delete a set of documents."""
    try:
        await bulk_delete_documents(db, request.doc_ids, user_id)
        return
    except Exception as exc:
        logger.error("Bulk delete endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Bulk deletion failed") from exc


@router.delete("/{doc_id}", status_code=204)
async def delete_doc(
    doc_id: int,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a specific document and its logs."""
    try:
        await delete_document(db, doc_id, user_id)
        return
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Delete document %s error: %s", doc_id, exc)
        raise HTTPException(status_code=500, detail="Could not delete document") from exc


@router.post("/create", response_model=DocumentResponse, status_code=201)
async def create_doc(
    data: DocumentCreate,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a document from typed content + recipient list."""
    try:
        doc = await create_document(db, user_id, data)
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Create document endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Document creation failed") from exc


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_doc(
    name: str = Form(...),
    font_size: int = Form(12),
    font_style: str = Form("Helvetica"),
    header: str = Form(None),
    footer: str = Form(None),
    file: UploadFile = File(...),
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF/DOCX/TXT file and create a document from it."""
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        doc = await create_document_from_file(
            db, user_id, name, file_bytes, file.filename,
            font_size, font_style, header, footer,
        )
        return doc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload document endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Document upload failed") from exc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the authenticated user."""
    try:
        return await get_user_documents(db, user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("List documents error: %s", exc)
        raise HTTPException(status_code=500, detail="Could not list documents") from exc


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_doc(
    doc_id: int,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document by ID."""
    try:
        return await get_document(db, doc_id, user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Get document %s error: %s", doc_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve document") from exc
