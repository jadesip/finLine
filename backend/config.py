"""
finLine Configuration

All settings are loaded from environment variables with sensible defaults.
snake_case naming convention throughout.
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/finline.db"

    # JWT Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # LLM Configuration (abstracted - change provider here)
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # gemini, claude, openai
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_api_key: str = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")

    # Perplexity (for business insights)
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")

    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Paths
    base_dir: Path = Path(__file__).parent
    data_dir: Path = Path(__file__).parent.parent / "data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
