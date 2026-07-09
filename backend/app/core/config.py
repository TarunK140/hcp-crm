"""
Application configuration.

Loads all environment variables from `.env` into a single, typed Settings
object so the rest of the codebase never touches `os.environ` directly.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Groq / LLM
    groq_api_key: str = ""
    # NOTE: the assignment brief specifies gemma2-9b-it, but Groq has fully
    # decommissioned that model (deprecated Aug 2025 in favor of
    # llama-3.1-8b-instant, which was itself deprecated June 2026). We use
    # Groq's currently recommended models instead — mention this in your
    # video/README as a provider-side change outside the project's control.
    groq_model: str = "openai/gpt-oss-20b"
    groq_model_fallback: str = "openai/gpt-oss-120b"

    # Database
    database_url: str = "sqlite:///./hcp_crm.db"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-reading .env every call)."""
    return Settings()
