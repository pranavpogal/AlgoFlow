import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_includes_request_and_trace_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health", headers={"x-request-id": "req_test"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req_test"
    assert response.headers["x-trace-id"].startswith("trace_")
    assert response.json() == {"status": "ok", "service": "algoflow"}


@pytest.mark.asyncio
async def test_validation_errors_use_safe_error_envelope():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/problems/analyze",
            json={"description": "missing title"},
            headers={"x-request-id": "req_validation"},
        )

    body = response.json()
    assert response.status_code == 422
    assert response.headers["x-request-id"] == "req_validation"
    assert body["request_id"] == "req_validation"
    assert body["trace_id"].startswith("trace_")
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["retryable"] is False
    assert "Traceback" not in body["error"]["message"]
