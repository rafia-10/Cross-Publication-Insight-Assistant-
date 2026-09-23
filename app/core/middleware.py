"""
app.core.middleware
~~~~~~~~~~~~~~~~~~~
FastAPI middleware for:
  1. Attaching a UUID correlation ID to every request (reads X-Correlation-ID
     header or generates a new UUID4).
  2. Logging request entry / exit with method, path, status code, and duration.
  3. Catching unhandled InsightAssistantError subclasses and returning a
     well-formed JSON error response that includes the correlation ID.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.exceptions import InsightAssistantError
from app.core.logging import correlation_id_var, get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Injects a correlation ID into each request context and logs every
    HTTP transaction with its outcome and duration.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # --- Resolve or generate correlation ID ---
        corr_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        token = correlation_id_var.set(corr_id)

        start_ns = time.perf_counter_ns()

        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "correlation_id": corr_id,
            },
        )

        try:
            response: Response = await call_next(request)
        except InsightAssistantError as exc:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.error(
                "Unhandled application error",
                extra={
                    "error_type": type(exc).__name__,
                    "error": exc.message,
                    "context": exc.context,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=exc.cause,
            )
            correlation_id_var.reset(token)
            return JSONResponse(
                status_code=500,
                content={
                    "error": type(exc).__name__,
                    "message": exc.message,
                    "correlation_id": corr_id,
                },
                headers={self.header_name: corr_id},
            )
        except Exception as exc:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.exception(
                "Unexpected unhandled error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            correlation_id_var.reset(token)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred.",
                    "correlation_id": corr_id,
                },
                headers={self.header_name: corr_id},
            )

        duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        # Propagate correlation ID in response header for client tracing
        response.headers[self.header_name] = corr_id
        correlation_id_var.reset(token)
        return response
