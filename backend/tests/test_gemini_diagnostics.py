import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import app
from app.services import gemini_diagnostics
from app.services.gemini_diagnostics import check_gemini_connection


@pytest.mark.asyncio
async def test_gemini_diagnostics_reports_missing_key_without_probe():
    result = await check_gemini_connection(Settings(google_api_key=None))

    assert result["ok"] is False
    assert result["status"] == "missing_google_api_key"
    assert result["key_configured"] is False


@pytest.mark.asyncio
async def test_gemini_diagnostics_sanitizes_probe_errors(monkeypatch):
    def fake_probe(settings):
        raise RuntimeError("bad key AIza123456789012345678901234567890")

    monkeypatch.setattr(gemini_diagnostics, "_probe_gemini_sync", fake_probe)

    result = await check_gemini_connection(Settings(google_api_key="test-key"))

    assert result["ok"] is False
    assert result["status"] == "failed"
    assert result["error"]["type"] == "RuntimeError"
    assert "[redacted-api-key]" in result["error"]["message"]
    assert "AIza" not in result["error"]["message"]


@pytest.mark.asyncio
async def test_gemini_diagnostics_endpoint_returns_safe_payload(monkeypatch):
    async def fake_check_gemini_connection():
        return {
            "key_configured": True,
            "model": "gemini-2.5-flash",
            "classification_enabled": True,
            "hints_enabled": False,
            "ok": False,
            "status": "failed",
            "error": {"type": "ClientError", "status_code": 403, "message": "PERMISSION_DENIED"},
            "latency_ms": 12.3,
        }

    monkeypatch.setattr("app.api.routes.check_gemini_connection", fake_check_gemini_connection)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/diagnostics/gemini", headers={"x-user-id": "diag-user"})

    assert response.status_code == 200
    body = response.json()
    assert body["key_configured"] is True
    assert body["error"]["status_code"] == 403
    assert "GOOGLE_API_KEY" not in str(body)
