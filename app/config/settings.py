from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "Atlas AI Financial Assistant"
    app_env: str = "development"
    app_version: str = "0.1.0"

    # Database
    database_url: str = ""
    redis_url: str = ""

    # Telegram
    telegram_bot_token: str = ""

    # AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    # Financial data providers
    finnhub_api_key: str = ""
    alpha_vantage_api_key: str = ""

    # Google integrations
    google_client_id: str = ""
    google_client_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()