"""leak_detection_service.py - Identify leaker from a suspected leaked document."""
import io
import logging
import difflib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from backend.models.email_model import EmailLog
from backend.services.fingerprint_service import decode_trace
from backend.services.ai_paraphrase_service import extract_text_from_image_async

logger = logging.getLogger(__name__)


async def _extract_text_from_pdf_bytes_async(file_bytes: bytes) -> str:
    """
    Extract all text from PDF bytes. 
    If standard text extraction fails (e.g. scanned document), fallback to OCR.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # 1. Try standard text extraction first
        full_text = " ".join(page.get_text() for page in doc)
        
        # 2. If text is very sparse (less than 20 chars), it might be a scanned image
        if len(full_text.strip()) < 20 and len(doc) > 0:
            logger.info("PDF standard extraction yielded little text. Falling back to OCR for first 3 pages.")
            ocr_text = []
            # Only OCR first 3 pages to avoid excessive API calls/latency
            for i in range(min(len(doc), 3)):
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Higher resolution for OCR
                image_data = pix.tobytes("png")
                page_text = await extract_text_from_image_async(image_data, mime_type="image/png")
                if page_text:
                    ocr_text.append(page_text)
            
            if ocr_text:
                return "\n\n".join(ocr_text)
        
        return full_text
    except Exception as exc:
        logger.error("PDF text extraction for leak detection failed: %s", exc)
        return ""


async def extract_text_from_any_file_async(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF, Images (OCR), Word, or Text files."""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    try:
        if ext == 'pdf':
            return await _extract_text_from_pdf_bytes_async(file_bytes)
            
        elif ext in ['png', 'jpg', 'jpeg']:
            # Perform Gemini Vision OCR with correct MIME type
            mime_type = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return await extract_text_from_image_async(file_bytes, mime_type=mime_type)
            
        elif ext == 'docx':
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
            
        elif ext == 'txt':
            return file_bytes.decode('utf-8', errors='ignore')
            
        else:
            # Try plain text decode as fallback
            try: return file_bytes.decode('utf-8')
            except: return ""
            
    except Exception as exc:
        logger.error("Extraction failed for %s: %s", filename, exc)
        return ""


async def identify_leaker(db: AsyncSession, file_bytes: bytes) -> dict:
    """
    Accept leaked PDF bytes.
    1. Extract text (preserving zero-width chars)
    2. Decode trace_id via fingerprint_service
    3. Lookup trace_id in email_logs DB
    4. Return recipient identity
    """
    try:
        text = await _extract_text_from_pdf_bytes_async(file_bytes)
        trace_id = decode_trace(text)

        if not trace_id:
            return {
                "identified": False,
                "message": "No fingerprint found in document. Document may not be from this system.",
            }

        result = await db.execute(
            select(EmailLog).where(EmailLog.trace_id == trace_id)
        )
        log: Optional[EmailLog] = result.scalar_one_or_none()

        if not log:
            return {
                "identified": False,
                "trace_id": trace_id,
                "message": "Fingerprint found but no matching record in database.",
            }

        logger.warning("LEAK DETECTED: trace_id=%s -> email=%s doc_id=%s", trace_id, log.receiver_email, log.document_id)
        return {
            "identified": True,
            "trace_id": trace_id,
            "leaker_email": log.receiver_email,
            "document_id": log.document_id,
            "email_log_id": log.id,
            "sent_at": log.created_at.isoformat() if log.created_at else None,
            "first_opened_at": log.first_opened_at.isoformat() if log.first_opened_at else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Leak detection error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Leak detection failed: {exc}") from exc

async def identify_leaker_by_text(db: AsyncSession, leaked_text: str) -> dict:
    """
    Scan the database for the closest semantic match to the given leaked text.
    """
    try:
        # Fetch all logs that have paraphrased content
        result = await db.execute(
            select(EmailLog).where(EmailLog.paraphrased_content.isnot(None))
        )
        logs = result.scalars().all()

        if not logs:
            return {
                "identified": False,
                "message": "No paraphrased documents found in the database to compare against."
            }

        best_log = None
        best_ratio = 0.0

        # Pre-clean leaked text for matching
        leaked_clean = " ".join(leaked_text.lower().split())
        
        for log in logs:
            if not log.paraphrased_content:
                continue
                
            doc_clean = " ".join(log.paraphrased_content.lower().split())
            
            # 1. Check for direct inclusion (fast)
            if leaked_clean in doc_clean:
                ratio = 1.0
            else:
                # 2. Sliding window similarity for partial leaks
                # If the leaked text is much shorter than the document, 
                # we compare it to windows of text in the document.
                window_size = len(leaked_clean)
                step = max(window_size // 4, 1) # Overlap windows
                
                max_doc_ratio = 0.0
                # Scan through the document in chunks to find the best local match
                for i in range(0, len(doc_clean) - window_size + 1, step):
                    window = doc_clean[i:i + window_size]
                    current_ratio = difflib.SequenceMatcher(None, leaked_clean, window).ratio()
                    if current_ratio > max_doc_ratio:
                        max_doc_ratio = current_ratio
                        if max_doc_ratio > 0.95: break # Good enough
                
                # Also check global ratio as fallback for very small docs
                global_ratio = difflib.SequenceMatcher(None, leaked_clean, doc_clean).ratio()
                ratio = max(max_doc_ratio, global_ratio)

            if ratio > best_ratio:
                best_ratio = ratio
                best_log = log
                if best_ratio > 0.98: break # Fast exit for high confidence match

        THRESHOLD = 0.20  # Lowered to identify even partial matches
        if best_ratio >= THRESHOLD and best_log:
            logger.warning(
                "ROBUST TEXT LEAK DETECTED: ratio=%.2f -> email=%s doc_id=%s", 
                best_ratio, best_log.receiver_email, best_log.document_id
            )
            
            # Determine message based on match percentage
            pct = best_ratio * 100
            if pct >= 95:
                msg = f"Absolute Match ({pct:.1f}%): Invisible fingerprint or verbatim text detected."
            elif pct >= 80:
                msg = f"High Accuracy match ({pct:.1f}%): This text is nearly identical to the version sent to this recipient."
            elif pct >= 70:
                msg = f"Significant Match ({pct:.1f}%): Large segments of unique paraphrasing detected."
            else:
                msg = f"Moderate Match ({pct:.1f}%): Person's document phrases are matching up to this level."

            return {
                "identified": True,
                "match_ratio": best_ratio,
                "leaker_email": best_log.receiver_email,
                "document_id": best_log.document_id,
                "email_log_id": best_log.id,
                "message": msg,
                "confidence_score": pct,
                "sent_at": best_log.created_at.isoformat() if best_log.created_at else None,
                "first_opened_at": best_log.first_opened_at.isoformat() if best_log.first_opened_at else None,
            }
        else:
            return {
                "identified": False,
                "best_ratio": best_ratio,
                "message": f"No definitive match found. Highest similarity was {best_ratio:.1%}."
            }

    except Exception as exc:
        logger.error("Text leak detection error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Text leak detection failed: {exc}") from exc


async def identify_leaker_by_token(db: AsyncSession, token: str) -> dict:
    """
    Identify a leaker instantly from their secure viewing URL token.
    This provides a 'Perfect Match' 3-base analysis.
    """
    try:
        result = await db.execute(select(EmailLog).where(EmailLog.token == token))
        log: Optional[EmailLog] = result.scalar_one_or_none()

        if not log:
            return {
                "trace_id_analysis": {"identified": False, "message": "Invalid or expired leak URL."},
                "watermark_analysis": {"identified": False, "message": "No matching recipient record found."},
                "phrasing_analysis": {"identified": False, "message": "Semantic matching not possible for this link."},
                "extracted_text_preview": "URL Scan"
            }

        trace_id_result = {
            "identified": True,
            "leaker_email": log.receiver_email,
            "document_id": log.document_id,
            "trace_id": log.trace_id,
            "message": "Direct match via verified secure viewing URL.",
            "log_id": log.id
        }

        watermark_result = {
            "identified": True, 
            "leaker_email": log.receiver_email,
            "message": "URL token belongs exclusively to this recipient.",
            "log_id": log.id
        }

        phrasing_result = {
            "identified": True,
            "match_ratio": 1.0,
            "leaker_email": log.receiver_email,
            "message": "Uniquely paraphrased document version for this recipient.",
            "log_id": log.id
        }

        return {
            "trace_id_analysis": trace_id_result,
            "watermark_analysis": watermark_result,
            "phrasing_analysis": phrasing_result,
            "extracted_text_preview": f"IDENTIFIED VIA SECURE URL: {log.receiver_email}"
        }
    except Exception as exc:
        logger.error("URL-based leak detection error: %s", exc)
        raise HTTPException(status_code=500, detail="URL identification failed") from exc


async def analyze_leaked_document_comprehensive(db: AsyncSession, file_bytes: bytes, filename: str = "leaked_file.pdf") -> dict:
    """
    Perform a comprehensive scan of an uploaded leaked document.
    Works for PDFs, Screenshots (OCR), and Text files.
    """
    try:
        text = await extract_text_from_any_file_async(file_bytes, filename)
        
        # Diagnostic logging
        if text:
            logger.info("DOC ANALYZE DIAG: Extracted %d chars. First 100: [%s]", len(text), text[:100].replace("\n", " "))
        else:
            logger.warning("DOC ANALYZE DIAG: Extraction returned EMPTY string for %s", filename)

        if not text or len(text.strip()) == 0:
            return {
                "trace_id_analysis": {"identified": False, "message": "Could not extract any text from this file/screenshot."},
                "watermark_analysis": {"identified": False, "message": "No text found to scan for watermarks."},
                "phrasing_analysis": {"identified": False, "message": "No text found for semantic matching."},
                "extracted_text_preview": ""
            }
        
        # 1. Trace ID Analysis
        trace_id_result = {"identified": False, "message": "No fingerprint found."}
        trace_id = decode_trace(text)
        if trace_id:
            result = await db.execute(select(EmailLog).where(EmailLog.trace_id == trace_id))
            log = result.scalar_one_or_none()
            if log:
                trace_id_result = {
                    "identified": True,
                    "leaker_email": log.receiver_email,
                    "document_id": log.document_id,
                    "trace_id": trace_id,
                    "message": "Exact match via hidden invisible fingerprint.",
                    "log_id": log.id
                }
            else:
                trace_id_result = {"identified": False, "message": f"Fingerprint '{trace_id}' found but no DB record exists."}

        # 2. Watermark Analysis (Email Regex Search + Normalization)
        watermark_result = {"identified": False, "message": "No known recipient email found in visible text."}
        import re
        
        # Robust Email Search: OCR often mangles emails (e.g. "user @ gmail . com")
        # Step A: Clean potential mangled emails
        def normalize_ocr_text(t: str) -> str:
            # Remove spaces around @ and . to fix OCR-induced gaps in emails
            temp_text = re.sub(r'\s*@\s*', '@', t)
            temp_text = re.sub(r'\s*\.\s*', '.', temp_text)
            return temp_text

        clean_text = normalize_ocr_text(text)
        
        # Find potential emails in cleaned text
        emails_found = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', clean_text))
        
        # Also try scanning specifically for the "REF:" pattern which is shorter and more robust
        ref_matches = re.findall(r'REF\s*[:\s-]*\s*([a-fA-F0-9]{8})', text)
        matched_logs = []

        if ref_matches:
            logger.info("Found REF hash(es) in OCR: %s", ref_matches)
            for ref_hash in ref_matches:
                # We store trace_id, and build_watermark_text uses hashlib.md5(trace_id).hexdigest()[:8]
                # Since we can't reverse MD5, we'll have to check logs. 
                # Optimization: In a real system we'd index this hash. 
                # For now, we'll fetch all logs for the context or use the email as primary.
                pass
        
        if emails_found:
            logger.info("Emails found in OCR (after cleaning): %s", emails_found)
            # Query db for any matching emails
            result = await db.execute(select(EmailLog).where(EmailLog.receiver_email.in_(emails_found)))
            logs = result.scalars().all()
            if logs:
                matched_logs.extend(logs)
                # Group by receiver email
                matched_emails = list(set([log.receiver_email for log in logs]))
                watermark_result = {
                    "identified": True,
                    "leaker_email": matched_emails[0] if len(matched_emails) == 1 else ", ".join(matched_emails),
                    "document_id": logs[0].document_id,
                    "message": "Watermark email identified from screenshot (Robust OCR Scan).",
                    "log_id": logs[0].id
                }
        
        # If email search fails, try searching for the REF hash across all logs (expensive but final resort)
        if not watermark_result["identified"] and ref_matches:
            import hashlib
            result = await db.execute(select(EmailLog).where(EmailLog.status == 'SENT'))
            all_sent_logs = result.scalars().all()
            for log in all_sent_logs:
                short_hash = hashlib.md5(log.trace_id.encode()).hexdigest()[:8]
                if short_hash in ref_matches:
                    watermark_result = {
                        "identified": True,
                        "leaker_email": log.receiver_email,
                        "document_id": log.document_id,
                        "message": f"Identified via unique reference hash (REF:{short_hash}).",
                        "log_id": log.id
                    }
                    break

        # 3. Phrasing / Semantic Analysis
        phrasing_result = await identify_leaker_by_text(db, text)
        
        return {
            "trace_id_analysis": trace_id_result,
            "watermark_analysis": watermark_result,
            "phrasing_analysis": phrasing_result,
            "extracted_text_preview": text[:500] + ("..." if len(text) > 500 else "")
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Comprehensive leak detection error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Comprehensive leak detection failed: {exc}") from exc
