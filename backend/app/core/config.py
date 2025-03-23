import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Project Information
    PROJECT_NAME: str = "Test Planning Helper"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database Configuration
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_planning")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # User Configuration
    MAX_STORAGE_PER_USER_MB: int = 100
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1
    RATE_LIMIT_WINDOW_SECONDS: int = 5
    RATE_LIMIT_BLOCK_MINUTES: int = 60
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")
    
    @field_validator("DATABASE_URI", mode='before')
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            port=values.data.get("POSTGRES_PORT"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 