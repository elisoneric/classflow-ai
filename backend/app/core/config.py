from functools import lru_cache
from urllib.parse import quote, unquote

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    timezone: str = "Africa/Lagos"
    frontend_origin: str = "http://localhost:5173"

    postgres_user: str = "classflow"
    postgres_password: str = "changeme"
    postgres_db: str = "classflow"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    database_url: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def sanitize_database_url(cls, v: str) -> str:
        if not v or "://" not in v:
            return v
        scheme, rest = v.split("://", 1)
        if "@" not in rest:
            return v
        userinfo, host_and_db = rest.rsplit("@", 1)
        if ":" not in userinfo:
            return v
        user, password = userinfo.split(":", 1)
        unquoted_password = unquote(password)
        quoted_password = quote(unquoted_password, safe="")
        return f"{scheme}://{user}:{quoted_password}@{host_and_db}"

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        if not self.database_url:
            quoted_pass = quote(self.postgres_password, safe="")
            self.database_url = f"postgresql+asyncpg://{self.postgres_user}:{quoted_pass}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        return self
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    course_rep_email: str = "elisoneric123@gmail.com"
    course_rep_password: str = "password"

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

    # Anthropic adapter kept as an alternate MessageInterpreter implementation
    # (ADR-6) — Gemini is the active provider (ADR-4), selected in
    # app/infrastructure/jobs/tasks.py, not here.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"

    ai_confidence_threshold: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()
