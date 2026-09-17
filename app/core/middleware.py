"""
FastAPI middleware stack.

- RequestID injection (every request gets a unique ID)
- Request timing
- Structured error handling (domain exceptions → JSON responses)
- CORS
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import SupportAIError
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Request context middleware
# ---------------------------------------------------------------------------

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Injects request_id into every request and logs timing.
    Binds request_id to structlog context vars for automatic inclusion.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind to structlog context for all downstream log calls
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Unhandled exceptions — log and return 500
            logger.exception("unhandled_exception")
            return _error_response(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                request_id=request_id,
            )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        logger.info(
            "request_completed",
            status=response.status_code,
            latency_ms=elapsed_ms,
        )

        return response


# ---------------------------------------------------------------------------
# Domain exception handler
# ---------------------------------------------------------------------------

async def domain_exception_handler(
    request: Request, exc: SupportAIError
) -> JSONResponse:
    """Convert domain exceptions into standardized JSON error responses."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Log at appropriate level
    if exc.status_code >= 500:
        logger.error(
            "domain_error",
            error_code=exc.error_code,
            status_code=exc.status_code,
            detail=str(exc.detail) if exc.detail else None,
        )
    else:
        logger.warning(
            "domain_error",
            error_code=exc.error_code,
            status_code=exc.status_code,
        )

    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_middleware(app: FastAPI, cors_origins: list[str]) -> None:
    """Register all middleware on the FastAPI app."""
    # Order matters: outermost middleware first

    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )

    # Register domain exception handler
    app.add_exception_handler(SupportAIError, domain_exception_handler)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
) -> JSONResponse:
    """Build a standardized error JSON response."""
    body: dict[str, Any] = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "request_id": request_id,
        },
    }
    return JSONResponse(status_code=status_code, content=body)
