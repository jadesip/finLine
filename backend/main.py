"""
finLine API

FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db

# Import API routers
from api.auth import router as auth_router
from api.projects import router as projects_router
from api.chat import router as chat_router
from api.extraction import router as extraction_router
from api.insights import router as insights_router
from api.payments import router as payments_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting finLine API...")
    await init_db()
    logger.info("finLine API started successfully")
    yield
    # Shutdown
    logger.info("Shutting down finLine API...")


# Create FastAPI app
app = FastAPI(
    title="finLine API",
    description="Simplified LBO financial modeling API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(chat_router, prefix="/api/projects", tags=["Chat"])
app.include_router(extraction_router, prefix="/api/projects", tags=["Extraction"])
app.include_router(insights_router, prefix="/api/projects", tags=["Insights"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "finLine API",
        "version": "1.0.0",
        "docs": "/docs"
    }
