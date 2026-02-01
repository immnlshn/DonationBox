"""
Application configuration and settings.

Uses pydantic-settings for environment variable management.
"""

import json
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # App
    APP_NAME: str = "DonationBox API"
    ENV: str = "production"
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "plain"

    # Security
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: str = "sqlite:///./backend/database.db"

    # CORS
    ALLOWED_ORIGINS: Union[list[str], str] = "*"

    # GPIO
    ENABLE_GPIO: bool = False
    PIN_FACTORY: str = "mock"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list."""
        if isinstance(v, str):
            # If it's "*", allow all origins
            if v == "*":
                return ["*"]
            # Try to parse as JSON
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Split by comma if it's a comma-separated string
            if "," in v:
                return [origin.strip() for origin in v.split(",")]
            # Single origin
            return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
