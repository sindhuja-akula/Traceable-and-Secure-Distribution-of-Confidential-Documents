"""progress_routes.py - Real-time progress stats + SSE stream."""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db, AsyncSessionLocal
from backend.routes.auth_routes import _get_current_user_id
from backend.schemas.email_schema import ProgressStats
from backend.services.progress_service import get_progress
from backend.models.document_model import Document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/{doc_id}", response_model=ProgressStats)
async def progress_stats(
    doc_id: int,
    user_id: int = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current email sending progress for a document."""
    try:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Document not found")
        return await get_progress(db, doc_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Progress endpoint error for doc %s: %s", doc_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve progress") from exc


@router.get("/stream/{doc_id}")
async def progress_stream(
    doc_id: int,
    token: str | None = None, # Explicitly for SSE auth via query param
    user_id: int = Depends(_get_current_user_id),
):
    """Server-Sent Events stream for live progress updates."""
    async def event_generator():
        logger.info("SSE stream started for Doc %s", doc_id)
        # Yield an initial connect event
        yield f"data: {json.dumps({'status': 'connected'})}\n\n"
        try:
            while True:
                async with AsyncSessionLocal() as session:
                    try:
                        # Verify ownership
                        result = await session.execute(
                            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
                        )
                        if not result.scalar_one_or_none():
                            logger.warning("SSE: Document %s not found or access denied", doc_id)
                            yield f"data: {json.dumps({'error': 'Document not found'})}\n\n"
                            break

                        stats = await get_progress(session, doc_id)
                        data = stats.model_dump()
                        logger.debug("SSE: Yielding stats for Doc %s: %s", doc_id, data)
                        yield f"data: {json.dumps(data)}\n\n"
                        
                        # Stop streaming once all done
                        if data["total"] > 0 and data["pending"] == 0 and data["in_progress"] == 0:
                            logger.info("SSE: Stream finished normally for Doc %s", doc_id)
                            break
                        
                        await asyncio.sleep(1.5)
                    except Exception as exc:
                        logger.error("SSE: Loop exception for Doc %s: %s", doc_id, exc)
                        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
                        break
                    finally:
                        await session.close()
        except asyncio.CancelledError:
            logger.info("SSE: Client disconnected for Doc %s", doc_id)
        except Exception as exc:
            logger.error("SSE: Top-level exception for Doc %s: %s", doc_id, exc)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

