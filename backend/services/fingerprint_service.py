"""
fingerprint_service.py - Core fingerprinting engine.
Each recipient gets a uniquely fingerprinted document variant using:
  1. Zero-width Unicode characters encoding the trace_id (binary steganography)
  2. Subtle text variations (punctuation, spacing) per recipient index
  3. Email watermark in the PDF watermark_text field
"""
import logging
import hashlib
from typing import Optional

logger = logging.getLogger(__name__)

# Zero-width characters used as binary encoding
ZWC_ZERO = "\u200B"   # zero-width space  -> bit 0
ZWC_ONE  = "\u200C"   # zero-width non-joiner -> bit 1
ZWC_SEP  = "\u200D"   # zero-width joiner -> separator


def _encode_trace(trace_id: str) -> str:
    """Encode trace_id as invisible zero-width Unicode string."""
    try:
        binary = "".join(format(ord(c), "08b") for c in trace_id[:16])
        encoded = ZWC_SEP
        for bit in binary:
            encoded += ZWC_ONE if bit == "1" else ZWC_ZERO
        encoded += ZWC_SEP
        return encoded
    except Exception as exc:
        logger.error("Trace encoding error: %s", exc)
        return ZWC_SEP


def decode_trace(text: str) -> Optional[str]:
    """
    Extract and decode trace_id from text containing zero-width characters.
    Returns trace_id string or None if not found.
    """
    try:
        if ZWC_SEP not in text:
            return None
        parts = text.split(ZWC_SEP)
        if len(parts) < 3:
            return None
        zwc_payload = parts[1]
        bits = ""
        for ch in zwc_payload:
            if ch == ZWC_ONE:
                bits += "1"
            elif ch == ZWC_ZERO:
                bits += "0"
        if len(bits) < 8:
            return None
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        return "".join(chars)
    except Exception as exc:
        logger.error("Trace decode error: %s", exc)
        return None


# Text variation patterns per recipient index (mod len)
_TEXT_VARIATIONS = [
    {"hi": "Hi!", "i am": "I am", "comma": ","},
    {"hi": "Hi,", "i am": "I am", "comma": ";"},
    {"hi": "Hey!", "i am": "I am", "comma": ","},
    {"hi": "Hello,", "i am": "I am", "comma": ","},
    {"hi": "Hi", "i am": "Iam", "comma": ","},
]


def _apply_text_variations(content: str, recipient_index: int) -> str:
    """Apply subtle text variations based on recipient index."""
    try:
        variation = _TEXT_VARIATIONS[recipient_index % len(_TEXT_VARIATIONS)]
        result = content
        # Minor spacing variations
        if recipient_index % 2 == 0:
            result = result.replace("  ", " ")          # normalize double spaces
        else:
            result = result.replace(". ", ".  ")        # add extra space after period
        return result
    except Exception as exc:
        logger.warning("Text variation error (non-fatal): %s", exc)
        return content


def fingerprint_content(
    content: str,
    trace_id: str,
    receiver_email: str,
    recipient_index: int = 0,
) -> str:
    """
    Return fingerprinted content string.
    Embeds invisible trace_id and applies text variations.
    """
    try:
        # Inject invisible watermark after the first word/sentence
        encoded_trace = _encode_trace(trace_id)
        parts = content.split(" ", 1)
        if len(parts) == 2:
            fingerprinted = parts[0] + encoded_trace + " " + parts[1]
        else:
            fingerprinted = content + encoded_trace

        # Apply text variation
        fingerprinted = _apply_text_variations(fingerprinted, recipient_index)
        return fingerprinted
    except Exception as exc:
        logger.error("Fingerprinting failed for %s: %s", receiver_email, exc)
        return content  # fallback to original if fingerprinting fails


def build_watermark_text(receiver_email: str, trace_id: str) -> str:
    """Build a visible-but-styled watermark string for PDF embedding."""
    short_hash = hashlib.md5(trace_id.encode()).hexdigest()[:8]
    return f"CONFIDENTIAL | {receiver_email} | REF:{short_hash}"
