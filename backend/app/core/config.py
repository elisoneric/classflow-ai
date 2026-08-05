from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    timezone: str = "Africa/Lagos"
    frontend_origin: str = "http://localhost:5173"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    course_rep_email: str = "you@example.com"
    course_rep_password: str = "changeme"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "classflow@example.com"
    smtp_use_tls: bool = True

    imap_host: str = ""
    imap_port: int = 993
    imap_username: str = ""
    imap_password: str = ""
    imap_mailbox: str = "INBOX"
    imap_use_ssl: bool = True
    imap_poll_interval_seconds: int = 75

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ai_confidence_threshold: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()
