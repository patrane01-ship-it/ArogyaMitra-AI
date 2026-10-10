"""
ArogyaMitra AI - FastAPI Main Application
Entry point for the backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.core.logger import logger

app = FastAPI(
    title="ArogyaMitra AI",
    description="Agentic Personal Health Intelligence System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Run startup validation."""
    logger.info("ArogyaMitra AI backend starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Validate critical settings
    if len(settings.SECRET_KEY) < 32:
        logger.critical("SECRET_KEY must be at least 32 characters")
        raise SystemExit("Startup aborted: SECRET_KEY too short")
    
    if settings.DEBUG and settings.ENVIRONMENT == "production":
        logger.critical("DEBUG=True is not allowed in production")
        raise SystemExit("Startup aborted: DEBUG cannot be True in production")
    
    logger.info("ArogyaMitra AI backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("ArogyaMitra AI backend shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
