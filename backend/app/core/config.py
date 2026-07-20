from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlgoFlow"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "sqlite+aiosqlite:///./algoflow.db"
    auto_create_db_schema: bool = True
    chroma_path: str = "./.chroma"
    auth_mode: str = "hmac"
    auth_token_secret: str | None = None
    trusted_header_auth_enabled: bool = False
    gemini_model: str = "gemini-2.5-flash"
    gemini_provider: str = "ai_studio"
    google_api_key: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    enable_gemini_classification: bool = False
    gemini_classification_timeout_seconds: float = 8.0
    enable_gemini_hints: bool = False
    gemini_hint_timeout_seconds: float = 8.0
    enable_gemini_code_review: bool = False
    enable_gemini_study_plan: bool = False
    enable_gemini_recommendations: bool = False
    enable_gemini_pattern_transfer: bool = False
    enable_gemini_mock_interview: bool = False
    enable_gemini_analytics: bool = False
    gemini_advisory_timeout_seconds: float = 8.0
    enable_live_adk: bool = False
    live_adk_timeout_seconds: float = 3.0
    live_adk_max_events: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def is_local(self) -> bool:
        return self.environment.lower() in {"local", "development", "dev", "test"}

    @property
    def is_demo(self) -> bool:
        return self.environment.lower() in {"demo", "cloud-demo"}

    @property
    def is_production_like(self) -> bool:
        return self.environment.lower() in {"production", "prod", "staging"}

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    def validate_runtime_config(self) -> None:
        if not self.is_production_like:
            return

        if self.database_url.startswith("sqlite"):
            raise RuntimeError("Production-like environments must not use local SQLite.")

        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise RuntimeError("Production-like environments must use postgresql+asyncpg DATABASE_URL.")

        if self.auto_create_db_schema:
            raise RuntimeError("Production-like environments must use migrations instead of create_all startup.")

        if self.chroma_path.startswith(".") or self.chroma_path.startswith("/tmp"):
            raise RuntimeError("Production-like environments must not use a local Chroma path.")

        if self.auth_mode == "hmac" and not self.auth_token_secret:
            raise RuntimeError("Production-like HMAC auth requires AUTH_TOKEN_SECRET.")

        if self.auth_mode == "trusted_header" and not self.trusted_header_auth_enabled:
            raise RuntimeError("Trusted-header auth must be explicitly enabled.")

        if self.auth_mode not in {"hmac", "trusted_header"}:
            raise RuntimeError("Production-like environments must use auth_mode=hmac or trusted_header.")

        if self.gemini_provider not in {"ai_studio", "vertex_ai"}:
            raise RuntimeError("GEMINI_PROVIDER must be ai_studio or vertex_ai.")

        if self.gemini_provider == "vertex_ai" and not self.google_cloud_project:
            raise RuntimeError("Vertex AI Gemini requires GOOGLE_CLOUD_PROJECT.")

        if self.enable_live_adk and self.gemini_provider == "ai_studio" and not self.google_api_key:
            raise RuntimeError("ENABLE_LIVE_ADK requires GOOGLE_API_KEY or Vertex AI credentials.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
