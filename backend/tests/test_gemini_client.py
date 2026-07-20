import sys
import types

import pytest

from app.core.config import Settings
from app.services.gemini_client import build_gemini_client, gemini_auth_configured


class FakeHttpOptions:
    def __init__(self, api_version: str):
        self.api_version = api_version


class FakeGenAIClient:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls.append(kwargs)


def install_fake_google_genai(monkeypatch):
    fake_google = types.ModuleType("google")
    fake_genai = types.ModuleType("google.genai")
    fake_types = types.ModuleType("google.genai.types")
    fake_genai.Client = FakeGenAIClient
    fake_genai.types = fake_types
    fake_types.HttpOptions = FakeHttpOptions
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    FakeGenAIClient.calls = []


def test_ai_studio_client_uses_api_key(monkeypatch):
    install_fake_google_genai(monkeypatch)

    client = build_gemini_client(Settings(gemini_provider="ai_studio", google_api_key="test-key"))

    assert isinstance(client, FakeGenAIClient)
    assert client.kwargs == {"api_key": "test-key"}


def test_vertex_ai_client_uses_project_location_and_v1_http_options(monkeypatch):
    install_fake_google_genai(monkeypatch)

    client = build_gemini_client(
        Settings(
            gemini_provider="vertex_ai",
            google_cloud_project="algoflow-demo",
            google_cloud_location="us-central1",
            google_api_key=None,
        )
    )

    assert client.kwargs["vertexai"] is True
    assert client.kwargs["project"] == "algoflow-demo"
    assert client.kwargs["location"] == "us-central1"
    assert client.kwargs["http_options"].api_version == "v1"


def test_vertex_ai_auth_configured_uses_project_not_api_key():
    settings = Settings(
        gemini_provider="vertex_ai",
        google_cloud_project="algoflow-demo",
        google_api_key=None,
    )

    assert gemini_auth_configured(settings) is True


def test_invalid_provider_fails_fast(monkeypatch):
    install_fake_google_genai(monkeypatch)

    with pytest.raises(RuntimeError, match="GEMINI_PROVIDER"):
        build_gemini_client(Settings(gemini_provider="unknown", google_api_key="test-key"))
