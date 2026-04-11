import logging
import asyncio
from typing import Optional, List
from google import genai
from google.genai import types
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_clients = []

def get_genai_clients() -> List[genai.Client]:
    """Initialize and retrieve all available Gemini clients."""
    global _clients
    if _clients:
        return _clients
        
    keys = [settings.GEMINI_API_KEY, settings.GEMINI_API_KEY2]
    unique_keys = [k for k in keys if k and k.strip()]
    
    if not unique_keys:
        logger.warning("No Gemini API keys found.")
        return []
        
    for key in unique_keys:
        try:
            client = genai.Client(api_key=key)
            _clients.append(client)
        except Exception:
            pass
            
    return _clients

async def paraphrase_text_async(content: str, recipient_index: int, receiver_email: str) -> str:
    """
    Paraphrase using Gemini 2.5 Flash (Current Stable).
    """
    clients = get_genai_clients()
    if not clients or not content:
        return content

    prompt = (
        f"Paraphrase this text for recipient '{receiver_email}'. "
        "Keep the meaning/tone unchanged. Output ONLY the rewritten text.\n\n"
        f"TEXT:\n{content}"
    )

    # Preferred Models: Gemini 2.5 Flash, Gemini 2.5 Flash-Lite
    # Note: Using shorthand names as required by v0.3.0 SDK (v1beta API)
    models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite']

    for client in clients:
        for model in models:
            try:
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue
                
    return content

async def extract_text_from_image_async(image_bytes: bytes, mime_type: str = 'image/png') -> str:
    """
    Extract text using Gemini 2.5 Stable Vision (returns raw error on failure).
    """
    clients = get_genai_clients()
    if not clients:
        return "ERROR: No Gemini API Key configured."

    contents = [
        "You are an expert security OCR engine. Extract every single word verbatim from this document screenshot. "
        "CRITICAL: Look specifically for diagonal, faint, or greyed-out watermarks (usually an email address) stretching across the background. "
        "If you see any text that looks like an email address, extract it prominently. Output ONLY the extracted text verbatim.",
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    ]

    # Models: 2.5 Flash then 2.5 Flash-Lite Fallback
    models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite']

    last_error = "Could not extract any text from this file."

    for i, client in enumerate(clients):
        for model in models:
            try:
                logger.debug("OCR Try: Key=%d, Model=%s", i+1, model)
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                last_error = str(exc)
                logger.warning("OCR Failed for %s: %s", model, last_error)
                continue
                
    # If all fail, return the LAST EXACT ERROR from Google for diagnosis
    return f"GOOGLE API ERROR: {last_error}"
