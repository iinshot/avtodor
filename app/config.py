from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path.home() / ".autodor"
    BASE_DIR.mkdir(exist_ok=True)
    ENV_PATH = BASE_DIR / ".env"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    HOST: str = os.getenv("DB_HOST")
    PORT: int = os.getenv("PORT")
    DEBUG: bool = True
    AVTODOR_USERNAME: str = os.getenv("AVTODOR_USERNAME")
    AVTODOR_PASSWORD: str = os.getenv("AVTODOR_PASSWORD")

    model_config = ConfigDict(
        env_file=ENV_PATH if ENV_PATH.exists() else None,
        env_file_encoding="utf-8"
    )

settings = Settings()