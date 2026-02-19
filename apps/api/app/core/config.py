from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sport SaaS"
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/sportsaas"
    SECRET_KEY: str = "supersecretkey"
    INTERNAL_KEY: str = "troque_isto"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"  # "lax" (dev) or "none"/"strict" (prod)
    COOKIE_DOMAIN: Optional[str] = None  # optional, defaults to host
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
