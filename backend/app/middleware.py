import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging import get_logger

log = get_logger("app.access")
REQUEST_ID_HEADER = "X-Request-ID"
QUIET_PATHS = {"/api/v1/health"}  # liveness probes hit this constantly


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns a request id, binds it to every log line, and logs one line per request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:12]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # The traceback is logged by the unhandled-exception handler.
            log.error(
                "request",
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=round((time.perf_counter() - start) * 1000, 1),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers[REQUEST_ID_HEADER] = request_id
        if request.url.path not in QUIET_PATHS:
            level = "warning" if response.status_code >= 400 else "info"
            getattr(log, level)(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )
        return response
