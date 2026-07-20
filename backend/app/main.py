from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import AlgoFlowError
from app.core.middleware import RequestContextMiddleware
from app.core.request_context import get_request_context, new_request_context
from app.db.init_db import init_db
from app.schemas.errors import ErrorBody, ErrorEnvelope

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime_config()
    await init_db()
    yield


app = FastAPI(
    title="AlgoFlow API",
    description="Production-grade multi-agent coding interview mentor powered by Google ADK.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


def _error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    retryable: bool = False,
) -> JSONResponse:
    context = get_request_context() or new_request_context(
        request_id=request.headers.get("x-request-id"),
        trace_id=request.headers.get("x-trace-id"),
    )
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
            retryable=retryable,
        ),
        request_id=context.request_id,
        trace_id=context.trace_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(),
        headers={
            "x-request-id": context.request_id,
            "x-trace-id": context.trace_id,
        },
    )


@app.exception_handler(AlgoFlowError)
async def algoflow_error_handler(request: Request, exc: AlgoFlowError) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        retryable=exc.retryable,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
        retryable=True,
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "algoflow",
        "status": "ok",
        "docs": "/docs",
        "api_health": f"{settings.api_prefix}/health",
    }
