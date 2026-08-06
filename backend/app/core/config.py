import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClassFlow AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # DATABASE
    DATABASE_URL: str = "postgresql://classflow:classflow_password@localhost:5432/classflow"
    
    # REDIS / RQ
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # EMAIL IMAP (Ingestion)
    IMAP_SERVER: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    
    # EMAIL SMTP (Sending)
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "classflow@example.com"
    
    # WHATSAPP BOT API URL (Internal microservice)
    WHATSAPP_BOT_URL: str = "http://whatsapp-bot:3000"
    WHATSAPP_GROUP_JID: str = ""
    
    # AI (Gemini)
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
