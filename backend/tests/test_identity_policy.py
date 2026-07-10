import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.auth import get_principal
from app.core.auth_tokens import create_auth_token
from app.core.config import Settings, get_settings
from app.core.errors import AlgoFlowError
from app.db.init_db import init_db
from app.db.base import ProblemAttempt
from app.db.session import AsyncSessionLocal
from app.main import app


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


@pytest.mark.asyncio
async def test_body_user_id_is_ignored_in_favor_of_resolved_principal():
    title = "Identity Boundary Audit Problem"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/problems/analyze",
            headers={"x-user-id": "principal-user"},
            json={
                "user_id": "spoofed-user",
                "title": title,
                "description": "A graph node edge traversal problem.",
            },
        )

    assert response.status_code == 200
    async with AsyncSessionLocal() as session:
        attempts = (
            await session.execute(select(ProblemAttempt).where(ProblemAttempt.title == title))
        ).scalars().all()

    assert attempts
    assert {attempt.user_id for attempt in attempts} == {"principal-user"}


@pytest.mark.asyncio
async def test_cross_user_analytics_request_is_forbidden():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/analytics/other-user",
            headers={"x-user-id": "principal-user"},
        )

    body = response.json()
    assert response.status_code == 403
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["retryable"] is False


@pytest.mark.asyncio
async def test_production_like_auth_requires_bearer_token(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-secret-value-that-is-long-enough")
    get_settings.cache_clear()
    try:
        with pytest.raises(AlgoFlowError) as exc_info:
            await get_principal(authorization=None, x_authenticated_user_id=None, x_user_id=None)
    finally:
        get_settings.cache_clear()

    assert exc_info.value.code == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_production_like_auth_accepts_valid_hmac_bearer_token(monkeypatch):
    secret = "test-secret-value-that-is-long-enough"
    token = create_auth_token("principal-user", secret, ttl_seconds=60)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_TOKEN_SECRET", secret)
    get_settings.cache_clear()
    try:
        principal = await get_principal(
            authorization=f"Bearer {token}",
            x_authenticated_user_id="spoofed-header-user",
            x_user_id="spoofed-local-user",
        )
    finally:
        get_settings.cache_clear()

    assert principal.user_id == "principal-user"
    assert principal.auth_mode == "hmac-bearer"


@pytest.mark.asyncio
async def test_production_like_auth_rejects_invalid_hmac_bearer_token(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-secret-value-that-is-long-enough")
    get_settings.cache_clear()
    try:
        with pytest.raises(AlgoFlowError) as exc_info:
            await get_principal(
                authorization="Bearer invalid.token",
                x_authenticated_user_id=None,
                x_user_id=None,
            )
    finally:
        get_settings.cache_clear()

    assert exc_info.value.code == "AUTH_INVALID"


@pytest.mark.asyncio
async def test_trusted_header_auth_requires_explicit_enablement(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_MODE", "trusted_header")
    monkeypatch.setenv("TRUSTED_HEADER_AUTH_ENABLED", "true")
    get_settings.cache_clear()
    try:
        principal = await get_principal(
            authorization=None,
            x_authenticated_user_id="gateway-user",
            x_user_id="spoofed-local-user",
        )
    finally:
        get_settings.cache_clear()

    assert principal.user_id == "gateway-user"
    assert principal.auth_mode == "trusted-header"


def test_production_like_config_rejects_sqlite():
    settings = Settings(environment="production", database_url="sqlite+aiosqlite:///./algoflow.db")

    with pytest.raises(RuntimeError, match="SQLite"):
        settings.validate_runtime_config()


def test_live_adk_requires_credentials_in_production_like_config():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/algoflow",
        auto_create_db_schema=False,
        chroma_path="managed-chroma",
        auth_token_secret="test-secret-value-that-is-long-enough",
        enable_live_adk=True,
        google_api_key=None,
    )

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        settings.validate_runtime_config()


def test_production_like_config_requires_asyncpg_postgres_url():
    settings = Settings(
        environment="production",
        database_url="postgresql://user:pass@db/algoflow",
        auto_create_db_schema=False,
        chroma_path="managed-chroma",
        auth_token_secret="test-secret-value-that-is-long-enough",
    )

    with pytest.raises(RuntimeError, match="postgresql\\+asyncpg"):
        settings.validate_runtime_config()


def test_production_like_config_requires_migration_managed_schema_startup():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/algoflow",
        auto_create_db_schema=True,
        chroma_path="managed-chroma",
        auth_token_secret="test-secret-value-that-is-long-enough",
    )

    with pytest.raises(RuntimeError, match="migrations"):
        settings.validate_runtime_config()


def test_production_like_config_accepts_postgres_hmac_auth_and_migration_startup():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/algoflow",
        auto_create_db_schema=False,
        chroma_path="managed-chroma",
        auth_token_secret="test-secret-value-that-is-long-enough",
    )

    settings.validate_runtime_config()
