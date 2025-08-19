"""
Configuration settings for the application
"""

from typing import List
from pydantic_settings import BaseSettings
import os
from pathlib import Path

# Get the base directory (2 levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "MJ Estimate API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8501",
        "http://127.0.0.1:3000",
    ]
    
    # Database Settings (Supabase)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # PDF Generation
    PDF_OUTPUT_DIR: Path = BASE_DIR / "data" / "pdfs"
    TEMPLATE_DIR: Path = BASE_DIR / "templates"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)