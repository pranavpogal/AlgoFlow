from __future__ import annotations

import os
import re
from typing import Any

from app.core.config import Settings, get_settings


def build_gemini_client(settings: Settings | None = None) -> Any:
    settings = settings or get_settings()
    from google import genai
    from google.genai import types

    if settings.gemini_provider == "vertex_ai":
        if not settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when GEMINI_PROVIDER=vertex_ai.")
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.google_cloud_project)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.google_cloud_location)
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            http_options=types.HttpOptions(api_version="v1"),
        )

    if settings.gemini_provider != "ai_studio":
        raise RuntimeError("GEMINI_PROVIDER must be ai_studio or vertex_ai.")
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required when GEMINI_PROVIDER=ai_studio.")
    return genai.Client(api_key=settings.google_api_key)


def gemini_auth_configured(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if settings.gemini_provider == "vertex_ai":
        return bool(settings.google_cloud_project)
    return bool(settings.google_api_key)


def sanitize_gemini_exception_message(message: str) -> str:
    collapsed = " ".join(message.split())
    redacted = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[redacted-api-key]", collapsed)
    return redacted[:240]


def gemini_exception_label(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    message = sanitize_gemini_exception_message(str(exc))
    parts = [type(exc).__name__]
    if status:
        parts.append(str(status))
    if message:
        parts.append(message)
    return ":".join(parts)
