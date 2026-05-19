"""
Настройки приложения.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Habit Tracker"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/habits"
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    HABIT_DAYS_GOAL: int = 21   # количество дней для закрепления привычки

    class Config:
        env_file = ".env"

settings = Settings()