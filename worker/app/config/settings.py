from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://ANBAdmin:ANB12345@db-instance-anb.cra7zjgxuryo.us-east-1.rds.amazonaws.com:3306/anb_rising_stars"
    DEBUG: bool = False
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # File Storage
    UPLOAD_DIR: str = "/storage/uploads"
    PROCESSED_DIR: str = "/storage/processed"
    
    # Video Processing
    MAX_VIDEO_DURATION: int = 480
    TARGET_DURATION: int = 30
    TARGET_RESOLUTION: str = "1280x720"

    # Amazon S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_SESSION_TOKEN: str = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str

    # S3 Paths
    S3_UPLOAD_PREFIX: str = "uploads/videos/originales"
    S3_PROCESSED_PREFIX: str = "processed/videos"
    
    class Config:
        env_file = ".env"

settings = Settings()