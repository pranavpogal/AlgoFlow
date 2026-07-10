from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import new_request_context, reset_request_context, set_request_context

logger = logging.getLogger("algoflow.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        context = new_request_context(
            request_id=request.headers.get("x-request-id"),
            trace_id=request.headers.get("x-trace-id"),
        )
        token = set_request_context(context)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["x-request-id"] = context.request_id
        response.headers["x-trace-id"] = context.trace_id
        logger.info(
            "request_complete",
            extra={
                "request_id": context.request_id,
                "trace_id": context.trace_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        return response
