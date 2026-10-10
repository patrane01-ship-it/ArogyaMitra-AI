"""
ArogyaMitra AI - FastAPI Main Application
Entry point for the backend server with production middleware stack,
global exception handlers, and startup validation.
Per PRODUCTION_BACKEND.md §1, §3, §6, §11.
"""

import os
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.core.logger import logger
from backend.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from backend.exceptions.arogya_errors import ArogyaError

# Import Routers
from backend.routers.records_router import router as records_router
from backend.routers.params_router import router as params_router
from backend.routers.risk_router import router as risk_router
from backend.routers.reminders_router import router as reminders_router
from backend.routers.reports_router import router as reports_router
from backend.routers.share_router import router as share_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context: runs startup validation and cleanup on shutdown."""
    logger.info("ArogyaMitra AI backend starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Startup validation checks per PRODUCTION_BACKEND.md §11
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        logger.critical("[Startup] SECRET_KEY must be at least 32 characters")
        raise SystemExit("Startup aborted: SECRET_KEY too short")

    if not settings.ENCRYPTION_KEY:
        logger.critical("[Startup] ENCRYPTION_KEY must be provided")
        raise SystemExit("Startup aborted: ENCRYPTION_KEY missing")

    try:
        key_bytes = base64.b64decode(settings.ENCRYPTION_KEY)
        if len(key_bytes) != 32:
            logger.critical("[Startup] ENCRYPTION_KEY must decode to 32 bytes")
            raise SystemExit("Startup aborted: ENCRYPTION_KEY invalid length")
    except Exception as e:
        logger.critical(f"[Startup] Invalid base64 in ENCRYPTION_KEY: {e}")
        raise SystemExit("Startup aborted: ENCRYPTION_KEY invalid base64")

    if not settings.GROQ_API_KEY:
        logger.warning("[Startup] GROQ_API_KEY not set. AI extraction and report generation will use heuristic fallbacks.")

    # Ensure required directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

    logger.info("ArogyaMitra AI startup validation complete")
    yield
    logger.info("ArogyaMitra AI backend shutting down...")


app = FastAPI(
    title="ArogyaMitra AI",
    description="Agentic Personal Health Intelligence System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middlewares ──────────────────────────────────────────
# Middleware order: RequestLoggingMiddleware -> SecurityHeadersMiddleware -> CORSMiddleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)


# ── Global Exception Handlers (PRODUCTION_BACKEND.md §6.1) ─
@app.exception_handler(ArogyaError)
async def arogya_error_handler(request: Request, exc: ArogyaError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] ArogyaError: {exc.error_code} | {exc.message} | path={request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message, "field": exc.field},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] ValidationError: path={request.url.path} | errors={exc.errors()}")
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"error": "VALIDATION_ERROR", "errors": errors},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] HTTPException: {exc.status_code} | {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"[{request_id}] UnhandledException: path={request.url.path} | err={exc}")
    # Never leak internal error details to client
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please contact support with the request ID.",
        },
        headers={"X-Request-ID": request_id},
    )


# ── Routers ──────────────────────────────────────────────
app.include_router(records_router)
app.include_router(params_router)
app.include_router(risk_router)
app.include_router(reminders_router)
app.include_router(reports_router)
app.include_router(share_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
