from __future__ import annotations

import asyncio
import time
from typing import Any

from app.core.config import Settings, get_settings
from app.services.gemini_client import (
    build_gemini_client,
    gemini_auth_configured,
    sanitize_gemini_exception_message,
)


async def check_gemini_connection(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    started = time.perf_counter()
    base = {
        "key_configured": bool(settings.google_api_key),
        "auth_configured": gemini_auth_configured(settings),
        "provider": settings.gemini_provider,
        "model": settings.gemini_model,
        "google_cloud_project_configured": bool(settings.google_cloud_project),
        "google_cloud_location": settings.google_cloud_location,
        "classification_enabled": settings.enable_gemini_classification,
        "hints_enabled": settings.enable_gemini_hints,
        "code_review_enabled": settings.enable_gemini_code_review,
        "study_plan_enabled": settings.enable_gemini_study_plan,
        "recommendations_enabled": settings.enable_gemini_recommendations,
        "pattern_transfer_enabled": settings.enable_gemini_pattern_transfer,
        "mock_interview_enabled": settings.enable_gemini_mock_interview,
        "analytics_enabled": settings.enable_gemini_analytics,
        "ok": False,
        "status": "not_checked",
        "error": None,
        "latency_ms": None,
    }
    if not gemini_auth_configured(settings):
        return {**base, "status": "missing_gemini_credentials"}

    try:
        await asyncio.wait_for(
            asyncio.to_thread(_probe_gemini_sync, settings),
            timeout=min(settings.gemini_classification_timeout_seconds, 20),
        )
    except Exception as exc:
        return {
            **base,
            "status": "failed",
            "error": _diagnostic_error(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    return {
        **base,
        "ok": True,
        "status": "ok",
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def _probe_gemini_sync(settings: Settings) -> None:
    from google.genai import types

    client = build_gemini_client(settings)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents='Return exactly this JSON: {"ok": true}',
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    text = (getattr(response, "text", "") or "").lower()
    if "ok" not in text:
        raise ValueError("Gemini probe returned a response without the expected ok marker.")


def _diagnostic_error(exc: Exception) -> dict[str, Any]:
    return {
        "type": type(exc).__name__,
        "status_code": getattr(exc, "status_code", None),
        "message": sanitize_gemini_exception_message(str(exc)),
    }
