"""
config.py - Pydantic Settings loaded from .env with full exception handling.
"""
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str | None = None
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "secure_docs"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # JWT
    SECRET_KEY: str = "change-me-to-a-256-bit-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "akulasindhuja666@gmail.com"

    # App
    UPLOAD_DIR: str = "./uploads"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY2: str = ""

try:
    _settings = Settings()
except ValidationError as exc:
    logger.critical("Configuration validation error: %s", exc)
    raise

@lru_cache
def get_settings() -> Settings:
    return _settings
