import os 
from pydantic_settings import BaseSettings 
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Base API settings 
    API_VERSION: str = 'v1'
    API_PREFIX: str = f"/api/{API_VERSION}"

    # Security  
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-needs-to-be-updated")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/scheduler")

    # TikTok API
    TIKTOK_CLIENT_KEY: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    TIKTOK_CLIENT_SECRET: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    TIKTOK_REDIRECT_URI: str = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/api/v1/auth/tiktok/callback")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()