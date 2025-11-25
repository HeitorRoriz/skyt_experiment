# api/config.py
"""
API Configuration

Environment-based configuration for the SKYT API.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Application settings loaded from environment."""
    
    # API Settings
    api_title: str = "SKYT API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://localhost/skyt"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # JWT Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Rate Limits
    rate_limit_requests_per_minute: int = 60
    rate_limit_jobs_per_day_free: int = 10
    rate_limit_jobs_per_day_pro: int = 1000
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            api_title=os.getenv("SKYT_API_TITLE", cls.api_title),
            api_version=os.getenv("SKYT_API_VERSION", cls.api_version),
            debug=os.getenv("SKYT_DEBUG", "false").lower() == "true",
            host=os.getenv("SKYT_HOST", cls.host),
            port=int(os.getenv("SKYT_PORT", cls.port)),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            celery_broker_url=os.getenv("CELERY_BROKER_URL", cls.celery_broker_url),
            celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", cls.celery_result_backend),
            jwt_secret=os.getenv("JWT_SECRET", cls.jwt_secret),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", cls.jwt_expiration_hours)),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", cls.rate_limit_requests_per_minute)),
        )


# Global settings instance
settings = Settings.from_env()
