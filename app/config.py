"""
Application configuration using Pydantic Settings.
Loads from environment variables with validation.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Discount Engine API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - using str instead of PostgresDsn for simplicity
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/discount_engine"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Redis (Optional - for caching)
    REDIS_URL: Optional[str] = None
    REDIS_CACHE_TTL: int = 900  # 15 minutes
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Discount Engine Settings
    LOYALTY_PROGRAM_THRESHOLD: int = 5  # Number of purchases for loyalty eligibility
    LOYALTY_DISCOUNT_AMOUNT: int = 500  # Flat discount in rupees


# Global settings instance
settings = Settings()