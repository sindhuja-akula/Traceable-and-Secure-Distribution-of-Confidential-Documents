"""token_utils.py - Secure URL token generation and helpers."""
import uuid
import secrets
import logging

logger = logging.getLogger(__name__)

def generate_token() -> str:
    """Generate a cryptographically secure URL-safe token."""
    try:
        return secrets.token_urlsafe(32)
    except Exception as exc:
        logger.error("Token generation error: %s", exc)
        return str(uuid.uuid4()).replace("-", "")

def generate_trace_id() -> str:
    """Generate a unique trace identifier for fingerprinting."""
    try:
        return str(uuid.uuid4())
    except Exception as exc:
        logger.error("Trace ID generation error: %s", exc)
        return secrets.token_hex(16)

def generate_doc_password() -> str:
    """Generate a random 8-char alphanumeric document password."""
    try:
        alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(8))
    except Exception as exc:
        logger.error("Password generation error: %s", exc)
        return secrets.token_hex(4)
