"""email_parser.py - Parse CSV/Excel files into recipient lists."""
import io
import logging
from typing import List, Dict, Any
import pandas as pd
from fastapi import HTTPException

logger = logging.getLogger(__name__)

REQUIRED_COLS = {"name", "email"}

def parse_recipients(file_bytes: bytes, filename: str) -> List[Dict[str, str]]:
    """
    Accept CSV or XLSX bytes. Returns list of {name, email} dicts.
    Raises HTTPException on malformed input.
    """
    try:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise HTTPException(status_code=400, detail="Only CSV or Excel files are supported.")

        df.columns = [c.strip().lower() for c in df.columns]
        missing = REQUIRED_COLS - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"File is missing required columns: {missing}. Found: {list(df.columns)}"
            )

        df = df[list(REQUIRED_COLS)].dropna()
        recipients = df.to_dict(orient="records")
        if not recipients:
            raise HTTPException(status_code=422, detail="File contains no valid recipient rows.")
        return [{"name": str(r["name"]).strip(), "email": str(r["email"]).strip().lower()} for r in recipients]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Recipient file parse error (%s): %s", filename, exc)
        raise HTTPException(status_code=400, detail=f"Could not parse recipient file: {exc}") from exc
