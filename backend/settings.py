from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  # App
  APP_NAME: str = "FastAPI"
  ENV: str = "production"
  DEBUG: bool = False

  # Logging
  LOG_LEVEL: str = "INFO"
  LOG_FORMAT: str = "plain"

  # Security
  SECRET_KEY: str = "your-secret-key"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

  # Database
  DATABASE_URL: str = "sqlite:///./database.db"

  # CORS
  ALLOWED_ORIGINS: list[str] = []

  # GPIO
  ENABLE_GPIO: bool = False
  PIN_FACTORY: str = "mock"

  model_config = SettingsConfigDict(
      env_file=".env",
      env_file_encoding="utf-8",
      case_sensitive=True,
  )

settings = Settings()
