import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator
from typing import List, Union

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClassFlow AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # DATABASE
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://classflow:classflow_password@localhost:5432/classflow")
    
    # REDIS / RQ
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # EMAIL IMAP (Ingestion)
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER: str = os.getenv("IMAP_USER", "")
    IMAP_PASSWORD: str = os.getenv("IMAP_PASSWORD", "")
    
    # EMAIL SMTP (Sending)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "classflow@example.com")
    
    # WHATSAPP BOT API URL (Internal microservice)
    WHATSAPP_BOT_URL: str = os.getenv("WHATSAPP_BOT_URL", "http://whatsapp-bot:3000")
    
    # AI (Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
