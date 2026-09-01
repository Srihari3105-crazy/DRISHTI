"""
DRISHTI-LENS Backend Configuration
Pydantic Settings for environment-based configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://drishti:drishti_dev@localhost:5432/drishti_lens"

    # JWT
    JWT_SECRET: str = "dev-secret-change-in-prod-32-chars-minimum-length"
    JWT_ALGO: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MIN: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # NATS
    NATS_URL: str = "nats://localhost:4222"

    # File paths
    UPLOAD_DIR: str = "./uploads"
    MODEL_DIR: str = "./assets/models"
    DEMO_IMAGES_DIR: str = "./assets/demo"

    # Seed CSVs
    DOCTOR_CSV_PATH: str = "./assets/seed/doctors.csv"
    HOSPITAL_CSV_PATH: str = "./assets/seed/hospitals.csv"
    OFFICER_CSV_PATH: str = "./assets/seed/officers.csv"
    PATIENT_CSV_PATH: str = "./assets/seed/patients.csv"

    # OTP (mock for MVP)
    OTP_EXPIRY_SECONDS: int = 300
    OTP_LENGTH: int = 6

    # App
    APP_NAME: str = "DRISHTI-LENS"
    APP_VERSION: str = "1.0.0-mvp"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
