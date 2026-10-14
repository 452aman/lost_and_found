from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LostFound"
    database_url: str = "sqlite:///./lostfound.db"
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    upload_dir: str = "uploads"
    max_upload_mb: int = 5
    cors_origins: list[str] = ["http://localhost:5173"]
    allowed_email_domain: str | None = None  # e.g. "iitr.ac.in" to restrict sign-ups
    match_threshold: float = 0.35
    claim_expiry_days: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()
