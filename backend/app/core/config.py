from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlgoFlow"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./algoflow.db"
    chroma_path: str = "./.chroma"
    gemini_model: str = "gemini-2.5-flash"
    google_api_key: str | None = None
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
    def is_production_like(self) -> bool:
        return not self.is_local

    def validate_runtime_config(self) -> None:
        if not self.is_production_like:
            return

        if self.database_url.startswith("sqlite"):
            raise RuntimeError("Production-like environments must not use local SQLite.")

        if self.chroma_path.startswith(".") or self.chroma_path.startswith("/tmp"):
            raise RuntimeError("Production-like environments must not use a local Chroma path.")

        if self.enable_live_adk and not self.google_api_key:
            raise RuntimeError("ENABLE_LIVE_ADK requires GOOGLE_API_KEY or configured Google credentials.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
