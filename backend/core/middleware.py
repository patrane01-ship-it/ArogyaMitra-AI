"""
ArogyaMitra AI - Custom Middlewares
Implements SecurityHeadersMiddleware and RequestLoggingMiddleware with X-Request-ID tracking.
Per PRODUCTION_BACKEND.md §1.5 and §3.2.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.core.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Assigns unique X-Request-ID to each request and logs entry and response performance.
    Logs do not contain sensitive tokens, Authorization headers, or passwords.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        user_agent = request.headers.get("user-agent", "unknown")[:50]
        logger.info(
            f"[{request_id}] -> {request.method} {request.url.path} | UA: {user_agent}"
        )

        start_time = time.time()
        try:
            response: Response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(
                f"[{request_id}] <- {response.status_code} | duration={duration_ms}ms"
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"[{request_id}] FAIL {request.method} {request.url.path} | duration={duration_ms}ms | err={type(exc).__name__}"
            )
            raise exc


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies strict security headers and strips identifying server information.
    Per PRODUCTION_BACKEND.md §3.2.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Standard OWASP security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Default no-store cache policy unless specifically overridden
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"

        # Remove identifying headers
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response
