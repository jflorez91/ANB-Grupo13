from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API
    APP_NAME: str = "ANBVideoManageAPI"
    DEBUG: bool = True
    SECRET_KEY: str = "anb-rising-stars-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "mysql+aiomysql://anb_app_user:StrongPassword123!@localhost/anb_rising_stars"
    
    # Redis (Celery broker)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File Storage
    UPLOAD_DIR: str = "/storage/uploads"
    PROCESSED_DIR: str = "/storage/processed"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = ["mp4"]
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000","http://localhost:8000"]
    
    # Video Processing
    MAX_VIDEO_DURATION: int = 480  # 5 minutos máximo original
    TARGET_DURATION: int = 30      # 30 segundos procesado
    TARGET_RESOLUTION: str = "1280x720"
    
    class Config:
        env_file = ".env"

settings = Settings()