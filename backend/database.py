"""
database.py - Async SQLAlchemy engine, session factory, and Base.
Uses environment variables from .env via python-dotenv.
"""
import os
import logging
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
logger = logging.getLogger(__name__)

def _build_database_url() -> str:
    # 1. Check for a direct DATABASE_URL (common on Render/Heroku)
    url = os.getenv("DATABASE_URL")
    if url:
        # SQLAlchemy requires 'postgresql://' or 'postgresql+asyncpg://'
        # Render/Heroku often provide 'postgres://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # 2. Fallback to manual construction
    user     = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host     = os.getenv("DB_HOST", "127.0.0.1")
    port     = os.getenv("DB_PORT", "5432")
    name     = os.getenv("DB_NAME", "secure_docs")
    
    # URL-encode the password to handle special characters like '@'
    encoded_password = urllib.parse.quote_plus(password)
    
    return f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{name}"

DATABASE_URL = _build_database_url()

try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    logger.info("Async database engine created.")
except Exception as exc:
    logger.critical("Failed to create database engine: %s", exc)
    raise RuntimeError(f"Database engine creation failed: {exc}") from exc

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("DB session error, rolling back: %s", exc)
            raise
        finally:
            await session.close()

async def create_tables() -> None:
    try:
        async with engine.begin() as conn:
            import backend.models.user_model      # noqa
            import backend.models.document_model  # noqa
            import backend.models.email_model     # noqa
            import backend.models.activity_model  # noqa
            import backend.models.security_model  # noqa
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created/verified.")
    except SQLAlchemyError as exc:
        logger.critical("Table creation failed: %s", exc)
        raise RuntimeError(f"Table creation failed: {exc}") from exc
