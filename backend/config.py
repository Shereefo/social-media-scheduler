import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Base API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"

    # Security — no fallback defaults. Missing env vars fail loudly at startup
    # rather than silently running with insecure placeholder values.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database — no fallback. If DATABASE_URL is not injected by ECS Secrets
    # Manager the app will raise a validation error at import time.
    DATABASE_URL: str

    # TikTok API
    TIKTOK_CLIENT_KEY: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    TIKTOK_CLIENT_SECRET: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    TIKTOK_REDIRECT_URI: str = os.getenv(
        "TIKTOK_REDIRECT_URI", "http://localhost:8000/api/v1/auth/tiktok/callback"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
