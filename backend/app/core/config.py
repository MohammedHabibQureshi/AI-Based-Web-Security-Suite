import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    API_PORT: int = 8000
    JWT_SECRET: str = "supersecretjwttokenchangeinproduction12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./sentinelai.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    WAF_PROXY_PORT: int = 8080
    DEFAULT_BLOCK_THRESHOLD: int = 50
    FAIL_SAFE_OPEN: bool = True

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@sentinelai.com"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITLAB_CLIENT_ID: str = ""
    GITLAB_CLIENT_SECRET: str = ""

settings = Settings()
