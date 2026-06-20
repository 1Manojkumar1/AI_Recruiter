"""
Application settings loaded from environment variables.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    APP_NAME: str = "AI Candidate Ranking System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Data paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROCESSED_CANDIDATES_PATH: Path = BASE_DIR / "processed_candidates.jsonl"

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # Retrieval
    DEFAULT_TOP_K: int = 100
    DEFAULT_TOP_N: int = 20
    MAX_TOP_N: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
