"""
main.py - FastAPI app entrypoint.
Registers all routers, configures CORS, and handles startup table creation.
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import create_tables
from backend.core.config import get_settings
from backend.routes import (
    auth_routes,
    document_routes,
    email_routes,
    progress_routes,
    tracking_routes,
    security_routes,
    activity_routes,
    leak_routes
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Secure Document Distribution API",
    description="Backend for secure document fingerprinting and tracking.",
    version="1.0.0"
)

# Configure CORS - set to catch all for troubleshooting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to create database tables
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    # Create the upload directory if it doesn't exist
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR)
        logger.info(f"Created upload directory: {settings.UPLOAD_DIR}")
    
    # Create database tables
    try:
        await create_tables()
        logger.info("Database initialization successful.")
    except Exception as exc:
        logger.error(f"Database initialization failed: {exc}")

# Mount static files for document uploads
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Register Routers
app.include_router(auth_routes.router)
app.include_router(document_routes.router)
app.include_router(email_routes.router)
app.include_router(progress_routes.router)
app.include_router(tracking_routes.router)
app.include_router(security_routes.router)
app.include_router(activity_routes.router)
app.include_router(leak_routes.router)

@app.get("/")
async def root():
    return {"message": "Secure Document Distribution API is online."}
